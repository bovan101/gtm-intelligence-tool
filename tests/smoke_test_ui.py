"""Headless browser smoke test for the Streamlit dashboard."""

import os
from pathlib import Path

from playwright.sync_api import sync_playwright

APP_URL = os.environ.get("APP_URL", "http://127.0.0.1:8501")
PREVIEW_PATH = Path(__file__).resolve().parents[1] / "assets" / "dashboard-preview.png"


def main() -> None:
    PREVIEW_PATH.parent.mkdir(parents=True, exist_ok=True)
    browser_errors: list[str] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(
            viewport={"width": 1440, "height": 1400}, device_scale_factor=1
        )
        page.on(
            "console",
            lambda message: (
                browser_errors.append(message.text) if message.type == "error" else None
            ),
        )
        page.goto(APP_URL, wait_until="networkidle", timeout=60_000)
        page.get_by_text("新能源汽车", exact=False).first.wait_for(timeout=30_000)
        page.get_by_text("每个信号均可追溯到具体记录", exact=True).wait_for(
            timeout=30_000
        )
        page.locator(".js-plotly-plot").first.wait_for(timeout=30_000)
        page.wait_for_timeout(2_000)

        body_text = page.locator("body").inner_text()
        assert "真实公开新闻" in body_text
        assert "iX3 核心信息触达率" in body_text
        assert "每个信号均可追溯到具体记录" in body_text
        assert "不使用任何宝马内部资料" in body_text
        assert "Traceback" not in body_text
        assert "ModuleNotFoundError" not in body_text

        page.screenshot(path=str(PREVIEW_PATH), full_page=True)

        page.get_by_text("English", exact=True).click()
        page.get_by_text("What the selected evidence says", exact=True).wait_for(
            timeout=30_000
        )
        page.get_by_text("iX3 message pull-through", exact=True).wait_for(
            timeout=30_000
        )
        page.get_by_text("Trace every signal to a record", exact=True).wait_for(
            timeout=30_000
        )
        english_body = page.locator("body").inner_text()
        assert "REAL PUBLIC NEWS · DAILY" in english_body
        assert "iX3 message pull-through" in english_body
        assert "Trace every signal to a record" in english_body
        browser.close()

    if browser_errors:
        raise RuntimeError(f"Browser console errors: {browser_errors}")
    print(f"UI smoke test passed; preview saved to {PREVIEW_PATH}")


if __name__ == "__main__":
    main()
