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
        """Capture screenshot with fallback strategies."""
        try:
            # Try full page screenshot first
            data = await page.screenshot(full_page=True, type="png")
            return base64.b64encode(data).decode("ascii")
        except Exception as e:
            self.logger.warning("Full page screenshot failed: {}, trying viewport only", e)
            try:
                # Fallback: viewport only (visible area)
                data = await page.screenshot(full_page=False, type="png")
                return base64.b64encode(data).decode("ascii")
            except Exception as e2:
                self.logger.error("Viewport screenshot also failed: {}, returning empty", e2)
                # Return a minimal 1x1 transparent PNG as last resort
                # This allows the extraction to continue without screenshot
                minimal_png = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
                return base64.b64encode(minimal_png).decode("ascii")

    async def _simplified_html(self, page) -> str:
        """Extract relevant HTML focusing on navigation areas."""
        script = """
            () => {
                // Priority 1: Extract navigation-related elements first
                const navElements = [];
                
                // Common navigation containers
                const navSelectors = [
                    'nav', 'header', 'aside', '.sidebar', '.navigation', 
                    '[role="navigation"]', '[class*="menu"]', '[class*="nav"]',
                    '[class*="category"]', '[class*="department"]', '[class*="collection"]'
                ];
                
                navSelectors.forEach(selector => {
                    try {
                        const elements = document.querySelectorAll(selector);
                        elements.forEach(el => {
                            if (el && !navElements.includes(el)) {
                                navElements.push(el);
                            }
                        });
                    } catch(e) {}
                });
                
                // Build HTML string prioritizing navigation
                let html = '';
                
                // Add navigation elements first (most important)
                navElements.forEach(el => {
                    const clone = el.cloneNode(true);
                    clone.querySelectorAll('script, style, noscript, img, svg').forEach(n => n.remove());
                    html += clone.outerHTML + '\\n';
                });
                
                // If we have space, add some body content for context
                if (html.length < 30000) {
                    const bodyClone = document.body.cloneNode(true);
                    bodyClone.querySelectorAll('script, style, noscript, img, svg, nav, header, aside').forEach(n => n.remove());
                    html += bodyClone.outerHTML.slice(0, 20000);
                }
                
                return html.slice(0, 60000);  // Increased limit
            }
        """
        return await page.evaluate(script)



__all__ = ["PageAnalyzerTool"]
