# AI Category Extractor: Technical Specification

## System Architecture

### High-Level Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    CLI Interface Layer                           │
│                 (category_agent_cli.py)                          │
│                                                                  │
│  • Argument parsing (argparse/click)                            │
│  • Configuration loading                                         │
│  • Agent initialization                                          │
│  • Progress reporting                                            │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                 Agent Orchestrator Layer                         │
│              (CategoryExtractionAgent)                           │
│                                                                  │
│  • Strands Agent wrapper                                        │
│  • Workflow coordination                                         │
│  • Tool registration                                             │
│  • State management                                              │
│  • Error handling                                                │
└────────────────────────┬────────────────────────────────────────┘
                         │
            ┌────────────┼────────────┐
            │            │            │
            ▼            ▼            ▼
    ┌───────────┐  ┌──────────┐  ┌──────────────┐
    │  Agent    │  │ Browser  │  │  Database    │
    │  Tools    │  │ Manager  │  │  Manager     │
    └─────┬─────┘  └────┬─────┘  └──────┬───────┘
          │             │                │
          │             │                │
          ▼             ▼                ▼
    ┌──────────────────────────────────────────┐
    │         Supporting Services              │
    │                                          │
    │  • PageAnalyzerTool                     │
    │  • CategoryExtractorTool                │
    │  • BlueprintGeneratorTool               │
    │  • PlaywrightBrowserManager             │
    │  • PostgreSQLManager                    │
    │  • TemplateValidator                    │
    └──────────────────────────────────────────┘
```

### Technology Stack Details

#### Core Framework
```python
# Strands Agents SDK
from strands import Agent, Tool
from strands.tools import tool

# Amazon Bedrock (default provider)
# Model: Claude 4 Sonnet (us.anthropic.claude-sonnet-4-20250514-v1:0)
```

#### Browser Automation
```python
# Playwright for Python
from playwright.async_api import async_playwright, Browser, Page
import playwright

# Advantages over Puppeteer:
# - Better async/await support in Python
# - Built-in network interception
# - Multi-browser support (Chromium, Firefox, WebKit)
# - Better screenshot capabilities
```

#### Database Layer
```python
# PostgreSQL with asyncpg
import asyncpg
from typing import List, Dict, Any

# Alternative: SQLAlchemy async
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
```

#### Data Validation
```python
# Pydantic for data models
from pydantic import BaseModel, Field, HttpUrl, validator
from typing import Optional, List, Dict
from datetime import datetime
```

## Core Components

### 1. CategoryExtractionAgent

**Purpose**: Main orchestrator that coordinates the entire extraction workflow.

**Class Definition**:
```python
from strands import Agent
from playwright.async_api import Browser
from typing import Optional, Dict, Any
import asyncio

