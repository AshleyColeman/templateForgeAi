# AI Agent Framework: Building Custom Scraping Agents

## Overview

This document explains the **agent framework pattern** used in this system and shows you how to create new AI agents for different scraping tasks (products, prices, reviews, etc.).

## Understanding the Agent Pattern

### The Core Concept

An **AI Agent** is a Python class that:
1. **Has a goal** (e.g., "extract all product categories")
2. **Has tools** (e.g., browser automation, HTML parsing, data saving)
3. **Uses AI/LLM** to decide which tools to use and when
4. **Learns from experience** by generating blueprints

### Why This Pattern?

**Traditional Scraper**:
```python
def scrape_categories(url):
    # Hard-coded logic
    soup = BeautifulSoup(html)
    categories = soup.select("nav > li > a")  # Breaks if site changes
    return categories
```

**AI Agent Scraper**:
```python
def scrape_categories(url):
    # AI-driven logic
    agent.run("Extract categories from this URL")
    # Agent figures out the selectors dynamically
    return agent.results
```

## Agent Architecture

### Component Diagram

```
┌────────────────────────────────────────────────────┐
│                   AI Agent                          │
│                                                     │
│  ┌──────────────────────────────────────────┐     │
│  │         LLM Brain (GPT/Claude/Ollama)     │     │
│  │  Decides: What tool to use? What next?   │     │
│  └──────────────────────────────────────────┘     │
│                                                     │
│  ┌──────────────────────────────────────────┐     │
│  │              Tool Registry                │     │
│  │  • analyze_page()                         │     │
│  │  • extract_data()                         │     │
│  │  • save_to_database()                     │     │
│  │  • generate_blueprint()                   │     │
│  └──────────────────────────────────────────┘     │
│                                                     │
│  ┌──────────────────────────────────────────┐     │
│  │             State Management              │     │
│  │  Tracks progress, stores findings         │     │
│  └──────────────────────────────────────────┘     │
│                                                     │
│  ┌──────────────────────────────────────────┐     │
│  │          Browser Automation               │     │
│  │  Playwright instance for web interactions │     │
│  └──────────────────────────────────────────┘     │
└────────────────────────────────────────────────────┘
```

## The Agent Template

Every agent follows this structure:

```python
from strands import Agent as StrandsAgent
from playwright.async_api import Browser, Page
from typing import Dict, Any, Optional

class MyCustomAgent:
    """AI agent for scraping [DESCRIBE WHAT]."""
    
    def __init__(self, config: Dict[str, Any]):
        # 1. Configuration
        self.config = config
        self.target_url = config['url']
        
        # 2. Browser setup
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        
        # 3. Database connection
        self.db = DatabaseConnection()
        
        # 4. State tracking
        self.state = {
            "stage": "initialized",
            "items_found": 0,
            "errors": []
        }
        
        # 5. Create tools
        self._register_tools()
        
        # 6. Create AI agent
        self.agent = self._create_ai_agent()
    
    def _register_tools(self):
        """Create and register tools."""
        from .tools.my_analyzer import MyAnalyzerTool
        from .tools.my_extractor import MyExtractorTool
        
        self.analyzer = MyAnalyzerTool(self)
        self.extractor = MyExtractorTool(self)
        # ... more tools
    
    def _create_ai_agent(self) -> StrandsAgent:
        """Create the AI agent with system prompt."""
        return StrandsAgent(
            model=self._get_model(),
            system_prompt=self._system_prompt(),
            tools=[
                self.analyzer.analyze,
                self.extractor.extract,
                # ... register tool methods
            ]
        )
    
    def _system_prompt(self) -> str:
        """Define what the agent should do."""
        return """
        You are an expert at [DESCRIBE TASK].
        
        Your goal:
        1. [STEP 1]
        2. [STEP 2]
        3. [STEP 3]
        
        Use the available tools to accomplish this task.
        """
    
    async def run(self) -> Dict[str, Any]:
        """Execute the agent's task."""
        try:
            # Initialize browser
            await self.initialize_browser()
            
            # Run AI agent
            prompt = f"[TASK DESCRIPTION] from {self.target_url}"
            result = await self.agent.arun(prompt)
            
            return {
                "success": True,
                "result": result,
                "state": self.state
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "state": self.state
            }
        finally:
            await self.cleanup()
    
    async def initialize_browser(self):
        """Set up Playwright browser."""
        # ... browser setup code
    
    async def cleanup(self):
        """Clean up resources."""
        # ... cleanup code
```

