# AI Category Extractor - Developer Implementation Guide

## 🎯 Mission

You are building an **AI-powered category extraction system** using Python that will automatically discover and extract product categories from e-commerce websites without manual configuration. This system will replace the existing TypeScript scraper with an intelligent, self-adapting solution.

## 📋 Context

### What You're Building

An autonomous AI agent that:
1. Takes a website URL as input
2. Analyzes the page structure using Claude Vision API
3. Automatically identifies category navigation patterns
4. Extracts all categories with hierarchical relationships
5. Saves data to PostgreSQL database
6. Generates reusable blueprints for future extractions

### Why This Matters

**Current Problem**: The existing TypeScript scraper requires 6-8 hours of manual configuration per retailer. Adding 50+ retailers is not feasible.

**Your Solution**: AI agent extracts categories in 10 minutes with ~$1 cost per site, enabling rapid scaling.

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                     CLI Interface                        │
│              (User provides URL + Retailer ID)           │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│            CategoryExtractionAgent (Orchestrator)        │
│  - Manages workflow                                      │
│  - Coordinates tools                                     │
│  - Uses Strands Agents SDK + Claude 4 Sonnet           │
└────────────┬────────────────────────────────────────────┘
             │
             │ Uses ↓
    ┌────────┴────────┬────────────┬────────────┐
    │                 │            │            │
    ▼                 ▼            ▼            ▼
┌─────────┐    ┌──────────┐  ┌─────────┐  ┌──────────┐
│  Page   │    │ Category │  │Database │  │Blueprint │
│Analyzer │    │Extractor │  │  Saver  │  │Generator │
│  Tool   │    │   Tool   │  │  Tool   │  │   Tool   │
└─────────┘    └──────────┘  └─────────┘  └──────────┘
     │              │             │             │
     │              │             ▼             │
     │              │      ┌──────────┐        │
     │              │      │PostgreSQL│        │
     │              │      │ Database │        │
     │              │      └──────────┘        │
     │              │                          │
     ▼              ▼                          ▼
┌──────────────────────────────────────────────────┐
│           Playwright Browser Automation          │
└──────────────────────────────────────────────────┘
```

## 🛠️ Technology Stack

### Core Technologies
- **Python 3.11+**: Primary language
- **Strands Agents SDK**: AI agent framework
- **Claude 4 Sonnet**: LLM for analysis (via AWS Bedrock)
- **Playwright**: Browser automation
- **PostgreSQL**: Database (existing schema)
- **Poetry**: Dependency management

### Key Libraries
```toml
strands-agents = "^0.3.0"      # AI agent framework
playwright = "^1.40.0"          # Browser automation
asyncpg = "^0.29.0"             # Async PostgreSQL driver
pydantic = "^2.5.0"             # Data validation
click = "^8.1.0"                # CLI framework
rich = "^13.7.0"                # Terminal formatting
loguru = "^0.7.2"               # Logging
anthropic = "^0.8.0"            # Anthropic Claude API
tenacity = "^8.2.0"             # Retry logic
beautifulsoup4 = "^4.12.0"      # HTML parsing
```

## 📊 Database Schema

Your system connects to an **existing PostgreSQL database**:

```sql
-- categories table (already exists)
CREATE TABLE categories (
    id serial4 PRIMARY KEY,
    name text NOT NULL,
    url text NULL,
    parent_id int4 NULL REFERENCES categories(id),
    retailer_id int4 NOT NULL REFERENCES retailers(id),
    depth int4 NULL,
    enabled bool DEFAULT false,
    created_at timestamptz DEFAULT CURRENT_TIMESTAMP
);

-- retailers table (already exists)
CREATE TABLE retailers (
    id serial4 PRIMARY KEY,
    name text NOT NULL,
    base_url text NULL,
    enabled bool DEFAULT true
);
```

**Connection String**:
```
postgresql://postgres:postgres@localhost:5432/products?schema=public
```

## 🎨 Design Principles

### 1. Spec-Driven Development
- Each task has detailed specifications
- Implementation must match specs exactly
- No shortcuts or "good enough" solutions

### 2. Minimal Dependencies
- Use async/await throughout
- Keep dependencies lean
- Prefer standard library when possible

### 3. Error Handling
- Every function has error handling
- Graceful degradation
- Clear, actionable error messages

### 4. Logging
- Log all major operations
- Include context in logs
- Use appropriate log levels (DEBUG, INFO, WARNING, ERROR)

### 5. Type Safety
- Use type hints everywhere
- Pydantic models for validation
- MyPy checks pass

## 🚀 Development Workflow

### Step 1: Setup Environment
```bash
# Create project directory
cd /home/ashleycoleman/Projects/product_scraper

