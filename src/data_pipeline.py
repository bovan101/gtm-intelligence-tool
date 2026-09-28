from __future__ import annotations

import hashlib
import json
import re
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import pandas as pd

LAUNCH_DATE = date(2025, 9, 5)
PRODUCT_QUERIES = {
    "BMW iX3": '"BMW iX3"',
    "Audi Q6 e-tron": '"Audi Q6 e-tron"',
    "Mercedes-Benz GLC Electric": '("Mercedes GLC Electric" OR "electric GLC")',
    "Porsche Macan Electric": '"Porsche Macan Electric"',
}
COLLECTION_MARKETS = ("United Kingdom", "Germany", "United States")
PRODUCT_REQUIRED_TERMS = {
    "BMW iX3": (("ix3",),),
    "Audi Q6 e-tron": (("q6",), ("e-tron", "etron")),
    "Mercedes-Benz GLC Electric": (("glc",), ("electric", "ev")),
    "Porsche Macan Electric": (("macan",), ("electric", "ev")),
}

OFFICIAL_SOURCE_NAMES = {
    "audi media center",
    "audi mediacenter",
    "bmw group",
    "bmw group pressclub",
    "bmw newsroom",
    "mercedes-benz",
    "mercedes-benz group",
    "porsche newsroom",
}
OFFICIAL_DOMAINS = {
    "audi-mediacenter.com",
    "bmwgroup.com",
    "group-media.mercedes-benz.com",
    "media.mercedes-benz.com",
    "newsroom.porsche.com",
    "press.bmwgroup.com",
}

CURATED_INDEPENDENT_MARKERS = (
    "adac",
    "ars technica",
    "auto bild",
    "auto express",
    "auto motor und sport",
    "autocar",
    "automotive news",
    "autotrader",
    "bbc",
    "bloomberg",
    "business insider",
    "car and driver",
    "car magazine",
    "carwow",
    "cnbc",
    "consumer reports",
    "electrek",
    "financial times",
    "fleet news",
    "forbes",
    "handelsblatt",
    "insideevs",
    "motor trend",
    "motor1",
    "road & track",
    "reuters",
    "techcrunch",
    "the drive",
    "the guardian",
    "the independent",
    "the verge",
    "this is money",
    "top gear",
    "what car",
    "wired",
)

LOW_VALUE_SOURCE_MARKERS = (
    "leasing",
    "dealer",
    "dealership",
    "inventory",
    "vehicle contracts",
)


def normalise_url(url: str) -> str:
    """Remove tracking parameters while preserving an evidence-link identity."""
    parts = urlsplit(str(url).strip())
    if parts.scheme not in {"http", "https"}:
        return ""
    query = [
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if not key.lower().startswith("utm_")
        and key.lower() not in {"gclid", "fbclid", "mc_cid", "mc_eid"}
    ]
    return urlunsplit(
        (parts.scheme.lower(), parts.netloc.lower(), parts.path, urlencode(query), "")
    )


def normalise_title(title: str) -> str:
    """Create a conservative title fingerprint for duplicate detection."""
    return re.sub(r"[^a-z0-9]+", " ", str(title).lower()).strip()


def source_classification(
    source: str, source_homepage: str = ""
) -> tuple[str, str, bool]:
    """Return source type, public quality tier, and core-KPI eligibility."""
    lowered = source.casefold().strip()
    hostname = (
        urlsplit(str(source_homepage or "")).netloc.casefold().removeprefix("www.")
    )
    if lowered in OFFICIAL_SOURCE_NAMES or any(
        hostname == domain or hostname.endswith(f".{domain}")
        for domain in OFFICIAL_DOMAINS
    ):
        return "Official newsroom", "Official", True
    if any(marker in lowered for marker in LOW_VALUE_SOURCE_MARKERS):
        return "Independent media", "Unverified public", False
    if any(marker in lowered for marker in CURATED_INDEPENDENT_MARKERS):
        return "Independent media", "Curated independent", True
    return "Independent media", "Unverified public", False


