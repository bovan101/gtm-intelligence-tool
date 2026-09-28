from __future__ import annotations

from datetime import datetime, timedelta, timezone
from html import escape
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.analysis import (
    analyze_dataframe,
    market_theme_matrix,
    message_pull_through,
    share_of_voice,
)
from src.data_pipeline import LAUNCH_DATE, load_status
from src.i18n import (
    MARKET_LABELS,
    RISK_LABELS,
    SOURCE_TIER_LABELS,
    THEME_LABELS,
    TONE_LABELS,
    format_date,
    format_timestamp,
    localise_value,
    translate,
)

ROOT = Path(__file__).resolve().parent
DEMO_PATH = ROOT / "data" / "demo_mentions.csv"
REAL_PATH = ROOT / "data" / "public_coverage.csv"
STATUS_PATH = ROOT / "data" / "collection_status.json"
STYLE_PATH = ROOT / "assets" / "styles.css"
HERO_PRODUCT = "BMW iX3"
PRODUCT_COLOURS = {
    "BMW iX3": "#1265E8",
    "Audi Q6 e-tron": "#687386",
    "Mercedes-Benz GLC Electric": "#1C2635",
    "Porsche Macan Electric": "#B56A42",
}
CHART_CONFIG = {"displayModeBar": False, "responsive": True}


