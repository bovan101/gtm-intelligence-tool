from __future__ import annotations

import argparse
import json
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

from src.data_pipeline import (
    COLLECTION_MARKETS,
    LAUNCH_DATE,
    PRODUCT_QUERIES,
    enrich_records,
    merge_records,
)
from src.feed_client import FeedError, fetch_google_news

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "public_coverage.csv"
STATUS_PATH = ROOT / "data" / "collection_status.json"


def add_months(value: date, months: int) -> date:
    month_index = value.year * 12 + value.month - 1 + months
    year, month_zero = divmod(month_index, 12)
    month = month_zero + 1
    month_lengths = [
        31,
        29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28,
        31,
        30,
        31,
        30,
        31,
        31,
        30,
        31,
        30,
        31,
    ]
    return date(year, month, min(value.day, month_lengths[month - 1]))


def date_windows(start: date, end: date, months: int) -> list[tuple[date, date]]:
    """Return inclusive date chunks without gaps."""
    windows: list[tuple[date, date]] = []
    cursor = start
    while cursor <= end:
        next_cursor = add_months(cursor, months)
        window_end = min(end, next_cursor - timedelta(days=1))
        windows.append((cursor, window_end))
        cursor = window_end + timedelta(days=1)
    return windows


def dated_query(base_query: str, start: date, end: date) -> str:
    """Build an inclusive Google News date query using exclusive operators."""
    after = start - timedelta(days=1)
    before = end + timedelta(days=1)
    return f"{base_query} after:{after.isoformat()} before:{before.isoformat()}"


def collect_window(
    product: str,
    market: str,
    start: date,
    end: date,
    limit: int,
    retries: int = 2,
) -> pd.DataFrame:
    query = dated_query(PRODUCT_QUERIES[product], start, end)
    for attempt in range(retries + 1):
        try:
            return fetch_google_news(query, market, limit=limit, product=product)
        except FeedError:
            if attempt == retries:
                raise
            time.sleep(1.5 * (attempt + 1))
    return pd.DataFrame()


def read_existing() -> pd.DataFrame:
    if not DATA_PATH.exists():
        return pd.DataFrame()
    return pd.read_csv(DATA_PATH)


def write_dataset(frame: pd.DataFrame) -> None:
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary = DATA_PATH.with_suffix(".tmp.csv")
    frame.to_csv(temporary, index=False)
    temporary.replace(DATA_PATH)


def write_status(payload: dict[str, object]) -> None:
    STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary = STATUS_PATH.with_suffix(".tmp.json")
    temporary.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    temporary.replace(STATUS_PATH)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Collect traceable EV public-news records."
    )
    parser.add_argument("--mode", choices=("backfill", "daily"), default="daily")
    parser.add_argument("--start", type=date.fromisoformat)
    parser.add_argument(
        "--end", type=date.fromisoformat, default=datetime.now(timezone.utc).date()
    )
    parser.add_argument("--chunk-months", type=int, default=3)
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--pause", type=float, default=0.35)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.chunk_months < 1 or args.chunk_months > 12:
        raise ValueError("--chunk-months must be between 1 and 12")
    if args.mode == "daily":
        start = args.start or (args.end - timedelta(days=2))
        windows = [(max(LAUNCH_DATE, start), args.end)]
    else:
        start = args.start or LAUNCH_DATE
        windows = date_windows(max(LAUNCH_DATE, start), args.end, args.chunk_months)

    collected_at = datetime.now(timezone.utc)
    frames: list[pd.DataFrame] = []
    errors: list[dict[str, str]] = []
    requests_attempted = 0
    raw_records = 0

    for product in PRODUCT_QUERIES:
        for market in COLLECTION_MARKETS:
            for window_start, window_end in windows:
                requests_attempted += 1
                try:
                    frame = collect_window(
                        product, market, window_start, window_end, args.limit
                    )
                    raw_records += len(frame)
                    if not frame.empty:
                        frames.append(frame)
                except FeedError as exc:
                    errors.append(
                        {
                            "product": product,
                            "market": market,
                            "window": f"{window_start}/{window_end}",
                            "error": str(exc),
                        }
                    )
                time.sleep(max(0.0, args.pause))

    incoming = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    incoming = enrich_records(incoming, collected_at=collected_at)
    existing_raw = read_existing()
    existing = enrich_records(existing_raw) if not existing_raw.empty else existing_raw
    merged = merge_records(existing, incoming) if not incoming.empty else existing

    if not merged.empty:
        write_dataset(merged)

    successful_requests = requests_attempted - len(errors)
    if successful_requests == 0:
        status = "failed"
    elif errors:
        status = "partial"
    else:
        status = "healthy"

    previous_status: dict[str, object] = {}
    if STATUS_PATH.exists():
        try:
            previous_status = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            previous_status = {}
    last_successful = (
        collected_at.isoformat()
        if successful_requests > 0 and not merged.empty
        else previous_status.get("last_successful_update")
    )
    dates = (
        pd.to_datetime(merged.get("published_at"), errors="coerce", utc=True)
        if not merged.empty
        else pd.Series(dtype="datetime64[ns, UTC]")
    )
    status_payload: dict[str, object] = {
        "status": status,
        "generated_at": collected_at.isoformat(),
        "last_successful_update": last_successful,
        "schedule": "daily",
        "provider": "Google News RSS",
        "requests_attempted": requests_attempted,
        "requests_succeeded": successful_requests,
        "raw_records_received": raw_records,
        "validated_records_received": len(incoming),
        "dataset_records": len(merged),
        "dataset_start": dates.min().date().isoformat()
        if not dates.empty and dates.notna().any()
        else None,
        "dataset_end": dates.max().date().isoformat()
        if not dates.empty and dates.notna().any()
        else None,
        "errors": errors[:20],
    }
    write_status(status_payload)
    print(json.dumps(status_payload, indent=2, ensure_ascii=False))
    return 0 if status != "failed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