def is_product_relevant(product: str, title: str, snippet: str = "") -> bool:
    """Require each product-specific term group to appear in title or snippet."""
    text = f"{title} {snippet}".casefold()
    groups = PRODUCT_REQUIRED_TERMS.get(product, ())
    return bool(groups) and all(any(term in text for term in group) for group in groups)


def record_id(product: str, market: str, source: str, title: str) -> str:
    """Build a stable identifier for one market-discovery occurrence."""
    identity = "|".join(
        [
            product.casefold(),
            market.casefold(),
            source.casefold(),
            normalise_title(title),
        ]
    )
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()[:24]


def enrich_records(
    frame: pd.DataFrame, collected_at: datetime | None = None
) -> pd.DataFrame:
    """Validate provenance fields and attach durable quality metadata."""
    if frame.empty:
        return frame.copy()
    now = collected_at or datetime.now(timezone.utc)
    data = frame.copy()
    if "collected_at" not in data:
        data["collected_at"] = now.isoformat()
    else:
        data["collected_at"] = data["collected_at"].fillna(now.isoformat())
    if "last_seen_at" not in data:
        data["last_seen_at"] = now.isoformat()
    else:
        data["last_seen_at"] = data["last_seen_at"].fillna(now.isoformat())
    if "provider" not in data:
        data["provider"] = "Google News RSS"
    if "source_homepage" not in data:
        data["source_homepage"] = ""
    if "language" not in data:
        data["language"] = "English"

    classifications = [
        source_classification(source, homepage)
        for source, homepage in zip(
            data["source"], data["source_homepage"], strict=True
        )
    ]
    data["source_type"] = [value[0] for value in classifications]
    data["source_tier"] = [value[1] for value in classifications]
    data["core_eligible"] = [value[2] for value in classifications]
    data["url"] = data["url"].map(normalise_url)
    data["record_id"] = [
        record_id(product, market, source, title)
        for product, market, source, title in zip(
            data["product"], data["market"], data["source"], data["title"], strict=True
        )
    ]
    data["data_mode"] = "real_public_news"
    return data.loc[
        data["url"].str.startswith(("http://", "https://"))
        & data["title"].astype(str).str.strip().ne("")
        & data["source"].astype(str).str.strip().ne("")
        & pd.Series(
            [
                is_product_relevant(product, title, snippet)
                for product, title, snippet in zip(
                    data["product"], data["title"], data["snippet"], strict=True
                )
            ],
            index=data.index,
        )
    ].reset_index(drop=True)


def merge_records(existing: pd.DataFrame, incoming: pd.DataFrame) -> pd.DataFrame:
    """Merge idempotently while preserving first collection and latest observation."""
    frames = [frame.copy() for frame in (existing, incoming) if not frame.empty]
    if not frames:
        return pd.DataFrame()
    combined = pd.concat(frames, ignore_index=True)
    combined["published_at"] = pd.to_datetime(
        combined["published_at"], errors="coerce", utc=True, format="mixed"
    )
    combined = combined.loc[combined["published_at"].dt.date.ge(LAUNCH_DATE)].copy()
    combined["collected_at"] = pd.to_datetime(
        combined["collected_at"], errors="coerce", utc=True, format="mixed"
    )
    combined["last_seen_at"] = pd.to_datetime(
        combined["last_seen_at"], errors="coerce", utc=True, format="mixed"
    )
    first_seen = combined.groupby("record_id")["collected_at"].min()
    last_seen = combined.groupby("record_id")["last_seen_at"].max()
    combined = combined.sort_values("last_seen_at").drop_duplicates(
        "record_id", keep="last"
    )
    combined["collected_at"] = combined["record_id"].map(first_seen)
    combined["last_seen_at"] = combined["record_id"].map(last_seen)
    combined = combined.sort_values(
        ["published_at", "product"], ascending=[False, True]
    )
    return combined.reset_index(drop=True)


def load_status(path: Path) -> dict[str, object]:
    """Load collection health metadata without making the dashboard fragile."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}
