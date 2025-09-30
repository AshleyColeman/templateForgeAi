# Task 1: Environment Setup & Project Structure

**Status**: ⬜ Not Started  
**Estimated Time**: 4-6 hours  
**Dependencies**: None  
**Priority**: Critical (blocking all other tasks)

---

## 📋 Objective

Set up the complete development environment, project structure, and dependencies for the AI category extraction system.

## 🎯 Success Criteria

- [ ] Python 3.11+ installed and verified
- [ ] Poetry dependency manager installed
- [ ] Project directory structure created
- [ ] All Python dependencies installed
- [ ] Playwright browsers installed
- [ ] Git repository initialized
- [ ] .env template created
- [ ] Can import project modules

## 📁 Directory Structure to Create

```
/home/ashleycoleman/Projects/product_scraper/
└── src/
    └── ai_agents/
        └── category_extractor/
            ├── __init__.py
            ├── cli.py
            ├── agent.py
            ├── config.py
            ├── database.py
            ├── errors.py
            ├── tools/
            │   ├── __init__.py
            │   ├── page_analyzer.py
            │   ├── category_extractor.py
            │   ├── blueprint_generator.py
            │   └── validators.py
            ├── utils/
            │   ├── __init__.py
            │   ├── logger.py
            │   ├── url_utils.py
            │   └── html_utils.py
            └── blueprints/
                └── .gitkeep

tests/
└── test_category_extractor/
    ├── __init__.py
    ├── conftest.py
    ├── fixtures/
    │   └── mock_categories.json
    ├── test_config.py
    ├── test_database.py
    ├── test_agent.py
    └── test_tools/
        ├── test_page_analyzer.py
        ├── test_category_extractor.py
        └── test_blueprint_generator.py

logs/
└── .gitkeep

.env.example
.env (create from example)
.gitignore
pyproject.toml
README.md (AI agent specific)
```

## 🔧 Step-by-Step Implementation

### Step 1: Verify Python Installation

```bash
# Check Python version (must be 3.11+)
python --version
# or
python3 --version

# If not installed or wrong version:
# Ubuntu/Debian:
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip

# macOS (using Homebrew):
brew install python@3.11

# Verify again
python3.11 --version  # Should show 3.11.x
```

**Expected Output**: `Python 3.11.x` or higher

### Step 2: Install Poetry

```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Add to PATH (add to ~/.bashrc or ~/.zshrc)
export PATH="$HOME/.local/bin:$PATH"

# Verify installation
poetry --version

# Configure Poetry to create virtual env in project
poetry config virtualenvs.in-project true
```

**Expected Output**: `Poetry (version 1.7.0 or higher)`

### Step 3: Navigate to Project Root

```bash
cd /home/ashleycoleman/Projects/product_scraper
```

### Step 4: Initialize Poetry Project

```bash
# Initialize Poetry (if not already done)
poetry init --name "ai-category-extractor" \
    --description "AI-powered category extraction for e-commerce sites" \
    --author "Ashley Coleman" \
    --python "^3.11" \
    --no-interaction
```

This creates `pyproject.toml`

### Step 5: Add Dependencies

```bash
# Core dependencies
poetry add strands-agents@^0.3.0
poetry add playwright@^1.40.0
poetry add asyncpg@^0.29.0
poetry add pydantic@^2.5.0
poetry add pydantic-settings@^2.1.0
poetry add click@^8.1.0
poetry add rich@^13.7.0
poetry add loguru@^0.7.2
poetry add anthropic@^0.8.0
poetry add tenacity@^8.2.0
poetry add beautifulsoup4@^4.12.0
poetry add lxml@^5.0.0
poetry add python-dotenv@^1.0.0
poetry add boto3@^1.34.0

# Development dependencies
poetry add --group dev pytest@^7.4.0
poetry add --group dev pytest-asyncio@^0.23.0
poetry add --group dev pytest-cov@^4.1.0
poetry add --group dev black@^23.12.0
poetry add --group dev mypy@^1.8.0
poetry add --group dev ruff@^0.1.0
poetry add --group dev types-beautifulsoup4
```

### Step 6: Install Playwright Browsers

```bash
# Activate poetry shell
poetry shell

# Install Playwright browsers
poetry run playwright install chromium

# If you need system dependencies (Linux)
poetry run playwright install-deps chromium
```

