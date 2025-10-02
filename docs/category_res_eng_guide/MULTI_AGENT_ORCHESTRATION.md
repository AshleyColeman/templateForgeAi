# Multi-Agent Orchestration: Coordinating Multiple AI Agents

## Overview

This guide explains how to coordinate multiple AI agents to work together on complex scraping workflows. Instead of one agent doing everything, specialized agents collaborate to accomplish larger goals.

## The Power of Multi-Agent Systems

### Single Agent Approach (Limited)
```
CategoryExtractionAgent
  └─> Extract categories
      ❌ Can't handle products
      ❌ Can't track prices
      ❌ Can't scrape reviews
```

### Multi-Agent Approach (Powerful)
```
Orchestrator
  ├─> CategoryExtractionAgent → Extract categories
  ├─> ProductExtractionAgent → Extract products per category
  ├─> PriceMonitorAgent → Track price changes
  └─> ReviewScraperAgent → Collect reviews
```

## Architecture

```
┌────────────────────────────────────────────────────────┐
│               Master Orchestrator                       │
│  Coordinates multiple specialized agents                │
└──────────┬────────────────────────────────────────────┘
           │
           ├─────────────────┬──────────────────┬─────────
           ▼                 ▼                  ▼
    ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
    │  Category   │   │  Product    │   │   Price     │
    │  Agent      │   │  Agent      │   │   Agent     │
    └──────┬──────┘   └──────┬──────┘   └──────┬──────┘
           │                 │                  │
           └────────┬────────┴──────────────────┘
                    ▼
            ┌───────────────┐
            │   Database    │
            │   Shared      │
            │   State       │
            └───────────────┘
```

## Use Case: Complete Retailer Data Extraction

### Goal
Extract everything from a new retailer:
1. All categories (hierarchical)
2. All products in each category
3. Current prices
4. Product images
5. Customer reviews
6. Stock status

### Traditional Approach
- Write one massive scraper with all logic
- Hard to maintain, test, and debug
- Breaks easily when site changes

### Multi-Agent Approach
- Each agent has a clear responsibility
- Agents can be tested independently
- Agents can run in parallel
- Easy to add new capabilities

## Implementation

### 1. Master Orchestrator

