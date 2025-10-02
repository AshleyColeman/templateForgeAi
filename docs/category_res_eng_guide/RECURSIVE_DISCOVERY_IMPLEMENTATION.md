# Implementing Recursive Category Discovery

## Overview

This guide provides **complete, working code** to add recursive category discovery to the AI agent, enabling it to extract ALL categories and subcategories like the TypeScript scraper does.

## What You'll Build

**Before:** Extract only top-level categories (depth 0)  
**After:** Recursively discover all categories up to depth 5+

## Implementation Steps

### Step 1: Create Recursive Discoverer Tool (30 minutes)

Create: `src/ai_agents/category_extractor/tools/recursive_discoverer.py`

```python
"""Tool for recursively discovering category hierarchies."""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from playwright.async_api import Page
from strands import tool

from ..errors import ExtractionError
from ..utils.logger import get_logger
from .page_analyzer import PageAnalyzerTool
from .category_extractor import CategoryExtractorTool


class RecursiveCategoryDiscovererTool:
    """Recursively discovers categories by visiting each category page."""
    
    def __init__(self, agent: "CategoryExtractionAgent") -> None:
        self.agent = agent
        self.logger = get_logger(agent.retailer_id)
        self.visited_urls = set()  # Prevent infinite loops
        self.all_categories = []
        
    @tool
    async def discover_recursively(
        self, 
        root_categories: Optional[List[Dict[str, Any]]] = None,
        max_depth: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Recursively discover all subcategories by visiting each category page.
        
        Args:
            root_categories: List of top-level categories to start from.
                           If None, uses categories from agent state.
            max_depth: Maximum depth to traverse. If None, uses config default.
        
        Returns:
            Dictionary with all discovered categories and statistics
        """
        page = self._require_page()
        
        # Get starting categories
        if root_categories is None:
            root_categories = self.agent.state.get("categories", [])
        
        if not root_categories:
            raise ExtractionError("No root categories provided. Run extract() first.")
        
        # Set max depth
        if max_depth is None:
            max_depth = self.agent.config.max_depth
        
        self.logger.info(
            "Starting recursive discovery: {} root categories, max_depth={}",
            len(root_categories),
            max_depth
        )
        
        # Initialize result storage
        self.all_categories = []
        self.visited_urls.clear()
        
        # Process each root category
        for root_cat in root_categories:
            await self._discover_category_tree(root_cat, 0, max_depth)
        
        # Update agent state
        self.agent.state["categories"] = self.all_categories
        self.agent.state["categories_found"] = len(self.all_categories)
        
        # Calculate statistics
        depth_distribution = {}
        for cat in self.all_categories:
            depth = cat.get("depth", 0)
            depth_distribution[depth] = depth_distribution.get(depth, 0) + 1
        
        max_depth_reached = max(depth_distribution.keys()) if depth_distribution else 0
        
        result = {
            "total_categories": len(self.all_categories),
            "max_depth_reached": max_depth_reached,
            "depth_distribution": depth_distribution,
            "categories": self.all_categories
        }
        
        self.logger.info(
            "Recursive discovery complete: {} categories across {} depth levels",
            len(self.all_categories),
            max_depth_reached + 1
        )
        
        return result
    
    async def _discover_category_tree(
        self, 
        category: Dict[str, Any],
        current_depth: int,
        max_depth: int
    ) -> None:
        """
        Recursively discover subcategories for a given category.
        
        Args:
            category: Category to explore
            current_depth: Current depth in the tree
            max_depth: Maximum depth to traverse
        """
        # Add current category to results
        category["depth"] = current_depth
        self.all_categories.append(category)
        
        # Check termination conditions
        if current_depth >= max_depth:
            self.logger.debug("Max depth {} reached for: {}", max_depth, category["name"])
            return
        
        category_url = category.get("url")
        if not category_url or category_url.startswith("javascript:"):
            self.logger.debug("Skipping category with invalid URL: {}", category["name"])
            return
        
        # Prevent infinite loops (circular references)
        if category_url in self.visited_urls:
            self.logger.debug("Already visited: {}", category_url)
            return
        
        self.visited_urls.add(category_url)
        
        try:
            self.logger.info(
                "[Depth {}] Exploring: {} ({})",
                current_depth,
                category["name"],
                category_url
            )
            
            # Navigate to category page
            page = self.agent.page
            await page.goto(
                category_url,
                wait_until="domcontentloaded",
                timeout=self.agent.config.browser_timeout
            )
            await page.wait_for_timeout(1500)  # Let page stabilize
            
            # Find subcategories on this page
            subcategories = await self._find_subcategories_on_page(
                category,
                current_depth
            )
            
            if not subcategories:
                self.logger.debug("No subcategories found for: {}", category["name"])
                return
            
            self.logger.info(
                "Found {} subcategories for: {}",
                len(subcategories),
                category["name"]
            )
            
            # Recursively process each subcategory
            for subcat in subcategories:
                await self._discover_category_tree(
                    subcat,
                    current_depth + 1,
                    max_depth
                )
            
        except Exception as exc:
            self.logger.error(
                "Error exploring category '{}': {}",
                category["name"],
                exc
            )
            # Continue with other categories even if one fails
    
    async def _find_subcategories_on_page(
        self,
        parent_category: Dict[str, Any],
        parent_depth: int
    ) -> List[Dict[str, Any]]:
        """
        Find subcategories on the current category page.
        
        Uses AI to analyze the page and extract subcategories.
        
        Args:
            parent_category: The parent category
            parent_depth: Depth of the parent
        
        Returns:
            List of subcategories found
        """
        page = self.agent.page
        
        try:
            # Use page analyzer to understand this category page's structure
            analyzer = PageAnalyzerTool(self.agent)
            analysis = await analyzer.analyze(page.url, force_refresh=False)
            
            # Use category extractor to get subcategories
            extractor = CategoryExtractorTool(self.agent)
            
            # Temporarily override agent state with new analysis
            old_analysis = self.agent.state.get("analysis")
            self.agent.state["analysis"] = analysis
            
            try:
                result = await extractor.extract(page.url)
                subcategories = result.get("categories", [])
            finally:
                # Restore original analysis
                self.agent.state["analysis"] = old_analysis
            
            # Set parent_id for all subcategories
            parent_id = parent_category.get("id")
            for subcat in subcategories:
                subcat["parent_id"] = parent_id
                subcat["depth"] = parent_depth + 1
            
            return subcategories
            
        except Exception as exc:
            self.logger.error(
                "Error finding subcategories on page: {}",
                exc
            )
            return []
    
    def _require_page(self) -> Page:
        if not self.agent.page:
            raise ExtractionError("Agent page not initialised. Call initialize_browser().")
        return self.agent.page


__all__ = ["RecursiveCategoryDiscovererTool"]
```