**Expected Output**: Chromium browser downloaded and installed

### Step 7: Create Directory Structure

```bash
# Create main source directories
mkdir -p src/ai_agents/category_extractor/{tools,utils,blueprints}

# Create test directories
mkdir -p tests/test_category_extractor/{fixtures,test_tools}

# Create logs directory
mkdir -p logs

# Create __init__.py files
touch src/ai_agents/__init__.py
touch src/ai_agents/category_extractor/__init__.py
touch src/ai_agents/category_extractor/tools/__init__.py
touch src/ai_agents/category_extractor/utils/__init__.py
touch tests/__init__.py
touch tests/test_category_extractor/__init__.py
touch tests/test_category_extractor/test_tools/__init__.py

# Create .gitkeep for empty directories
touch src/ai_agents/category_extractor/blueprints/.gitkeep
touch logs/.gitkeep
```

### Step 8: Create .env.example Template

Create `/home/ashleycoleman/Projects/product_scraper/.env.example`:

```bash
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=products
DB_USER=postgres
DB_PASSWORD=your_password_here

# AWS Bedrock Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_aws_key_here
AWS_SECRET_ACCESS_KEY=your_aws_secret_here

# Model Configuration
MODEL_ID=us.anthropic.claude-sonnet-4-20250514-v1:0
MODEL_TEMPERATURE=0.0
MAX_TOKENS=4096

# Browser Configuration
BROWSER_HEADLESS=true
BROWSER_TIMEOUT=60000

# Extraction Configuration
MAX_DEPTH=5
MAX_CATEGORIES=10000

# Blueprint Configuration
BLUEPRINT_DIR=./src/ai_agents/category_extractor/blueprints

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/category_extractor.log
```

### Step 9: Create Actual .env File

```bash
# Copy template
cp .env.example .env

# Edit with your actual credentials
nano .env  # or vim, code, etc.

# IMPORTANT: Add to .gitignore
echo ".env" >> .gitignore
```

### Step 10: Update .gitignore

Create or append to `.gitignore`:

```bash
cat >> .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv/
ENV/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Poetry
poetry.lock

# Environment
.env
.env.local

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Logs
logs/*.log
*.log

# Playwright
.pytest_cache/
test-results/
screenshots/

# OS
.DS_Store
Thumbs.db

# Blueprints (optional - comment out if you want to track them)
# src/ai_agents/category_extractor/blueprints/*.json

# Test coverage
htmlcov/
.coverage
.coverage.*
coverage.xml
*.cover

EOF
```

### Step 11: Initialize Git (if needed)

```bash
# Check if already initialized
git status

# If not initialized:
git init
git add .
git commit -m "Initial project setup for AI category extractor"
```

### Step 12: Create Minimal __init__.py Files

Create `/home/ashleycoleman/Projects/product_scraper/src/ai_agents/__init__.py`:
```python
"""AI agents package."""
```

Create `/home/ashleycoleman/Projects/product_scraper/src/ai_agents/category_extractor/__init__.py`:
```python
"""
AI-powered category extraction for e-commerce websites.

This package provides an autonomous agent that can analyze website structure
and extract product categories without manual configuration.
"""

__version__ = "0.1.0"
__author__ = "Ashley Coleman"

from .agent import CategoryExtractionAgent
from .database import CategoryDatabase
from .config import get_config

__all__ = [
    "CategoryExtractionAgent",
    "CategoryDatabase",
    "get_config",
]
```

### Step 13: Create Minimal README

Create `/home/ashleycoleman/Projects/product_scraper/src/ai_agents/category_extractor/README.md`:

```markdown
# AI Category Extractor

Autonomous AI agent for extracting product categories from e-commerce websites.

## Installation

```bash
poetry install
poetry run playwright install chromium
```

## Configuration

Copy `.env.example` to `.env` and fill in your credentials.

## Usage

```bash
poetry run python -m src.ai_agents.category_extractor.cli extract \
    --url https://example.com \
    --retailer-id 1
```

## Development

See `docs/category_res_eng_guide/tasks/` for implementation tasks.
```

### Step 14: Verify Installation

Create a test script `/home/ashleycoleman/Projects/product_scraper/verify_setup.py`:

```python
"""Verify environment setup."""
import sys

def verify_python_version():
    """Check Python version."""
    version = sys.version_info
    if version.major == 3 and version.minor >= 11:
        print(f"✅ Python version: {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"❌ Python version {version.major}.{version.minor}.{version.micro} is too old (need 3.11+)")
        return False

def verify_imports():
    """Check if critical packages can be imported."""
    packages = [
        ("playwright", "playwright.async_api"),
        ("asyncpg", "asyncpg"),
        ("pydantic", "pydantic"),
        ("click", "click"),
        ("rich", "rich"),
        ("loguru", "loguru"),
        ("anthropic", "anthropic"),
    ]
    
    all_ok = True
    for name, module in packages:
        try:
            __import__(module)
            print(f"✅ {name} installed")
        except ImportError as e:
            print(f"❌ {name} NOT installed: {e}")
            all_ok = False
    
    return all_ok

def verify_directory_structure():
    """Check if directories exist."""
    from pathlib import Path
    
    directories = [
        "src/ai_agents/category_extractor",
        "src/ai_agents/category_extractor/tools",
        "src/ai_agents/category_extractor/utils",
        "src/ai_agents/category_extractor/blueprints",
        "tests/test_category_extractor",
        "logs",
    ]
    
    all_ok = True
    for directory in directories:
        path = Path(directory)
        if path.exists():
            print(f"✅ Directory exists: {directory}")
        else:
            print(f"❌ Directory missing: {directory}")
            all_ok = False
    
    return all_ok

def verify_env_file():
    """Check if .env file exists."""
    from pathlib import Path
    
    env_file = Path(".env")
    if env_file.exists():
        print("✅ .env file exists")
        return True
    else:
        print("⚠️  .env file missing (copy from .env.example)")
        return False

if __name__ == "__main__":
    print("\n🔍 Verifying Environment Setup\n")
    
    results = [
        verify_python_version(),
        verify_imports(),
        verify_directory_structure(),
        verify_env_file(),
    ]
    
    print("\n" + "="*50)
    if all(results):
        print("✅ All checks passed! Environment is ready.")
        sys.exit(0)
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        sys.exit(1)
```

Run verification:
```bash
poetry run python verify_setup.py
```

## ✅ Validation Checklist

Before marking this task complete, verify:

- [ ] Python 3.11+ is installed and active
- [ ] Poetry is installed and working
- [ ] All dependencies installed successfully
- [ ] Playwright chromium browser installed
- [ ] Directory structure matches specification
- [ ] `.env` file created from template
- [ ] `.gitignore` properly configured
- [ ] All `__init__.py` files created
- [ ] `verify_setup.py` runs and all checks pass
- [ ] Can import project modules:
  ```python
  poetry run python -c "from src.ai_agents import category_extractor; print('✅ Import works')"
  ```

## 📝 Deliverables

1. ✅ Working Poetry environment
2. ✅ Complete directory structure
3. ✅ All dependencies installed
4. ✅ `.env` file configured
5. ✅ Git repository initialized
6. ✅ Verification script passes

## 🚨 Common Issues & Solutions

### Issue: Poetry not found after installation
**Solution**:
```bash
export PATH="$HOME/.local/bin:$PATH"
# Add to ~/.bashrc or ~/.zshrc to make permanent
```

### Issue: Python version too old
**Solution**: Install Python 3.11+, then specify it:
```bash
poetry env use python3.11
```

### Issue: Playwright browser install fails
**Solution**: Install system dependencies:
```bash
sudo apt install -y libgbm1 libxkbcommon0 libgtk-3-0 libnss3
poetry run playwright install-deps chromium
```

### Issue: Permission denied creating directories
**Solution**: Check permissions:
```bash
ls -la /home/ashleycoleman/Projects/
chmod -R u+w /home/ashleycoleman/Projects/product_scraper
```

## 📚 Next Steps

Once this task is complete:
1. Mark task as ✅ Complete in MASTER_TASKLIST.md
2. Commit changes to git
3. Proceed to **Task 2: Configuration Management**

## 🎯 Time Tracking

**Estimated**: 4-6 hours  
**Actual**: ___ hours  
**Notes**: ___

---

**Status**: Complete this task before moving to Task 2!
**Last Updated**: 2025-09-30