```python
# src/ai_agents/orchestrator/master_orchestrator.py

from typing import Dict, Any, List
import asyncio
from dataclasses import dataclass

from ..category_extractor.agent import CategoryExtractionAgent
from ..product_extractor.agent import ProductExtractionAgent
from ..price_monitor.agent import PriceMonitorAgent
from ..review_scraper.agent import ReviewScraperAgent


@dataclass
class RetailerConfig:
    """Configuration for a retailer to scrape."""
    retailer_id: int
    retailer_name: str
    base_url: str
    extract_categories: bool = True
    extract_products: bool = True
    extract_prices: bool = True
    extract_reviews: bool = False
    max_categories: int = 1000
    max_products_per_category: int = 1000


class MasterOrchestrator:
    """Orchestrates multiple AI agents for complete retailer scraping."""
    
    def __init__(self, config: RetailerConfig):
        self.config = config
        self.state = {
            "stage": "initialized",
            "categories_extracted": 0,
            "products_extracted": 0,
            "errors": []
        }
    
    async def run_complete_extraction(self) -> Dict[str, Any]:
        """
        Run complete extraction workflow:
        1. Extract categories
        2. Extract products for each category
        3. Monitor prices
        4. Scrape reviews (optional)
        """
        results = {
            "success": True,
            "retailer": self.config.retailer_name,
            "stages": {}
        }
        
        try:
            # Stage 1: Extract Categories
            if self.config.extract_categories:
                print(f"\n[Stage 1] Extracting categories from {self.config.base_url}")
                category_result = await self._extract_categories()
                results["stages"]["categories"] = category_result
                
                if not category_result["success"]:
                    results["success"] = False
                    return results
            
            # Stage 2: Extract Products
            if self.config.extract_products:
                print(f"\n[Stage 2] Extracting products from all categories")
                
                categories = category_result.get("categories", [])
                product_result = await self._extract_products_for_categories(categories)
                results["stages"]["products"] = product_result
            
            # Stage 3: Monitor Prices (if enabled)
            if self.config.extract_prices:
                print(f"\n[Stage 3] Setting up price monitoring")
                price_result = await self._setup_price_monitoring()
                results["stages"]["prices"] = price_result
            
            # Stage 4: Scrape Reviews (if enabled)
            if self.config.extract_reviews:
                print(f"\n[Stage 4] Scraping customer reviews")
                review_result = await self._scrape_reviews()
                results["stages"]["reviews"] = review_result
            
            return results
            
        except Exception as e:
            results["success"] = False
            results["error"] = str(e)
            return results
    
    async def _extract_categories(self) -> Dict[str, Any]:
        """Stage 1: Extract categories using CategoryExtractionAgent."""
        agent = CategoryExtractionAgent(
            retailer_id=self.config.retailer_id,
            site_url=self.config.base_url
        )
        
        result = await agent.run_extraction()
        
        self.state["categories_extracted"] = result.get("state", {}).get("categories_found", 0)
        
        # Get categories from database for next stage
        if result["success"]:
            from ..category_extractor.database import CategoryDatabase
            db = CategoryDatabase()
            await db.connect()
            
            categories = await db.get_categories_by_retailer(self.config.retailer_id)
            result["categories"] = categories
            
            await db.disconnect()
        
        return result
    
    async def _extract_products_for_categories(
        self, 
        categories: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Stage 2: Extract products for each category."""
        
        # Filter to leaf categories (no children) to avoid duplicates
        leaf_categories = [
            cat for cat in categories 
            if not any(c.get("parent_id") == cat["id"] for c in categories)
        ]
        
        print(f"  Found {len(leaf_categories)} leaf categories to process")
        
        # Limit categories if configured
        if self.config.max_categories:
            leaf_categories = leaf_categories[:self.config.max_categories]
        
        total_products = 0
        successful = 0
        failed = 0
        errors = []
        
        # Process categories (could be parallelized)
        for i, category in enumerate(leaf_categories, 1):
            print(f"\n  [{i}/{len(leaf_categories)}] {category['name']}")
            
            try:
                agent = ProductExtractionAgent(
                    category_url=category["url"],
                    category_id=category["id"],
                    retailer_id=self.config.retailer_id
                )
                
                result = await agent.run_extraction()
                
                if result["success"]:
                    products_found = result.get("products_found", 0)
                    total_products += products_found
                    successful += 1
                    print(f"    ✓ {products_found} products")
                else:
                    failed += 1
                    error_msg = f"{category['name']}: {result.get('error')}"
                    errors.append(error_msg)
                    print(f"    ✗ Failed: {result.get('error')}")
                    
            except Exception as e:
                failed += 1
                errors.append(f"{category['name']}: {str(e)}")
                print(f"    ✗ Exception: {e}")
        
        self.state["products_extracted"] = total_products
        
        return {
            "success": failed < len(leaf_categories),
            "total_products": total_products,
            "categories_processed": len(leaf_categories),
            "successful": successful,
            "failed": failed,
            "errors": errors
        }
    
    async def _extract_products_for_categories_parallel(
        self,
        categories: List[Dict[str, Any]],
        max_concurrent: int = 3
    ) -> Dict[str, Any]:
        """
        Stage 2 (Parallel version): Extract products with concurrency control.
        Process multiple categories simultaneously but limit concurrent agents.
        """
        
        # Filter leaf categories
        leaf_categories = [
            cat for cat in categories 
            if not any(c.get("parent_id") == cat["id"] for c in categories)
        ]
        
        if self.config.max_categories:
            leaf_categories = leaf_categories[:self.config.max_categories]
        
        print(f"  Processing {len(leaf_categories)} categories with {max_concurrent} concurrent workers")
        
        total_products = 0
        successful = 0
        failed = 0
        errors = []
        
        # Semaphore to limit concurrency
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_category(category: Dict[str, Any], index: int):
            """Process a single category with concurrency control."""
            nonlocal total_products, successful, failed
            
            async with semaphore:
                print(f"\n  [{index}/{len(leaf_categories)}] {category['name']}")
                
                try:
                    agent = ProductExtractionAgent(
                        category_url=category["url"],
                        category_id=category["id"],
                        retailer_id=self.config.retailer_id
                    )
                    
                    result = await agent.run_extraction()
                    
                    if result["success"]:
                        products = result.get("products_found", 0)
                        total_products += products
                        successful += 1
                        print(f"    ✓ {products} products")
                    else:
                        failed += 1
                        errors.append(f"{category['name']}: {result.get('error')}")
                        print(f"    ✗ Failed")
                except Exception as e:
                    failed += 1
                    errors.append(f"{category['name']}: {str(e)}")
                    print(f"    ✗ Exception: {e}")
        
        # Create tasks for all categories
        tasks = [
            process_category(cat, i) 
            for i, cat in enumerate(leaf_categories, 1)
        ]
        
        # Run all tasks concurrently (but limited by semaphore)
        await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            "success": failed < len(leaf_categories),
            "total_products": total_products,
            "categories_processed": len(leaf_categories),
            "successful": successful,
            "failed": failed,
            "errors": errors
        }
    
    async def _setup_price_monitoring(self) -> Dict[str, Any]:
        """Stage 3: Set up price monitoring for all products."""
        
        # Get all products for retailer
        from ..product_extractor.database import ProductDatabase
        db = ProductDatabase()
        await db.connect()
        
        products = await db.get_products_by_retailer(self.config.retailer_id)
        
        await db.disconnect()
        
        # Create price monitor agent
        agent = PriceMonitorAgent(
            retailer_id=self.config.retailer_id,
            products=products
        )
        
        result = await agent.setup_monitoring()
        
        return result
    
    async def _scrape_reviews(self) -> Dict[str, Any]:
        """Stage 4: Scrape customer reviews for all products."""
        
        # Similar to products - get all products and scrape reviews
        from ..product_extractor.database import ProductDatabase
        db = ProductDatabase()
        await db.connect()
        
        products = await db.get_products_by_retailer(self.config.retailer_id)
        
        await db.disconnect()
        
        # Process reviews (simplified)
        agent = ReviewScraperAgent(
            retailer_id=self.config.retailer_id,
            products=products[:100]  # Limit for demo
        )
        
        result = await agent.scrape_all_reviews()
        
        return result
```

