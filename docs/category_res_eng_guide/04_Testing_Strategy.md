# AI Category Extractor: Testing Strategy

## Testing Pyramid

```
         /\
        /  \      E2E Tests (Few)
       /____\     - Full extraction workflows
      /      \    - Real websites (sandbox)
     /        \   
    /__________\  Integration Tests (Some)
   /            \ - Tool integration
  /              \- Database operations
 /________________\
/                  \ Unit Tests (Many)
                    - Individual functions
                    - Data validation
                    - URL normalization
```

## Test Categories

### 1. Unit Tests

Test individual functions in isolation.

**File**: `tests/test_category_extractor/test_utils.py`

```python
"""Unit tests for utility functions."""
import pytest
from src.ai_agents.category_extractor.utils.url_utils import normalize_url

def test_normalize_url_with_relative_path():
    """Test URL normalization with relative path."""
    base = "https://example.com/categories"
    relative = "../products"
    result = normalize_url(relative, base)
    assert result == "https://example.com/products"

def test_normalize_url_with_absolute_path():
    """Test URL normalization with absolute path."""
    base = "https://example.com/categories"
    absolute = "/products/new"
    result = normalize_url(absolute, base)
    assert result == "https://example.com/products/new"

def test_normalize_url_with_query_params():
    """Test URL normalization preserves query params."""
    base = "https://example.com"
    url = "/search?q=test&page=2"
    result = normalize_url(url, base)
    assert result == "https://example.com/search?q=test&page=2"

def test_normalize_url_removes_fragments():
    """Test URL normalization removes fragments."""
    base = "https://example.com"
    url = "/page#section"
    result = normalize_url(url, base)
    assert result == "https://example.com/page"
```

**File**: `tests/test_category_extractor/test_validators.py`

```python
"""Unit tests for data validators."""
import pytest
from src.ai_agents.category_extractor.tools.validators import (
    validate_category,
    validate_hierarchy
)

def test_validate_category_success():
    """Test category validation with valid data."""
    category = {
        "name": "Electronics",
        "url": "https://example.com/electronics",
        "depth": 0,
        "parent_id": None
    }
    assert validate_category(category) is True

def test_validate_category_missing_name():
    """Test category validation fails without name."""
    category = {
        "url": "https://example.com/electronics",
        "depth": 0
    }
    with pytest.raises(ValueError, match="name"):
        validate_category(category)

def test_validate_hierarchy_success():
    """Test hierarchy validation with valid data."""
    categories = [
        {"id": 1, "name": "Root", "depth": 0, "parent_id": None},
        {"id": 2, "name": "Child", "depth": 1, "parent_id": 1}
    ]
    assert validate_hierarchy(categories) is True

def test_validate_hierarchy_orphaned_child():
    """Test hierarchy validation fails with orphaned child."""
    categories = [
        {"id": 1, "name": "Root", "depth": 0, "parent_id": None},
        {"id": 2, "name": "Orphan", "depth": 1, "parent_id": 99}
    ]
    with pytest.raises(ValueError, match="parent"):
        validate_hierarchy(categories)
```

### 2. Integration Tests

Test component interactions.

**File**: `tests/test_category_extractor/test_database_integration.py`

```python
"""Integration tests for database operations."""
import pytest
import asyncio
from src.ai_agents.category_extractor.database import CategoryDatabase

@pytest.fixture
async def db():
    """Database fixture."""
    db = CategoryDatabase()
    await db.connect()
    yield db
    await db.disconnect()

@pytest.mark.asyncio
async def test_save_categories(db):
    """Test saving categories to database."""
    categories = [
        {
            "id": 1,
            "name": "Test Category",
            "url": "https://test.com/cat1",
            "depth": 0,
            "parent_id": None
        },
        {
            "id": 2,
            "name": "Test Subcategory",
            "url": "https://test.com/cat1/sub1",
            "depth": 1,
            "parent_id": 1
        }
    ]
    
    retailer_id = 999  # Test retailer
    stats = await db.save_categories(categories, retailer_id)
    
    assert stats["saved"] >= 1
    assert stats["errors"] == 0

@pytest.mark.asyncio
async def test_save_duplicate_category(db):
    """Test saving duplicate category updates existing."""
    category = {
        "id": 1,
        "name": "Duplicate Test",
        "url": "https://test.com/dup",
        "depth": 0,
        "parent_id": None
    }
    
    retailer_id = 999
    
    # First save
    stats1 = await db.save_categories([category], retailer_id)
    assert stats1["saved"] == 1
    
    # Second save (should update)
    stats2 = await db.save_categories([category], retailer_id)
    assert stats2["updated"] == 1
    assert stats2["saved"] == 0
```