# Create Python project structure
mkdir -p src/ai_agents/category_extractor/{tools,utils,blueprints}

# Initialize Poetry
poetry init
poetry add [dependencies...]
poetry run playwright install chromium

# Configure environment
cp .env.example .env
# Edit with AWS and DB credentials
```

### Step 2: Implement Tasks in Order

Follow the task files in sequence:
1. `01_environment_setup.md` - Project setup
2. `02_configuration_management.md` - Config system
3. `03_database_integration.md` - Database layer
4. `04_core_agent.md` - Main agent class
5. `05_page_analyzer_tool.md` - Page analysis
6. `06_category_extractor_tool.md` - Extraction logic
7. `07_blueprint_generator_tool.md` - Blueprint creation
8. `08_cli_interface.md` - Command-line interface
9. `09_error_handling.md` - Error management
10. `10_blueprint_system.md` - Blueprint usage
11. `11_testing.md` - Test suite (last)

### Step 3: Test Each Component

After implementing each task:
1. Manual testing (run the code)
2. Verify output matches specifications
3. Check logs for errors
4. Test edge cases

### Step 4: Integration

Once all components work individually:
1. Test full workflow end-to-end
2. Extract from a real website
3. Verify database persistence
4. Generate and validate blueprint

## 🔑 Key Concepts

### 1. AI Agent Pattern

The agent follows this workflow:
```python
# Agent receives task
task = "Extract categories from https://example.com"

# Agent thinks and plans
plan = agent.think(task)  # Uses LLM to analyze

# Agent executes tools
for step in plan:
    result = agent.execute_tool(step.tool_name, step.parameters)
    
# Agent validates and returns
return agent.validate_and_format(results)
```

### 2. Tool Pattern

Each tool is a Python function/class that:
- Has clear input/output contracts
- Is registered with the agent
- Can be called by the LLM
- Returns structured data

```python
from strands import tool

@tool
async def analyze_page(url: str) -> Dict[str, Any]:
    """Analyze page structure to identify categories."""
    # Implementation
    return {"navigation_type": "...", "selectors": {...}}
```

### 3. Blueprint Pattern

Blueprints capture successful extraction strategies:
```json
{
  "version": "1.0",
  "selectors": {
    "nav_container": "nav.main",
    "category_links": "a.category"
  },
  "interactions": [
    {"action": "hover", "target": "..."},
    {"action": "extract", "target": "..."}
  ]
}
```

Once created, blueprints enable fast extraction without LLM costs.

## ⚠️ Critical Requirements

### Must-Haves

1. **AWS Bedrock Integration**: Use Claude 4 Sonnet via AWS Bedrock (not Anthropic direct API)
2. **Async/Await**: All I/O operations must be async
3. **PostgreSQL Connection Pooling**: Use asyncpg with connection pool
4. **Error Handling**: Try-except blocks with specific exception types
5. **Type Hints**: Every function has complete type hints
6. **Logging**: Use loguru for all logging
7. **Configuration**: Use Pydantic for config management
8. **CLI**: Use Click for CLI framework

### Nice-to-Haves (Optional)

- Retry logic with exponential backoff
- Metrics and monitoring
- Progress bars (using Rich)
- Blueprint validation
- Cache layer

## 🎯 Success Criteria

Your implementation is successful when:

### Functional Requirements
- ✅ Can extract categories from any e-commerce site
- ✅ Identifies navigation patterns automatically
- ✅ Saves data correctly to PostgreSQL
- ✅ Generates valid blueprints
- ✅ Handles errors gracefully
- ✅ CLI is intuitive and documented

### Non-Functional Requirements
- ✅ Extraction completes in <15 minutes
- ✅ LLM cost <$2 per site
- ✅ 90%+ accuracy vs manual inspection
- ✅ No memory leaks in browser automation
- ✅ Logs are clear and actionable
- ✅ Code passes type checking (mypy)

### Testing Requirements (Phase 11)
- ✅ Unit tests for core functions
- ✅ Integration tests for database
- ✅ E2E test with real website
- ✅ 80%+ code coverage

## 📝 Code Style Guidelines

### Python Style
```python
# Use descriptive variable names
navigation_type = "hover_menu"  # Good
nt = "hover_menu"  # Bad

# Type hints always
async def extract_categories(
    page: Page,
    selectors: Dict[str, str]
) -> List[Dict[str, Any]]:
    ...

