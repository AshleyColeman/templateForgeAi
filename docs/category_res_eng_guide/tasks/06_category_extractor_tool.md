# Task 6: Category Extractor Tool

**Status**: 🔒 Blocked (depends on Task 5)  
**Estimated Time**: 8-10 hours  
**Dependencies**: Task 4 (Core Agent), Task 5 (Page Analyzer)  
**Priority**: High

---

## 📋 Objective

Create the `CategoryExtractorTool` that operationalizes the strategy emitted by the page analyzer. The tool should navigate category structures (hover menus, sidebars, accordions), harvest hierarchical category data, normalize URLs, validate the hierarchy, and update the agent state prior to persistence.

## 🎯 Success Criteria

- [ ] `src/ai_agents/category_extractor/tools/category_extractor.py` implemented
- [ ] Tool exposes `async extract(url: Optional[str] = None) -> Dict[str, Any]`
- [ ] Executes interaction sequence defined by `agent.state["analysis"]["interactions"]`
- [ ] Supports dynamic loading (click/hover/show more) with retry logic
- [ ] Extracts categories into list of dicts including `id`, `name`, `url`, `depth`, `parent_id`
- [ ] Validates data via `validators.validate_category` and `validators.validate_hierarchy`
- [ ] Deduplicates categories by normalized URL + depth
- [ ] Updates `agent.state["categories_found"]` and stores raw results for blueprint generation

## 📝 Specifications

### File: `src/ai_agents/category_extractor/tools/category_extractor.py`

```python
"""Tool for extracting categories using Playwright and LLM strategy."""
from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional, Tuple

from playwright.async_api import Page
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

from ..errors import BotDetectionError, ExtractionError, ValidationError
from ..utils.logger import log
from ..utils.url_utils import ensure_absolute, normalize_url
from .validators import validate_category, validate_hierarchy

Category = Dict[str, Any]


class CategoryExtractorTool:
    """Extracts hierarchical categories based on analyzer output."""

    def __init__(self, agent: "CategoryExtractionAgent") -> None:
        self.agent = agent
        self._next_id = 1

    async def extract(self, url: Optional[str] = None) -> Dict[str, Any]:
        """Run the extraction workflow and return categories + stats."""
        page = self._require_page()
        target_url = url or self.agent.site_url

        await self._navigate(page, target_url)
        strategy = self._get_strategy()

        raw_categories: List[Category] = []
        try:
            if strategy["navigation_type"] == "hover_menu":
                raw_categories = await self._extract_hover_menu(page, strategy)
            elif strategy["navigation_type"] in {"sidebar", "accordion"}:
                raw_categories = await self._extract_click_navigation(page, strategy)
            else:
                raw_categories = await self._extract_generic_links(page, strategy)
        except BotDetectionError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise ExtractionError(f"Extraction failed: {exc}") from exc

        categories = self._post_process(raw_categories, target_url)
        validate_hierarchy(categories)

        self.agent.state["categories_found"] = len(categories)
        self.agent.state["categories"] = categories
        return {
            "categories": categories,
            "total": len(categories),
            "navigation_type": strategy["navigation_type"],
        }

    def _require_page(self) -> Page:
        if not self.agent.page:
            raise ExtractionError("Agent page not initialized. Call initialize_browser() first.")
        return self.agent.page

    async def _navigate(self, page: Page, url: str) -> None:
        if page.url != url:
            await page.goto(url, wait_until="domcontentloaded", timeout=self.agent.config.browser_timeout)
            await page.wait_for_timeout(1500)

    def _get_strategy(self) -> Dict[str, Any]:
        strategy = self.agent.state.get("analysis")
        if not strategy:
            raise ExtractionError("No analysis strategy found. Run PageAnalyzerTool first.")
        return strategy

    async def _extract_hover_menu(self, page: Page, strategy: Dict[str, Any]) -> List[Category]:
        selectors = strategy.get("selectors", {})
        interactions = strategy.get("interactions", [])

        nav_container = selectors.get("nav_container")
        top_level = selectors.get("top_level_items")
        category_link = selectors.get("category_links")

        if not all([nav_container, top_level, category_link]):
            raise ExtractionError("Hover menu extraction requires nav_container, top_level_items, category_links selectors")

        categories: List[Category] = []

        menu_items = await page.query_selector_all(f"{nav_container} >> {top_level}")
        for depth0_index, item in enumerate(menu_items):
            try:
                await item.hover()
                await page.wait_for_timeout(500)
                name, url = await self._extract_link(item, category_link)
                parent_id = None
                current_id = self._next_category_id()
                categories.append(self._build_category(current_id, name, url, 0, parent_id))

                flyout_selector = selectors.get("flyout_panel")
                if flyout_selector:
                    flyout = await page.query_selector(flyout_selector)
                    if flyout:
                        sub_links = await flyout.query_selector_all(selectors.get("subcategory_items", "a"))
                        for sub in sub_links:
                            sub_name, sub_url = await self._extract_link(sub, selectors.get("subcategory_link", "a"))
                            child_id = self._next_category_id()
                            categories.append(self._build_category(child_id, sub_name, sub_url, 1, current_id))
            except Exception as exc:  # noqa: BLE001
                log.warning("Hover extraction error: %s", exc)
                continue
        return categories

    async def _extract_click_navigation(self, page: Page, strategy: Dict[str, Any]) -> List[Category]:
        selectors = strategy.get("selectors", {})
        container = selectors.get("nav_container")
        link_selector = selectors.get("category_links")
        if not (container and link_selector):
            raise ExtractionError("Click navigation requires nav_container and category_links selectors")

        categories: List[Category] = []
        containers = await page.query_selector_all(container)
        for block in containers:
            links = await block.query_selector_all(link_selector)
            for link in links:
                try:
                    name, url = await self._extract_link(link, None)
                    current_id = self._next_category_id()
                    categories.append(self._build_category(current_id, name, url, 0, None))
                except Exception as exc:  # noqa: BLE001
                    log.debug("Skipping link due to error: %s", exc)
                    continue
        return categories

    async def _extract_generic_links(self, page: Page, strategy: Dict[str, Any]) -> List[Category]:
        selector = strategy.get("selectors", {}).get("category_links")
        if not selector:
            raise ExtractionError("Generic extraction requires category_links selector")
        elements = await page.query_selector_all(selector)
        categories = []
        for element in elements:
            try:
                name, url = await self._extract_link(element, None)
                current_id = self._next_category_id()
                categories.append(self._build_category(current_id, name, url, 0, None))
            except Exception:
                continue
        return categories

    async def _extract_link(self, element, fallback_selector: Optional[str]) -> Tuple[str, str]:
        handle = element
        if fallback_selector:
            maybe = await element.query_selector(fallback_selector)
            if maybe:
                handle = maybe

        name = (await handle.inner_text()).strip()
        url = await handle.get_attribute("href")
        if not url:
            raise ExtractionError("Category link missing href")
        return name, url

    def _build_category(self, cid: int, name: str, url: str, depth: int, parent_id: Optional[int]) -> Category:
        category = {
            "id": cid,
            "name": name,
            "url": url,
            "depth": depth,
            "parent_id": parent_id,
        }
        validate_category(category)
        return category

    def _next_category_id(self) -> int:
        cid = self._next_id
        self._next_id += 1
        return cid

    def _post_process(self, categories: List[Category], base_url: str) -> List[Category]:
        deduped: Dict[Tuple[str, int], Category] = {}
        for category in categories:
            category["url"] = ensure_absolute(category["url"], base_url)
            category["url"] = normalize_url(category["url"])
            key = (category["url"], category["depth"])
            if key not in deduped:
                deduped[key] = category
        return list(deduped.values())
```

