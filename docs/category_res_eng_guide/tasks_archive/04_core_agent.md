# Task 4: Core Agent Implementation

**Status**: 🔒 Blocked (depends on Tasks 1-3)  
**Estimated Time**: 8-10 hours  
**Dependencies**: Task 1 (Environment Setup), Task 2 (Configuration), Task 3 (Database)  
**Priority**: Critical (foundation for all remaining work)

---

## 📋 Objective

Build the `CategoryExtractionAgent` orchestrator that coordinates the AI workflow, initializes the browser, registers tools, communicates with Ollama/OpenAI/Anthropic via the Strands Agents SDK, and manages lifecycle concerns (cleanup, error capture, and state tracking).

## 🎯 Success Criteria

- [ ] `src/ai_agents/category_extractor/agent.py` created with `CategoryExtractionAgent` class
- [ ] Agent initializes Strands SDK with Bedrock model + system prompt
- [ ] Playwright browser/context/page lifecycle handled with async/await
- [ ] Tool registration wires PageAnalyzer, CategoryExtractor, BlueprintGenerator, and Database saver helpers
- [ ] `run_extraction()` executes full workflow, updates state, and returns structured results
- [ ] Errors elevate through custom exceptions and are logged with Loguru
- [ ] Cleanup closes browser, stops Playwright, and releases DB connections even on failure
- [ ] Minimal smoke test proves agent bootstraps without hitting the network (mock tools)

## 📝 Specifications

### File: `src/ai_agents/category_extractor/agent.py`

```python
"""Main AI agent orchestrating category extraction."""
from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional

from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from strands import Agent as StrandsAgent

from .config import get_config
from .database import CategoryDatabase
from .errors import (
    AnalysisError,
    BotDetectionError,
    ExtractorError,
    NavigationError,
)
from .utils.logger import log


class CategoryExtractionAgent:
    """Coordinates LLM-driven category extraction workflow."""

    def __init__(self, retailer_id: int, site_url: str, headless: Optional[bool] = None) -> None:
        self.retailer_id = retailer_id
        self.site_url = site_url
        self.config = get_config()
        self.headless = headless if headless is not None else self.config.browser_headless

        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

        self.db = CategoryDatabase()
        self.state: Dict[str, Any] = {
            "stage": "initialized",
            "categories_found": 0,
            "analysis": None,
            "blueprint_path": None,
            "errors": [],
        }

        self.agent = StrandsAgent(
            model_provider="bedrock",
            model_id=self.config.model_id,
            region=self.config.aws_region,
            system_prompt=self._system_prompt(),
        )

        self._register_tools()

    def _system_prompt(self) -> str:
        """Return system prompt that drives the LLM behaviour."""
        return (
            "You are an expert e-commerce scraping assistant. "
            "Identify navigation patterns, extract hierarchical categories, "
            "save findings, and generate reusable extraction blueprints. "
            "Be thorough, report confidence, and surface blockers clearly."
        )

    def _register_tools(self) -> None:
        """Register custom tools with the Strands agent."""
        from .tools.page_analyzer import PageAnalyzerTool
        from .tools.category_extractor import CategoryExtractorTool
        from .tools.blueprint_generator import BlueprintGeneratorTool
        from .tools.validators import build_database_tool

        self.page_analyzer = PageAnalyzerTool(self)
        self.category_extractor = CategoryExtractorTool(self)
        self.blueprint_generator = BlueprintGeneratorTool(self)
        self.database_tool = build_database_tool(self)

        self.agent.add_tool(self.page_analyzer.analyze)  # type: ignore[arg-type]
        self.agent.add_tool(self.category_extractor.extract)  # type: ignore[arg-type]
        self.agent.add_tool(self.blueprint_generator.generate)  # type: ignore[arg-type]
        self.agent.add_tool(self.database_tool.persist)  # type: ignore[arg-type]

    async def initialize_browser(self) -> None:
        """Start Playwright, create browser context, and prepare page."""
        if self.browser:
            log.debug("Browser already initialized")
            return

        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-blink-features=AutomationControlled",
            ],
        )
        self.context = await self.browser.new_context(
            viewport={"width": self.config.browser_width, "height": self.config.browser_height},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            locale="en-US",
            timezone_id="Africa/Johannesburg",
        )
        await self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
        """)
        self.page = await self.context.new_page()
        log.info("Browser initialized for %s", self.site_url)

    async def run_extraction(self) -> Dict[str, Any]:
        """Execute the end-to-end extraction workflow."""
        task_prompt = (
            f"Extract hierarchical product categories from {self.site_url}. "
            "Workflow: analyze_page → extract_categories → persist_categories → generate_blueprint. "
            f"Use retailer_id={self.retailer_id}. Report stats and confidence."
        )

        try:
            await self.initialize_browser()
            await self.db.connect()

            log.info("Starting LLM-guided extraction")
            result = await self.agent.arun(task_prompt)
            self.state["stage"] = "completed"
            log.info("Extraction completed successfully")
            return {"success": True, "result": result, "state": self.state}

        except (NavigationError, AnalysisError, BotDetectionError) as exc:
            await self._record_error(str(exc))
            return {"success": False, "error": str(exc), "state": self.state}
        except Exception as exc:  # noqa: BLE001
            log.exception("Unexpected extraction failure")
            await self._record_error(str(exc))
            return {
                "success": False,
                "error": "Unexpected error during extraction",
                "state": self.state,
            }
        finally:
            await self.cleanup()

    async def _record_error(self, message: str) -> None:
        """Append error to state and mark stage as failed."""
        self.state.setdefault("errors", []).append(message)
        self.state["stage"] = "failed"
        log.error("Extraction error: %s", message)

    async def cleanup(self) -> None:
        """Release browser and database resources safely."""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
        finally:
            await self.db.disconnect()
            self.browser = None
            self.context = None
            self.page = None
            self.playwright = None
            log.info("Cleanup complete")


__all__ = ["CategoryExtractionAgent"]
```

