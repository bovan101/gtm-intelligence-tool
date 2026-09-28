from __future__ import annotations

import html
import re
from collections.abc import Iterable

import pandas as pd

POSITIVE_WORDS = {
    "best",
    "breakthrough",
    "confident",
    "easy",
    "efficient",
    "fast",
    "impressive",
    "improved",
    "innovative",
    "intuitive",
    "leading",
    "powerful",
    "recommended",
    "refined",
    "reliable",
    "strong",
    "upgrade",
}

NEGATIVE_WORDS = {
    "complaint",
    "complex",
    "concern",
    "controversial",
    "difficult",
    "expensive",
    "fail",
    "issue",
    "limited",
    "problem",
    "recall",
    "risk",
    "slow",
    "uncertain",
    "weak",
}

THEME_KEYWORDS = {
    "Range & charging": {
        "800v",
        "battery",
        "charge",
        "charging",
        "efficient",
        "efficiency",
        "range",
        "runtime",
    },
    "Digital experience": {
        "cockpit",
        "display",
        "idrive",
        "infotainment",
        "interface",
        "panoramic",
        "screen",
    },
    "Driving dynamics": {
        "agile",
        "cornering",
        "dynamics",
        "handling",
        "heart",
        "ride",
        "steering",
    },
    "Design": {"cabin", "design", "exterior", "interior", "lighting", "styling"},
    "Sustainability": {
        "carbon",
        "circular",
        "emissions",
        "fossil",
        "recycled",
        "sustainable",
        "sustainability",
    },
    "ADAS & safety": {
        "adas",
        "assist",
        "assistance",
        "automated",
        "safe",
        "safety",
        "sensor",
    },
    "Practicality": {
        "boot",
        "comfort",
        "family",
        "practical",
        "seats",
        "space",
        "storage",
    },
    "Price & value": {
        "affordable",
        "cost",
        "deal",
        "discount",
        "expensive",
        "finance",
        "price",
        "value",
    },
    "Performance": {
        "acceleration",
        "fast",
        "performance",
        "power",
        "powerful",
        "speed",
        "torque",
    },
    "Software & connectivity": {
        "app",
        "connected",
        "connectivity",
        "ota",
        "software",
        "update",
        "voice",
    },
}

RISK_KEYWORDS = {
    "Price pressure": {"cost", "expensive", "price", "value"},
    "Interface usability": {"complex", "difficult", "interface", "usability"},
    "Availability": {"availability", "delay", "delivery", "limited", "waiting"},
    "Range confidence": {"battery", "charging", "range", "slow"},
    "Design response": {"controversial", "design", "styling"},
    "Reliability": {"complaint", "fail", "issue", "problem", "recall", "reliability"},
}


def clean_text(value: object) -> str:
    """Remove simple markup and normalise whitespace."""
    text = html.unescape(str(value or ""))
    text = re.sub(r"<[^>]+>", " ", text)
    return " ".join(text.split())


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9][a-z0-9-]*", text.lower())


def score_sentiment(text: str) -> int:
    """Return a transparent lexical tone-proxy score."""
    tokens = tokenize(text)
    return sum(token in POSITIVE_WORDS for token in tokens) - sum(
        token in NEGATIVE_WORDS for token in tokens
    )


def sentiment_label(score: int) -> str:
    if score > 0:
        return "Positive"
    if score < 0:
        return "Negative"
    return "Neutral"


def classify_themes(text: str, max_themes: int = 3) -> list[str]:
    """Return up to three matching commercial themes in score order."""
    tokens = set(tokenize(text))
    scored = [
        (theme, len(tokens.intersection(keywords)))
        for theme, keywords in THEME_KEYWORDS.items()
    ]
    matches = [
        theme
        for theme, score in sorted(scored, key=lambda item: (-item[1], item[0]))
        if score > 0
    ]
    return matches[:max_themes] or ["General coverage"]


def classify_theme(text: str) -> str:
    """Return the strongest commercial theme for backward compatibility."""
    return classify_themes(text, max_themes=1)[0]


def classify_risk(text: str, sentiment_score: int) -> str:
    """Classify a review-prioritisation signal when critical language appears."""
    if sentiment_score >= 0:
        return "No flagged risk"
    tokens = set(tokenize(text))
    scored = [
        (risk, len(tokens.intersection(keywords)))
        for risk, keywords in RISK_KEYWORDS.items()
    ]
    risk, score = max(scored, key=lambda item: item[1])
    return risk if score else "Other critical signal"


