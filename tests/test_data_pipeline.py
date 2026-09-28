from datetime import date, datetime, timezone

import pandas as pd

from scripts.collect_news import date_windows, dated_query
from src.data_pipeline import (
    enrich_records,
    is_product_relevant,
    merge_records,
    normalise_url,
    source_classification,
)


def test_url_normalisation_removes_tracking_only() -> None:
    url = "https://Example.com/story?utm_source=x&section=ev#top"
    assert normalise_url(url) == "https://example.com/story?section=ev"
    assert normalise_url("javascript:alert(1)") == ""


def test_source_quality_uses_publisher_provenance() -> None:
    assert source_classification("BMW Group", "https://www.press.bmwgroup.com") == (
        "Official newsroom",
        "Official",
        True,
    )
    assert source_classification("Reuters") == (
        "Independent media",
        "Curated independent",
        True,
    )
    assert source_classification("Example Vehicle Leasing") == (
        "Independent media",
        "Unverified public",
        False,
    )


def test_product_relevance_requires_all_term_groups() -> None:
    assert is_product_relevant("BMW iX3", "BMW iX3 road test")
    assert is_product_relevant("Audi Q6 e-tron", "Audi Q6 e-tron charging review")
    assert not is_product_relevant("Audi Q6 e-tron", "Audi Q6 petrol review")
    assert not is_product_relevant("Porsche Macan Electric", "Used Porsche Macan")


def test_enrichment_and_merge_are_idempotent() -> None:
    raw = pd.DataFrame(
        [
            {
                "query": '"BMW iX3"',
                "product": "BMW iX3",
                "title": "BMW iX3 charging review",
                "source": "Reuters",
                "source_homepage": "https://reuters.com",
                "url": "https://reuters.com/story?utm_source=test",
                "published_at": "2025-09-06T08:00:00Z",
                "snippet": "The BMW iX3 battery range is reviewed.",
                "market": "United Kingdom",
            }
        ]
    )
    first_time = datetime(2026, 9, 27, tzinfo=timezone.utc)
    second_time = datetime(2026, 9, 28, tzinfo=timezone.utc)
    first = enrich_records(raw, collected_at=first_time)
    second = enrich_records(raw, collected_at=second_time)
    merged = merge_records(first, second)
    assert len(merged) == 1
    assert merged.loc[0, "source_tier"] == "Curated independent"
    assert pd.Timestamp(merged.loc[0, "collected_at"]) == pd.Timestamp(first_time)
    assert pd.Timestamp(merged.loc[0, "last_seen_at"]) == pd.Timestamp(second_time)


def test_prelaunch_records_are_removed_during_merge() -> None:
    frame = pd.DataFrame(
        {
            "record_id": ["old"],
            "published_at": ["2025-09-04T08:00:00Z"],
            "collected_at": ["2026-09-28T08:00:00Z"],
            "last_seen_at": ["2026-09-28T08:00:00Z"],
            "product": ["BMW iX3"],
        }
    )
    assert merge_records(pd.DataFrame(), frame).empty


def test_date_windows_and_queries_cover_boundaries() -> None:
    windows = date_windows(date(2025, 9, 5), date(2026, 1, 5), months=3)
    assert windows == [
        (date(2025, 9, 5), date(2025, 12, 4)),
        (date(2025, 12, 5), date(2026, 1, 5)),
    ]
    query = dated_query('"BMW iX3"', windows[0][0], windows[0][1])
    assert "after:2025-09-04" in query
    assert "before:2025-12-05" in query