> **Note**: Tool imports defer to avoid circular dependencies. The actual tool implementations are part of Tasks 5-7.

## 🔧 Implementation Steps

1. **Create agent module**: Add `agent.py` under `src/ai_agents/category_extractor/` using the specification above as the baseline. Ensure docstrings, type hints, and logging mirror project standards.
2. **Wire configuration + DB**: Reuse `get_config()` and `CategoryDatabase` from previous tasks. Confirm `connect()` and `disconnect()` are awaited in the agent lifecycle.
3. **Integrate Strands**: Instantiate `StrandsAgent` pointing at Bedrock with the configured model and region. Include a purposeful system prompt that enumerates available tools.
4. **Register tools**: Instantiate PageAnalyzerTool, CategoryExtractorTool, BlueprintGeneratorTool, and the database persistence helper (implemented in Task 6/validators). Register their async callables with `self.agent.add_tool`.
5. **Implement browser startup**: Follow stealth/browser settings from the architecture doc. Expose `initialize_browser()` for reuse in integration tests.
6. **Handle workflow**: `run_extraction()` should initialize resources, execute `agent.arun(...)`, capture results, update internal state, and return a dictionary shaped for the CLI.
7. **Error + cleanup discipline**: Any failure must append to `self.state["errors"]`, log context, and still run `cleanup()`.
8. **Expose exports**: Update `__init__.py` if needed so `CategoryExtractionAgent` is importable from the package root (verify Task 1 spec already handles this).

## ✅ Validation Checklist

- [ ] `poetry run python -c "from src.ai_agents.category_extractor.agent import CategoryExtractionAgent"` succeeds
- [ ] `initialize_browser()` opens and closes Chromium without hanging
- [ ] `run_extraction()` returns a dict with `success`, `state`, and no unhandled exceptions when tools are mocked
- [ ] Logs show agent start, tool registration, browser init, and cleanup
- [ ] LLM system prompt references available tools and responsibilities
- [ ] MyPy recognizes type hints (no missing annotations)

## 🧪 Manual Testing

```python
import asyncio
from unittest.mock import AsyncMock

from src.ai_agents.category_extractor.agent import CategoryExtractionAgent


class DummyTool:
    async def analyze(self, url: str):
        return {"navigation_type": "hover_menu"}

    async def extract(self, url: str):
        return [{"id": 1, "name": "Root", "url": url, "depth": 0}]


async def smoke_test() -> None:
    agent = CategoryExtractionAgent(retailer_id=999, site_url="https://example.com")
    agent.page_analyzer = DummyTool()
    agent.category_extractor = DummyTool()
    agent.blueprint_generator.generate = AsyncMock(return_value="/tmp/blueprint.json")
    agent.database_tool.persist = AsyncMock(return_value={"saved": 1})
    agent.agent.arun = AsyncMock(return_value={"summary": "ok"})

    result = await agent.run_extraction()
    assert result["success"] is True


asyncio.run(smoke_test())
```

## 📝 Deliverables

1. `agent.py` implementing the orchestrator class
2. Updated package exports if necessary
3. Smoke test snippet or pytest ensuring initialization works
4. Logs demonstrating lifecycle events during a dry run

## 🚨 Common Issues & Solutions

| Issue | Symptoms | Fix |
|-------|----------|-----|
| Circular imports | `ImportError` when loading tools | Use local imports inside `_register_tools()` as shown |
| Playwright not closed | Stale Chromium processes linger | Ensure `cleanup()` covers page, context, browser, and playwright handles |
| Strands credentials missing | Bedrock call fails with auth error | Verify Task 2 `.env` variables and AWS CLI profile |
| Tool coroutine signature mismatch | Strands raises validation error | Ensure registered methods accept keyword arguments matching tool decorators |
| State not updated | CLI shows zero categories | Tools must update `agent.state`; add helper methods if needed |

## 📚 Next Steps

After completing Task 4:
1. Mark Task 4 as ✅ in `MASTER_TASKLIST.md` with time taken and notes.
2. Commit changes (include agent implementation and supporting tweaks).
3. Proceed to **Task 5: Page Analyzer Tool** to flesh out the first agent tool.

**Last Updated**: 2025-09-30