class CategoryExtractionAgent:
    """
    AI-powered agent for extracting product categories from e-commerce sites.
    
    Workflow:
    1. Analyze page structure
    2. Identify category elements
    3. Extract category hierarchy
    4. Validate and store data
    5. Generate blueprint
    """
    
    def __init__(
        self,
        retailer_id: int,
        site_url: str,
        bedrock_region: str = "us-east-1",
        model_id: str = "us.anthropic.claude-sonnet-4-20250514-v1:0",
        headless: bool = True
    ):
        self.retailer_id = retailer_id
        self.site_url = site_url
        self.headless = headless
        
        # Initialize Strands Agent
        self.agent = Agent(
            model_provider="bedrock",
            model_id=model_id,
            region=bedrock_region,
            system_prompt=self._get_system_prompt()
        )
        
        # Browser instance
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        
        # State management
        self.extraction_state: Dict[str, Any] = {
            "stage": "initialized",
            "categories_found": 0,
            "errors": []
        }
        
        # Register custom tools
        self._register_tools()
    
    def _get_system_prompt(self) -> str:
        """Return the agent's system prompt."""
        return """
        You are an expert web scraping agent specializing in e-commerce category extraction.
        
        Your goal is to:
        1. Analyze e-commerce websites to understand their category structure
        2. Identify navigation patterns (hover menus, sidebars, dropdowns)
        3. Extract all product categories with their hierarchical relationships
        4. Generate accurate CSS selectors for extraction
        5. Create reusable blueprints for future scraping
        
        Key principles:
        - Be methodical and thorough
        - Verify your findings before proceeding
        - Handle edge cases gracefully
        - Document your reasoning
        - Prioritize accuracy over speed
        
        Available tools:
        - analyze_page: Capture and analyze page structure
        - extract_categories: Execute category extraction
        - validate_extraction: Verify extracted data
        - save_to_database: Persist categories to PostgreSQL
        - generate_blueprint: Create reusable template
        """
    
    def _register_tools(self):
        """Register custom tools with the agent."""
        from .tools import (
            PageAnalyzerTool,
            CategoryExtractorTool,
            DatabaseSaverTool,
            BlueprintGeneratorTool
        )
        
        # Tool instances
        self.page_analyzer = PageAnalyzerTool(self)
        self.category_extractor = CategoryExtractorTool(self)
        self.db_saver = DatabaseSaverTool(self)
        self.blueprint_generator = BlueprintGeneratorTool(self)
        
        # Register with agent
        self.agent.add_tool(self.page_analyzer.as_tool())
        self.agent.add_tool(self.category_extractor.as_tool())
        self.agent.add_tool(self.db_saver.as_tool())
        self.agent.add_tool(self.blueprint_generator.as_tool())
    
    async def initialize_browser(self):
        """Initialize Playwright browser."""
        from playwright.async_api import async_playwright
        
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-blink-features=AutomationControlled'
            ]
        )
        
        # Create context with realistic settings
        context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='en-US',
            timezone_id='Africa/Johannesburg'
        )
        
        self.page = await context.new_page()
        
        # Enable stealth mode
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
    
    async def run_extraction(self) -> Dict[str, Any]:
        """
        Execute the full category extraction workflow.
        
        Returns:
            Dict with extraction results and statistics
        """
        try:
            await self.initialize_browser()
            
            # Create the main prompt for the agent
            task_prompt = f"""
            Extract all product categories from the website: {self.site_url}
            
            Follow this workflow:
            
            1. ANALYZE: Use the analyze_page tool to understand the site structure
               - Navigate to the URL
               - Capture a screenshot
               - Extract HTML structure
               - Identify where categories are located
            
            2. EXTRACT: Use the extract_categories tool to gather all categories
               - Follow the strategy from analysis
               - Handle interactions (hover, click, scroll)
               - Build the category hierarchy
               - Validate extracted data
            
            3. SAVE: Use save_to_database to persist categories
               - Insert categories with parent-child relationships
               - Set retailer_id to {self.retailer_id}
               - Handle duplicates gracefully
            
            4. BLUEPRINT: Use generate_blueprint to create a template
               - Document the extraction strategy
               - Include selectors and interactions
               - Save for future fast extraction
            
            Provide a detailed summary of:
            - Total categories found
            - Maximum depth
            - Any issues encountered
            - Confidence in extraction accuracy
            """
            
            # Run the agent
            result = await self.agent.arun(task_prompt)
            
            return {
                "success": True,
                "result": result,
                "state": self.extraction_state
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "state": self.extraction_state
            }
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        """Clean up resources."""
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()
```

### 2. PageAnalyzerTool

**Purpose**: Analyze website structure and identify category elements.

**Implementation**:
```python
from strands.tools import tool
from playwright.async_api import Page
from typing import Dict, Any, Optional
import base64
import json