## The Tool Pattern

Each tool is a specialized function the agent can call:

```python
from typing import Dict, Any

class MyExtractorTool:
    """Tool for extracting [DESCRIBE WHAT]."""
    
    def __init__(self, agent):
        self.agent = agent  # Reference to parent agent
    
    async def extract(self, selector: str, filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract data from page.
        
        Args:
            selector: CSS selector to use
            filters: Optional filters to apply
        
        Returns:
            Extracted data with metadata
        """
        page = self.agent.page
        
        # 1. Find elements
        elements = await page.query_selector_all(selector)
        
        # 2. Extract data
        items = []
        for element in elements:
            data = await self._extract_from_element(element, filters)
            if data:
                items.append(data)
        
        # 3. Update agent state
        self.agent.state["items_found"] = len(items)
        self.agent.state["extracted_items"] = items
        
        # 4. Return results
        return {
            "items": items,
            "count": len(items),
            "selector": selector
        }
    
    async def _extract_from_element(self, element, filters):
        """Helper to extract data from single element."""
        # ... extraction logic
```

## Creating a New Agent: Step-by-Step

### Step 1: Define Your Goal

**Example**: Create a Product Extractor Agent

**Goal**: Extract all products that belong to a specific category, including:
- Product names
- Prices
- Images
- Descriptions
- SKUs
- Stock status

### Step 2: Create Project Structure

```bash
mkdir -p src/ai_agents/product_extractor/{tools,utils}
touch src/ai_agents/product_extractor/__init__.py
touch src/ai_agents/product_extractor/agent.py
touch src/ai_agents/product_extractor/config.py
touch src/ai_agents/product_extractor/tools/product_analyzer.py
touch src/ai_agents/product_extractor/tools/product_extractor.py
```

### Step 3: Design Your Tools

Identify what tools your agent needs:

**For Product Extractor**:
1. **ProductPageAnalyzerTool**: Analyze a category page to find product listings
2. **ProductExtractorTool**: Extract individual product details
3. **PaginationHandlerTool**: Handle "Load More" / pagination
4. **ProductValidatorTool**: Validate extracted products
5. **DatabaseSaverTool**: Save products to database
6. **BlueprintGeneratorTool**: Generate reusable template

### Step 4: Implement the Agent Class

```python
# src/ai_agents/product_extractor/agent.py

from strands import Agent as StrandsAgent
from playwright.async_api import async_playwright, Browser, Page
from typing import Dict, Any, Optional

class ProductExtractionAgent:
    """AI agent for extracting products from category pages."""
    
    def __init__(self, category_url: str, category_id: int):
        self.category_url = category_url
        self.category_id = category_id
        
        # Browser
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        
        # State
        self.state = {
            "stage": "initialized",
            "products_found": 0,
            "pages_processed": 0,
            "errors": []
        }
        
        # Create tools
        from .tools.product_analyzer import ProductAnalyzerTool
        from .tools.product_extractor import ProductExtractorTool
        from .tools.pagination_handler import PaginationHandlerTool
        
        self.analyzer = ProductAnalyzerTool(self)
        self.extractor = ProductExtractorTool(self)
        self.paginator = PaginationHandlerTool(self)
        
        # Create AI agent
        self.agent = StrandsAgent(
            model=self._get_model(),
            system_prompt=self._system_prompt(),
            tools=[
                self.analyzer.analyze,
                self.extractor.extract,
                self.paginator.handle_pagination
            ]
        )
    
    def _system_prompt(self) -> str:
        return """
        You are an expert at extracting product information from e-commerce sites.
        
        Your mission:
        1. Analyze the category page to understand product layout
        2. Extract all products with: name, price, image, description, SKU
        3. Handle pagination to get all products (not just first page)
        4. Validate extracted data
        5. Save to database with category relationship
        
        Use the available tools systematically.
        """
    
    async def run_extraction(self) -> Dict[str, Any]:
        """Execute product extraction."""
        try:
            await self.initialize_browser()
            
            prompt = f"""
            Extract all products from category: {self.category_url}
            Category ID: {self.category_id}
            
            Workflow:
            1. analyze() - Understand page structure
            2. extract() - Get products from current page
            3. handle_pagination() - Move to next page if available
            4. Repeat steps 2-3 until all pages processed
            5. Report total products found
            """
            
            result = await self.agent.arun(prompt)
            
            return {
                "success": True,
                "products": self.state.get("products", []),
                "total": self.state["products_found"],
                "pages": self.state["pages_processed"]
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            await self.cleanup()
    
    # ... browser setup, cleanup, etc.
```

