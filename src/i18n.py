from __future__ import annotations

from collections.abc import Mapping
from datetime import date, datetime, timezone

Language = str

COPY: dict[str, dict[str, str]] = {
    "language": {"en": "Language", "zh": "语言"},
    "portfolio_case": {
        "en": "Independent portfolio case study · BMW iX3",
        "zh": "独立作品集案例 · BMW iX3",
    },
    "data_source": {"en": "Data source", "zh": "数据来源"},
    "real_dataset": {"en": "Real public-news dataset", "zh": "真实公开新闻数据"},
    "synthetic_demo": {"en": "Synthetic demo", "zh": "合成演示数据"},
    "real_caption": {
        "en": "Traceable public-news sample · updated daily",
        "zh": "可追溯公开新闻样本 · 每日更新",
    },
    "demo_caption": {
        "en": "Reproducible fictional records · not market evidence",
        "zh": "可复现虚构记录 · 不可作为市场证据",
    },
    "view_controls": {"en": "View controls", "zh": "视图控制"},
    "coverage_scope": {"en": "Coverage scope", "zh": "报道范围"},
    "verified_independent": {"en": "Verified independent media", "zh": "可信独立媒体"},
    "verified_all": {"en": "All verified sources", "zh": "全部可信来源"},
    "all_public": {"en": "All collected public sources", "zh": "全部已采集公开来源"},
    "products": {"en": "Products", "zh": "车型"},
    "markets": {"en": "Markets", "zh": "市场"},
    "coverage_window": {"en": "Coverage window", "zh": "数据窗口"},
    "private_boundary": {
        "en": "No private BMW information is used or required.",
        "zh": "本项目不使用也不需要任何宝马内部资料。",
    },
    "eyebrow": {
        "en": "Premium EV market signal monitor",
        "zh": "高端新能源汽车市场信号监测",
    },
    "hero_title": {"en": "EV Launch<br>Intelligence", "zh": "新能源汽车<br>上市情报"},
    "hero_copy": {
        "en": "An evidence-first view of how the BMW iX3 is discussed across markets, messages and premium electric-SUV competitors.",
        "zh": "以证据为基础，观察BMW iX3在不同市场、核心信息与高端纯电SUV竞品中的公开讨论。",
    },
    "current_dataset": {"en": "Current dataset", "zh": "当前数据集"},
    "real_mode_label": {
        "en": "REAL PUBLIC NEWS · DAILY",
        "zh": "真实公开新闻 · 每日更新",
    },
    "demo_mode_label": {
        "en": "SYNTHETIC DEMO · NOT MARKET EVIDENCE",
        "zh": "合成演示 · 不可作为市场证据",
    },
    "last_updated": {"en": "Last updated", "zh": "最近更新"},
    "source_health": {"en": "Source health", "zh": "数据源状态"},
    "healthy": {"en": "Healthy", "zh": "正常"},
    "partial": {"en": "Partial", "zh": "部分成功"},
    "failed": {"en": "Failed", "zh": "失败"},
    "stale": {"en": "Stale", "zh": "数据过期"},
    "unknown": {"en": "Unknown", "zh": "未知"},
    "stale_warning": {
        "en": "The real dataset is more than 36 hours old. Showing the last successful snapshot.",
        "zh": "真实数据已超过36小时未更新，当前显示最后一次成功快照。",
    },
    "daily_frequency": {"en": "Daily collection", "zh": "每日采集"},
    "provider_google": {
        "en": "Google News RSS + publisher provenance",
        "zh": "Google News RSS + 原始发布方溯源",
    },
    "launch_anchor": {"en": "iX3 world premiere", "zh": "iX3全球首发"},
    "refresh_data": {"en": "Reload latest snapshot", "zh": "重新载入最新快照"},
    "no_real_data": {
        "en": "No real dataset is available yet. Run the collection script or switch to the synthetic demo.",
        "zh": "尚未生成真实数据，请先运行采集脚本或切换到合成演示模式。",
    },
    "no_records": {
        "en": "No records match the current filters.",
        "zh": "当前筛选条件下没有记录。",
    },
    "invalid_dates": {
        "en": "The selected records do not include valid publication dates.",
        "zh": "所选记录缺少有效发布时间。",
    },
    "filtered_mentions": {"en": "Filtered mentions", "zh": "筛选后报道量"},
    "markets_in_view": {
        "en": "{count} market(s) in view",
        "zh": "当前查看{count}个市场",
    },
    "independent_sources": {"en": "Independent sources", "zh": "独立媒体数量"},
    "unique_publishers": {
        "en": "Unique publishers in current view",
        "zh": "当前范围内的独立发布方",
    },
    "ix3_sov": {"en": "iX3 share of voice", "zh": "iX3 声量占比"},
    "mentions_fraction": {
        "en": "{ix3} of {total} mentions",
        "zh": "{total}条中有{ix3}条",
    },
    "lead_message": {"en": "Lead iX3 message", "zh": "iX3 核心触达信息"},
    "no_data": {"en": "No data", "zh": "暂无数据"},
    "include_ix3": {
        "en": "Include BMW iX3 in the selection",
        "zh": "请在筛选中包含BMW iX3",
    },
    "present_in": {
        "en": "Present in {rate:.0%} of iX3 coverage",
        "zh": "出现在{rate:.0%}的iX3报道中",
    },
    "section_executive": {"en": "Executive read", "zh": "管理摘要"},
    "executive_title": {
        "en": "What the selected evidence says",
        "zh": "当前证据反映了什么",
    },
    "calculated_filters": {
        "en": "Calculated from the current filters",
        "zh": "根据当前筛选结果计算",
    },
    "competitive_attention": {"en": "Competitive attention", "zh": "竞品关注度"},
    "message_pull_through": {"en": "Message pull-through", "zh": "核心信息触达"},
    "review_queue": {"en": "Review queue", "zh": "人工复核队列"},
    "leader_insight": {
        "en": "{product} leads with {share:.0%} share of voice.",
        "zh": "{product}以{share:.0%}的声量占比领先。",
    },
    "no_sov": {
        "en": "No competitive share is available for this view.",
        "zh": "当前视图无法计算竞品声量占比。",
    },
    "message_insight": {
        "en": "{strongest} is strongest ({strongest_rate:.0%}); {weakest} is least visible ({weakest_rate:.0%}).",
        "zh": "{strongest}触达最高（{strongest_rate:.0%}）；{weakest}触达最低（{weakest_rate:.0%}）。",
    },
    "single_message_insight": {
        "en": "{theme} appears in {rate:.0%} of selected iX3 coverage.",
        "zh": "{theme}出现在{rate:.0%}的所选iX3报道中。",
    },
    "include_ix3_insight": {
        "en": "Include iX3 records to calculate message pull-through.",
        "zh": "请包含iX3记录以计算核心信息触达率。",
    },
    "no_risk": {
        "en": "No lexical risk signals are flagged in the current evidence set.",
        "zh": "当前证据集中未发现需要标记的词汇风险信号。",
    },
    "risk_insight": {
        "en": "{count} record(s) need review; {risk} is the most frequent signal.",
        "zh": "有{count}条记录需要复核；最常见信号为{risk}。",
    },
    "sample_size": {"en": "Sample size: n={count}.", "zh": "样本量：n={count}。"},
    "signal": {"en": "SIGNAL", "zh": "信号"},
    "section_attention": {"en": "Attention", "zh": "关注度"},
    "attention_title": {
        "en": "Launch momentum and competitive share",
        "zh": "上市声量趋势与竞品占比",
    },
    "attention_note": {
        "en": "Volume indicates attention — not demand or sales",
        "zh": "报道量代表关注度，不代表需求或销量",
    },
    "week": {"en": "Week", "zh": "周"},
    "month": {"en": "Month", "zh": "月"},
    "mentions": {"en": "Mentions", "zh": "报道量"},
    "product": {"en": "Product", "zh": "车型"},
    "share_of_voice": {"en": "Share of voice", "zh": "声量占比"},
    "section_message": {"en": "Message", "zh": "信息触达"},
    "message_title": {"en": "iX3 message pull-through", "zh": "iX3 核心信息触达率"},
    "message_note": {
        "en": "Multi-label theme detection across selected iX3 records",
        "zh": "对所选iX3记录进行多标签主题识别",
    },
    "share_ix3": {"en": "Share of iX3 coverage", "zh": "iX3报道占比"},
    "market_lens_empty": {
        "en": "Include BMW iX3 and at least one market to view the market lens.",
        "zh": "请包含BMW iX3和至少一个市场以查看市场差异。",
    },
    "pull_through": {"en": "Pull-through", "zh": "触达率"},
    "section_signals": {"en": "Signals", "zh": "风险信号"},
    "signals_title": {
        "en": "Risk and opportunity review queue",
        "zh": "风险与机会复核队列",
    },
    "signals_note": {
        "en": "Heuristic flags for human review — not consumer sentiment",
        "zh": "启发式标记仅供人工复核，不代表消费者情绪",
    },
    "flags": {"en": "{count} FLAG(S)", "zh": "{count}条标记"},
    "example": {"en": "Example", "zh": "示例"},
    "tone_proxy": {"en": "Tone proxy", "zh": "语气代理指标"},
    "section_evidence": {"en": "Evidence", "zh": "证据"},
    "evidence_title": {
        "en": "Trace every signal to a record",
        "zh": "每个信号均可追溯到具体记录",
    },
    "evidence_note": {
        "en": "Filter the evidence before exporting",
        "zh": "导出前可筛选证据",
    },
    "search": {"en": "Search titles and snippets", "zh": "搜索标题与摘要"},
    "search_placeholder": {
        "en": "e.g. charging or interface",
        "zh": "例如：充电或交互",
    },
    "primary_theme": {"en": "Primary theme", "zh": "主要主题"},
    "all_themes": {"en": "All themes", "zh": "全部主题"},
    "all_tones": {"en": "All tone labels", "zh": "全部语气标签"},
    "published": {"en": "Published", "zh": "发布时间"},
    "market": {"en": "Market", "zh": "市场"},
    "source": {"en": "Source", "zh": "来源"},
    "source_type": {"en": "Source type", "zh": "来源类型"},
    "source_tier": {"en": "Source tier", "zh": "来源等级"},
    "title": {"en": "Title", "zh": "标题"},
    "lead_theme": {"en": "Lead theme", "zh": "主要主题"},
    "review_flag": {"en": "Review flag", "zh": "复核标记"},
    "evidence_link": {"en": "Evidence", "zh": "证据链接"},
    "open_source": {"en": "Open source", "zh": "打开来源"},
    "export": {"en": "Export filtered evidence", "zh": "导出筛选后证据"},
    "export_count": {
        "en": "Export contains {shown} of {total} records in the current view.",
        "zh": "导出文件包含当前视图{total}条记录中的{shown}条。",
    },
    "method_title": {
        "en": "Method and interpretation boundaries",
        "zh": "方法与解读边界",
    },
    "method_html": {
        "en": "<strong>Share of voice</strong> is a record-count share within the selected evidence set. It is not sales, demand or market share.<br><br><strong>Message pull-through</strong> is the share of selected iX3 records containing a transparent theme dictionary. One record may contain several messages.<br><br><strong>Tone and risk signals</strong> use a small lexical heuristic to prioritise manual review. They are not measures of consumer opinion.<br><br><strong>Real mode</strong> is a traceable public-news sample discovered through Google News RSS. It is not exhaustive global media monitoring.",
        "zh": "<strong>声量占比</strong>是所选证据集中报道数量的占比，不代表销量、需求或市场份额。<br><br><strong>核心信息触达率</strong>表示所选iX3记录中命中透明主题词典的比例，一条记录可以包含多个主题。<br><br><strong>语气与风险信号</strong>使用小型词汇规则安排人工复核优先级，不代表消费者情绪。<br><br><strong>真实数据模式</strong>是通过Google News RSS发现的可追溯公开新闻样本，不代表完整全球媒体监测。",
    },
    "footer": {
        "en": "Independent portfolio project based on public or explicitly synthetic information. Not affiliated with or endorsed by BMW Group. No private BMW information is used.",
        "zh": "本项目是基于公开信息或明确合成数据的独立作品集项目，不隶属于BMW Group，也不代表其官方立场，且不使用任何宝马内部资料。",
    },
}