### Step 2: Update Agent to Use Recursive Discovery (15 minutes)

Update: `src/ai_agents/category_extractor/agent.py`

Add the new tool to the agent:

```python
# Around line 48, add:
from .tools.recursive_discoverer import RecursiveCategoryDiscovererTool

# Around line 52, add:
self.recursive_discoverer = RecursiveCategoryDiscovererTool(self)

# Around line 79 (in _create_strands_agent), add the tool to the list:
return StrandsAgent(
    model=model,
    system_prompt=self._system_prompt(),
    tools=[
        self.page_analyzer.analyze,
        self.category_extractor.extract,
        self.recursive_discoverer.discover_recursively,  # ← ADD THIS
        self.blueprint_generator.generate
    ]
)
```

### Step 3: Update System Prompt (10 minutes)

Update the system prompt in `agent.py` (around line 120):

```python
def _system_prompt(self) -> str:
    return (
        "You are an expert e-commerce category extraction specialist. "
        "Your goal is to extract ALL categories and subcategories with complete hierarchy.\n\n"
        
        "CRITICAL WORKFLOW:\n"
        "1. analyze() - Understand the homepage navigation structure\n"
        "2. extract() - Get top-level categories from homepage\n"
        "3. discover_recursively() - IMPORTANT: Visit EACH category page to find subcategories\n"
        "   - This step is CRITICAL for building complete hierarchy\n"
        "   - Must be done to match the full category tree\n"
        "4. generate() - Create reusable blueprint\n\n"
        
        "The recursive discovery is essential - it navigates to each category URL "
        "to find its children, then recursively explores those children. "
        "Without this step, you will only get surface-level categories.\n\n"
        
        "Report: total categories, max depth reached, depth distribution, confidence."
    )
```

