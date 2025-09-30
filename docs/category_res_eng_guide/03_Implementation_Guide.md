# AI Category Extractor: Step-by-Step Implementation Guide

## Phase 1: Environment Setup

### Step 1.1: Create Project Structure

```bash
# Navigate to your project root
cd /home/ashleycoleman/Projects/product_scraper

# Create directory structure
mkdir -p src/ai_agents/category_extractor/{tools,utils,blueprints}
mkdir -p tests/test_category_extractor

# Create __init__.py files
touch src/ai_agents/__init__.py
touch src/ai_agents/category_extractor/__init__.py
touch src/ai_agents/category_extractor/tools/__init__.py
touch src/ai_agents/category_extractor/utils/__init__.py
```

### Step 1.2: Install Dependencies

```bash
# Install Poetry if not already installed
curl -sSL https://install.python-poetry.org | python3 -

# Initialize Poetry project
cd src/ai_agents/category_extractor
poetry init

# Add dependencies
poetry add strands-agents
poetry add playwright asyncpg pydantic click rich loguru
poetry add anthropic tenacity beautifulsoup4 lxml

# Add dev dependencies
poetry add --group dev pytest pytest-asyncio black mypy ruff

# Install Playwright browsers
poetry run playwright install chromium
```

### Step 1.3: Configure Environment

Create `.env` file:

```bash
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=product_scraper
DB_USER=postgres
DB_PASSWORD=your_password_here

# Ollama/OpenAI/Anthropic Configuration
LLM_PROVIDER=ollama
OPENAI_API_KEY (if using OpenAI)=sk-your_openai_key
ANTHROPIC_API_KEY (if using Anthropic)=sk-ant-your_anthropic_key

# Model Configuration
MODEL_ID=gemma3:1b (Ollama) or gpt-4o-mini (OpenAI)
MODEL_TEMPERATURE=0.0
MAX_TOKENS=4096

# Browser Configuration
BROWSER_HEADLESS=true
BROWSER_TIMEOUT=60000

# Extraction Configuration
MAX_DEPTH=5
MAX_CATEGORIES=10000

# Blueprint Configuration
BLUEPRINT_DIR=./blueprints

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/category_extractor.log
```

### Step 1.4: LLM Provider Setup

**Option A: Ollama (FREE, Recommended for Testing)**
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull a model
ollama pull gemma3:1b

# Start Ollama server
ollama serve

# Verify
ollama list
```

**Option B: OpenAI (Cloud, Low Cost)**
```bash
# Get API key from: https://platform.openai.com/api-keys
# Add to .env:
# OPENAI_API_KEY=sk-...
```

**Option C: Anthropic (Cloud, High Quality)**
```bash
# Get API key from: https://console.anthropic.com/
# Add to .env:
# ANTHROPIC_API_KEY=sk-ant-...
```

## Phase 2: Core Implementation

### Step 2.1: Create Configuration Module

**File**: `src/ai_agents/category_extractor/config.py`

```python
"""Configuration management."""
from pydantic import BaseSettings, Field
from typing import Optional
import os

class ExtractorConfig(BaseSettings):
    """Configuration for category extractor."""
    
    # Database
    db_host: str = Field(default="localhost", env="DB_HOST")
    db_port: int = Field(default=5432, env="DB_PORT")
    db_name: str = Field(default="product_scraper", env="DB_NAME")
    db_user: str = Field(default="postgres", env="DB_USER")
    db_password: str = Field(default="", env="DB_PASSWORD")
    
    # AWS
    aws_region: str = Field(default="us-east-1", env="AWS_REGION")
    
    # Model
    model_id: str = Field(
        default="gemma3:1b (Ollama) or gpt-4o-mini (OpenAI)",
        env="MODEL_ID"
    )
    model_temperature: float = Field(default=0.0, env="MODEL_TEMPERATURE")
    max_tokens: int = Field(default=4096, env="MAX_TOKENS")
    
    # Browser
    browser_headless: bool = Field(default=True, env="BROWSER_HEADLESS")
    browser_timeout: int = Field(default=60000, env="BROWSER_TIMEOUT")
    
    # Extraction
    max_depth: int = Field(default=5, env="MAX_DEPTH")
    max_categories: int = Field(default=10000, env="MAX_CATEGORIES")
    
    # Blueprints
    blueprint_dir: str = Field(default="./blueprints", env="BLUEPRINT_DIR")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: Optional[str] = Field(default=None, env="LOG_FILE")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Singleton instance
_config: Optional[ExtractorConfig] = None

def get_config() -> ExtractorConfig:
    """Get configuration instance."""
    global _config
    if _config is None:
        _config = ExtractorConfig()
    return _config
