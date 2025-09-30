"""Execute stored blueprints without invoking the LLM."""
from __future__ import annotations

from typing import Any, Dict, List

from playwright.async_api import Page

from ..errors import BlueprintError
from ..utils.logger import get_logger
from ..utils.url_utils import ensure_absolute, normalize_url


async def execute_blueprint(page: Page, blueprint, base_url: str) -> List[Dict[str, Any]]:
    logger = get_logger()
    selectors = blueprint.selectors
    interactions = blueprint.interactions

    await _perform_interactions(page, interactions, selectors, logger)
    categories = await _extract_categories(page, selectors, base_url)
    return categories


async def _perform_interactions(page: Page, interactions, selectors, logger) -> None:
    for step in interactions:
        action = step.get("action")
        target_key = step.get("target")
        target_selector = selectors.get(target_key, target_key)
        wait_for = step.get("wait_for")
        timeout = step.get("timeout", 2000)

        if action == "hover":
            element = await page.wait_for_selector(target_selector, timeout=timeout)
            await element.hover()
        elif action == "click":
            element = await page.wait_for_selector(target_selector, timeout=timeout)
            await element.click()
        elif action == "wait":
            await page.wait_for_timeout(step.get("duration", 500))
        elif action == "scroll":
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
        else:
            logger.debug("Skipping unknown action {}", action)

        if wait_for:
            await page.wait_for_selector(selectors.get(wait_for, wait_for), timeout=timeout)


async def _extract_categories(page: Page, selectors: Dict[str, Any], base_url: str) -> List[Dict[str, Any]]:
    link_selector = selectors.get("category_links")
    if not link_selector:
        raise BlueprintError("Blueprint missing category_links selector")

    elements = await page.query_selector_all(link_selector)
    categories: List[Dict[str, Any]] = []
    for element in elements:
        try:
            name = (await element.inner_text()).strip()
            url = await element.get_attribute("href")
            if not url:
                continue
            categories.append(
                {
                    "name": name,
                    "url": normalize_url(ensure_absolute(url, base_url)),
                    "depth": 0,
                    "parent_id": None,
                }
            )
        except Exception:
            continue

    if not categories:
        raise BlueprintError("Blueprint execution returned no categories")
    return categories


__all__ = ["execute_blueprint"]
