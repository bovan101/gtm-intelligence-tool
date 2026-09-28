import pandas as pd

from src.analysis import (
    analyze_dataframe,
    classify_risk,
    classify_theme,
    classify_themes,
    market_theme_matrix,
    message_pull_through,
    score_sentiment,
    share_of_voice,
)


def test_positive_and_negative_words_change_score() -> None:
    assert score_sentiment("A reliable and innovative upgrade") > 0
    assert score_sentiment("An expensive product with a safety issue") < 0


def test_theme_classification_supports_multiple_messages() -> None:
    assert classify_theme("battery range and fast charging") == "Range & charging"
    assert (
        classify_theme("panoramic display and cockpit interface")
        == "Digital experience"
    )
    assert classify_themes("battery charging and software update") == [
        "Range & charging",
        "Software & connectivity",
    ]


def test_risk_requires_critical_language() -> None:
    assert classify_risk("An expensive price creates concern", -2) == "Price pressure"
    assert classify_risk("An impressive interface", 1) == "No flagged risk"


def test_analysis_normalises_enriches_and_deduplicates() -> None:
    frame = pd.DataFrame(
        [
            {
                "query": "BMW iX3",
                "title": "A reliable iX3 with fast charging",
                "source": "Demo Source",
                "url": "https://example.com/review",
                "published_at": "2026-09-01",
                "snippet": "Panoramic display and easy interface",
                "market": "United Kingdom",
            },
            {
                "query": "BMW iX3",
                "title": "A reliable iX3 with fast charging",
                "source": "Demo Source",
                "url": "https://example.com/review",
                "published_at": "2026-09-01",
                "snippet": "Panoramic display and easy interface",
                "market": "United Kingdom",
            },
        ]
    )
    result = analyze_dataframe(frame)
    assert len(result) == 1
    assert result.loc[0, "product"] == "BMW iX3"
    assert result.loc[0, "sentiment"] == "Positive"
    assert result.loc[0, "data_mode"] == "live_public_rss"
    assert "Range & charging" in result.loc[0, "themes"]
    assert "Digital experience" in result.loc[0, "themes"]


def test_share_of_voice_and_message_pull_through() -> None:
    frame = pd.DataFrame(
        {
            "product": ["BMW iX3", "BMW iX3", "Competitor"],
            "themes": [
                "Range & charging | Digital experience",
                "Range & charging",
                "Price & value",
            ],
            "market": ["UK", "DE", "UK"],
        }
    )
    sov = share_of_voice(frame)
    pull_through = message_pull_through(frame, "BMW iX3")
    assert sov.loc[sov["product"].eq("BMW iX3"), "share_of_voice"].iloc[0] == 2 / 3
    assert pull_through.iloc[0].to_dict() == {
        "theme": "Range & charging",
        "mentions": 2,
        "coverage_rate": 1.0,
    }


def test_market_theme_matrix_uses_market_level_base() -> None:
    frame = pd.DataFrame(
        {
            "product": ["BMW iX3", "BMW iX3", "BMW iX3"],
            "themes": [
                "Range & charging | Digital experience",
                "Range & charging",
                "Design",
            ],
            "market": ["UK", "UK", "DE"],
        }
    )
    matrix = market_theme_matrix(frame, "BMW iX3")
    assert matrix.loc["UK", "Range & charging"] == 1.0
    assert matrix.loc["UK", "Digital experience"] == 0.5
    assert matrix.loc["DE", "Design"] == 1.0
