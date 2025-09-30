"""Main AI agent orchestrating category extraction."""
from __future__ import annotations

from typing import Any, Dict, Optional

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from .config import get_config
from .database import CategoryDatabase
from .errors import AnalysisError, BotDetectionError, ExtractorError, NavigationError
from .utils.logger import get_logger
from .blueprints.loader import load_blueprint
from .blueprints.executor import execute_blueprint

try:  # pragma: no cover - strands may be unavailable in test environment
    from strands import Agent as StrandsAgent
except ImportError:  # pragma: no cover
    StrandsAgent = None  # type: ignore[misc]


class CategoryExtractionAgent:
    """Coordinates browser automation, LLM tools, and persistence."""

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
        self.logger = get_logger(retailer_id)
        self.state: Dict[str, Any] = {
            "stage": "initialized",
            "categories_found": 0,
            "analysis": None,
            "blueprint_path": None,
            "errors": [],
        }

        # Create tools first
        from .tools.page_analyzer import PageAnalyzerTool
        from .tools.category_extractor import CategoryExtractorTool
        from .tools.blueprint_generator import BlueprintGeneratorTool

        self.page_analyzer = PageAnalyzerTool(self)
        self.category_extractor = CategoryExtractorTool(self)
        self.blueprint_generator = BlueprintGeneratorTool(self)
        
        # Create agent (tools registered after creation in _register_tools)
        self.agent = self._create_strands_agent()
        self._register_tools()

    def _create_strands_agent(self) -> Any:
        if StrandsAgent is None:
            raise ImportError(
                "Strands Agents SDK is required. Install strands-agents to use CategoryExtractionAgent."
            )
        
        # Create agent based on configured provider
        provider = self.config.llm_provider.lower()
        
        if provider == "ollama":
            from strands.models.ollama import OllamaModel
            model = OllamaModel(
                host=self.config.ollama_host,
                model_id=self.config.ollama_model,
                temperature=self.config.model_temperature,
                keep_alive=self.config.ollama_keep_alive,
            )
            return StrandsAgent(model=model, system_prompt=self._system_prompt())
        
        elif provider == "openai":
            from strands.models.openai import OpenAIModel
            model = OpenAIModel(
                model_id=self.config.openai_model,
                api_key=self.config.openai_api_key,
                base_url=self.config.openai_base_url,
                temperature=self.config.model_temperature,
            )
            return StrandsAgent(model=model, system_prompt=self._system_prompt())
        
        elif provider == "anthropic":
            from strands.models.anthropic import AnthropicModel
            model = AnthropicModel(
                model_id=self.config.anthropic_model,
                api_key=self.config.anthropic_api_key,
                temperature=self.config.model_temperature,
            )
            return StrandsAgent(model=model, system_prompt=self._system_prompt())
        
        else:
            # Fallback to basic configuration
            return StrandsAgent(
                model_provider=provider,
                model_id=self.config.model_id,
                system_prompt=self._system_prompt()
            )

    def _system_prompt(self) -> str:
        return (
            "You are an expert e-commerce scraping assistant. "
            "Identify navigation patterns, extract hierarchical categories, "
            "persist results, and generate reusable blueprints. "
            "Use the registered tools, report confidence, and note blockers."
        )

    def _register_tools(self) -> None:
        """Register tools with Strands 1.10 using the @tool decorator pattern."""
        # Strands 1.10 uses the @agent.tool() decorator
        # We need to wrap our methods as standalone functions
        
        @self.agent.tool()
        async def analyze_page(url: str, force_refresh: bool = False) -> dict:
            """Analyze webpage structure to determine category extraction strategy.
            
            Args:
                url: The URL to analyze
                force_refresh: Whether to force page reload
                
            Returns:
                Analysis results with navigation type, selectors, and confidence
            """
            return await self.page_analyzer.analyze(url, force_refresh)
        
        @self.agent.tool()
        async def extract_categories(url: str, parent_id: int = None, depth: int = 0) -> dict:
            """Extract categories from a webpage.
            
            Args:
                url: The URL to extract categories from
                parent_id: Parent category ID (None for top-level)
                depth: Current recursion depth
                
            Returns:
                Extracted categories with hierarchy information
            """
            return await self.category_extractor.extract(url, parent_id, depth)
        
        @self.agent.tool()
        async def generate_blueprint(analysis: dict, categories: list) -> dict:
            """Generate a reusable blueprint from extraction results.
            
            Args:
                analysis: Page analysis results
                categories: Extracted categories
                
            Returns:
                Blueprint path and metadata
            """
            return await self.blueprint_generator.generate(analysis, categories)

    async def initialize_browser(self) -> None:
        if self.browser:
            self.logger.debug("Browser already initialised")
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
        self.logger.info("Browser initialised for {}", self.site_url)

    async def run_extraction(self) -> Dict[str, Any]:
        prompt = (
            f"Extract hierarchical product categories from {self.site_url}. "
            "Workflow: analyze_page -> extract_categories -> persist -> generate_blueprint. "
            f"Use retailer_id={self.retailer_id}. Return summary and confidence."
        )

        try:
            await self.initialize_browser()
            await self.db.connect()
            self.logger.info("Starting LLM-guided extraction")
            result = await self.agent.arun(prompt)
            self.state["stage"] = "completed"
            return {"success": True, "result": result, "state": self.state}
        except (NavigationError, AnalysisError, BotDetectionError) as exc:
            await self._record_error(str(exc))
            return {"success": False, "error": str(exc), "state": self.state}
        except Exception as exc:  # noqa: BLE001
            self.logger.exception("Unexpected failure during extraction")
            await self._record_error(str(exc))
            return {
                "success": False,
                "error": "Unexpected error during extraction",
                "state": self.state,
            }
        finally:
            await self.cleanup()

    async def run_blueprint(self, blueprint_path: str) -> Dict[str, Any]:
        try:
            await self.initialize_browser()
            blueprint = load_blueprint(blueprint_path)
            categories = await execute_blueprint(self.page, blueprint, self.site_url)
            self.state["categories"] = categories
            self.state["categories_found"] = len(categories)
            self.state["stage"] = "completed"
            return {"success": True, "categories": categories, "state": self.state}
        except Exception as exc:  # noqa: BLE001
            self.logger.exception("Blueprint execution failed")
            await self._record_error(str(exc))
            return {"success": False, "error": str(exc), "state": self.state}
        finally:
            await self.cleanup()

    async def _record_error(self, message: str) -> None:
        self.state.setdefault("errors", []).append(message)
        self.state["stage"] = "failed"
        self.logger.error("Extraction error: {}", message)

    async def cleanup(self) -> None:
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
            self.playwright = None
            self.browser = None
            self.context = None
            self.page = None
            self.logger.info("Cleanup complete")


__all__ = ["CategoryExtractionAgent"]