THEME_LABELS: dict[str, dict[str, str]] = {
    "Range & charging": {"en": "Range & charging", "zh": "续航与充电"},
    "Digital experience": {"en": "Digital experience", "zh": "数字体验"},
    "Driving dynamics": {"en": "Driving dynamics", "zh": "驾驶动态"},
    "Design": {"en": "Design", "zh": "设计"},
    "Sustainability": {"en": "Sustainability", "zh": "可持续性"},
    "ADAS & safety": {"en": "ADAS & safety", "zh": "辅助驾驶与安全"},
    "Practicality": {"en": "Practicality", "zh": "实用性"},
    "Price & value": {"en": "Price & value", "zh": "价格与价值"},
    "Performance": {"en": "Performance", "zh": "性能"},
    "Software & connectivity": {"en": "Software & connectivity", "zh": "软件与互联"},
    "General coverage": {"en": "General coverage", "zh": "综合报道"},
}

RISK_LABELS: dict[str, dict[str, str]] = {
    "No flagged risk": {"en": "No flagged risk", "zh": "无标记风险"},
    "Price pressure": {"en": "Price pressure", "zh": "价格压力"},
    "Interface usability": {"en": "Interface usability", "zh": "交互易用性"},
    "Availability": {"en": "Availability", "zh": "供应与交付"},
    "Range confidence": {"en": "Range confidence", "zh": "续航信心"},
    "Design response": {"en": "Design response", "zh": "设计评价"},
    "Reliability": {"en": "Reliability", "zh": "可靠性"},
    "Other critical signal": {"en": "Other critical signal", "zh": "其他关键风险"},
}