```

### Step 2.2: Create Error Classes

**File**: `src/ai_agents/category_extractor/errors.py`

```python
"""Custom exceptions."""

class ExtractorError(Exception):
    """Base exception for all extractor errors."""
    pass

class NavigationError(ExtractorError):
    """Error during page navigation."""
    pass

class AnalysisError(ExtractorError):
    """Error during page analysis."""
    pass

class ExtractionError(ExtractorError):
    """Error during category extraction."""
    pass

class DatabaseError(ExtractorError):
    """Error during database operations."""
    pass

class BotDetectionError(ExtractorError):
    """Bot detection or Cloudflare challenge encountered."""
    pass

class ValidationError(ExtractorError):
    """Data validation error."""
    pass
```

### Step 2.3: Create Logging Utility

**File**: `src/ai_agents/category_extractor/utils/logger.py`

```python
"""Logging configuration."""
from loguru import logger
import sys
from ..config import get_config

def setup_logger():
    """Configure loguru logger."""
    config = get_config()
    
    # Remove default handler
    logger.remove()
    
    # Add console handler
    logger.add(
        sys.stdout,
        level=config.log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        colorize=True
    )
    
    # Add file handler if configured
    if config.log_file:
        logger.add(
            config.log_file,
            level=config.log_level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} - {message}",
            rotation="10 MB",
            retention="30 days"
        )
    
    return logger

# Create global logger instance
log = setup_logger()
```

### Step 2.4: Create Database Manager

**File**: `src/ai_agents/category_extractor/database.py`

```python
"""Database operations for categories."""
import asyncpg
from typing import List, Dict, Any, Optional
from datetime import datetime
from .config import get_config
from .utils.logger import log
from .errors import DatabaseError

class CategoryDatabase:
    """Manages database operations for categories."""
    
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        self.config = get_config()
    
    async def connect(self):
        """Create database connection pool."""
        if self.pool is not None:
            return
        
        try:
            self.pool = await asyncpg.create_pool(
                host=self.config.db_host,
                port=self.config.db_port,
                database=self.config.db_name,
                user=self.config.db_user,
                password=self.config.db_password,
                min_size=2,
                max_size=10,
                command_timeout=60
            )
            log.info("Database connection pool created")
        except Exception as e:
            raise DatabaseError(f"Failed to connect to database: {e}")
    
    async def disconnect(self):
        """Close database connection pool."""
        if self.pool:
            await self.pool.close()
            self.pool = None
            log.info("Database connection pool closed")
    
    async def save_categories(
        self,
        categories: List[Dict[str, Any]],
        retailer_id: int
    ) -> Dict[str, int]:
        """
        Save categories to database with hierarchy.
        
        Returns:
            Statistics dict with saved, updated, skipped, errors counts
        """
        await self.connect()
        
        stats = {"saved": 0, "updated": 0, "skipped": 0, "errors": 0}
        id_map = {}  # Map local IDs to database IDs
        
        # Sort by depth to insert parents first
        sorted_cats = sorted(categories, key=lambda c: c.get("depth", 0))
        
        async with self.pool.acquire() as conn:
            for cat in sorted_cats:
                try:
                    # Resolve parent_id
                    local_parent_id = cat.get("parent_id")
                    db_parent_id = None
                    
                    if local_parent_id is not None:
                        db_parent_id = id_map.get(local_parent_id)
                    
                    # Check if exists
                    existing = await conn.fetchrow(
                        "SELECT id FROM categories WHERE url = $1 AND retailer_id = $2",
                        cat["url"],
                        retailer_id
                    )
                    
                    if existing:
                        # Update
                        await conn.execute(
                            """
                            UPDATE categories
                            SET name = $1, parent_id = $2, depth = $3, enabled = $4
                            WHERE id = $5
                            """,
                            cat["name"],
                            db_parent_id,
                            cat.get("depth", 0),
                            True,
                            existing["id"]
                        )
                        id_map[cat.get("id")] = existing["id"]
                        stats["updated"] += 1
                    else:
                        # Insert
                        result = await conn.fetchrow(
                            """
                            INSERT INTO categories (
                                name, url, parent_id, retailer_id, depth,
                                enabled, created_at
                            )
                            VALUES ($1, $2, $3, $4, $5, $6, $7)
                            RETURNING id
                            """,
                            cat["name"],
                            cat["url"],
                            db_parent_id,
                            retailer_id,
                            cat.get("depth", 0),
                            True,
                            datetime.now()
                        )
                        id_map[cat.get("id")] = result["id"]
                        stats["saved"] += 1
                        
                except Exception as e:
                    log.error(f"Error saving category '{cat.get('name')}': {e}")
                    stats["errors"] += 1
        
        log.info(f"Database save complete: {stats}")
        return stats
    
    async def get_retailer_info(self, retailer_id: int) -> Optional[Dict[str, Any]]:
        """Get retailer information."""
        await self.connect()
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id, name, base_url FROM retailers WHERE id = $1",
                retailer_id
            )
            return dict(row) if row else None