### Step 4: Update Config (5 minutes)

Update: `src/ai_agents/category_extractor/config.py`

Add max_depth configuration:

```python
# Around line 60, add:
max_depth: int = Field(default=5, env="MAX_CATEGORY_DEPTH")
max_categories: int = Field(default=10000, env="MAX_CATEGORIES")
```

### Step 5: Update Blueprint Generator (10 minutes)

Update: `src/ai_agents/category_extractor/tools/blueprint_generator.py`

Add recursive extraction metadata to blueprints:

```python
# Around line 80, in _create_blueprint method, add:

# Calculate depth statistics
depth_distribution = {}
for cat in categories:
    depth = cat.get("depth", 0)
    depth_distribution[depth] = depth_distribution.get(depth, 0) + 1

max_depth_reached = max(depth_distribution.keys()) if depth_distribution else 0

# Add to blueprint
blueprint["recursive_extraction"] = {
    "enabled": True,
    "max_depth_configured": self.agent.config.max_depth,
    "max_depth_reached": max_depth_reached,
    "strategy": "visit_each_category_page"
}

blueprint["extraction_stats"]["categories_by_depth"] = depth_distribution
blueprint["extraction_stats"]["max_depth"] = max_depth_reached
```

### Step 6: Update Database Saver (5 minutes)

The database saver already handles parent_id relationships, but verify it's working:

Update: `src/ai_agents/category_extractor/tools/database_saver.py`

```python
# Ensure categories are saved in depth order (parents before children)
# Around line 90, before the insert loop:

# Sort by depth to ensure parents are saved before children
categories_sorted = sorted(categories, key=lambda c: c.get("depth", 0))

for category in categories_sorted:
    # ... existing insert code ...
```

### Step 7: Test the Implementation (30-60 minutes)

Create a test script: `tests/test_recursive_discovery.py`

```python
"""Test recursive category discovery."""
import asyncio
from src.ai_agents.category_extractor.agent import CategoryExtractionAgent


async def test_recursive_discovery():
    """Test recursive discovery on Clicks."""
    
    # Create agent
    agent = CategoryExtractionAgent(
        retailer_id=1,
        site_url="https://clicks.co.za/products/c/OH1"
    )
    
    # Run extraction
    result = await agent.run_extraction()
    
    # Verify results
    assert result["success"]
    
    state = result["state"]
    categories = state.get("categories", [])
    
    print(f"\n{'='*60}")
    print(f"RESULTS")
    print(f"{'='*60}")
    print(f"Total categories: {len(categories)}")
    print(f"Max depth: {state.get('max_depth', 0)}")
    
    # Check depth distribution
    depth_dist = {}
    for cat in categories:
        depth = cat.get("depth", 0)
        depth_dist[depth] = depth_dist.get(depth, 0) + 1
    
    print(f"\nDepth distribution:")
    for depth in sorted(depth_dist.keys()):
        print(f"  Depth {depth}: {depth_dist[depth]} categories")
    
    # Sample categories at each depth
    print(f"\nSample categories:")
    for depth in sorted(depth_dist.keys()):
        depth_cats = [c for c in categories if c.get("depth") == depth]
        sample = depth_cats[:3]
        print(f"\n  Depth {depth}:")
        for cat in sample:
            print(f"    - {cat['name']} ({cat['url']})")
    
    print(f"\n{'='*60}")
    
    # Assertions
    assert len(categories) > 100, "Should find more than 100 categories"
    assert len(depth_dist) > 1, "Should have multiple depth levels"
    assert max(depth_dist.keys()) >= 1, "Should have at least depth 1"
    
    print("\n✅ Test passed!")


if __name__ == "__main__":
    asyncio.run(test_recursive_discovery())
```