### 2. CLI Interface for Orchestrator

```python
# src/ai_agents/orchestrator/cli.py

import asyncio
import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from .master_orchestrator import MasterOrchestrator, RetailerConfig

console = Console()

@click.command()
@click.option('--retailer-id', required=True, type=int, help='Retailer ID')
@click.option('--retailer-name', required=True, help='Retailer name')
@click.option('--url', required=True, help='Base URL')
@click.option('--categories/--no-categories', default=True, help='Extract categories')
@click.option('--products/--no-products', default=True, help='Extract products')
@click.option('--prices/--no-prices', default=True, help='Monitor prices')
@click.option('--reviews/--no-reviews', default=False, help='Scrape reviews')
@click.option('--parallel/--sequential', default=False, help='Run product extraction in parallel')
def run_orchestrator(
    retailer_id: int,
    retailer_name: str,
    url: str,
    categories: bool,
    products: bool,
    prices: bool,
    reviews: bool,
    parallel: bool
):
    """Run complete retailer data extraction with multiple AI agents."""
    
    console.print("\n[bold blue]═══════════════════════════════════════════════════[/bold blue]")
    console.print("[bold blue]   Multi-Agent Orchestrator[/bold blue]")
    console.print("[bold blue]═══════════════════════════════════════════════════[/bold blue]\n")
    
    # Create config
    config = RetailerConfig(
        retailer_id=retailer_id,
        retailer_name=retailer_name,
        base_url=url,
        extract_categories=categories,
        extract_products=products,
        extract_prices=prices,
        extract_reviews=reviews
    )
    
    # Display plan
    console.print(f"[cyan]Retailer:[/cyan] {retailer_name} (ID: {retailer_id})")
    console.print(f"[cyan]URL:[/cyan] {url}\n")
    
    console.print("[bold]Extraction Plan:[/bold]")
    if categories:
        console.print("  ✓ Extract categories")
    if products:
        mode = "parallel" if parallel else "sequential"
        console.print(f"  ✓ Extract products ({mode})")
    if prices:
        console.print("  ✓ Monitor prices")
    if reviews:
        console.print("  ✓ Scrape reviews")
    
    console.print("")
    
    # Run orchestrator
    result = asyncio.run(_run_orchestration(config))
    
    # Display results
    _display_results(result)

async def _run_orchestration(config: RetailerConfig):
    """Execute orchestration."""
    orchestrator = MasterOrchestrator(config)
    return await orchestrator.run_complete_extraction()

def _display_results(result: Dict[str, Any]):
    """Display formatted results."""
    console.print("\n[bold]═══════════════════════════════════════════════════[/bold]")
    console.print("[bold]   Results[/bold]")
    console.print("[bold]═══════════════════════════════════════════════════[/bold]\n")
    
    if result["success"]:
        console.print("[green]✓ Extraction completed successfully[/green]\n")
    else:
        console.print("[red]✗ Extraction completed with errors[/red]\n")
    
    stages = result.get("stages", {})
    
    # Categories
    if "categories" in stages:
        cat_result = stages["categories"]
        console.print("[bold]Categories:[/bold]")
        if cat_result.get("success"):
            count = cat_result.get("state", {}).get("categories_found", 0)
            console.print(f"  ✓ Extracted: [bold]{count}[/bold] categories")
        else:
            console.print(f"  ✗ Failed: {cat_result.get('error')}")
        console.print("")
    
    # Products
    if "products" in stages:
        prod_result = stages["products"]
        console.print("[bold]Products:[/bold]")
        console.print(f"  Total products: [bold]{prod_result.get('total_products', 0)}[/bold]")
        console.print(f"  Categories processed: {prod_result.get('categories_processed', 0)}")
        console.print(f"  Successful: [green]{prod_result.get('successful', 0)}[/green]")
        console.print(f"  Failed: [red]{prod_result.get('failed', 0)}[/red]")
        
        if prod_result.get('errors'):
            console.print("\n  [bold]Errors:[/bold]")
            for error in prod_result['errors'][:5]:  # Show first 5
                console.print(f"    • {error}")
        console.print("")
    
    # Prices
    if "prices" in stages:
        price_result = stages["prices"]
        console.print("[bold]Price Monitoring:[/bold]")
        console.print(f"  Status: {price_result.get('status', 'N/A')}")
        console.print("")
    
    # Reviews
    if "reviews" in stages:
        review_result = stages["reviews"]
        console.print("[bold]Reviews:[/bold]")
        console.print(f"  Reviews scraped: {review_result.get('total_reviews', 0)}")
        console.print("")

if __name__ == '__main__':
    run_orchestrator()
```

