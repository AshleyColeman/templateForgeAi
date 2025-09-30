# Quick Reference Guide

## One-Page Cheat Sheet

### Installation

```bash
# Install dependencies
poetry add strands-agents playwright asyncpg pydantic click rich loguru anthropic

# Install Playwright browsers
poetry run playwright install chromium

# Configure environment
cp .env.example .env
# Edit .env with your AWS and DB credentials
```

### Basic Usage

```bash
# Extract categories from a website
python -m src.ai_agents.category_extractor.cli \
    --url https://example.com \
    --retailer-id 1

# Non-headless mode (see browser)
python -m src.ai_agents.category_extractor.cli \
    --url https://example.com \
    --retailer-id 1 \
    --no-headless

# Using blueprint (fast, no AI)
python -m src.ai_agents.category_extractor.cli \
    --url https://example.com \
    --retailer-id 1 \
    --use-blueprint blueprints/example_v1.json
```

### Environment Variables

```bash
# Required
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
DB_PASSWORD=your_db_password

# Optional
AWS_REGION=us-east-1
MODEL_ID=us.anthropic.claude-sonnet-4-20250514-v1:0
BROWSER_HEADLESS=true
LOG_LEVEL=INFO
```

### Common Commands

```bash
# Run tests
poetry run pytest

# Run with coverage
poetry run pytest --cov

# Lint code
poetry run ruff check .

# Format code
poetry run black .

# Type check
poetry run mypy src/
```

### Project Structure

```
src/ai_agents/category_extractor/
├── cli.py                 # CLI entry point
├── agent.py              # Main agent class
├── config.py             # Configuration
├── database.py           # DB operations
├── tools/
│   ├── page_analyzer.py
│   ├── category_extractor.py
│   └── blueprint_generator.py
└── utils/
    └── logger.py
```

### Key Classes

```python
# Main agent
from src.ai_agents.category_extractor.agent import CategoryExtractionAgent

agent = CategoryExtractionAgent(
    retailer_id=1,
    site_url="https://example.com",
    headless=True
)
result = await agent.run_extraction()

# Database operations
from src.ai_agents.category_extractor.database import CategoryDatabase

db = CategoryDatabase()
await db.connect()
stats = await db.save_categories(categories, retailer_id=1)

# Configuration
from src.ai_agents.category_extractor.config import get_config

config = get_config()
print(config.model_id)
```

### Common Patterns

#### Extract and Save

```python
import asyncio
from src.ai_agents.category_extractor.agent import CategoryExtractionAgent

async def extract():
    agent = CategoryExtractionAgent(
        retailer_id=1,
        site_url="https://example.com"
    )
    result = await agent.run_extraction()
    
    if result['success']:
        print(f"Found {result['state']['categories_found']} categories")
    else:
        print(f"Error: {result['error']}")

asyncio.run(extract())
```

#### Use Blueprint

```python
import json
from playwright.async_api import async_playwright

async def extract_with_blueprint(blueprint_path, url):
    with open(blueprint_path) as f:
        blueprint = json.load(f)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        await page.goto(url)
        
        # Execute blueprint strategy
        selectors = blueprint['selectors']
        items = await page.query_selector_all(selectors['category_items'])
        
        categories = []
        for item in items:
            name_el = await item.query_selector(selectors['category_name'])
            name = await name_el.text_content()
            # ... extract more fields
            categories.append({'name': name, ...})
        
        await browser.close()
        return categories
```

#### Custom Analysis

```python
from src.ai_agents.category_extractor.tools.page_analyzer import PageAnalyzerTool

# Analyze without full extraction
agent = CategoryExtractionAgent(retailer_id=1, site_url="https://example.com")
await agent.initialize_browser()

analyzer = PageAnalyzerTool(agent)
analysis = await analyzer.analyze("https://example.com")

print(f"Navigation type: {analysis['navigation_type']}")
print(f"Confidence: {analysis['confidence']}")
print(f"Selectors: {analysis['selectors']}")
```

### Database Queries

```sql
-- Get all categories for retailer
SELECT * FROM categories WHERE retailer_id = 1 ORDER BY depth, name;

-- Count categories by depth
SELECT depth, COUNT(*) FROM categories WHERE retailer_id = 1 GROUP BY depth;

-- Find root categories
SELECT * FROM categories WHERE parent_id IS NULL AND retailer_id = 1;

-- Check for orphans
SELECT * FROM categories 
WHERE parent_id IS NOT NULL 
  AND parent_id NOT IN (SELECT id FROM categories)
  AND retailer_id = 1;

-- Get category hierarchy (recursive)
WITH RECURSIVE category_tree AS (
    SELECT id, name, parent_id, 0 AS depth, name AS path
    FROM categories
    WHERE parent_id IS NULL AND retailer_id = 1
    
    UNION ALL
    
    SELECT c.id, c.name, c.parent_id, ct.depth + 1, 
           ct.path || ' > ' || c.name
    FROM categories c
    JOIN category_tree ct ON c.parent_id = ct.id
)
SELECT * FROM category_tree ORDER BY path;
```