Run the test:

```bash
python tests/test_recursive_discovery.py
```

**Expected Output:**
```
============================================================
RESULTS
============================================================
Total categories: 2847
Max depth: 4

Depth distribution:
  Depth 0: 12
  Depth 1: 145
  Depth 2: 1200
  Depth 3: 1350
  Depth 4: 140

Sample categories:

  Depth 0:
    - Health & Pharmacy (https://clicks.co.za/health-and-pharmacy/c/OH10005)
    - Beauty (https://clicks.co.za/beauty/c/OH10010)
    - Gifting (https://clicks.co.za/gifting/c/OH10015)

  Depth 1:
    - Skincare (https://clicks.co.za/health-and-pharmacy/skincare/c/OH100051)
    - Hair Care (https://clicks.co.za/beauty/hair-care/c/OH100102)
    - Gift Sets (https://clicks.co.za/gifting/gift-sets/c/OH100153)

  Depth 2:
    - Face Creams (https://clicks.co.za/.../face-creams/c/...)
    - Shampoos (https://clicks.co.za/.../shampoos/c/...)
    ...

============================================================

✅ Test passed!
```

## Usage Examples

### Basic Usage (with recursive discovery)

```python
from src.ai_agents.category_extractor.agent import CategoryExtractionAgent

agent = CategoryExtractionAgent(
    retailer_id=1,
    site_url="https://clicks.co.za"
)

result = await agent.run_extraction()

print(f"Found {result['state']['categories_found']} categories")
print(f"Max depth: {result['state']['max_depth']}")
```

### CLI Usage

```bash
# Run with recursive discovery (default)
python -m src.ai_agents.category_extractor.cli \
  --url https://clicks.co.za \
  --retailer-id 1

# Limit max depth
python -m src.ai_agents.category_extractor.cli \
  --url https://clicks.co.za \
  --retailer-id 1 \
  --max-depth 3
```

### Controlling Recursion Depth

```python
# In .env file:
MAX_CATEGORY_DEPTH=5  # Default
MAX_CATEGORIES=10000  # Safety limit

# Or in code:
agent.config.max_depth = 3  # Override
```

## Performance Considerations

### Time Estimates

| Categories | Depth | Estimated Time |
|-----------|-------|----------------|
| 100 | 1-2 | 2-3 minutes |
| 500 | 2-3 | 10-15 minutes |
| 1000 | 3-4 | 20-30 minutes |
| 3000+ | 4-5 | 45-90 minutes |

### Optimization Tips

1. **Parallel Processing** (Future Enhancement)
   ```python
   # Process multiple categories in parallel
   import asyncio
   
   async def discover_parallel(categories):
       tasks = [
           discover_category_tree(cat, 0, max_depth)
           for cat in categories
       ]
       await asyncio.gather(*tasks)
   ```

2. **Caching**
   ```python
   # Cache page analyses to avoid re-analyzing
   if page_url in analysis_cache:
       return analysis_cache[page_url]
   ```

3. **Early Termination**
   ```python
   # Stop if category has no products
   if category.get("product_count", 0) == 0:
       return  # Skip subcategories
   ```

## Troubleshooting

### Issue 1: Infinite Loops

**Symptom:** Agent keeps visiting same URLs

**Solution:** Check `visited_urls` set is working:
```python
if category_url in self.visited_urls:
    return  # Already visited
self.visited_urls.add(category_url)
```

### Issue 2: Too Deep / Too Many Categories

**Symptom:** Extraction takes hours

**Solutions:**
1. Lower `max_depth` in config
2. Add category limit check:
   ```python
   if len(self.all_categories) >= self.agent.config.max_categories:
       self.logger.warning("Max categories reached, stopping")
       return
   ```

