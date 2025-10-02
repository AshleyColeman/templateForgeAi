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
        elif navigation_type in {"sidebar", "accordion", "filter_sidebar"}:
            categories = await self._extract_click_navigation(page, strategy)
        else:
            categories = await self._extract_generic_links(page, strategy)

        # Universal fallback: If no categories found OR extraction looks suspicious, try common patterns
        needs_fallback = False
        
        if len(categories) == 0:
            self.logger.warning("No categories found with navigation_type={}, trying universal fallback...", navigation_type)
            needs_fallback = True
        elif len(categories) < 5:
            # Very few categories - might be wrong (menu buttons, not categories)
            self.logger.warning("Only {} categories found, seems suspicious, trying fallback...", len(categories))
            needs_fallback = True
        elif self._looks_like_noise(categories):
            # Categories look like navigation noise (Sign In, Cart, etc.)
            self.logger.warning("Categories look like navigation noise, trying fallback...")
            needs_fallback = True
        
        if needs_fallback:
            fallback_categories = await self._fallback_extraction(page, strategy)
            if len(fallback_categories) > len(categories):
                self.logger.info("Fallback found more categories ({} vs {}), using fallback", len(fallback_categories), len(categories))
                categories = fallback_categories
                self.agent.state["extraction_method"] = "fallback"
            elif len(categories) > 0:
                self.agent.state["extraction_method"] = "ai"
            else:
                self.agent.state["extraction_method"] = "fallback"
        else:
            self.agent.state["extraction_method"] = "ai"

        processed = self._post_process(categories, target_url)
        validate_hierarchy(processed)
        self.agent.state["categories_found"] = len(processed)
        self.agent.state["categories"] = processed
        return {"categories": processed, "total": len(processed), "navigation_type": navigation_type}

    def _looks_like_noise(self, categories: List[Category]) -> bool:
        """Check if extracted categories look like navigation noise."""
        noise_keywords = [
            'sign in', 'login', 'register', 'cart', 'basket', 'wishlist',
            'account', 'checkout', 'search', 'help', 'contact', 'about',
            'skip to', 'menu', 'close', 'open', 'toggle', 'show', 'hide',
            'store locator', 'stores', 'find a store', 'rewards', 'loyalty',
            'track order', 'my orders', 'my account', 'sign up', 'subscribe'
        ]
        
        # Also check for generic single-word categories that are likely wrong
        generic_words = ['menu', 'home', 'shop', 'browse', 'stores', 'rewards']
        
        noise_count = 0
        for cat in categories[:10]:  # Check first 10
            name_lower = cat.get('name', '').lower().strip()
            
            # Check noise keywords
            if any(keyword in name_lower for keyword in noise_keywords):
                noise_count += 1
            # Check if it's a single generic word
            elif name_lower in generic_words:
                noise_count += 1
        
        # If more than 50% look like noise, it's probably wrong
        return noise_count > len(categories[:10]) * 0.5

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

        # Try to activate sidebar if there's a trigger button
        await self._activate_sidebar_menu(page, strategy)
        
        categories: List[Category] = []
        
        # Wait for sidebar to be visible
        await page.wait_for_timeout(500)
        
        # First, extract all top-level categories
        blocks = await page.query_selector_all(container)
        self.logger.info("Found {} navigation blocks with selector: {}", len(blocks), container)
        
        # Track unique URLs to avoid duplicates across blocks
        seen_urls = set()
        max_blocks_to_process = 5  # Limit to first 5 blocks to avoid duplicates
        
        for idx, block in enumerate(blocks):
            # Stop if we've processed enough blocks
            if idx >= max_blocks_to_process:
                self.logger.info("Stopping after {} blocks to avoid duplicates", max_blocks_to_process)
                break
                
            links = await block.query_selector_all(link_selector)
            self.logger.info("Block {}/{}: Found {} links", idx + 1, min(len(blocks), max_blocks_to_process), len(links))
            
            block_categories = 0
            for link in links:
                try:
                    # Check if this is an expandable item (has arrow/chevron)
                    is_expandable = await self._is_expandable(link)
                    
                    name, url = await self._extract_link(link, None)
                    
                    # Skip if we've already seen this URL
                    if url in seen_urls:
                        continue
                    seen_urls.add(url)
                    
                    self.logger.debug("Extracted: {} -> {} (expandable: {})", name, url, is_expandable)
                    parent_id = self._next_category_id()
                    categories.append(self._build_category(parent_id, name, url, 0, None))
                    block_categories += 1
                    
                    # If expandable, click to reveal subcategories
                    if is_expandable:
                        subcats = await self._extract_expandable_children(page, link, parent_id)
                        categories.extend(subcats)
                        
                except Exception as exc:  # noqa: BLE001
                    self.logger.debug("Skipping link due to error: {}", exc)
                    continue
            
            self.logger.info("Block {}: Extracted {} unique categories", idx, block_categories)
        
        self.logger.info("Total categories extracted: {} (from {} blocks)", len(categories), min(len(blocks), max_blocks_to_process))
        return categories
    
    async def _fallback_extraction(self, page: Page, strategy: Dict[str, Any]) -> List[Category]:
        """Fallback extraction using common e-commerce patterns."""
        fallback_patterns = [
            # Sidebar filters/categories
            {"container": "aside", "links": "a"},
            {"container": ".sidebar", "links": "a"},
            {"container": ".filters", "links": "a"},
            {"container": "[class*='category']", "links": "a"},
            {"container": "[class*='filter']", "links": "a"},
            # Navigation menus
            {"container": "nav", "links": "a"},
            {"container": ".navigation", "links": "a"},
            {"container": "[role='navigation']", "links": "a"},
        ]
        
        categories: List[Category] = []
        seen_urls = set()
        
        for pattern in fallback_patterns:
            try:
                containers = await page.query_selector_all(pattern["container"])
                if not containers:
                    continue
                
                self.logger.info("Fallback: Found {} containers with selector: {}", len(containers), pattern["container"])
                
                for container in containers[:3]:  # Limit to first 3 containers
                    links = await container.query_selector_all(pattern["links"])
                    self.logger.info("Fallback: Found {} links in container", len(links))
                    
                    for link in links[:50]:  # Limit to 50 links per container
                        try:
                            name, url = await self._extract_link(link, None)
                            
                            # Filter out non-category links (common patterns)
                            if any(skip in url.lower() for skip in ['login', 'register', 'cart', 'checkout', 'account', 'search', 'contact', 'about', 'help', 'faq']):
                                continue
                            
                            # Skip duplicates
                            if url in seen_urls:
                                continue
                            seen_urls.add(url)
                            
                            # Only add if it looks like a category (has meaningful text)
                            if len(name) > 2 and len(name) < 100:
                                cat_id = self._next_category_id()
                                categories.append(self._build_category(cat_id, name, url, 0, None))
                                
                        except Exception:  # noqa: BLE001
                            continue
                
                # If we found categories, stop trying other patterns
                if categories:
                    self.logger.info("Fallback: Extracted {} categories with pattern: {}", len(categories), pattern["container"])
                    break
                    
            except Exception as exc:  # noqa: BLE001
                self.logger.debug("Fallback pattern {} failed: {}", pattern["container"], exc)
                continue
        
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

    async def _is_expandable(self, element) -> bool:
        """Check if a category item is expandable (has arrow/chevron icon)."""
        try:
            # Look for common expansion indicators
            indicators = [
                "svg",  # SVG icons
                ".icon",
                ".arrow",
                ".chevron",
                "[class*='expand']",
                "[class*='toggle']",
            ]
            
            for indicator in indicators:
                icon = await element.query_selector(indicator)
                if icon:
                    return True
            
            # Check parent for expansion indicators
            parent = await element.evaluate_handle("el => el.parentElement")
            if parent:
                for indicator in indicators:
                    icon = await parent.query_selector(indicator)
                    if icon:
                        return True
                        
            return False
        except Exception:  # noqa: BLE001
            return False

    async def _extract_expandable_children(
        self, page: Page, parent_element, parent_id: int
    ) -> List[Category]:
        """Extract subcategories from an expandable parent category."""
        subcategories: List[Category] = []
        
        try:
            # Click to expand
            await parent_element.click()
            await page.wait_for_timeout(800)  # Wait for expansion animation
            
            # Look for subcategory container
            # Common patterns for nested/child lists
            child_selectors = [
                "ul",  # Direct child list
                "+ ul",  # Adjacent sibling list
                "~ ul",  # Following sibling list
                "[class*='submenu']",
                "[class*='child']",
                "[class*='nested']",
            ]
            
            for selector in child_selectors:
                try:
                    child_container = await parent_element.query_selector(selector)
                    if not child_container:
                        # Try finding in parent's parent
                        parent_parent = await parent_element.evaluate_handle("el => el.parentElement")
                        if parent_parent:
                            child_container = await parent_parent.query_selector(selector)
                    
                    if child_container:
                        # Check if it's visible
                        is_visible = await child_container.is_visible()
                        if is_visible:
                            # Extract all links from child container
                            child_links = await child_container.query_selector_all("a")
                            self.logger.debug("Found {} child links", len(child_links))
                            
                            for child_link in child_links:
                                try:
                                    name, url = await self._extract_link(child_link, None)
                                    child_id = self._next_category_id()
                                    subcategories.append(
                                        self._build_category(child_id, name, url, 1, parent_id)
                                    )
                                except Exception:  # noqa: BLE001
                                    continue
                            
                            if subcategories:
                                break  # Found subcategories, no need to try other selectors
                                
                except Exception:  # noqa: BLE001
                    continue
            
            # Click again to collapse (cleanup)
            if subcategories:
                await parent_element.click()
                await page.wait_for_timeout(300)
                
        except Exception as exc:  # noqa: BLE001
            self.logger.debug("Error extracting expandable children: {}", exc)
        
        return subcategories

    async def _activate_sidebar_menu(self, page: Page, strategy: Dict[str, Any]) -> None:
        """Try to activate sidebar menu if there's a trigger button (e.g., 'Shop by Products')."""
        trigger_selectors = [
            "button:has-text('Shop by Products')",
            "a:has-text('Shop by Products')",
            "[data-testid='shop-by-products']",
            ".shop-by-products",
            # Additional common patterns
            "button:has-text('Categories')",
            "button:has-text('Browse')",
            "[aria-label*='Shop']",
            "[aria-label*='Categories']",
        ]
        
        for selector in trigger_selectors:
            try:
                trigger = await page.query_selector(selector)
                if trigger:
                    # Check if it's visible
                    is_visible = await trigger.is_visible()
                    if is_visible:
                        self.logger.info("Found sidebar trigger: {}", selector)
                        await trigger.click()
                        await page.wait_for_timeout(1000)  # Wait for sidebar to appear
                        self.logger.info("Activated sidebar menu")
                        return
            except Exception as exc:  # noqa: BLE001
                self.logger.debug("Trigger selector {} failed: {}", selector, exc)
                continue
        
        self.logger.debug("No sidebar trigger found, menu may already be visible")

    def _post_process(self, categories: List[Category], base_url: str) -> List[Category]:
        deduped: Dict[Tuple[str, int], Category] = {}
        for category in categories:
            category["url"] = normalize_url(ensure_absolute(category["url"], base_url))
            key = (category["url"], category.get("depth", 0))
            if key not in deduped:
                deduped[key] = category
        return list(deduped.values())


__all__ = ["CategoryExtractorTool"]