TONE_LABELS: dict[str, dict[str, str]] = {
    "Positive": {"en": "Positive", "zh": "正向"},
    "Neutral": {"en": "Neutral", "zh": "中性"},
    "Negative": {"en": "Negative", "zh": "负向"},
}

SOURCE_TIER_LABELS: dict[str, dict[str, str]] = {
    "Official": {"en": "Official", "zh": "官方来源"},
    "Curated independent": {"en": "Curated independent", "zh": "可信独立媒体"},
    "Unverified public": {"en": "Unverified public", "zh": "未验证公开来源"},
    "Synthetic demo": {"en": "Synthetic demo", "zh": "合成演示"},
}

MARKET_LABELS: dict[str, dict[str, str]] = {
    "United Kingdom": {"en": "United Kingdom", "zh": "英国"},
    "Germany": {"en": "Germany", "zh": "德国"},
    "Germany (English query)": {"en": "Germany", "zh": "德国"},
    "United States": {"en": "United States", "zh": "美国"},
    "Australia": {"en": "Australia", "zh": "澳大利亚"},
    "Unspecified": {"en": "Unspecified", "zh": "未指定"},
}


def translate(key: str, language: Language, **values: object) -> str:
    """Return localised UI copy and interpolate named values."""
    language = language if language in {"en", "zh"} else "en"
    template = COPY.get(key, {}).get(language, key)
    return template.format(**values) if values else template


def localise_value(
    value: str, labels: Mapping[str, Mapping[str, str]], language: Language
) -> str:
    """Localise a canonical analytical label while preserving unknown values."""
    return labels.get(value, {}).get(language, value)


def format_date(value: date | datetime, language: Language) -> str:
    """Format dates consistently for the selected interface language."""
    return (
        value.strftime("%Y-%m-%d") if language == "zh" else value.strftime("%d %b %Y")
    )


def format_timestamp(value: datetime, language: Language) -> str:
    """Format a timezone-aware collection time with an explicit UTC marker."""
    utc_value = value.astimezone(timezone.utc)
    return (
        utc_value.strftime("%Y-%m-%d %H:%M UTC")
        if language == "zh"
        else utc_value.strftime("%d %b %Y %H:%M UTC")
    )