**File**: `tests/test_category_extractor/test_page_analyzer_integration.py`

```python
"""Integration tests for page analyzer."""
import pytest
from playwright.async_api import async_playwright
from src.ai_agents.category_extractor.tools.page_analyzer import PageAnalyzerTool

class MockAgent:
    """Mock agent for testing."""
    def __init__(self, page):
        self.page = page
        self.extraction_state = {}

@pytest.mark.asyncio
async def test_analyze_simple_page():
    """Test analyzing a simple HTML page."""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        # Create simple test HTML
        await page.set_content("""
            <html>
                <body>
                    <nav>
                        <ul>
                            <li><a href="/cat1">Category 1</a></li>
                            <li><a href="/cat2">Category 2</a></li>
                        </ul>
                    </nav>
                </body>
            </html>
        """)
        
        agent = MockAgent(page)
        analyzer = PageAnalyzerTool(agent)
        
        result = await analyzer.analyze("about:blank")
        
        assert "navigation_type" in result
        assert "selectors" in result
        assert result["confidence"] > 0
        
        await browser.close()
```

### 3. End-to-End Tests

Test complete workflows with real websites.

**File**: `tests/test_category_extractor/test_e2e.py`

```python
"""End-to-end tests."""
import pytest
import asyncio
from src.ai_agents.category_extractor.agent import CategoryExtractionAgent

@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.asyncio
async def test_extract_from_test_site():
    """Test full extraction from a test website."""
    # Use a stable, simple test site
    agent = CategoryExtractionAgent(
        retailer_id=999,
        site_url="https://books.toscrape.com",  # Public test site
        headless=True
    )
    
    result = await agent.run_extraction()
    
    assert result["success"] is True
    assert result["state"]["categories_found"] > 0

@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.skip(reason="Requires real retailer credentials")
@pytest.mark.asyncio
async def test_extract_from_clicks():
    """Test extraction from Clicks (South African retailer)."""
    agent = CategoryExtractionAgent(
        retailer_id=1,
        site_url="https://clicks.co.za",
        headless=True
    )
    
    result = await agent.run_extraction()
    
    assert result["success"] is True
    assert result["state"]["categories_found"] > 50  # Clicks has many categories
    assert result["state"]["saved_count"] > 0
```

## Test Configuration

**File**: `pytest.ini`

```ini
[pytest]
markers =
    unit: Unit tests (fast)
    integration: Integration tests (medium)
    e2e: End-to-end tests (slow)
    slow: Slow tests (skip by default)

testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

asyncio_mode = auto

# Skip slow tests by default
addopts = 
    -v
    --tb=short
    --strict-markers
    -m "not slow"
```

## Running Tests

```bash
# Run all tests (except slow)
poetry run pytest

# Run only unit tests
poetry run pytest -m unit

# Run integration tests
poetry run pytest -m integration

# Run E2E tests (including slow)
poetry run pytest -m e2e --slow

# Run specific test file
poetry run pytest tests/test_category_extractor/test_utils.py

# Run with coverage
poetry run pytest --cov=src/ai_agents/category_extractor

# Run in parallel
poetry run pytest -n auto
```

## Mock Data for Testing

**File**: `tests/fixtures/mock_categories.json`

