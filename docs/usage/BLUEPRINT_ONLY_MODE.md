# 🎯 Blueprint-Only Mode (Template Generation)

## What You Need

You want to **generate the extraction template/blueprint** for your scraper **without saving categories to the database**.

## ✅ Use the `--blueprint-only` Flag

```powershell
python -m src.ai_agents.category_extractor.cli extract `
    --url https://www.wellnesswarehouse.com/ `
    --retailer-id 99 `
    --no-headless `
    --blueprint-only
```

**Or use the alias `--dry-run`:**
```powershell
python -m src.ai_agents.category_extractor.cli extract `
    --url https://www.wellnesswarehouse.com/ `
    --retailer-id 99 `
    --no-headless `
    --dry-run
```

## 🎯 What This Does

1. ✅ **Analyzes** the website with AI (65 seconds)
2. ✅ **Extracts** categories to understand structure (2-3 minutes)
3. ✅ **Generates blueprint** JSON file with extraction strategy
4. ❌ **SKIPS** database save (no categories written to PostgreSQL)

## 📄 What You Get

**Blueprint file saved to:**
```
src/ai_agents/category_extractor/blueprints/retailer_99_[timestamp].json
```

**Blueprint contains:**
```json
{
  "version": "1.0",
  "metadata": {
    "site_url": "https://www.wellnesswarehouse.com/",
    "retailer_id": 99,
    "generated_at": "2025-10-02T12:00:00Z"
  },
  "extraction_strategy": {
    "navigation_type": "sidebar",
    "selectors": {
      "nav_container": ".v-navigation .v-navigation__list",
      "category_links": ".v-navigation__item a",
      "top_level_items": ".v-navigation__item a"
    },
    "interactions": [
      {"type": "click", "target": "a:has-text('Shop by Products')"}
    ]
  },
  "categories_found": 76,
  "max_depth": 1
}
```

## 🔧 Use This Blueprint in Your Scraper

The blueprint tells your scraper:
- **What navigation type** the site uses (sidebar, hover menu, etc.)
- **Which CSS selectors** to use
- **What interactions** are needed (clicks, hovers)
- **How deep** the category hierarchy goes

## 💰 Cost Comparison

| Mode | Database Save | Blueprint Generated | AI Cost |
|------|---------------|---------------------|---------|
| **Normal** | ✅ Yes | ✅ Yes | $0 (Ollama) |
| **--blueprint-only** | ❌ No | ✅ Yes | $0 (Ollama) |

**Both modes cost the same** - the difference is just whether categories are saved to the database.

## 🚀 Full Workflow

### Step 1: Generate Blueprint (No DB Save)
```powershell
python -m src.ai_agents.category_extractor.cli extract `
    --url https://www.wellnesswarehouse.com/ `
    --retailer-id 99 `
    --no-headless `
    --blueprint-only
```

**Output:**
```
✅ Categories discovered: 76
✅ Blueprint saved to: src/ai_agents/.../retailer_99_20251002_120000.json
```

### Step 2: Review the Blueprint
```powershell
# View the generated blueprint
cat src/ai_agents/category_extractor/blueprints/retailer_99_*.json
```

### Step 3: Use in Your Scraper
```python
# Your scraper can load and use the blueprint
import json

with open('blueprints/retailer_99_20251002_120000.json') as f:
    blueprint = json.load(f)

# Now you know:
navigation_type = blueprint['extraction_strategy']['navigation_type']
selectors = blueprint['extraction_strategy']['selectors']
interactions = blueprint['extraction_strategy']['interactions']

# Use these in your scraper!
```

## 🎓 When to Use Each Mode

### Use `--blueprint-only` when:
- ✅ You just want the extraction template
- ✅ You're testing different sites
- ✅ You don't need categories in the database yet
- ✅ You're building a scraper and need the strategy

### Use normal mode (no flag) when:
- ✅ You want to populate your database
- ✅ You're doing a production extraction
- ✅ You need both the blueprint AND the data

## 📊 Example Output

**With `--blueprint-only`:**
```
╭─────────────── Extraction Complete ───────────────╮
│ Categories discovered: 76                         │
│ Blueprint saved to: .../retailer_99_[time].json   │
╰───────────────────────────────────────────────────╯
```

**Without flag (normal mode):**
```
╭─────────────── Extraction Complete ───────────────╮
│ Categories discovered: 76                         │
│ Database -> saved: 70, updated: 6                 │
│ Blueprint saved to: .../retailer_99_[time].json   │
╰───────────────────────────────────────────────────╯
```

## 💡 Pro Tips

### Tip 1: Test Multiple Sites Quickly
```powershell
# Generate blueprints for multiple sites without DB clutter
python -m src.ai_agents.category_extractor.cli extract --url https://site1.com --retailer-id 1 --blueprint-only
python -m src.ai_agents.category_extractor.cli extract --url https://site2.com --retailer-id 2 --blueprint-only
python -m src.ai_agents.category_extractor.cli extract --url https://site3.com --retailer-id 3 --blueprint-only
```

### Tip 2: Compare Strategies
```powershell
# Generate blueprints and compare which sites use similar patterns
ls src/ai_agents/category_extractor/blueprints/
# Look at navigation_type in each blueprint
```

### Tip 3: Iterate Quickly
```powershell
# If extraction fails, try again without polluting database
python -m src.ai_agents.category_extractor.cli extract --url https://example.com --retailer-id 99 --blueprint-only
```

## 🎯 Summary

**Command:**
```powershell
python -m src.ai_agents.category_extractor.cli extract `
    --url https://www.wellnesswarehouse.com/ `
    --retailer-id 99 `
    --no-headless `
    --blueprint-only
```

**What you get:**
- ✅ Blueprint/template JSON file
- ✅ Extraction strategy for your scraper
- ✅ No database pollution

**Time:** 3-5 minutes  
**Cost:** $0 (with Ollama)  
**Output:** Template for your scraper to use

---

**Perfect for:** Getting the extraction strategy without saving data!