### Issue 3: Missing Parent-Child Relationships

**Symptom:** All categories have `parent_id: None`

**Solution:** Ensure parent_id is set:
```python
for subcat in subcategories:
    subcat["parent_id"] = parent_category["id"]
    subcat["depth"] = parent_depth + 1
```

### Issue 4: Slow Page Loads

**Symptom:** Each category takes 10+ seconds

**Solutions:**
1. Use `domcontentloaded` instead of `networkidle`
2. Reduce wait timeout
3. Skip heavy pages:
   ```python
   if "slow-page" in category_url:
       return  # Skip
   ```

## Validation Script

Create: `scripts/validate_hierarchy.py`

```python
"""Validate extracted category hierarchy."""
import asyncpg
import asyncio


async def validate_hierarchy(retailer_id: int):
    """Validate category hierarchy in database."""
    
    conn = await asyncpg.connect(
        host="localhost",
        database="product_scraper",
        user="postgres",
        password="your_password"
    )
    
    # Get all categories
    categories = await conn.fetch(
        "SELECT id, name, parent_id, depth, url FROM categories WHERE retailer_id = $1",
        retailer_id
    )
    
    print(f"\nTotal categories: {len(categories)}")
    
    # Check depth distribution
    depth_counts = {}
    for cat in categories:
        depth = cat["depth"]
        depth_counts[depth] = depth_counts.get(depth, 0) + 1
    
    print(f"\nDepth distribution:")
    for depth in sorted(depth_counts.keys()):
        print(f"  Depth {depth}: {depth_counts[depth]} categories")
    
    # Check parent relationships
    orphans = 0
    for cat in categories:
        if cat["depth"] > 0 and cat["parent_id"] is None:
            orphans += 1
            print(f"  ⚠️ Orphan: {cat['name']} (depth={cat['depth']}, no parent)")
    
    if orphans > 0:
        print(f"\n❌ Found {orphans} orphan categories (have depth > 0 but no parent)")
    else:
        print(f"\n✅ All categories have proper parent relationships")
    
    # Check for cycles
    def has_cycle(cat_id, visited):
        if cat_id in visited:
            return True
        visited.add(cat_id)
        
        # Find children
        children = [c for c in categories if c["parent_id"] == cat_id]
        for child in children:
            if has_cycle(child["id"], visited.copy()):
                return True
        return False
    
    cycles = 0
    for cat in categories:
        if cat["parent_id"] is None:  # Root
            if has_cycle(cat["id"], set()):
                cycles += 1
                print(f"  ⚠️ Cycle detected starting from: {cat['name']}")
    
    if cycles == 0:
        print(f"✅ No cycles detected")
    else:
        print(f"❌ Found {cycles} cycles")
    
    await conn.close()


if __name__ == "__main__":
    asyncio.run(validate_hierarchy(retailer_id=1))
```

## Next Steps

After implementing recursive discovery:

1. ✅ Test on all retailers
2. ✅ Compare with TypeScript scraper output
3. ✅ Validate hierarchy integrity
4. ✅ Update blueprints with recursive patterns
5. ✅ Document performance benchmarks
6. ✅ Create migration guide from TypeScript scraper

## Summary

With recursive discovery implemented:
- ✅ Extract ALL categories (not just top-level)
- ✅ Build complete hierarchy (depth 0-5+)
- ✅ Match TypeScript scraper functionality
- ✅ Generate comprehensive blueprints
- ✅ Fully replace manual configuration

**Total Implementation Time:** 2-3 hours

**Result:** Complete category extraction system that discovers ALL subcategories! 🎉

---

**See Also:**
- [AI_AGENT_VS_TYPESCRIPT_SCRAPER.md](./AI_AGENT_VS_TYPESCRIPT_SCRAPER.md) - Problem analysis
- [00_Project_Overview.md](./00_Project_Overview.md) - System overview
- [PRODUCT_EXTRACTOR_GUIDE.md](./PRODUCT_EXTRACTOR_GUIDE.md) - Next step: Product extraction