> Extend the extraction helpers (`_extract_hover_menu`, `_extract_click_navigation`, etc.) as needed to cover other navigation patterns emitted by the analyzer (mega menu, tabs, grid). Keep code modular to simplify testing.

## 🔧 Implementation Steps

1. **Create module** in `tools/` and ensure it is importable.
2. **Design strategy interpreter**: map `navigation_type` to concrete helper method(s). Use analyzer output to know which selectors/interactions to follow.
3. **Implement interaction playback**: For dynamic steps (click/hover/scroll/show more) reuse interaction metadata (action, target, wait_for, optional). Consider adding `_execute_interactions()` helper that loops through instructions prior to extracting link sets.
4. **Extract categories**: Build hierarchical structure using simple integer IDs (incremental) and parent IDs. Keep `depth` consistent with traversal.
5. **Post-process results**: Normalize and deduplicate categories. Sort by depth/name if necessary before returning.
6. **Validate**: Use `validate_category` per item and `validate_hierarchy` for the final list. Bubble `ValidationError` up to the agent with useful context.
7. **Update agent state**: Track `categories_found` and store full category list for Task 7 blueprint generation.
8. **Instrument logging**: Info-level summary, debug-level details for each navigation block, warnings for skipped entries.

## ✅ Validation Checklist

- [ ] Unit tests cover `_post_process`, `_build_category`, and navigation helpers with Playwright mocks
- [ ] Manual run against at least one real site yields >0 categories
- [ ] Deduplication prevents identical URLs at same depth
- [ ] Validation errors surface meaningful message (e.g., missing name/href)
- [ ] Agent state updated with categories list and count
- [ ] MyPy passes (no `Any` leakage)

## 🧪 Manual Testing

```python
import asyncio

from src.ai_agents.category_extractor.agent import CategoryExtractionAgent

async def main() -> None:
    agent = CategoryExtractionAgent(retailer_id=5, site_url="https://example.com")
    await agent.initialize_browser()
    analysis = {
        "navigation_type": "generic",
        "selectors": {"category_links": "nav a"},
        "interactions": [],
    }
    agent.state["analysis"] = analysis
    result = await agent.category_extractor.extract("https://example.com")
    print(result["total"], "categories captured")
    await agent.cleanup()

asyncio.run(main())
```

## 📝 Deliverables

1. `category_extractor.py` with fully implemented strategy execution
2. Supporting updates to `validators.py`, `utils/url_utils.py`, etc., if gaps exist
3. Local manual run notes (e.g., which retailer/page tested)
4. Task log update in `MASTER_TASKLIST.md`

## 🚨 Common Issues & Solutions

| Issue | Symptom | Fix |
|-------|---------|-----|
| Analyzer selectors missing | Keys absent in strategy | Add guard clauses raising `ExtractionError` with actionable message |
| Dynamic loading not triggered | Subcategories missing | Ensure interactions loop clicks `show_more` buttons before scraping |
| Duplicate categories | CLI output contains repeats | Confirm `_post_process` key uses normalized URL and depth |
| Missing href values | Some anchors triggered via JavaScript | Fallback to evaluating `data-url` or raising validation error |
| Bot detection page | Page replaced with captcha mid-run | Raise `BotDetectionError` so agent can retry with delays or manual intervention |

## 📚 Next Steps

After delivering Task 6:
1. Update `MASTER_TASKLIST.md` status/time.
2. Commit code (tool, validators, tests).
3. Continue to **Task 7: Blueprint Generator Tool** using the captured category data.

**Last Updated**: 2025-09-30
