# AI Category Extractor - Implementation Prompt

## 🎯 System Prompt for AI Assistant

Use this prompt when working with an AI assistant (like Claude, GPT-4, etc.) to help implement the system:

---

## Core Context

You are helping build an **AI-powered category extraction system** for e-commerce websites using Python. The system uses:

- **Strands Agents SDK** for AI agent framework
- **Claude or GPT models** (via Ollama/OpenAI/Anthropic) for analysis
- **Playwright** for browser automation  
- **PostgreSQL** (asyncpg) for data storage
- **Python 3.11+** with async/await throughout

### System Architecture

```
CLI → CategoryExtractionAgent → Tools (PageAnalyzer, CategoryExtractor, BlueprintGenerator) → PostgreSQL
                  ↓
           Playwright Browser
```

### Existing Database Schema

```sql
-- DO NOT CREATE - already exists
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

CREATE TABLE retailers (
    id serial4 PRIMARY KEY,
    name text NOT NULL,
    base_url text NULL,
    enabled bool DEFAULT true
);
```

**Connection**: `postgresql://postgres:postgres@localhost:5432/products?schema=public`

## Implementation Guidelines

### Code Style

1. **Always use async/await** for I/O operations
2. **Type hints everywhere** - every function must have complete type hints
3. **Pydantic for validation** - use Pydantic models for data structures
4. **Loguru for logging** - use logger from loguru
5. **Error handling** - try/except with specific exception types
6. **Docstrings** - Google style docstrings for all public functions

### Example Code Pattern

```python
from typing import List, Dict, Any, Optional
from playwright.async_api import Page
from loguru import logger
from pydantic import BaseModel

class CategoryData(BaseModel):
    """Category data model."""
    name: str
    url: str
    depth: int = 0
    parent_id: Optional[int] = None

async def extract_categories(
    page: Page,
    selectors: Dict[str, str]
) -> List[Dict[str, Any]]:
    """Extract categories from page.
    
    Args:
        page: Playwright page instance
        selectors: Dict of CSS selectors
    
    Returns:
        List of category dicts
    
    Raises:
        ExtractionError: If extraction fails
    """
    try:
        logger.info("Starting category extraction")
        
        # Implementation here
        categories = []
        
        logger.info(f"Extracted {len(categories)} categories")
        return categories
        
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        raise ExtractionError(f"Failed to extract categories: {e}")
```

## Key Requirements

### Critical Must-Haves

1. **Ollama/OpenAI/Anthropic Integration**: Use boto3 to call Claude via Bedrock, NOT Anthropic direct API
2. **Connection Pooling**: Use asyncpg.create_pool() for database
3. **Hierarchy Handling**: Categories must preserve parent-child relationships
4. **Blueprint Generation**: Create JSON templates for future fast extraction
5. **Error Recovery**: Graceful degradation, never crash the process
6. **Logging**: Log all major operations with appropriate levels

### Project Structure

```
src/ai_agents/category_extractor/
├── __init__.py
├── agent.py              # Main CategoryExtractionAgent class
├── config.py             # Pydantic configuration
├── database.py           # CategoryDatabase class
├── errors.py             # Custom exceptions
├── tools/
│   ├── page_analyzer.py      # PageAnalyzerTool
│   ├── category_extractor.py # CategoryExtractorTool
│   └── blueprint_generator.py # BlueprintGeneratorTool
└── utils/
    ├── logger.py         # Logging setup
    └── url_utils.py      # URL utilities
```

## When Implementing a Task

1. **Read the task specification completely**
2. **Check dependencies** - ensure previous tasks are complete
3. **Follow the code patterns** from specifications exactly
4. **Add comprehensive error handling**
5. **Include detailed logging**
6. **Write docstrings** for all functions
7. **Test manually** before marking complete

## Common Patterns

### Async Database Operations

```python
async def save_to_db(self, categories: List[Dict], retailer_id: int):
    db = CategoryDatabase()
    await db.connect()
    
    try:
        stats = await db.save_categories(categories, retailer_id)
        return stats
    finally:
        await db.disconnect()
```

### Browser Automation

```python
async def initialize_browser(self):
    self.playwright = await async_playwright().start()
    self.browser = await self.playwright.chromium.launch(
        headless=self.headless,
        args=['--no-sandbox', '--disable-setuid-sandbox']
    )
    self.page = await self.browser.new_page()
```

### LLM Integration (Ollama/OpenAI/Anthropic)

```python
import openai or anthropic
import json

bedrock = openai.AsyncOpenAI or anthropic.AsyncAnthropic(
    'LLM provider client',
    region_name=config.aws_region
)

response = bedrock.invoke_model(
    modelId=config.model_id,
    body=json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": config.max_tokens,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    })
)
```

### Strands Agents Tool Pattern

```python
from strands import tool

@tool
async def analyze_page(url: str) -> Dict[str, Any]:
    """Analyze page structure.
    
    This docstring is shown to the LLM!
    """
    # Implementation
    return {"navigation_type": "...", "selectors": {...}}
```

## Testing Approach

For each component:

1. **Unit test**: Test function in isolation
2. **Integration test**: Test with real database/browser
3. **Manual test**: Run and verify output
4. **Edge cases**: Test error scenarios

## Success Metrics

Your implementation is correct when:

- ✅ Can extract categories from a real website
- ✅ Data saves correctly to PostgreSQL
- ✅ Blueprints generate and are reusable
- ✅ Handles errors without crashing
- ✅ Logs are clear and informative
- ✅ Type checks pass (mypy)
- ✅ Code follows style guidelines

## Important Reminders

1. **Never skip error handling** - every I/O operation needs try/except
2. **Always close resources** - browsers, database connections
3. **Log important events** - helps debugging in production
4. **Validate data** - use Pydantic models
5. **Test incrementally** - don't write everything then test
6. **Follow the specs** - don't add features not in the spec
7. **Ask questions** - if spec is unclear, ask before implementing

## Example Session

```python
# Good implementation session:

# 1. Read task specification
# 2. Understand requirements
# 3. Implement step by step
# 4. Test after each step
# 5. Handle errors
# 6. Add logging
# 7. Write docstrings
# 8. Run full test
# 9. Fix any issues
# 10. Mark complete
```

## When You're Stuck

1. Check the reference documentation in `docs/category_res_eng_guide/`
2. Review similar code in existing tasks
3. Test in isolation (smaller piece of code)
4. Check logs for error messages
5. Verify environment variables are set
6. Ensure database/AWS credentials work
7. Ask specific questions about the issue

## Quality Checklist

Before submitting any code:

- [ ] Type hints on all functions
- [ ] Docstrings in Google style
- [ ] Error handling with try/except
- [ ] Logging at appropriate levels
- [ ] Async/await used correctly
- [ ] Resources cleaned up (finally blocks)
- [ ] No hardcoded values (use config)
- [ ] Tested manually and works
- [ ] Follows existing code patterns
- [ ] No obvious bugs or issues

---

## Final Notes

This is a **production system** that will handle real e-commerce data. Quality matters more than speed. Take your time, follow the specifications, test thoroughly, and build something robust.

**Remember**: Every hour spent building it right saves 10 hours of debugging later!

---

**Use this prompt** when asking AI assistants for help implementing specific tasks. It provides all the context needed for consistent, high-quality code generation.

**Last Updated**: 2025-09-30