### Troubleshooting Quick Fixes

```bash
# AWS access denied
aws configure
aws bedrock list-foundation-models --region us-east-1

# Database connection failed
psql -h localhost -U postgres -d product_scraper

# Browser not found
poetry run playwright install chromium

# Module not found
poetry install
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Check logs
tail -f logs/category_extractor.log

# Debug mode
export LOG_LEVEL=DEBUG
python -m src.ai_agents.category_extractor.cli --url ... --no-headless
```

### Error Messages

| Error | Meaning | Fix |
|-------|---------|-----|
| `AccessDeniedException` | No Bedrock access | Enable model in AWS Console |
| `InvalidCatalogNameError` | Database doesn't exist | Create database |
| `TimeoutError` | Page load timeout | Increase timeout or check network |
| `ElementNotFoundError` | Selector invalid | Re-run analysis |
| `BotDetectionError` | Cloudflare challenge | Increase timeout, use stealth |

### Performance Tips

```python
# Parallel extraction (multiple retailers)
import asyncio

async def extract_all(retailers):
    tasks = [extract_retailer(r) for r in retailers]
    return await asyncio.gather(*tasks)

# Optimize browser settings
context = await browser.new_context(
    viewport={'width': 1920, 'height': 1080},
    java_script_enabled=True,
    images_enabled=False,  # Skip images for speed
)

# Use connection pooling
pool = await asyncpg.create_pool(
    host=config.db_host,
    min_size=5,
    max_size=20
)
```

### Cost Estimation

```python
# Estimate cost before extraction
def estimate_cost(complexity='medium'):
    costs = {
        'simple': 0.20,
        'medium': 0.75,
        'complex': 1.50
    }
    return costs.get(complexity, 0.75)

# Track actual costs
total_tokens = result['state'].get('total_tokens', {})
input_cost = total_tokens.get('input', 0) * 3.00 / 1_000_000
output_cost = total_tokens.get('output', 0) * 15.00 / 1_000_000
total_cost = input_cost + output_cost
```

### Blueprint Validation

```python
import json

def validate_blueprint(blueprint_path):
    with open(blueprint_path) as f:
        blueprint = json.load(f)
    
    required_fields = ['version', 'metadata', 'selectors', 'extraction_strategy']
    
    for field in required_fields:
        if field not in blueprint:
            print(f"❌ Missing required field: {field}")
            return False
    
    if blueprint['metadata']['confidence_score'] < 0.7:
        print(f"⚠️  Low confidence: {blueprint['metadata']['confidence_score']}")
    
    print("✅ Blueprint valid")
    return True
```

### Monitoring

```python
# Add monitoring
from datetime import datetime

def log_extraction_metrics(result):
    metrics = {
        'timestamp': datetime.now().isoformat(),
        'retailer_id': result['retailer_id'],
        'success': result['success'],
        'categories_found': result['state'].get('categories_found', 0),
        'duration_ms': result['state'].get('duration_ms', 0),
        'cost': result['state'].get('cost', 0),
    }
    
    # Log to file, database, or monitoring service
    print(f"Metrics: {metrics}")
```

### Testing

```bash
# Run specific test
poetry run pytest tests/test_category_extractor/test_agent.py::test_agent_initialization

# Run with verbose output
poetry run pytest -v

# Run only fast tests
poetry run pytest -m "not slow"

# Run with coverage report
poetry run pytest --cov --cov-report=html

# Debug test
poetry run pytest --pdb
```

### Useful Snippets

```python
# Get retailer info from database
async def get_retailer(retailer_id):
    db = CategoryDatabase()
    await db.connect()
    info = await db.get_retailer_info(retailer_id)
    await db.disconnect()
    return info

# Clean up old categories
async def cleanup_old_categories(retailer_id, days=30):
    query = """
    DELETE FROM categories 
    WHERE retailer_id = $1 
      AND created_at < NOW() - INTERVAL '%s days'
    """ % days
    
    async with db.pool.acquire() as conn:
        result = await conn.execute(query, retailer_id)
        return result

# Export categories to JSON
async def export_categories(retailer_id, output_file):
    db = CategoryDatabase()
    categories = await db.get_retailer_categories(retailer_id)
    
    with open(output_file, 'w') as f:
        json.dump(categories, f, indent=2)
```

### Resources

- **Strands Docs**: https://strandsagents.com/latest/
- **Playwright Docs**: https://playwright.dev/python/
- **Claude API**: https://docs.anthropic.com/claude/
- **Project Docs**: `docs/category_res_eng_guide/`

### Support

1. Check `06_FAQ_and_Troubleshooting.md`
2. Review logs: `logs/category_extractor.log`
3. Run in debug mode: `--no-headless` + `LOG_LEVEL=DEBUG`
4. Check AWS costs: AWS Console → Cost Explorer
