"""Tool for analyzing webpage structure."""
from __future__ import annotations

import base64
from datetime import datetime
from typing import Any, Dict

import tenacity
from strands import tool

from ..config import get_config
from ..errors import AnalysisError
from ..llm_client import create_llm_client
from ..utils.logger import get_logger
from ..utils.url_utils import ensure_absolute


class PageAnalyzerTool:
    """Analyzes a page to determine category extraction strategy."""

    def __init__(self, agent: "CategoryExtractionAgent") -> None:
        self.agent = agent
        self.config = get_config()
        self.llm_client = create_llm_client(self.config)
        self.logger = get_logger(agent.retailer_id)

    @tool
    async def analyze(self, url: str, force_refresh: bool = False) -> Dict[str, Any]:
        if not self.agent.page:
            raise AnalysisError("Agent page not initialised. Call initialize_browser().")

        page = self.agent.page
        self.logger.info("Analyzing page: {}", url)

        if force_refresh or page.url != url:
            # Use domcontentloaded instead of networkidle for sites with persistent connections
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=self.config.browser_timeout)
            except Exception as e:
                # Fallback to load if domcontentloaded fails
                self.logger.warning("domcontentloaded wait failed, trying load: {}", e)
                await page.goto(url, wait_until="load", timeout=self.config.browser_timeout)
            await page.wait_for_timeout(2000)

        await self._handle_cookie_consent(page)
        screenshot_b64 = await self._capture_screenshot(page)
        html_snippet = await self._simplified_html(page)

        analysis = await self.llm_client.analyze_page(url, screenshot_b64, html_snippet)
        self.agent.state["analysis"] = analysis
        return analysis

    async def _handle_cookie_consent(self, page) -> None:
        selectors = [
            "button:has-text('Accept')",
            "button:has-text('I Agree')",
            "#accept-cookies",
        ]
        for selector in selectors:
            try:
                button = await page.query_selector(selector)
                if button:
                    await button.click()
                    await page.wait_for_timeout(500)
                    self.logger.debug("Accepted cookies via {}", selector)
                    return
            except Exception:  # noqa: BLE001
                continue

    async def _capture_screenshot(self, page) -> str:
        data = await page.screenshot(full_page=True, type="png")
        return base64.b64encode(data).decode("ascii")

    async def _simplified_html(self, page) -> str:
        script = """
            () => {
                const clone = document.body.cloneNode(true);
                clone.querySelectorAll('script, style, noscript').forEach(node => node.remove());
                return clone.outerHTML.slice(0, 50000);
            }
        """
        return await page.evaluate(script)



__all__ = ["PageAnalyzerTool"]