class PageAnalyzerTool:
    """Tool for analyzing page structure using LLM vision capabilities."""
    
    def __init__(self, agent: 'CategoryExtractionAgent'):
        self.agent = agent
    
    @tool
    async def analyze_page(self, url: str) -> Dict[str, Any]:
        """
        Analyze a webpage to identify category structure.
        
        Args:
            url: The URL to analyze
        
        Returns:
            Analysis result with navigation type, selectors, and strategy
        """
        page = self.agent.page
        
        # Navigate to URL
        await page.goto(url, wait_until='networkidle', timeout=60000)
        
        # Wait for page to stabilize
        await page.wait_for_timeout(2000)
        
        # Handle cookie consent if present
        await self._handle_cookie_consent(page)
        
        # Capture full-page screenshot
        screenshot_bytes = await page.screenshot(full_page=True)
        screenshot_b64 = base64.b64encode(screenshot_bytes).decode('utf-8')
        
        # Extract HTML structure (cleaned)
        html_structure = await self._extract_html_structure(page)
        
        # Analyze with Vision API
        analysis_prompt = f"""
        Analyze this e-commerce website screenshot and HTML to identify product categories.
        
        HTML Structure (excerpt):
        ```html
        {html_structure[:3000]}
        ```
        
        Please identify:
        1. Navigation type (hover_menu, sidebar, dropdown, accordion, other)
        2. Location of category elements (header, left sidebar, footer, etc.)
        3. CSS selectors for:
           - Main navigation container
           - Top-level category items
           - Category links/anchors
           - Submenu/flyout panels (if applicable)
           - Subcategory lists
        4. Required interactions (hover, click, scroll)
        5. Any dynamic loading (lazy load, AJAX)
        
        Return as JSON:
        {{
          "navigation_type": "...",
          "category_location": "...",
          "selectors": {{
            "nav_container": "...",
            "top_level_items": "...",
            "category_links": "...",
            "flyout_panel": "..." | null,
            "subcategory_list": "..." | null
          }},
          "interactions": [
            {{"type": "hover|click|scroll", "target": "...", "wait_for": "..."}}
          ],
          "dynamic_loading": true|false,
          "confidence": 0.0-1.0,
          "notes": "Any observations..."
        }}
        """
        
        # Use Anthropic Vision API (via Bedrock)
        # This would be handled by the Strands agent's vision capabilities
        analysis_result = await self._analyze_with_vision(
            screenshot_b64=screenshot_b64,
            prompt=analysis_prompt
        )
        
        # Update agent state
        self.agent.extraction_state["stage"] = "analyzed"
        self.agent.extraction_state["analysis"] = analysis_result
        
        return analysis_result
    
    async def _handle_cookie_consent(self, page: Page):
        """Automatically handle cookie consent popups."""
        consent_selectors = [
            'button:has-text("Accept")',
            'button:has-text("I Agree")',
            'button:has-text("OK")',
            'button:has-text("Got it")',
            '#accept-cookies',
            '.cookie-accept',
            '.consent-accept'
        ]
        
        for selector in consent_selectors:
            try:
                button = await page.wait_for_selector(
                    selector, 
                    timeout=2000,
                    state='visible'
                )
                if button:
                    await button.click()
                    await page.wait_for_timeout(1000)
                    break
            except:
                continue
    
    async def _extract_html_structure(self, page: Page) -> str:
        """Extract and clean HTML structure."""
        html = await page.evaluate("""
            () => {
                // Remove scripts, styles, comments
                const clone = document.documentElement.cloneNode(true);
                clone.querySelectorAll('script, style, noscript, svg').forEach(el => el.remove());
                
                // Simplify to just structural elements
                return clone.outerHTML;
            }
        """)
        
        # Minify and truncate
        import re
        html = re.sub(r'\s+', ' ', html)  # Collapse whitespace
        html = re.sub(r'<!--.*?-->', '', html)  # Remove comments
        
        return html[:10000]  # First 10K chars
    
    async def _analyze_with_vision(
        self, 
        screenshot_b64: str, 
        prompt: str
    ) -> Dict[str, Any]:
        """
        Analyze screenshot using Claude Vision API.
        
        Note: Strands Agents may not have built-in vision support yet.
        This would use Anthropic API directly.
        """
        import anthropic
        
        client = anthropic.Anthropic()
        
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2048,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": screenshot_b64
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }]
        )
        
        # Parse JSON response
        response_text = message.content[0].text
        
        # Extract JSON from response (may be wrapped in markdown)
        import re
        json_match = re.search(r'```json\n(.*?)\n```', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            json_str = response_text
        
        return json.loads(json_str)
    
    def as_tool(self):
        """Return as Strands tool."""
        return self.analyze_page
```

### 3. CategoryExtractorTool

**Purpose**: Execute the extraction strategy and gather categories.

**Implementation**:
```python
from strands.tools import tool
from playwright.async_api import Page, ElementHandle
from typing import List, Dict, Any
import asyncio

class CategoryExtractorTool:
    """Tool for extracting categories based on analysis strategy."""
    
    def __init__(self, agent: 'CategoryExtractionAgent'):
        self.agent = agent
    
    @tool
    async def extract_categories(
        self,
        strategy: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract categories using the provided strategy.
        
        Args:
            strategy: Extraction strategy from page analysis.
                     If None, uses strategy from agent state.
        
        Returns:
            List of extracted categories with hierarchy
        """
        if strategy is None:
            strategy = self.agent.extraction_state.get("analysis", {})
        
        if not strategy:
            raise ValueError("No extraction strategy available")
        
        page = self.agent.page
        selectors = strategy["selectors"]
        interactions = strategy.get("interactions", [])
        
        categories = []
        
        # Extract based on navigation type
        nav_type = strategy["navigation_type"]
        
        if nav_type == "hover_menu":
            categories = await self._extract_from_hover_menu(page, selectors, interactions)
        elif nav_type == "sidebar":
            categories = await self._extract_from_sidebar(page, selectors)
        elif nav_type == "dropdown":
            categories = await self._extract_from_dropdown(page, selectors, interactions)
        else:
            # Generic extraction
            categories = await self._extract_generic(page, selectors)
        
        # Build hierarchy
        categories_with_hierarchy = self._build_hierarchy(categories)
        
        # Update state
        self.agent.extraction_state["stage"] = "extracted"
        self.agent.extraction_state["categories_found"] = len(categories_with_hierarchy)
        self.agent.extraction_state["raw_categories"] = categories_with_hierarchy
        
        return categories_with_hierarchy
    
    async def _extract_from_hover_menu(
        self,
        page: Page,
        selectors: Dict[str, str],
        interactions: List[Dict[str, str]]
    ) -> List[Dict[str, Any]]:
        """Extract categories from hover menu navigation."""
        categories = []
        
        # Find top-level menu items
        top_level_items = await page.query_selector_all(selectors["top_level_items"])
        
        for index, item in enumerate(top_level_items):
            try:
                # Extract top-level category
                name = await item.text_content()
                name = name.strip() if name else f"Category_{index}"
                
                # Get URL
                link = await item.query_selector(selectors.get("category_links", "a"))
                url = await link.get_attribute("href") if link else None
                
                # Hover to reveal submenu
                await item.hover()
                await page.wait_for_timeout(500)
                
                # Wait for flyout
                flyout_selector = selectors.get("flyout_panel")
                if flyout_selector:
                    try:
                        await page.wait_for_selector(
                            flyout_selector,
                            state='visible',
                            timeout=3000
                        )
                        
                        # Extract subcategories from flyout
                        subcategories = await self._extract_subcategories_from_flyout(
                            page,
                            flyout_selector,
                            selectors
                        )
                    except:
                        subcategories = []
                else:
                    subcategories = []
                
                categories.append({
                    "name": name,
                    "url": self._normalize_url(url, page.url),
                    "depth": 0,
                    "parent_id": None,
                    "children": subcategories
                })
                
                # Move mouse away to close flyout
                await page.mouse.move(0, 0)
                await page.wait_for_timeout(300)
                
            except Exception as e:
                print(f"Error extracting category {index}: {e}")
                continue
        
        return categories
    
    async def _extract_subcategories_from_flyout(
        self,
        page: Page,
        flyout_selector: str,
        selectors: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """Extract subcategories from flyout panel."""
        subcategories = []
        
        flyout = await page.query_selector(flyout_selector)
        if not flyout:
            return subcategories
        
        # Find all subcategory links
        subcat_selector = selectors.get("subcategory_list", "a")
        subcat_links = await flyout.query_selector_all(subcat_selector)
        
        for link in subcat_links:
            try:
                name = await link.text_content()
                url = await link.get_attribute("href")
                
                if name and name.strip():
                    subcategories.append({
                        "name": name.strip(),
                        "url": self._normalize_url(url, page.url),
                        "depth": 1,
                        "children": []
                    })
            except:
                continue
        
        return subcategories
    
    async def _extract_from_sidebar(
        self,
        page: Page,
        selectors: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """Extract categories from sidebar navigation."""
        categories = []
        
        # Similar logic for sidebar extraction
        # ...
        
        return categories
    
    async def _extract_from_dropdown(
        self,
        page: Page,
        selectors: Dict[str, str],
        interactions: List[Dict[str, str]]
    ) -> List[Dict[str, Any]]:
        """Extract categories from dropdown menus."""
        categories = []
        
        # Similar logic for dropdown extraction
        # ...
        
        return categories
    
    async def _extract_generic(
        self,
        page: Page,
        selectors: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """Generic extraction when navigation type is unclear."""
        categories = []
        
        # Find all links that look like categories
        category_links = await page.query_selector_all(
            selectors.get("category_links", "a")
        )
        
        for link in category_links:
            try:
                name = await link.text_content()
                url = await link.get_attribute("href")
                
                if name and name.strip() and url:
                    categories.append({
                        "name": name.strip(),
                        "url": self._normalize_url(url, page.url),
                        "depth": 0,
                        "parent_id": None,
                        "children": []
                    })
            except:
                continue
        
        return categories
    
    def _build_hierarchy(
        self,
        categories: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Build parent-child hierarchy from flat list."""
        # For categories extracted with children already nested,
        # flatten and assign proper parent IDs
        
        result = []
        id_counter = 1
        
        def process_category(cat: Dict[str, Any], parent_id: Optional[int], depth: int):
            nonlocal id_counter
            
            cat_id = id_counter
            id_counter += 1
            
            result.append({
                "id": cat_id,
                "name": cat["name"],
                "url": cat["url"],
                "depth": depth,
                "parent_id": parent_id,
                "retailer_id": self.agent.retailer_id
            })
            
            # Process children
            for child in cat.get("children", []):
                process_category(child, cat_id, depth + 1)
        
        for cat in categories:
            process_category(cat, None, 0)
        
        return result
    
    def _normalize_url(self, url: Optional[str], base_url: str) -> Optional[str]:
        """Normalize and make URL absolute."""
        if not url:
            return None
        
        from urllib.parse import urljoin, urlparse
        
        # Make absolute
        absolute_url = urljoin(base_url, url)
        
        # Remove fragments
        parsed = urlparse(absolute_url)
        clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if parsed.query:
            clean_url += f"?{parsed.query}"
        
        return clean_url
    
    def as_tool(self):
        """Return as Strands tool."""
        return self.extract_categories
```

### 4. DatabaseSaverTool

**Purpose**: Persist extracted categories to PostgreSQL.

**Implementation**:
```python
from strands.tools import tool
import asyncpg
from typing import List, Dict, Any
from datetime import datetime

class DatabaseSaverTool:
    """Tool for saving categories to PostgreSQL database."""
    
    def __init__(self, agent: 'CategoryExtractionAgent'):
        self.agent = agent
        self.db_pool: Optional[asyncpg.Pool] = None
    
    async def _get_db_pool(self) -> asyncpg.Pool:
        """Get or create database connection pool."""
        if self.db_pool is None:
            # Load from environment or config
            import os
            
            self.db_pool = await asyncpg.create_pool(
                host=os.getenv("DB_HOST", "localhost"),
                port=int(os.getenv("DB_PORT", "5432")),
                database=os.getenv("DB_NAME", "product_scraper"),
                user=os.getenv("DB_USER", "postgres"),
                password=os.getenv("DB_PASSWORD"),
                min_size=1,
                max_size=5
            )
        
        return self.db_pool
    
    @tool
    async def save_to_database(
        self,
        categories: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Save extracted categories to PostgreSQL database.
        
        Args:
            categories: List of categories to save.
                       If None, uses categories from agent state.
        
        Returns:
            Statistics about saved categories
        """
        if categories is None:
            categories = self.agent.extraction_state.get("raw_categories", [])
        
        if not categories:
            return {
                "saved": 0,
                "skipped": 0,
                "errors": []
            }
        
        pool = await self._get_db_pool()
        
        saved_count = 0
        skipped_count = 0
        errors = []
        
        # Map local IDs to database IDs
        id_mapping = {}
        
        async with pool.acquire() as conn:
            # Sort by depth to insert parents before children
            sorted_categories = sorted(categories, key=lambda c: c.get("depth", 0))
            
            for category in sorted_categories:
                try:
                    # Map parent_id
                    local_parent_id = category.get("parent_id")
                    db_parent_id = None
                    if local_parent_id is not None:
                        db_parent_id = id_mapping.get(local_parent_id)
                    
                    # Insert or update
                    result = await conn.fetchrow(
                        """
                        INSERT INTO categories (
                            name, url, parent_id, retailer_id, depth,
                            enabled, created_at
                        )
                        VALUES ($1, $2, $3, $4, $5, $6, $7)
                        ON CONFLICT (url)
                        DO UPDATE SET
                            name = EXCLUDED.name,
                            parent_id = EXCLUDED.parent_id,
                            depth = EXCLUDED.depth
                        RETURNING id
                        """,
                        category["name"],
                        category["url"],
                        db_parent_id,
                        self.agent.retailer_id,
                        category.get("depth", 0),
                        True,  # enabled
                        datetime.now()
                    )
                    
                    # Store mapping
                    id_mapping[category.get("id")] = result["id"]
                    saved_count += 1
                    
                except Exception as e:
                    errors.append(f"Error saving {category.get('name')}: {str(e)}")
                    skipped_count += 1
        
        # Update agent state
        self.agent.extraction_state["stage"] = "saved"
        self.agent.extraction_state["saved_count"] = saved_count
        
        return {
            "saved": saved_count,
            "skipped": skipped_count,
            "errors": errors
        }
    
    def as_tool(self):
        """Return as Strands tool."""
        return self.save_to_database
```

## (Continued in next document due to length...)

This specification continues in **02_Architecture_Design.md** with:
- BlueprintGeneratorTool implementation
- Configuration management
- Error handling strategies
- Performance optimization
- Testing approaches