### Step 5: Implement Each Tool

**Example: ProductAnalyzerTool**

```python
# src/ai_agents/product_extractor/tools/product_analyzer.py

class ProductAnalyzerTool:
    """Analyzes category page to identify product listing pattern."""
    
    def __init__(self, agent):
        self.agent = agent
    
    async def analyze(self, url: str) -> Dict[str, Any]:
        """
        Analyze category page structure.
        
        Returns:
            Selectors and patterns for product extraction
        """
        page = self.agent.page
        
        # Navigate to category
        await page.goto(url, wait_until='networkidle')
        await page.wait_for_timeout(2000)
        
        # Extract HTML structure
        html_sample = await self._get_product_container_html(page)
        
        # Use LLM to analyze
        # (In real implementation, would call Claude/GPT vision API)
        analysis = {
            "product_container": ".product-grid",
            "product_item": ".product-card",
            "product_name": "h3.product-title",
            "product_price": "span.price",
            "product_image": "img.product-image",
            "product_link": "a.product-link",
            "pagination_type": "load_more_button",
            "pagination_selector": "button.load-more"
        }
        
        self.agent.state["analysis"] = analysis
        self.agent.state["stage"] = "analyzed"
        
        return analysis
    
    async def _get_product_container_html(self, page):
        """Extract relevant HTML for LLM analysis."""
        # Find product listing area
        html = await page.evaluate("""
            () => {
                // Look for common product container patterns
                const containers = document.querySelectorAll(
                    '.products, .product-list, .product-grid, [data-products]'
                );
                return containers[0]?.outerHTML || document.body.innerHTML;
            }
        """)
        return html[:3000]  # Truncate for LLM
```

**Example: ProductExtractorTool**

```python
# src/ai_agents/product_extractor/tools/product_extractor.py

class ProductExtractorTool:
    """Extracts product data from page."""
    
    def __init__(self, agent):
        self.agent = agent
    
    async def extract(self) -> Dict[str, Any]:
        """
        Extract all products from current page.
        
        Returns:
            List of products with all details
        """
        page = self.agent.page
        analysis = self.agent.state.get("analysis")
        
        if not analysis:
            return {"error": "Must call analyze() first"}
        
        # Find all product elements
        product_elements = await page.query_selector_all(
            analysis["product_item"]
        )
        
        products = []
        for element in product_elements:
            try:
                product = await self._extract_product(element, analysis)
                if product:
                    products.append(product)
            except Exception as e:
                self.agent.state["errors"].append(str(e))
        
        # Update state
        existing = self.agent.state.get("products", [])
        self.agent.state["products"] = existing + products
        self.agent.state["products_found"] = len(self.agent.state["products"])
        
        return {
            "products": products,
            "count": len(products),
            "page": self.agent.state["pages_processed"]
        }
    
    async def _extract_product(self, element, analysis):
        """Extract data from a single product element."""
        try:
            # Name
            name_el = await element.query_selector(analysis["product_name"])
            name = await name_el.text_content() if name_el else None
            
            # Price
            price_el = await element.query_selector(analysis["product_price"])
            price_text = await price_el.text_content() if price_el else None
            price = self._parse_price(price_text)
            
            # Image
            img_el = await element.query_selector(analysis["product_image"])
            image_url = await img_el.get_attribute("src") if img_el else None
            
            # Link
            link_el = await element.query_selector(analysis["product_link"])
            url = await link_el.get_attribute("href") if link_el else None
            
            # SKU (try to extract from URL or data attributes)
            sku = await self._extract_sku(element, url)
            
            return {
                "name": name.strip() if name else None,
                "price": price,
                "image_url": self._normalize_url(image_url),
                "url": self._normalize_url(url),
                "sku": sku,
                "category_id": self.agent.category_id,
                "in_stock": True  # Could extract from page
            }
        except Exception as e:
            return None
    
    def _parse_price(self, price_text: str) -> float:
        """Parse price from text."""
        if not price_text:
            return None
        
        import re
        # Extract numbers
        numbers = re.findall(r'\d+\.?\d*', price_text.replace(',', ''))
        return float(numbers[0]) if numbers else None
    
    async def _extract_sku(self, element, url):
        """Try to extract SKU from various sources."""
        # Try data attributes
        sku = await element.get_attribute("data-sku")
        if sku:
            return sku
        
        # Try data-product-id
        sku = await element.get_attribute("data-product-id")
        if sku:
            return sku
        
        # Try extracting from URL
        if url:
            import re
            match = re.search(r'/product/([A-Za-z0-9_-]+)', url)
            if match:
                return match.group(1)
        
        return None
```