st.set_page_config(
    page_title="EV Launch Intelligence | iX3 Case Study",
    page_icon="EV",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(
    f"<style>{STYLE_PATH.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True
)


@st.cache_data(ttl=300, show_spinner=False)
def load_csv(path: str, modified_time: float) -> pd.DataFrame:
    """Load a snapshot while invalidating the cache when the file changes."""
    del modified_time
    return pd.read_csv(path)


def style_figure(figure: go.Figure, height: int = 380) -> go.Figure:
    figure.update_layout(
        height=height,
        margin={"l": 24, "r": 24, "t": 28, "b": 24},
        paper_bgcolor="rgba(255,255,255,0)",
        plot_bgcolor="rgba(255,255,255,0)",
        font={
            "family": "Avenir Next, Helvetica Neue, sans-serif",
            "color": "#42536A",
            "size": 12,
        },
        legend={
            "title_text": "",
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "left",
            "x": 0,
        },
        hoverlabel={
            "bgcolor": "#102033",
            "font_color": "#FFFFFF",
            "bordercolor": "#102033",
        },
    )
    figure.update_xaxes(gridcolor="#E3E7EC", zeroline=False, linecolor="#C9D1DA")
    figure.update_yaxes(gridcolor="#E3E7EC", zeroline=False, linecolor="#C9D1DA")
    return figure


def metric_card(label: str, value: str, note: str, compact: bool = False) -> None:
    value_class = "metric-value compact" if compact else "metric-value"
    st.markdown(
        f'<div class="metric-card"><div class="metric-label">{escape(label)}</div>'
        f'<div class="{value_class}">{escape(value)}</div><div class="metric-note">{escape(note)}</div></div>',
        unsafe_allow_html=True,
    )


def section_header(index: str, title: str, note: str) -> None:
    st.markdown(
        f'<div class="section-kicker">{escape(index)}</div><div class="section-head">'
        f'<h2>{escape(title)}</h2><div class="section-note">{escape(note)}</div></div>',
        unsafe_allow_html=True,
    )


def local_theme(value: str, language: str) -> str:
    return localise_value(value, THEME_LABELS, language)


def local_risk(value: str, language: str) -> str:
    return localise_value(value, RISK_LABELS, language)


def parse_update_time(status: dict[str, object]) -> datetime | None:
    value = status.get("last_successful_update")
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


with st.sidebar:
    st.markdown('<div class="brand-mark">EV / GTM / 02</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sidebar-title">Launch Intelligence</div>', unsafe_allow_html=True
    )
    language_name = st.radio(
        "Language / 语言",
        ["中文", "English"],
        horizontal=True,
        label_visibility="collapsed",
    )
    language = "zh" if language_name == "中文" else "en"
    t = lambda key, **values: translate(key, language, **values)
    st.caption(t("portfolio_case"))
    st.markdown('<div class="sidebar-rule"></div>', unsafe_allow_html=True)

    source_labels = {
        "real": t("real_dataset"),
        "demo": t("synthetic_demo"),
    }
    mode = st.radio(
        t("data_source"),
        list(source_labels),
        format_func=lambda value: source_labels[value],
    )
    if st.button(t("refresh_data"), use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    if mode == "real":
        if not REAL_PATH.exists():
            st.error(t("no_real_data"))
            st.stop()
        raw_data = load_csv(str(REAL_PATH), REAL_PATH.stat().st_mtime)
        status = load_status(STATUS_PATH)
        st.caption(t("real_caption"))
    else:
        raw_data = load_csv(str(DEMO_PATH), DEMO_PATH.stat().st_mtime)
        status = {"status": "healthy", "provider": "Synthetic demo"}
        st.caption(t("demo_caption"))

    if raw_data.empty:
        st.warning(t("no_records"))
        st.stop()

    data = analyze_dataframe(raw_data)
    data["core_eligible"] = (
        data["core_eligible"].astype(str).str.lower().isin({"true", "1"})
    )

    st.markdown('<div class="sidebar-rule"></div>', unsafe_allow_html=True)
    st.markdown(f"#### {t('view_controls').upper()}")
    scope_labels = {
        "verified_independent": t("verified_independent"),
        "verified_all": t("verified_all"),
        "all_public": t("all_public"),
    }
    scope = st.radio(
        t("coverage_scope"),
        list(scope_labels),
        format_func=lambda value: scope_labels[value],
    )
    product_values = data["product"].drop_duplicates().tolist()
    product_options = sorted(
        product_values,
        key=lambda value: (
            list(PRODUCT_COLOURS).index(value)
            if value in PRODUCT_COLOURS
            else len(PRODUCT_COLOURS)
        ),
    )
    selected_products = st.multiselect(
        t("products"), product_options, default=product_options
    )
    market_options = sorted(data["market"].dropna().unique())
    selected_markets = st.multiselect(
        t("markets"),
        market_options,
        default=market_options,
        format_func=lambda value: localise_value(value, MARKET_LABELS, language),
    )
    dated = data["published_at"].dropna()
    if dated.empty:
        st.error(t("invalid_dates"))
        st.stop()
    min_date = dated.min().date()
    max_date = dated.max().date()
    if min_date == max_date:
        date_range = (min_date, max_date)
        st.caption(
            f"{t('coverage_window').upper()} · {format_date(min_date, language)}"
        )
    else:
        date_range = st.slider(
            t("coverage_window"),
            min_value=min_date,
            max_value=max_date,
            value=(min_date, max_date),
            format="YYYY-MM-DD",
        )
    st.markdown('<div class="sidebar-rule"></div>', unsafe_allow_html=True)
    st.caption(t("private_boundary"))


filtered = data.loc[
    data["product"].isin(selected_products)
    & data["market"].isin(selected_markets)
    & data["published_at"].dt.date.between(date_range[0], date_range[1])
].copy()
if scope == "verified_independent":
    filtered = filtered.loc[filtered["core_eligible"] & ~filtered["is_official"]].copy()
elif scope == "verified_all":
    filtered = filtered.loc[filtered["core_eligible"]].copy()

if filtered.empty:
    st.warning(t("no_records"))
    st.stop()

last_update = parse_update_time(status)
is_stale = mode == "real" and (
    last_update is None
    or datetime.now(timezone.utc) - last_update > timedelta(hours=36)
)
raw_health = str(status.get("status", "unknown"))
health_key = (
    "stale"
    if is_stale
    else raw_health
    if raw_health in {"healthy", "partial", "failed"}
    else "unknown"
)
health_label = t(health_key)
mode_label = t("real_mode_label") if mode == "real" else t("demo_mode_label")
last_update_label = (
    format_timestamp(last_update, language) if last_update else t("unknown")
)
status_dot = (
    "status-dot stale"
    if is_stale or raw_health in {"partial", "failed"}
    else "status-dot"
)

st.markdown(
    f"""
    <div class="hero">
        <div class="eyebrow">{escape(t("eyebrow"))}</div>
        <div class="hero-grid">
            <div><h1>{t("hero_title")}</h1><div class="hero-copy">{escape(t("hero_copy"))}</div></div>
            <div class="status-box">
                <div class="status-label">{escape(t("current_dataset"))}</div>
                <div class="status-value">{escape(mode_label)}</div>
                <div class="status-label" style="margin-top:.75rem">{escape(t("coverage_window"))}</div>
                <div class="status-value">{format_date(date_range[0], language)} — {format_date(date_range[1], language)}</div>
                <div class="status-label" style="margin-top:.75rem">{escape(t("source_health"))}</div>
                <div class="status-value status-line"><span class="{status_dot}"></span>{escape(health_label)}</div>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)
if is_stale:
    st.warning(t("stale_warning"))

st.markdown(
    f"""
    <div class="provenance-strip">
      <div class="provenance-item"><div class="provenance-label">{escape(t("data_source"))}</div><div class="provenance-value">{escape(t("provider_google") if mode == "real" else t("synthetic_demo"))}</div></div>
      <div class="provenance-item"><div class="provenance-label">{escape(t("last_updated"))}</div><div class="provenance-value">{escape(last_update_label)}</div></div>
      <div class="provenance-item"><div class="provenance-label">{escape(t("daily_frequency"))}</div><div class="provenance-value">{status.get("requests_succeeded", "—")} / {status.get("requests_attempted", "—")} requests</div></div>
      <div class="provenance-item"><div class="provenance-label">{escape(t("coverage_window"))}</div><div class="provenance-value">{format_date(LAUNCH_DATE, language)} → {format_date(max_date, language)}</div></div>
    </div>
    """,
    unsafe_allow_html=True,
)

sov = share_of_voice(filtered)
ix3_row = sov.loc[sov["product"].eq(HERO_PRODUCT)]
ix3_share = float(ix3_row["share_of_voice"].iloc[0]) if not ix3_row.empty else 0.0
pull_through = message_pull_through(filtered, HERO_PRODUCT)
top_message = pull_through.iloc[0] if not pull_through.empty else None
ix3_count = int((filtered["product"] == HERO_PRODUCT).sum())
independent_source_count = filtered.loc[~filtered["is_official"], "source"].nunique()

metric_columns = st.columns(4)
with metric_columns[0]:
    metric_card(
        t("filtered_mentions"),
        f"{len(filtered):,}",
        t("markets_in_view", count=len(selected_markets)),
    )
with metric_columns[1]:
    metric_card(
        t("independent_sources"),
        f"{independent_source_count:,}",
        t("unique_publishers"),
    )
with metric_columns[2]:
    metric_card(
        t("ix3_sov"),
        f"{ix3_share:.0%}",
        t("mentions_fraction", ix3=ix3_count, total=len(filtered)),
    )
with metric_columns[3]:
    if top_message is None:
        metric_card(t("lead_message"), t("no_data"), t("include_ix3"), compact=True)
    else:
        metric_card(
            t("lead_message"),
            local_theme(str(top_message["theme"]), language),
            t("present_in", rate=float(top_message["coverage_rate"])),
            compact=True,
        )

section_header(
    f"01 / {t('section_executive')}", t("executive_title"), t("calculated_filters")
)
if not sov.empty:
    leader = sov.iloc[0]
    insight_one = t(
        "leader_insight",
        product=leader["product"],
        share=float(leader["share_of_voice"]),
    )
else:
    insight_one = t("no_sov")
if len(pull_through) >= 2:
    strongest = pull_through.iloc[0]
    weakest = pull_through.iloc[-1]
    insight_two = t(
        "message_insight",
        strongest=local_theme(str(strongest["theme"]), language),
        strongest_rate=float(strongest["coverage_rate"]),
        weakest=local_theme(str(weakest["theme"]), language),
        weakest_rate=float(weakest["coverage_rate"]),
    )
elif top_message is not None:
    insight_two = t(
        "single_message_insight",
        theme=local_theme(str(top_message["theme"]), language),
        rate=float(top_message["coverage_rate"]),
    )
else:
    insight_two = t("include_ix3_insight")

flagged = filtered.loc[filtered["risk_signal"].ne("No flagged risk")]
if flagged.empty:
    insight_three = t("no_risk")
else:
    lead_risk = flagged["risk_signal"].value_counts().index[0]
    insight_three = t(
        "risk_insight", count=len(flagged), risk=local_risk(lead_risk, language)
    )

insight_columns = st.columns(3)
for index, (title, copy) in enumerate(
    [
        (t("competitive_attention"), insight_one),
        (t("message_pull_through"), insight_two),
        (t("review_queue"), insight_three),
    ],
    start=1,
):
    with insight_columns[index - 1]:
        st.markdown(
            f'<div class="insight-card"><div class="insight-index">{escape(t("signal"))} 0{index}</div>'
            f"<h3>{escape(title)}</h3><p>{escape(copy)} {escape(t('sample_size', count=len(filtered)))}</p></div>",
            unsafe_allow_html=True,
        )

section_header(
    f"02 / {t('section_attention')}", t("attention_title"), t("attention_note")
)
trend_column, share_column = st.columns([1.7, 1])
trend = filtered.copy()
span_days = (date_range[1] - date_range[0]).days
if span_days > 180:
    trend["period"] = (
        trend["published_at"].dt.tz_convert(None).dt.to_period("M").dt.start_time
    )
    period_label = t("month")
else:
    trend["period"] = (
        trend["published_at"].dt.tz_convert(None).dt.to_period("W").dt.start_time
    )
    period_label = t("week")
trend = (
    trend.groupby(["period", "product"], as_index=False)
    .size()
    .rename(columns={"size": "mentions"})
)
with trend_column:
    trend_chart = px.line(
        trend,
        x="period",
        y="mentions",
        color="product",
        markers=True,
        color_discrete_map=PRODUCT_COLOURS,
        labels={
            "period": period_label,
            "mentions": t("mentions"),
            "product": t("product"),
        },
    )
    trend_chart.update_traces(line={"width": 2.6}, marker={"size": 6})
    trend_chart.update_yaxes(rangemode="tozero")
    if date_range[0] <= LAUNCH_DATE <= date_range[1]:
        trend_chart.add_vline(
            x=pd.Timestamp(LAUNCH_DATE),
            line_dash="dot",
            line_color="#607086",
            opacity=0.75,
        )
        trend_chart.add_annotation(
            x=pd.Timestamp(LAUNCH_DATE),
            y=1,
            yref="paper",
            text=t("launch_anchor"),
            showarrow=False,
            xanchor="left",
            yanchor="bottom",
            font={"size": 10, "color": "#607086"},
        )
    st.plotly_chart(
        style_figure(trend_chart), use_container_width=True, config=CHART_CONFIG
    )
with share_column:
    sov_sorted = sov.sort_values("share_of_voice")
    share_chart = px.bar(
        sov_sorted,
        x="share_of_voice",
        y="product",
        orientation="h",
        color="product",
        text=sov_sorted["share_of_voice"].map(lambda value: f"{value:.0%}"),
        color_discrete_map=PRODUCT_COLOURS,
        labels={"share_of_voice": t("share_of_voice"), "product": ""},
    )
    share_chart.update_layout(showlegend=False)
    share_chart.update_traces(textposition="outside", cliponaxis=False)
    share_chart.update_xaxes(
        tickformat=".0%", range=[0, max(0.5, sov["share_of_voice"].max() * 1.2)]
    )
    st.plotly_chart(
        style_figure(share_chart), use_container_width=True, config=CHART_CONFIG
    )

section_header(f"03 / {t('section_message')}", t("message_title"), t("message_note"))
message_column, market_column = st.columns([1, 1.35])
with message_column:
    if pull_through.empty:
        st.info(t("include_ix3_insight"))
    else:
        message_data = pull_through.sort_values("coverage_rate").copy()
        message_data["theme_label"] = message_data["theme"].map(
            lambda value: local_theme(value, language)
        )
        message_chart = px.bar(
            message_data,
            x="coverage_rate",
            y="theme_label",
            orientation="h",
            text=message_data["coverage_rate"].map(lambda value: f"{value:.0%}"),
            color_discrete_sequence=["#1265E8"],
            labels={"coverage_rate": t("share_ix3"), "theme_label": ""},
        )
        message_chart.update_traces(textposition="outside", cliponaxis=False)
        message_chart.update_xaxes(tickformat=".0%", range=[0, 1.08])
        st.plotly_chart(
            style_figure(message_chart, 440),
            use_container_width=True,
            config=CHART_CONFIG,
        )
with market_column:
    market_matrix = market_theme_matrix(filtered, HERO_PRODUCT)
    if market_matrix.empty:
        st.info(t("market_lens_empty"))
    else:
        market_matrix = market_matrix.reindex(
            columns=pull_through["theme"].tolist(), fill_value=0
        )
        market_matrix.columns = [
            local_theme(value, language) for value in market_matrix.columns
        ]
        market_matrix.index = [
            localise_value(value, MARKET_LABELS, language)
            for value in market_matrix.index
        ]
        heatmap = go.Figure(
            data=go.Heatmap(
                z=market_matrix.values,
                x=market_matrix.columns,
                y=market_matrix.index,
                colorscale=[[0, "#F1F4F8"], [0.5, "#82AEEF"], [1, "#0C55BE"]],
                zmin=0,
                zmax=1,
                text=[
                    [f"{value:.0%}" for value in row] for row in market_matrix.values
                ],
                texttemplate="%{text}",
                textfont={"size": 11},
                hovertemplate="%{y}<br>%{x}: %{z:.0%}<extra></extra>",
                colorbar={
                    "title": t("pull_through"),
                    "tickformat": ".0%",
                    "thickness": 12,
                },
            )
        )
        heatmap.update_xaxes(tickangle=-35)
        st.plotly_chart(
            style_figure(heatmap, 440), use_container_width=True, config=CHART_CONFIG
        )

section_header(f"04 / {t('section_signals')}", t("signals_title"), t("signals_note"))
signal_column, tone_column = st.columns([1.15, 1])
with signal_column:
    risk_counts = flagged["risk_signal"].value_counts()
    if risk_counts.empty:
        st.success(t("no_risk"))
    else:
        for risk_name, count in risk_counts.head(5).items():
            example_title = flagged.loc[
                flagged["risk_signal"].eq(risk_name), "title"
            ].iloc[0]
            st.markdown(
                f'<div class="signal-card"><div class="signal-top"><div class="signal-title">{escape(local_risk(risk_name, language))}</div>'
                f'<div class="signal-count">{escape(t("flags", count=count))}</div></div>'
                f'<div class="signal-copy">{escape(t("example"))}: {escape(example_title)}</div></div>',
                unsafe_allow_html=True,
            )
with tone_column:
    tone_counts = filtered.groupby(["product", "sentiment"], as_index=False).size()
    tone_counts["tone_label"] = tone_counts["sentiment"].map(
        lambda value: localise_value(value, TONE_LABELS, language)
    )
    tone_colours = {
        localise_value("Positive", TONE_LABELS, language): "#2E8067",
        localise_value("Neutral", TONE_LABELS, language): "#AAB4C0",
        localise_value("Negative", TONE_LABELS, language): "#C76D43",
    }
    tone_chart = px.bar(
        tone_counts,
        x="product",
        y="size",
        color="tone_label",
        barmode="stack",
        color_discrete_map=tone_colours,
        labels={"product": "", "size": t("mentions"), "tone_label": t("tone_proxy")},
    )
    tone_chart.update_xaxes(tickangle=-18)
    st.plotly_chart(
        style_figure(tone_chart, 380), use_container_width=True, config=CHART_CONFIG
    )

section_header(f"05 / {t('section_evidence')}", t("evidence_title"), t("evidence_note"))
filter_one, filter_two, filter_three = st.columns([1.5, 1, 1])
with filter_one:
    search_term = st.text_input(t("search"), placeholder=t("search_placeholder"))
with filter_two:
    theme_options = [""] + sorted(filtered["primary_theme"].unique())
    evidence_theme = st.selectbox(
        t("primary_theme"),
        theme_options,
        format_func=lambda value: (
            t("all_themes") if value == "" else local_theme(value, language)
        ),
    )
with filter_three:
    tone_options = [""] + sorted(filtered["sentiment"].unique())
    evidence_tone = st.selectbox(
        t("tone_proxy"),
        tone_options,
        format_func=lambda value: (
            t("all_tones")
            if value == ""
            else localise_value(value, TONE_LABELS, language)
        ),
    )

evidence = filtered.copy()
if search_term.strip():
    search_mask = evidence["title"].str.contains(
        search_term.strip(), case=False, regex=False
    ) | evidence["snippet"].str.contains(search_term.strip(), case=False, regex=False)
    evidence = evidence.loc[search_mask]
if evidence_theme:
    evidence = evidence.loc[evidence["primary_theme"].eq(evidence_theme)]
if evidence_tone:
    evidence = evidence.loc[evidence["sentiment"].eq(evidence_tone)]

evidence_display = evidence.copy()
evidence_display["market"] = evidence_display["market"].map(
    lambda value: localise_value(value, MARKET_LABELS, language)
)
evidence_display["primary_theme"] = evidence_display["primary_theme"].map(
    lambda value: local_theme(value, language)
)
evidence_display["sentiment"] = evidence_display["sentiment"].map(
    lambda value: localise_value(value, TONE_LABELS, language)
)
evidence_display["risk_signal"] = evidence_display["risk_signal"].map(
    lambda value: local_risk(value, language)
)
evidence_display["source_tier"] = evidence_display["source_tier"].map(
    lambda value: localise_value(value, SOURCE_TIER_LABELS, language)
)
display_columns = [
    "published_at",
    "market",
    "product",
    "source",
    "source_tier",
    "title",
    "primary_theme",
    "sentiment",
    "risk_signal",
    "url",
]
column_names = {
    "published_at": t("published"),
    "market": t("market"),
    "product": t("product"),
    "source": t("source"),
    "source_tier": t("source_tier"),
    "title": t("title"),
    "primary_theme": t("lead_theme"),
    "sentiment": t("tone_proxy"),
    "risk_signal": t("review_flag"),
    "url": t("evidence_link"),
}
table = (
    evidence_display[display_columns]
    .sort_values("published_at", ascending=False)
    .rename(columns=column_names)
)
st.dataframe(
    table,
    use_container_width=True,
    hide_index=True,
    column_config={
        t("published"): st.column_config.DatetimeColumn(
            t("published"), format="YYYY-MM-DD"
        ),
        t("evidence_link"): st.column_config.LinkColumn(
            t("evidence_link"), display_text=t("open_source")
        ),
    },
)
download_column, count_column = st.columns([1, 3])
with download_column:
    st.download_button(
        t("export"),
        data=table.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"ev_launch_intelligence_{language}.csv",
        mime="text/csv",
        use_container_width=True,
    )
with count_column:
    st.caption(t("export_count", shown=len(evidence), total=len(filtered)))

with st.expander(t("method_title")):
    st.markdown(
        f'<div class="method-note">{t("method_html")}</div>', unsafe_allow_html=True
    )

st.markdown(
    f'<div class="footer-rule">{escape(t("footer"))}</div>', unsafe_allow_html=True
)