```

### Step 2.5: Create Main Agent Class

**File**: `src/ai_agents/category_extractor/agent.py`

```python
"""Main AI agent for category extraction."""
from strands import Agent
from playwright.async_api import async_playwright, Browser, Page
from typing import Optional, Dict, Any
import asyncio

from .config import get_config
from .database import CategoryDatabase
from .utils.logger import log
from .errors import ExtractorError, NavigationError

class CategoryExtractionAgent:
    """AI-powered agent for extracting product categories."""
    
    def __init__(
        self,
        retailer_id: int,
        site_url: str,
        headless: Optional[bool] = None
    ):
        self.retailer_id = retailer_id
        self.site_url = site_url
        self.config = get_config()
        self.headless = headless if headless is not None else self.config.browser_headless
        
        # Initialize Strands Agent
        # Agent initialization handled by _create_strands_agent()
        # Supports: Ollama, OpenAI, Anthropic, OpenRouter
        self.agent = self._create_strands_agent()
        
        # Browser instances
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        
        # Database
        self.db = CategoryDatabase()
        
        # State
        self.extraction_state: Dict[str, Any] = {
            "stage": "initialized",
            "categories_found": 0,
            "errors": []
        }
        
        # Register tools
        self._register_tools()
    
    def _get_system_prompt(self) -> str:
        """Return agent system prompt."""
        return """
You are an expert web scraping agent for e-commerce category extraction.

Your mission:
1. Analyze website structure to find product categories
2. Identify navigation patterns (hover menus, sidebars, etc.)
3. Extract all categories with hierarchical relationships
4. Generate accurate CSS selectors
5. Create reusable blueprints

Principles:
- Be thorough and methodical
- Verify your findings
- Handle edge cases gracefully
- Document your reasoning
- Prioritize accuracy

Available tools:
- analyze_page: Analyze page structure
- extract_categories: Execute extraction
- save_to_database: Persist to PostgreSQL
- generate_blueprint: Create template
"""
    
    def _register_tools(self):
        """Register custom tools with agent."""
        from .tools.page_analyzer import PageAnalyzerTool
        from .tools.category_extractor import CategoryExtractorTool
        from .tools.blueprint_generator import BlueprintGeneratorTool
        
        self.page_analyzer = PageAnalyzerTool(self)
        self.category_extractor = CategoryExtractorTool(self)
        self.blueprint_generator = BlueprintGeneratorTool(self)
        
        # Register tools (Strands syntax)
        self.agent.add_tool(self.page_analyzer.analyze)
        self.agent.add_tool(self.category_extractor.extract)
        self.agent.add_tool(self.blueprint_generator.generate)
    
    async def initialize_browser(self):
        """Initialize Playwright browser."""
        log.info("Initializing browser...")
        
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-blink-features=AutomationControlled'
            ]
        )
        
        context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            locale='en-US',
            timezone_id='Africa/Johannesburg'
        )
        
        self.page = await context.new_page()
        
        # Stealth mode
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        log.info("Browser initialized")
    
    async def run_extraction(self) -> Dict[str, Any]:
        """Execute full extraction workflow."""
        try:
            await self.initialize_browser()
            
            task_prompt = f"""
Extract all product categories from: {self.site_url}

Workflow:
1. Use analyze_page to understand site structure
2. Use extract_categories to gather all categories
3. Use save_to_database to persist (retailer_id={self.retailer_id})
4. Use generate_blueprint to create template

Provide detailed summary of results.
"""
            
            log.info("Starting agent execution...")
            result = await self.agent.arun(task_prompt)
            
            log.info("Agent execution complete")
            
            return {
                "success": True,
                "result": result,
                "state": self.extraction_state
            }
            
        except Exception as e:
            log.error(f"Extraction failed: {e}")
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
        if self.playwright:
            await self.playwright.stop()
        await self.db.disconnect()
        
        log.info("Cleanup complete")
```

## Phase 3: Tool Implementation

### Step 3.1: Page Analyzer Tool (Simplified)

**File**: `src/ai_agents/category_extractor/tools/page_analyzer.py`

```python
"""Tool for analyzing webpage structure."""
from playwright.async_api import Page
from typing import Dict, Any
import base64
import json
import re
from ..utils.logger import log
from ..errors import AnalysisError

