"""
WorkBuddy 浏览器工具客户端

使用 Playwright 控制真实浏览器，支持：
- 打开页面并等待加载
- 截图
- 提取页面文本
- 点击/输入/截图等常见自动化操作
"""

from __future__ import annotations

import base64
from dataclasses import dataclass
from typing import Optional

try:
    from playwright.sync_api import sync_playwright, Page, Browser
except ImportError:  # pragma: no cover - tested with mock
    sync_playwright = None  # type: ignore
    Page = None  # type: ignore
    Browser = None  # type: ignore


@dataclass
class BrowserResult:
    url: str
    title: str
    text: str
    screenshot_b64: Optional[str] = None
    status: str = "ok"

    def validate(self) -> dict:
        if self.status != "ok":
            return {"passed": False, "issues": [f"browser status {self.status}"]}
        if not self.url:
            return {"passed": False, "issues": ["missing url"]}
        if not self.text:
            return {"passed": False, "issues": ["empty page text"]}
        return {"passed": True, "issues": []}


class BrowserClient:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self._playwright = None
        self._browser: Optional[Browser] = None

    def _ensure_playwright(self):
        if sync_playwright is None:
            raise RuntimeError(
                "Playwright not installed. Run: pip install playwright && playwright install"
            )

    def start(self):
        self._ensure_playwright()
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=self.headless)

    def stop(self):
        if self._browser:
            self._browser.close()
            self._browser = None
        if self._playwright:
            self._playwright.stop()
            self._playwright = None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def fetch(
        self,
        url: str,
        wait_for: Optional[str] = None,
        screenshot: bool = False,
    ) -> BrowserResult:
        if self._browser is None:
            raise RuntimeError("Browser not started. Use start() or context manager.")

        page: Page = self._browser.new_page()
        try:
            page.goto(url, wait_until="networkidle", timeout=30000)
            if wait_for:
                page.wait_for_selector(wait_for, timeout=30000)

            title = page.title()
            text = page.inner_text("body")
            screenshot_b64 = None
            if screenshot:
                png_bytes = page.screenshot(full_page=True)
                screenshot_b64 = base64.b64encode(png_bytes).decode("utf-8")

            return BrowserResult(
                url=page.url,
                title=title,
                text=text,
                screenshot_b64=screenshot_b64,
            )
        finally:
            page.close()

    def run_js(self, url: str, script: str) -> str:
        if self._browser is None:
            raise RuntimeError("Browser not started.")

        page: Page = self._browser.new_page()
        try:
            page.goto(url, wait_until="networkidle", timeout=30000)
            return page.evaluate(script)
        finally:
            page.close()


if __name__ == "__main__":
    with BrowserClient() as client:
        result = client.fetch("https://example.com")
        print(result.title)
        print(result.text[:500])
