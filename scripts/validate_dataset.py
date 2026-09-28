from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.data_pipeline import LAUNCH_DATE, normalise_url

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "public_coverage.csv"
STATUS_PATH = ROOT / "data" / "collection_status.json"
REQUIRED_COLUMNS = {
    "record_id",
    "product",
    "market",
    "title",
    "source",
    "source_homepage",
    "url",
    "published_at",
    "collected_at",
    "last_seen_at",
    "provider",
    "source_type",
    "source_tier",
    "core_eligible",
}


def validate_dataset(frame: pd.DataFrame) -> list[str]:
    errors: list[str] = []
    missing = REQUIRED_COLUMNS.difference(frame.columns)
    if missing:
        return [f"Missing required columns: {sorted(missing)}"]
    if frame.empty:
        return ["Dataset is empty"]
    if frame["record_id"].duplicated().any():
        errors.append("record_id values are not unique")
    if frame["title"].fillna("").str.strip().eq("").any():
        errors.append("One or more records have an empty title")
    if frame["source"].fillna("").str.strip().eq("").any():
        errors.append("One or more records have an empty publisher")
    if frame["url"].map(normalise_url).eq("").any():
        errors.append("One or more evidence URLs are invalid")

    published = pd.to_datetime(
        frame["published_at"], errors="coerce", utc=True, format="mixed"
    )
    collected = pd.to_datetime(
        frame["collected_at"], errors="coerce", utc=True, format="mixed"
    )
    last_seen = pd.to_datetime(
        frame["last_seen_at"], errors="coerce", utc=True, format="mixed"
    )
    if published.isna().any() or collected.isna().any() or last_seen.isna().any():
        errors.append("One or more provenance timestamps are invalid")
    if published.dropna().dt.date.lt(LAUNCH_DATE).any():
        errors.append("Dataset contains pre-launch records")
    if (last_seen.dropna() < collected.dropna()).any():
        errors.append("A last_seen_at value precedes collected_at")

    valid_tiers = {"Official", "Curated independent", "Unverified public"}
    unknown_tiers = set(frame["source_tier"].dropna()) - valid_tiers
    if unknown_tiers:
        errors.append(f"Unknown source tiers: {sorted(unknown_tiers)}")
    return errors


def main() -> int:
    if not DATA_PATH.exists():
        print("Dataset file is missing")
        return 1
    frame = pd.read_csv(DATA_PATH)
    errors = validate_dataset(frame)
    status = (
        json.loads(STATUS_PATH.read_text(encoding="utf-8"))
        if STATUS_PATH.exists()
        else {}
    )
    report = {
        "records": len(frame),
        "products": int(frame["product"].nunique()) if "product" in frame else 0,
        "markets": int(frame["market"].nunique()) if "market" in frame else 0,
        "dataset_start": status.get("dataset_start"),
        "dataset_end": status.get("dataset_end"),
        "collection_status": status.get("status", "unknown"),
        "validation_errors": errors,
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