### Step 6: Create CLI Interface

```python
# src/ai_agents/product_extractor/cli.py

import asyncio
import click
from .agent import ProductExtractionAgent

@click.command()
@click.option('--url', required=True, help='Category URL')
@click.option('--category-id', required=True, type=int, help='Category ID')
def extract_products(url: str, category_id: int):
    """Extract products from a category page."""
    
    print(f"\nExtracting products from: {url}")
    print(f"Category ID: {category_id}\n")
    
    result = asyncio.run(_run(url, category_id))
    
    if result['success']:
        print(f"✓ Success!")
        print(f"  Products found: {result['total']}")
        print(f"  Pages processed: {result['pages']}")
    else:
        print(f"✗ Failed: {result['error']}")

async def _run(url: str, category_id: int):
    agent = ProductExtractionAgent(url, category_id)
    return await agent.run_extraction()

if __name__ == '__main__':
    extract_products()
```

### Step 7: Test Your Agent

```python
# tests/test_product_extractor/test_agent.py

import pytest
from src.ai_agents.product_extractor.agent import ProductExtractionAgent

@pytest.mark.asyncio
async def test_product_extraction():
    """Test product extraction."""
    agent = ProductExtractionAgent(
        category_url="https://example.com/electronics",
        category_id=42
    )
    
    result = await agent.run_extraction()
    
    assert result['success']
    assert result['total'] > 0
    assert len(result['products']) > 0
```

### Step 8: Run Your Agent

```bash
python -m src.ai_agents.product_extractor.cli \
  --url "https://clicks.co.za/products/c/OH1" \
  --category-id 123
```

## Agent Communication Pattern

Agents can work together:

```python
# Extract categories first
category_agent = CategoryExtractionAgent(...)
category_result = await category_agent.run_extraction()

# Then extract products from each category
for category in category_result['categories']:
    product_agent = ProductExtractionAgent(
        category_url=category['url'],
        category_id=category['id']
    )
    await product_agent.run_extraction()
```

## Best Practices

### 1. **Single Responsibility**
Each agent should have one clear purpose:
- ✅ CategoryExtractionAgent - extracts categories
- ✅ ProductExtractionAgent - extracts products
- ❌ EverythingAgent - extracts everything (too broad)

### 2. **Tool Granularity**
Tools should be focused and reusable:
- ✅ PaginationHandlerTool - handles pagination
- ✅ ImageDownloaderTool - downloads images
- ❌ DoEverythingTool - does too much

### 3. **State Management**
Always track progress in `self.state`:
```python
self.state = {
    "stage": "extracting",  # Current stage
    "items_found": 42,      # Progress
    "errors": [],           # Issues encountered
    "metadata": {}          # Custom data
}
```

### 4. **Error Handling**
Be graceful with errors:
```python
try:
    result = await tool.extract()
except ExtractorError as e:
    self.state["errors"].append(str(e))
    # Continue with partial results
```

### 5. **Blueprint Generation**
Always generate blueprints for reusability:
```python
blueprint = {
    "version": "1.0",
    "selectors": self.state["analysis"],
    "extraction_stats": {
        "items": self.state["items_found"],
        "duration": time_taken
    }
}
```

## Summary

To create a new agent:

1. ✅ Define clear goal and scope
2. ✅ Design specialized tools
3. ✅ Implement agent class (orchestrator)
4. ✅ Implement each tool
5. ✅ Create system prompt (instructs AI)
6. ✅ Add CLI interface
7. ✅ Test thoroughly
8. ✅ Generate blueprints

**Next**: See `PRODUCT_EXTRACTOR_GUIDE.md` for a complete, production-ready product extractor implementation.

---

