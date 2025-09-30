# Task 5: Page Analyzer Tool

**Status**: 🔒 Blocked (depends on Task 4)  
**Estimated Time**: 6-8 hours  
**Dependencies**: Task 4 (Core Agent Implementation)  
**Priority**: High (first agent tool)

---

## 📋 Objective

Implement the `PageAnalyzerTool` that inspects a retailer homepage or category landing page, captures screenshots/HTML, sends the context to Claude 4 Sonnet (via AWS Bedrock) for analysis, and returns structured insights that later tools consume (navigation pattern, selectors, interactions, confidence score).

## 🎯 Success Criteria

- [ ] `src/ai_agents/category_extractor/tools/page_analyzer.py` created with `PageAnalyzerTool`
- [ ] Tool exposes `async analyze(url: str, force_refresh: bool = False) -> Dict[str, Any]`
- [ ] Captures full-page screenshot and simplified HTML
- [ ] Invokes AWS Bedrock Claude 4 vision endpoint with screenshot + HTML context
- [ ] Returns dict containing `navigation_type`, `selectors`, `interactions`, `confidence`, and `notes`
- [ ] Handles cookie banners / popups via helper method
- [ ] Retries transient failures using `tenacity`
- [ ] Logs analysis steps, durations, and failures
- [ ] Updates agent state (analysis metadata)

## 📝 Specifications

### File: `src/ai_agents/category_extractor/tools/page_analyzer.py`

```python
"""Tool for analyzing webpage structure."""
from __future__ import annotations

import base64
import json
from datetime import datetime
from io import BytesIO
from typing import Any, Dict, Optional

import tenacity
from botocore.config import Config as BotoConfig
from playwright.async_api import Page

from ..config import get_config
from ..errors import AnalysisError, BotDetectionError
from ..utils.logger import log
from ..utils.url_utils import ensure_absolute


class PageAnalyzerTool:
    """Analyzes a page to determine category extraction strategy."""

    def __init__(self, agent: "CategoryExtractionAgent") -> None:
        self.agent = agent
        self.config = get_config()
        self._bedrock = None

    @property
    def bedrock(self):
        """Lazy-load Bedrock runtime client."""
        if self._bedrock is None:
            import boto3

            self._bedrock = boto3.client(
                "bedrock-runtime",
                region_name=self.config.aws_region,
                config=BotoConfig(retries={"max_attempts": self.config.max_retries}),
            )
        return self._bedrock

    async def analyze(self, url: str, force_refresh: bool = False) -> Dict[str, Any]:
        """Analyze the URL and return extraction strategy insights."""
        page = self._require_page()

        log.info("Analyzing page: %s", url)
        await self._navigate(page, url, force_refresh)
        await self._handle_cookie_consent(page)
        await self._dismiss_popups(page)

        screenshot_b64 = await self._capture_screenshot(page)
        simplified_html = await self._get_simplified_html(page)

        response = await self._call_bedrock(url, screenshot_b64, simplified_html)
        analysis = self._parse_response(response, url)

        self.agent.state["analysis"] = analysis
        return analysis

    def _require_page(self) -> Page:
        if not self.agent.page:
            raise AnalysisError("Agent page not initialized. Call initialize_browser() first.")
        return self.agent.page

    async def _navigate(self, page: Page, url: str, force_refresh: bool) -> None:
        if not force_refresh and page.url == url:
            log.debug("Reusing existing page session for %s", url)
            return
        try:
            await page.goto(url, wait_until="networkidle", timeout=self.config.browser_timeout)
            await page.wait_for_timeout(2000)
        except Exception as exc:  # noqa: BLE001
            raise AnalysisError(f"Failed to load {url}: {exc}") from exc

    async def _handle_cookie_consent(self, page: Page) -> None:
        selectors = [
            "button:has-text('Accept')",
            "button:has-text('I Agree')",
            "#accept-cookies",
            "button[aria-label='Accept cookies']",
        ]
        for selector in selectors:
            try:
                button = await page.query_selector(selector)
                if button:
                    await button.click()
                    await page.wait_for_timeout(750)
                    log.debug("Accepted cookies via %s", selector)
                    return
            except Exception:
                continue

    async def _dismiss_popups(self, page: Page) -> None:
        selectors = [
            "button.close",
            "button[aria-label='Close']",
            ".modal-close",
            "#closeButton",
        ]
        for selector in selectors:
            try:
                popup = await page.query_selector(selector)
                if popup:
                    await popup.click()
                    await page.wait_for_timeout(500)
            except Exception:
                continue

    async def _capture_screenshot(self, page: Page) -> str:
        data = await page.screenshot(full_page=True, type="png")
        return base64.b64encode(data).decode("ascii")

    async def _get_simplified_html(self, page: Page) -> str:
        script = """
            () => {
                const clone = document.body.cloneNode(true);
                clone.querySelectorAll('script, style, noscript').forEach(node => node.remove());
                return clone.outerHTML.slice(0, 50000);
            }
        """
        return await page.evaluate(script)

    @tenacity.retry(stop=tenacity.stop_after_attempt(3), wait=tenacity.wait_fixed(2), reraise=True)
    async def _call_bedrock(self, url: str, screenshot_b64: str, html: str) -> Dict[str, Any]:
        prompt = self._build_prompt(url, html)
        body = json.dumps(
            {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": self.config.max_tokens,
                "temperature": self.config.model_temperature,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": screenshot_b64}},
                        ],
                    }
                ],
            }
        )
        response = self.bedrock.invoke_model(modelId=self.config.model_id, body=body)
        payload = json.loads(response["body"].read())
        return payload

    def _build_prompt(self, url: str, html: str) -> str:
        return (
            "You are inspecting an e-commerce homepage. "
            "Identify the navigation pattern, category selectors, interactions, "
            "and potential obstacles. Provide CSS selectors that can be used with Playwright."\
            f"\nURL: {url}\nHTML snippet:\n{html[:5000]}"
        )

    def _parse_response(self, payload: Dict[str, Any], base_url: str) -> Dict[str, Any]:
        try:
            text = payload["output"]["content"][0]["text"]
            structured = json.loads(text)
            self._normalize_selectors(structured, base_url)
            return {
                "navigation_type": structured.get("navigation_type", "unknown"),
                "selectors": structured.get("selectors", {}),
                "interactions": structured.get("interactions", []),
                "confidence": structured.get("confidence", 0.5),
                "notes": structured.get("notes", []),
                "analyzed_at": datetime.utcnow().isoformat(),
            }
        except KeyError as exc:
            raise AnalysisError(f"Malformed response from Bedrock: {payload}") from exc
        except json.JSONDecodeError as exc:
            raise AnalysisError("Claude returned non-JSON analysis output") from exc

    def _normalize_selectors(self, structured: Dict[str, Any], base_url: str) -> None:
        selectors = structured.get("selectors", {})
        interactions = structured.get("interactions", [])
        # Ensure any URLs in selectors/interactions are absolute
        for key, value in selectors.items():
            if key.endswith("_url") and isinstance(value, str):
                selectors[key] = ensure_absolute(value, base_url)
        for interaction in interactions:
            if isinstance(interaction, dict) and "target_url" in interaction:
                interaction["target_url"] = ensure_absolute(interaction["target_url"], base_url)
```

