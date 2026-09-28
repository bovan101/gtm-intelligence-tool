from datetime import date

from src.i18n import THEME_LABELS, format_date, localise_value, translate


def test_ui_copy_switches_language_without_changing_keys() -> None:
    assert translate("data_source", "en") == "Data source"
    assert translate("data_source", "zh") == "数据来源"
    assert translate("markets_in_view", "zh", count=3) == "当前查看3个市场"


def test_canonical_theme_is_localised_only_at_display_boundary() -> None:
    canonical = "Range & charging"
    assert localise_value(canonical, THEME_LABELS, "en") == canonical
    assert localise_value(canonical, THEME_LABELS, "zh") == "续航与充电"


def test_date_formatting_is_language_aware() -> None:
    value = date(2025, 9, 5)
    assert format_date(value, "en") == "05 Sep 2025"
    assert format_date(value, "zh") == "2025-09-05"
