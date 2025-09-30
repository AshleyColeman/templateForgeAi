"""Tool for extracting categories from analyzed navigation strategies."""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from playwright.async_api import Page
from strands import tool

from ..errors import ExtractionError
from ..utils.logger import get_logger
from ..utils.url_utils import ensure_absolute, normalize_url
from .validators import validate_category, validate_hierarchy

Category = Dict[str, Any]


class CategoryExtractorTool:
    """Execute analyzer strategies to collect category hierarchies."""

    def __init__(self, agent: "CategoryExtractionAgent") -> None:
        self.agent = agent
        self._next_id = 1
        self.logger = get_logger(agent.retailer_id)

    @tool
    async def extract(self, url: Optional[str] = None) -> Dict[str, Any]:
        page = self._require_page()
        target_url = url or self.agent.site_url

        if page.url != target_url:
            await page.goto(target_url, wait_until="domcontentloaded", timeout=self.agent.config.browser_timeout)
            await page.wait_for_timeout(1500)

        strategy = self._get_strategy()
        navigation_type = strategy.get("navigation_type", "generic")
        
        # Handle pipe-separated navigation types (e.g., "sidebar|hover_menu")
        # Take the first option if multiple are provided
        if "|" in navigation_type:
            navigation_type = navigation_type.split("|")[0].strip()
            self.logger.info("Multiple navigation types detected, using: {}", navigation_type)

        if navigation_type == "hover_menu":
            categories = await self._extract_hover_menu(page, strategy)
        elif navigation_type in {"sidebar", "accordion"}:
            categories = await self._extract_click_navigation(page, strategy)
        else:
            categories = await self._extract_generic_links(page, strategy)

        processed = self._post_process(categories, target_url)
        validate_hierarchy(processed)
        self.agent.state["categories_found"] = len(processed)
        self.agent.state["categories"] = processed
        return {"categories": processed, "total": len(processed), "navigation_type": navigation_type}

    def _require_page(self) -> Page:
        if not self.agent.page:
            raise ExtractionError("Agent page not initialised. Call initialize_browser().")
        return self.agent.page

    def _get_strategy(self) -> Dict[str, Any]:
        analysis = self.agent.state.get("analysis")
        if not analysis:
            raise ExtractionError("No analysis available. Run PageAnalyzerTool first.")
        return analysis

    async def _extract_hover_menu(self, page: Page, strategy: Dict[str, Any]) -> List[Category]:
        selectors = strategy.get("selectors", {})
        nav_container = selectors.get("nav_container")
        top_level = selectors.get("top_level_items")
        category_link = selectors.get("category_links")

        if not all([nav_container, top_level, category_link]):
            raise ExtractionError("Hover menu strategy missing selectors")

        categories: List[Category] = []
        items = await page.query_selector_all(f"{nav_container} >> {top_level}")
        for item in items:
            try:
                await item.hover()
                await page.wait_for_timeout(500)
                name, url = await self._extract_link(item, category_link)
                parent_id = None
                current_id = self._next_category_id()
                categories.append(self._build_category(current_id, name, url, 0, parent_id))

                flyout_selector = selectors.get("flyout_panel")
                sub_selector = selectors.get("subcategory_items")
                sub_link_selector = selectors.get("subcategory_link")
                if flyout_selector and sub_selector:
                    flyout = await page.query_selector(flyout_selector)
                    if flyout:
                        subs = await flyout.query_selector_all(sub_selector)
                        for sub in subs:
                            sub_name, sub_url = await self._extract_link(sub, sub_link_selector)
                            child_id = self._next_category_id()
                            categories.append(self._build_category(child_id, sub_name, sub_url, 1, current_id))
            except Exception as exc:  # noqa: BLE001
                self.logger.warning("Hover extraction error: {}", exc)
                continue
        return categories

    async def _extract_click_navigation(self, page: Page, strategy: Dict[str, Any]) -> List[Category]:
        selectors = strategy.get("selectors", {})
        container = selectors.get("nav_container")
        link_selector = selectors.get("category_links")
        if not container or not link_selector:
            raise ExtractionError("Click navigation missing selectors")

        categories: List[Category] = []
        blocks = await page.query_selector_all(container)
        self.logger.info("Found {} navigation blocks with selector: {}", len(blocks), container)
        
        for idx, block in enumerate(blocks):
            links = await block.query_selector_all(link_selector)
            self.logger.info("Block {}: Found {} links with selector: {}", idx, len(links), link_selector)
            
            for link in links:
                try:
                    name, url = await self._extract_link(link, None)
                    self.logger.debug("Extracted: {} -> {}", name, url)
                    current_id = self._next_category_id()
                    categories.append(self._build_category(current_id, name, url, 0, None))
                except Exception as exc:  # noqa: BLE001
                    self.logger.debug("Skipping link due to error: {}", exc)
                    continue
        
        self.logger.info("Total categories extracted: {}", len(categories))
        return categories

    async def _extract_generic_links(self, page: Page, strategy: Dict[str, Any]) -> List[Category]:
        selector = strategy.get("selectors", {}).get("category_links")
        if not selector:
            raise ExtractionError("Generic strategy missing category_links selector")
        elements = await page.query_selector_all(selector)
        categories: List[Category] = []
        for element in elements:
            try:
                name, url = await self._extract_link(element, None)
                current_id = self._next_category_id()
                categories.append(self._build_category(current_id, name, url, 0, None))
            except Exception:  # noqa: BLE001
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
            category["url"] = normalize_url(ensure_absolute(category["url"], base_url))
            key = (category["url"], category.get("depth", 0))
            if key not in deduped:
                deduped[key] = category
        return list(deduped.values())


__all__ = ["CategoryExtractorTool"]