# Docstrings for public functions
async def analyze_page(url: str) -> Dict[str, Any]:
    """
    Analyze page structure to identify category navigation.
    
    Args:
        url: Website URL to analyze
        
    Returns:
        Analysis dict with navigation_type, selectors, confidence
        
    Raises:
        NavigationError: If page cannot be loaded
        AnalysisError: If analysis fails
    """
    ...

# Use Pydantic for data validation
class CategoryData(BaseModel):
    name: str
    url: str
    depth: int = 0
    parent_id: Optional[int] = None
```

### File Organization
```python
# Imports organized: standard lib, third-party, local
import asyncio
import json
from typing import Dict, List, Optional

from playwright.async_api import Page, Browser
from loguru import logger

from .config import get_config
from .errors import ExtractionError
```

### Async Patterns
```python
# Always use async/await for I/O
async def fetch_data():
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()

# Use asyncio.gather for parallel operations
results = await asyncio.gather(
    extract_retailer(1),
    extract_retailer(2),
    extract_retailer(3)
)
```

## 🐛 Debugging Tips

### Enable Debug Logging
```python
# In config or .env
LOG_LEVEL=DEBUG

# Or at runtime
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Run Browser in Non-Headless Mode
```bash
python -m src.ai_agents.category_extractor.cli \
    --url https://example.com \
    --retailer-id 1 \
    --no-headless  # See what's happening
```

### Inspect Page with Playwright
```python
# Add breakpoints in code
await page.screenshot(path="debug.png")
html = await page.content()
print(html[:5000])

# Or use Playwright inspector
# PWDEBUG=1 python your_script.py
```

### Check Database State
```sql
-- Verify data was saved
SELECT COUNT(*) FROM categories WHERE retailer_id = 1;

-- Check hierarchy
SELECT id, name, parent_id, depth FROM categories 
WHERE retailer_id = 1 
ORDER BY depth, name;
```

## 📚 Reference Documents

As you work through tasks, refer to:
- **Technical Specification**: `01_Technical_Specification.md`
- **Architecture Design**: `02_Architecture_Design.md`
- **Implementation Guide**: `03_Implementation_Guide.md`
- **Prompt Engineering**: `07_Prompt_Engineering_Guide.md`
- **Real Examples**: `08_Real_World_Examples.md`
- **Quick Reference**: `10_Quick_Reference.md`

## 🎓 Learning Path

### New to AI Agents?
1. Read Strands Agents docs: https://strandsagents.com/latest/
2. Understand the agent/tool pattern
3. Review `07_Prompt_Engineering_Guide.md`

### New to Playwright?
1. Playwright Python docs: https://playwright.dev/python/
2. Focus on: page.goto, page.query_selector, page.click
3. Understand async_playwright pattern

### New to AWS Bedrock?
1. Set up AWS CLI credentials
2. Enable Claude 4 Sonnet in console
3. Test with boto3 example

## ⏱️ Time Estimates

Realistic time estimates per task:
- Tasks 1-3 (Setup): 4-6 hours
- Task 4 (Core Agent): 6-8 hours
- Tasks 5-7 (Tools): 12-16 hours total
- Task 8 (CLI): 2-3 hours
- Task 9 (Error Handling): 3-4 hours
- Task 10 (Blueprints): 4-6 hours
- Task 11 (Testing): 8-12 hours

**Total: 40-60 hours** for complete implementation

## 🚨 Common Pitfalls to Avoid

1. **Forgetting async/await**: All Playwright and database operations are async
2. **Not using connection pooling**: Creates too many DB connections
3. **Hardcoding values**: Use configuration system
4. **Poor error messages**: Always provide context in errors
5. **Not closing browser**: Memory leaks if browser not cleaned up
6. **Ignoring bot detection**: Handle Cloudflare/bot detection gracefully
7. **Not validating data**: Use Pydantic models
8. **Skipping logging**: You'll need logs for debugging production issues

## ✅ Definition of Done

A task is complete when:
1. Code is written following specifications
2. Type hints are present and mypy passes
3. Error handling is implemented
4. Logging is in place
5. Manual testing shows it works
6. Code is committed to git
7. Documentation is updated if needed

## 🎉 Getting Started

1. Read through this guide completely
2. Review the master task list: `MASTER_TASKLIST.md`
3. Start with Task 1: Environment Setup
4. Work through tasks sequentially
5. Ask questions if specifications are unclear
6. Test thoroughly at each step

**Remember**: Quality over speed. Take your time to build it right the first time.

---

**Good luck! You're building something that will save hundreds of hours of manual work and enable rapid scaling. Make it count! 🚀**
