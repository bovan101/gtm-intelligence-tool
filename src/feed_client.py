from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import quote_plus

import feedparser
import pandas as pd
import requests

MARKET_OPTIONS = {
    "United States": {"hl": "en-US", "gl": "US", "ceid": "US:en"},
    "United Kingdom": {"hl": "en-GB", "gl": "GB", "ceid": "GB:en"},
    "Germany": {"hl": "en", "gl": "DE", "ceid": "DE:en"},
    "Australia": {"hl": "en-AU", "gl": "AU", "ceid": "AU:en"},
}


class FeedError(RuntimeError):
    """Raised when the public RSS feed cannot be collected or parsed."""


@dataclass(frozen=True)
class FeedConfig:
    timeout_seconds: float = 12.0
    user_agent: str = "EVLaunchIntelligence/2.0 (public portfolio research)"


def _published_datetime(entry: object) -> datetime | None:
    parsed = getattr(entry, "published_parsed", None)
    if parsed is None:
        return None
    return datetime.fromtimestamp(calendar.timegm(parsed), tz=timezone.utc)


def _source_name(entry: object) -> str:
    source = getattr(entry, "source", None)
    if isinstance(source, dict):
        return str(source.get("title") or "Unknown source")
    return "Unknown source"


def _source_homepage(entry: object) -> str:
    source = getattr(entry, "source", None)
    if isinstance(source, dict):
        return str(source.get("href") or "")
    return ""


def _clean_entry_title(entry: object, source: str) -> str:
    title = str(getattr(entry, "title", ""))
    suffix = f" - {source}"
    return (
        title[: -len(suffix)].strip()
        if source != "Unknown source" and title.endswith(suffix)
        else title
    )


def build_feed_url(query: str, market_name: str) -> str:
    if market_name not in MARKET_OPTIONS:
        raise ValueError(f"Unsupported market: {market_name}")
    locale = MARKET_OPTIONS[market_name]
    return (
        "https://news.google.com/rss/search"
        f"?q={quote_plus(query)}"
        f"&hl={locale['hl']}&gl={locale['gl']}&ceid={locale['ceid']}"
    )


def fetch_google_news(
    query: str,
    market_name: str,
    limit: int = 20,
    config: FeedConfig | None = None,
    product: str | None = None,
) -> pd.DataFrame:
    """Fetch public Google News RSS metadata for one query."""
    clean_query = query.strip()
    if not clean_query:
        raise ValueError("Query cannot be empty")
    if limit < 1 or limit > 100:
        raise ValueError("Limit must be between 1 and 100")

    active_config = config or FeedConfig()
    url = build_feed_url(clean_query, market_name)

    try:
        response = requests.get(
            url,
            timeout=active_config.timeout_seconds,
            headers={"User-Agent": active_config.user_agent},
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise FeedError(f"Unable to collect the public RSS feed: {exc}") from exc

    feed = feedparser.parse(response.content)
    if feed.bozo and not feed.entries:
        raise FeedError(f"Unable to parse the public RSS feed: {feed.bozo_exception}")

    rows = []
    for entry in feed.entries[:limit]:
        source = _source_name(entry)
        rows.append(
            {
                "query": clean_query,
                "product": product or clean_query,
                "title": _clean_entry_title(entry, source),
                "source": source,
                "source_homepage": _source_homepage(entry),
                "url": getattr(entry, "link", ""),
                "published_at": _published_datetime(entry),
                "snippet": getattr(entry, "summary", ""),
                "market": market_name,
                "language": "English",
                "provider": "Google News RSS",
                "data_mode": "live_public_rss",
            }
        )

    return pd.DataFrame(rows)
