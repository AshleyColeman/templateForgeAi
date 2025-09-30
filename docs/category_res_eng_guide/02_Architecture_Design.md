# AI Category Extractor: Architecture Design

## Complete Project Structure

```
src/ai_agents/category_extractor/
├── __init__.py
├── cli.py                      # CLI interface
├── agent.py                    # Main agent orchestrator
├── config.py                   # Configuration management
├── database.py                 # Database operations
├── errors.py                   # Custom exceptions
├── tools/
│   ├── __init__.py
│   ├── page_analyzer.py       # Page analysis tool
│   ├── category_extractor.py  # Category extraction tool
│   ├── blueprint_generator.py # Blueprint generation
│   └── validators.py          # Data validation
├── utils/
│   ├── __init__.py
│   ├── url_utils.py           # URL normalization
│   ├── html_cleaner.py        # HTML cleaning
│   └── logger.py              # Logging setup
└── blueprints/                # Generated blueprints
    └── README.md

tests/
└── test_category_extractor/
    ├── test_agent.py
    ├── test_tools.py
    └── test_database.py
```

## Configuration Management

**File**: `config.py`

```python
from pydantic import BaseSettings, Field
import os

class ExtractorConfig(BaseSettings):
    # Database
    db_host: str = Field(default="localhost", env="DB_HOST")
    db_port: int = Field(default=5432, env="DB_PORT")
    db_name: str = Field(default="product_scraper", env="DB_NAME")
    db_user: str = Field(default="postgres", env="DB_USER")
    db_password: str = Field(default="", env="DB_PASSWORD")
    
    # AWS Bedrock
    aws_region: str = Field(default="us-east-1", env="AWS_REGION")
    
    # Model
    model_id: str = Field(
        default="us.anthropic.claude-sonnet-4-20250514-v1:0",
        env="MODEL_ID"
    )
    
    # Browser
    browser_headless: bool = Field(default=True, env="BROWSER_HEADLESS")
    browser_timeout: int = Field(default=60000, env="BROWSER_TIMEOUT")
    
    # Extraction
    max_depth: int = Field(default=5, env="MAX_DEPTH")
    max_categories: int = Field(default=10000, env="MAX_CATEGORIES")
    
    # Blueprints
    blueprint_dir: str = Field(default="./blueprints", env="BLUEPRINT_DIR")
    
    class Config:
        env_file = ".env"

config = ExtractorConfig()
```

## Error Handling

**File**: `errors.py`

```python
class ExtractorError(Exception):
    """Base exception."""
    pass

class NavigationError(ExtractorError):
    """Navigation failed."""
    pass

class AnalysisError(ExtractorError):
    """Analysis failed."""
    pass

class ExtractionError(ExtractorError):
    """Extraction failed."""
    pass

class DatabaseError(ExtractorError):
    """Database operation failed."""
    pass

class BotDetectionError(ExtractorError):
    """Bot detected."""
    pass
```

## Dependencies

**File**: `pyproject.toml`

```toml
[tool.poetry]
name = "ai-category-extractor"
version = "0.1.0"

[tool.poetry.dependencies]
python = "^3.11"
strands-agents = "^0.1.0"
playwright = "^1.40.0"
asyncpg = "^0.29.0"
pydantic = "^2.5.0"
click = "^8.1.7"
rich = "^13.7.0"
loguru = "^0.7.2"
anthropic = "^0.28.0"
tenacity = "^8.2.3"

[tool.poetry.dev-dependencies]
pytest = "^7.4.3"
pytest-asyncio = "^0.21.1"
black = "^23.12.0"
mypy = "^1.7.1"
ruff = "^0.1.8"
```

## Database Schema Integration

Uses existing PostgreSQL schema:

```sql
CREATE TABLE categories (
    id serial4 PRIMARY KEY,
    name text NOT NULL,
    url text NULL,
    parent_id int4 NULL,
    retailer_id int4 NOT NULL,
    depth int4 NULL,
    enabled bool DEFAULT false NOT NULL,
    created_at timestamptz DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(url, retailer_id)
);
```

## Workflow Diagram

```
1. CLI Input
   ↓
2. Agent Initialize → Playwright Browser
   ↓
3. PageAnalyzerTool
   - Navigate to URL
   - Capture screenshot
   - Extract HTML
   - LLM Vision Analysis
   ↓
4. CategoryExtractorTool
   - Execute strategy
   - Handle interactions
   - Extract categories
   - Build hierarchy
   ↓
5. DatabaseSaverTool
   - Validate data
   - Save to PostgreSQL
   - Track statistics
   ↓
6. BlueprintGeneratorTool
   - Create JSON template
   - Save for future use
   ↓
7. Output Results
```

See next documents for implementation details.