> **Data contract**: The tool **must** return JSON-serializable data. Downstream tools rely on `selectors` keys like `nav_container`, `category_links`, and optional `subcategory_items`.

## 🔧 Implementation Steps

1. **Create module scaffold** under `tools/` and wire imports in `tools/__init__.py` if needed.
2. **Implement navigation helpers** for cookie consent, popups, and forced refresh.
3. **Add screenshot + HTML capture** using Playwright APIs described in the implementation guide.
4. **Integrate Bedrock** with boto3. Reuse AWS credentials from Task 2. Include retries and helpful logs (start/end, payload size).
5. **Parse LLM response**: Expect Claude to return JSON (per Implementation Prompt). Validate shape and provide defaults.
6. **Normalize selectors** ensuring any relative URLs are made absolute via `ensure_absolute` helper (will be built in Task 6 utilities if not already).
7. **Update agent state** so later components see `agent.state["analysis"]`.
8. **Add docstrings + type hints** and ensure tenacity/backoff decorators follow async pattern.

## ✅ Validation Checklist

- [ ] `poetry run python -c "from src.ai_agents.category_extractor.tools.page_analyzer import PageAnalyzerTool"`
- [ ] Manual call to `analyze('https://example.com')` (with headless browser) returns dict containing `navigation_type`, `selectors`, `confidence`
- [ ] Screenshot saved to temp for debugging (optional) and base64 string length > 0
- [ ] Bedrock invocation logged with model ID and timing
- [ ] Errors from Claude produce `AnalysisError` with helpful message
- [ ] Retry decorator confirmed (simulate failure by raising in `_call_bedrock`)

## 🧪 Manual Testing

```python
import asyncio

from src.ai_agents.category_extractor.agent import CategoryExtractionAgent

async def main() -> None:
    agent = CategoryExtractionAgent(retailer_id=999, site_url="https://example.com")
    await agent.initialize_browser()
    analysis = await agent.page_analyzer.analyze("https://example.com")
    print(analysis)
    await agent.cleanup()

asyncio.run(main())
```

## 📝 Deliverables

1. `page_analyzer.py` with production-ready implementation
2. Optional debug helper to dump Claude output when `LOG_LEVEL=DEBUG`
3. Notes added to `MASTER_TASKLIST.md` after completion (actual time, blockers)

## 🚨 Common Issues & Solutions

| Issue | Symptom | Fix |
|-------|---------|-----|
| Bedrock returns validation error | HTTP 400 during `invoke_model` | Ensure prompt content <= token limit, include `anthropic_version` |
| Screenshot dimension problems | Partial captures or blank images | Use `full_page=True` and ensure page fully loaded before capture |
| JSON decode failure | Claude response not JSON | Update prompt to instruct JSON output; log raw text for debugging |
| Bot detection triggered | Page shows captcha | Raise `BotDetectionError` with context and instruct retries/different strategy |
| Missing selectors | Response lacks required keys | Add fallback defaults and log warning; consider augmenting prompt |

## 📚 Next Steps

After completing Task 5:
1. Update status in `MASTER_TASKLIST.md`.
2. Commit tool implementation and any supporting utilities.
3. Proceed to **Task 6: Category Extractor Tool** to consume the analysis output and perform hierarchical extraction.

**Last Updated**: 2025-09-30