## Usage Examples

### Example 1: Complete Retailer Setup

```bash
# Extract everything for a new retailer
python -m src.ai_agents.orchestrator.cli \
  --retailer-id 5 \
  --retailer-name "Wellness Warehouse" \
  --url "https://wellnesswarehouse.com" \
  --categories \
  --products \
  --prices
```

### Example 2: Just Categories and Products

```bash
python -m src.ai_agents.orchestrator.cli \
  --retailer-id 5 \
  --retailer-name "Wellness Warehouse" \
  --url "https://wellnesswarehouse.com" \
  --categories \
  --products \
  --no-prices \
  --no-reviews
```

### Example 3: Parallel Product Extraction

```bash
python -m src.ai_agents.orchestrator.cli \
  --retailer-id 5 \
  --retailer-name "Wellness Warehouse" \
  --url "https://wellnesswarehouse.com" \
  --categories \
  --products \
  --parallel  # Process multiple categories simultaneously
```

### Example 4: Python Script

```python
# scripts/setup_new_retailer.py

import asyncio
from src.ai_agents.orchestrator.master_orchestrator import (
    MasterOrchestrator,
    RetailerConfig
)

async def setup_retailer(name: str, url: str, retailer_id: int):
    """Complete setup for a new retailer."""
    
    config = RetailerConfig(
        retailer_id=retailer_id,
        retailer_name=name,
        base_url=url,
        extract_categories=True,
        extract_products=True,
        extract_prices=True,
        extract_reviews=False,  # Reviews can be added later
        max_categories=500,
        max_products_per_category=1000
    )
    
    orchestrator = MasterOrchestrator(config)
    result = await orchestrator.run_complete_extraction()
    
    return result

# Usage
if __name__ == '__main__':
    retailers = [
        ("Clicks", "https://clicks.co.za", 1),
        ("Dis-Chem", "https://dischem.co.za", 2),
        ("Wellness Warehouse", "https://wellnesswarehouse.com", 3),
    ]
    
    for name, url, rid in retailers:
        print(f"\n{'='*60}")
        print(f"Setting up: {name}")
        print(f"{'='*60}")
        
        result = asyncio.run(setup_retailer(name, url, rid))
        
        if result["success"]:
            print(f"✓ {name} setup complete")
        else:
            print(f"✗ {name} setup failed: {result.get('error')}")
```