def _require_columns(columns: Iterable[str]) -> None:
    required = {"query", "title", "source", "url", "published_at"}
    missing = required.difference(columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")


def analyze_dataframe(frame: pd.DataFrame) -> pd.DataFrame:
    """Normalise, classify, and deduplicate a public-coverage dataset."""
    _require_columns(frame.columns)
    data = frame.copy()
    defaults = {
        "snippet": "",
        "data_mode": "live_public_rss",
        "product": "",
        "market": "Unspecified",
        "source_type": "Independent media",
        "event": "",
        "source_tier": "Synthetic demo",
        "core_eligible": True,
        "provider": "Synthetic demo",
        "source_homepage": "",
        "collected_at": "",
        "last_seen_at": "",
        "language": "English",
    }
    for column, default in defaults.items():
        if column not in data:
            data[column] = default

    for column in [
        "query",
        "product",
        "title",
        "source",
        "url",
        "snippet",
        "market",
        "source_type",
        "event",
        "source_tier",
        "provider",
        "source_homepage",
        "language",
    ]:
        data[column] = data[column].map(clean_text)

    data["product"] = data["product"].mask(data["product"].eq(""), data["query"])
    data["published_at"] = pd.to_datetime(
        data["published_at"], errors="coerce", utc=True, format="mixed"
    )
    combined_text = data["title"] + " " + data["snippet"]
    data["sentiment_score"] = combined_text.map(score_sentiment)
    data["sentiment"] = data["sentiment_score"].map(sentiment_label)
    theme_lists = combined_text.map(classify_themes)
    data["primary_theme"] = theme_lists.map(lambda themes: themes[0])
    data["themes"] = theme_lists.map(lambda themes: " | ".join(themes))
    data["theme"] = data["primary_theme"]
    data["risk_signal"] = [
        classify_risk(text, score)
        for text, score in zip(combined_text, data["sentiment_score"], strict=True)
    ]
    data["is_official"] = data["source_type"].str.lower().eq("official newsroom")

    if "record_id" in data and data["record_id"].astype(str).str.strip().ne("").any():
        return data.drop_duplicates(subset=["record_id"]).reset_index(drop=True)
    return data.drop_duplicates(subset=["query", "url"]).reset_index(drop=True)


def share_of_voice(data: pd.DataFrame) -> pd.DataFrame:
    """Calculate product-level mention count and share of voice."""
    if data.empty:
        return pd.DataFrame(columns=["product", "mentions", "share_of_voice"])
    result = (
        data.groupby("product", as_index=False)
        .size()
        .rename(columns={"size": "mentions"})
        .sort_values("mentions", ascending=False)
    )
    result["share_of_voice"] = result["mentions"] / result["mentions"].sum()
    return result.reset_index(drop=True)


def message_pull_through(data: pd.DataFrame, product: str) -> pd.DataFrame:
    """Calculate multi-label message penetration for one product."""
    product_data = data.loc[data["product"].eq(product)].copy()
    if product_data.empty:
        return pd.DataFrame(columns=["theme", "mentions", "coverage_rate"])
    exploded = product_data.assign(
        theme=product_data["themes"].str.split(" | ", regex=False)
    ).explode("theme")
    result = (
        exploded.loc[exploded["theme"].ne("General coverage")]
        .groupby("theme", as_index=False)
        .size()
        .rename(columns={"size": "mentions"})
    )
    result["coverage_rate"] = result["mentions"] / len(product_data)
    return result.sort_values(
        ["coverage_rate", "theme"], ascending=[False, True]
    ).reset_index(drop=True)


def market_theme_matrix(data: pd.DataFrame, product: str) -> pd.DataFrame:
    """Return message penetration by market for a selected product."""
    product_data = data.loc[data["product"].eq(product)].copy()
    if product_data.empty:
        return pd.DataFrame()
    exploded = product_data.assign(
        theme=product_data["themes"].str.split(" | ", regex=False)
    ).explode("theme")
    exploded = exploded.loc[exploded["theme"].ne("General coverage")]
    counts = exploded.groupby(["market", "theme"]).size().rename("mentions")
    bases = product_data.groupby("market").size().rename("market_total")
    matrix = counts.reset_index().join(bases, on="market")
    matrix["coverage_rate"] = matrix["mentions"] / matrix["market_total"]
    return matrix.pivot(index="market", columns="theme", values="coverage_rate").fillna(
        0
    )