class PageAnalyzerTool:
    """Analyzes webpage to identify categories."""
    
    def __init__(self, agent):
        self.agent = agent
    
    async def analyze(self, url: str) -> Dict[str, Any]:
        """
        Analyze page structure.
        
        Args:
            url: URL to analyze
        
        Returns:
            Analysis with navigation_type, selectors, interactions
        """
        page = self.agent.page
        
        log.info(f"Analyzing: {url}")
        
        # Navigate
        await page.goto(url, wait_until='networkidle', timeout=60000)
        await page.wait_for_timeout(2000)
        
        # Handle obstacles
        await self._handle_cookie_consent(page)
        
        # Extract HTML structure
        html = await self._get_simplified_html(page)
        
        # Analyze with LLM (simplified - return basic structure)
        analysis = {
            "navigation_type": "hover_menu",
            "selectors": {
                "nav_container": "nav",
                "top_level_items": "nav li",
                "category_links": "nav a"
            },
            "interactions": [],
            "confidence": 0.7
        }
        
        log.info(f"Analysis complete: {analysis['navigation_type']}")
        
        self.agent.extraction_state["analysis"] = analysis
        return analysis
    
    async def _handle_cookie_consent(self, page: Page):
        """Handle cookie consent."""
        selectors = [
            'button:has-text("Accept")',
            'button:has-text("I Agree")',
            '#accept-cookies'
        ]
        
        for selector in selectors:
            try:
                btn = await page.wait_for_selector(selector, timeout=2000)
                if btn:
                    await btn.click()
                    await page.wait_for_timeout(1000)
                    return
            except:
                continue
    
    async def _get_simplified_html(self, page: Page) -> str:
        """Extract simplified HTML."""
        html = await page.evaluate("""
            () => {
                const clone = document.body.cloneNode(true);
                clone.querySelectorAll('script, style').forEach(el => el.remove());
                return clone.outerHTML;
            }
        """)
        return html[:5000]
```

## Phase 4: CLI Interface

**File**: `src/ai_agents/category_extractor/cli.py`

```python
"""CLI for category extractor."""
import asyncio
import click
from rich.console import Console
from .agent import CategoryExtractionAgent
from .utils.logger import log

console = Console()

@click.command()
@click.option('--url', required=True, help='Website URL')
@click.option('--retailer-id', required=True, type=int, help='Retailer ID')
@click.option('--headless/--no-headless', default=True, help='Headless browser')
def extract(url: str, retailer_id: int, headless: bool):
    """Extract categories using AI agent."""
    
    console.print(f"\n[bold blue]AI Category Extractor[/bold blue]")
    console.print(f"URL: {url}")
    console.print(f"Retailer: {retailer_id}\n")
    
    result = asyncio.run(_run(url, retailer_id, headless))
    
    if result['success']:
        console.print("[green]✓ Success[/green]")
        console.print(f"Categories: {result['state']['categories_found']}")
    else:
        console.print(f"[red]✗ Failed: {result['error']}[/red]")

async def _run(url: str, retailer_id: int, headless: bool):
    """Execute extraction."""
    agent = CategoryExtractionAgent(retailer_id, url, headless)
    return await agent.run_extraction()

if __name__ == '__main__':
    extract()
```

## Phase 5: Testing

Create basic test:

**File**: `tests/test_category_extractor/test_agent.py`

```python
"""Test agent functionality."""
import pytest
from src.ai_agents.category_extractor.agent import CategoryExtractionAgent

@pytest.mark.asyncio
async def test_agent_initialization():
    """Test agent can be initialized."""
    agent = CategoryExtractionAgent(
        retailer_id=1,
        site_url="https://example.com"
    )
    assert agent.retailer_id == 1
    assert agent.site_url == "https://example.com"

# Add more tests as needed
```

## Phase 6: Run First Extraction

```bash
# Set up environment
export OPENAI_API_KEY (if using OpenAI)=your_key
export ANTHROPIC_API_KEY (if using Anthropic)=your_secret
export DB_PASSWORD=your_db_password

# Run extraction
python -m src.ai_agents.category_extractor.cli \
    --url https://clicks.co.za \
    --retailer-id 1

# Or with Poetry
poetry run python -m src.ai_agents.category_extractor.cli \
    --url https://clicks.co.za \
    --retailer-id 1 \
    --no-headless  # To see browser
```

## Next Steps

1. Implement remaining tools (CategoryExtractorTool, BlueprintGeneratorTool)
2. Add vision API integration for screenshot analysis
3. Enhance error handling and retry logic
4. Add comprehensive tests
5. Create blueprint validation
6. Add monitoring and metrics

See **04_Testing_Strategy.md** for testing approach.