## Advanced Patterns

### Pattern 1: Agent Communication via Shared State

```python
class SharedState:
    """Shared state that agents can read/write."""
    
    def __init__(self):
        self.categories = []
        self.products = []
        self.prices = {}
        self.metadata = {}
    
    def add_categories(self, categories: List[Dict]):
        self.categories.extend(categories)
    
    def add_products(self, category_id: int, products: List[Dict]):
        self.products.extend(products)
    
    def update_prices(self, product_id: int, price: float):
        self.prices[product_id] = {
            "price": price,
            "timestamp": datetime.now()
        }
```

### Pattern 2: Agent Pipeline

```python
async def run_pipeline(retailer_id: int, url: str):
    """Run agents in a pipeline where each feeds the next."""
    
    shared_state = SharedState()
    
    # Stage 1: Categories
    cat_agent = CategoryExtractionAgent(retailer_id, url)
    cat_result = await cat_agent.run_extraction()
    shared_state.add_categories(cat_result["categories"])
    
    # Stage 2: Products (uses categories from stage 1)
    for category in shared_state.categories:
        prod_agent = ProductExtractionAgent(
            category["url"], 
            category["id"], 
            retailer_id
        )
        prod_result = await prod_agent.run_extraction()
        shared_state.add_products(category["id"], prod_result["products"])
    
    # Stage 3: Prices (uses products from stage 2)
    price_agent = PriceMonitorAgent(shared_state.products)
    await price_agent.monitor()
    
    return shared_state
```

### Pattern 3: Conditional Agent Execution

```python
async def smart_extraction(retailer_id: int):
    """Intelligently decide which agents to run."""
    
    # Check what data already exists
    db = Database()
    existing_categories = await db.count_categories(retailer_id)
    existing_products = await db.count_products(retailer_id)
    
    # Run agents based on what's missing
    if existing_categories == 0:
        print("No categories found, running category extraction...")
        await run_category_agent(retailer_id)
    else:
        print(f"Found {existing_categories} existing categories, skipping...")
    
    if existing_products == 0:
        print("No products found, running product extraction...")
        await run_product_agent(retailer_id)
    else:
        print(f"Found {existing_products} existing products")
        
        # But always update prices
        print("Updating prices...")
        await run_price_monitor(retailer_id)
```

## Benefits of Multi-Agent Architecture

### 1. **Modularity**
- Each agent is independent
- Easy to test in isolation
- Can be developed separately

### 2. **Reusability**
- Agents can be reused across different retailers
- Mix and match agents as needed

### 3. **Scalability**
- Agents can run in parallel
- Easy to add new agents without affecting existing ones

### 4. **Maintainability**
- Changes to one agent don't affect others
- Clear separation of concerns

### 5. **Flexibility**
- Can run full pipeline or individual agents
- Easy to customize workflow

## Best Practices

### 1. **Clear Agent Responsibilities**
Each agent should have ONE clear purpose:
- ✅ CategoryExtractionAgent - categories only
- ✅ ProductExtractionAgent - products only
- ❌ DataExtractionAgent - everything (too broad)

### 2. **Shared State Management**
Use a central state object or database:
```python
# Good: Shared database
agent1.run() → saves to DB
agent2.run() → reads from DB

# Also good: Explicit state passing
result1 = agent1.run()
result2 = agent2.run(input=result1.output)
```

### 3. **Error Isolation**
One agent failure shouldn't crash the entire pipeline:
```python
try:
    await category_agent.run()
except Exception as e:
    log_error(e)
    # Continue with partial data
    
try:
    await product_agent.run()
except Exception as e:
    log_error(e)
    # Continue
```

### 4. **Progress Tracking**
Always provide visibility into what's happening:
```python
print(f"[1/4] Extracting categories...")
print(f"[2/4] Extracting products...")
print(f"[3/4] Monitoring prices...")
print(f"[4/4] Complete!")
```

## Summary

Multi-agent orchestration allows you to:
- ✅ Break complex scraping into specialized agents
- ✅ Run agents sequentially or in parallel
- ✅ Reuse agents across different retailers
- ✅ Scale easily to handle large volumes
- ✅ Maintain and test each agent independently

**The orchestrator pattern makes it easy to scrape entire e-commerce sites with minimal manual configuration.**

---