```json
{
  "simple_hierarchy": [
    {
      "id": 1,
      "name": "Electronics",
      "url": "https://test.com/electronics",
      "depth": 0,
      "parent_id": null
    },
    {
      "id": 2,
      "name": "Computers",
      "url": "https://test.com/electronics/computers",
      "depth": 1,
      "parent_id": 1
    },
    {
      "id": 3,
      "name": "Laptops",
      "url": "https://test.com/electronics/computers/laptops",
      "depth": 2,
      "parent_id": 2
    }
  ],
  "complex_hierarchy": [
    {
      "id": 1,
      "name": "Health & Beauty",
      "url": "https://test.com/health",
      "depth": 0,
      "parent_id": null
    },
    {
      "id": 2,
      "name": "Skincare",
      "url": "https://test.com/health/skincare",
      "depth": 1,
      "parent_id": 1
    },
    {
      "id": 3,
      "name": "Face",
      "url": "https://test.com/health/skincare/face",
      "depth": 2,
      "parent_id": 2
    },
    {
      "id": 4,
      "name": "Body",
      "url": "https://test.com/health/skincare/body",
      "depth": 2,
      "parent_id": 2
    },
    {
      "id": 5,
      "name": "Makeup",
      "url": "https://test.com/health/makeup",
      "depth": 1,
      "parent_id": 1
    }
  ]
}
```

## Test Fixtures

**File**: `tests/conftest.py`

```python
"""Pytest configuration and fixtures."""
import pytest
import asyncio
import json
from pathlib import Path

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_categories():
    """Load mock category data."""
    fixture_path = Path(__file__).parent / "fixtures" / "mock_categories.json"
    with open(fixture_path) as f:
        return json.load(f)

@pytest.fixture
def simple_hierarchy(mock_categories):
    """Simple category hierarchy fixture."""
    return mock_categories["simple_hierarchy"]

@pytest.fixture
def complex_hierarchy(mock_categories):
    """Complex category hierarchy fixture."""
    return mock_categories["complex_hierarchy"]
```

## Performance Testing

**File**: `tests/test_category_extractor/test_performance.py`

```python
"""Performance tests."""
import pytest
import time
from src.ai_agents.category_extractor.agent import CategoryExtractionAgent

@pytest.mark.performance
@pytest.mark.asyncio
async def test_extraction_speed():
    """Test extraction completes within time limit."""
    agent = CategoryExtractionAgent(
        retailer_id=999,
        site_url="https://books.toscrape.com",
        headless=True
    )
    
    start = time.time()
    result = await agent.run_extraction()
    duration = time.time() - start
    
    assert result["success"] is True
    assert duration < 300  # Should complete within 5 minutes

@pytest.mark.performance
def test_database_save_speed(simple_hierarchy):
    """Test database save performance."""
    from src.ai_agents.category_extractor.database import CategoryDatabase
    
    db = CategoryDatabase()
    
    # Generate large dataset
    categories = simple_hierarchy * 100  # 300 categories
    
    start = time.time()
    asyncio.run(db.save_categories(categories, 999))
    duration = time.time() - start
    
    assert duration < 30  # Should save 300 categories in < 30 seconds
```

## Continuous Integration

**File**: `.github/workflows/test.yml`

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: product_scraper_test
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: testpass
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install Poetry
        run: |
          curl -sSL https://install.python-poetry.org | python3 -
      
      - name: Install dependencies
        run: |
          poetry install
          poetry run playwright install chromium
      
      - name: Run tests
        env:
          DB_HOST: localhost
          DB_PORT: 5432
          DB_NAME: product_scraper_test
          DB_USER: postgres
          DB_PASSWORD: testpass
        run: |
          poetry run pytest -v --cov
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Test Coverage Goals

- **Unit Tests**: > 80% coverage
- **Integration Tests**: All critical paths covered
- **E2E Tests**: At least 2 real-world scenarios

## Manual Testing Checklist

Before deploying:

- [ ] Test with at least 3 different retailer websites
- [ ] Verify extracted categories match manual inspection
- [ ] Check database integrity after extraction
- [ ] Test error handling with invalid URLs
- [ ] Verify blueprint generation
- [ ] Test with headless and non-headless modes
- [ ] Check logs for errors/warnings
- [ ] Verify Ollama/OpenAI/Anthropic costs are within budget
- [ ] Test recovery from network failures
- [ ] Verify no memory leaks in long-running extractions
