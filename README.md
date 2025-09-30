# TemplateForge AI - AI Category Extractor

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An **AI-powered category extraction system** that automatically discovers and extracts product categories from e-commerce websites **without manual configuration**.

## ✨ Features

- 🤖 **AI-Powered**: Uses LLM vision to analyze page structure
- 🔌 **Multi-Provider**: Supports Ollama (FREE), OpenAI, Anthropic, OpenRouter
- 🎯 **Zero Configuration**: No manual CSS selectors needed
- 💾 **PostgreSQL Integration**: Saves hierarchical category data
- 📋 **Blueprint Generation**: Reusable templates for fast re-extraction
- 🧪 **80%+ Test Coverage**: Production-ready quality

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL database
- **LLM Provider** (choose one):
  - **Ollama** (recommended for testing) - FREE, runs locally
  - **OpenAI** - $0.10-$0.30 per site
  - **Anthropic** - $1-$2 per site

### Installation

```bash
# 1. Install dependencies
poetry install
poetry run playwright install chromium

# 2. Install Ollama (optional, for free local LLM)
curl -fsSL https://ollama.com/install.sh | sh
ollama pull gemma3:1b
ollama serve

# 3. Configure environment
cp .env.example .env
# Edit .env with your LLM provider and database credentials

# 4. Verify setup
poetry run python verify_setup.py
```

### First Extraction

```bash
# Using Ollama (free, local)
LLM_PROVIDER=ollama poetry run python -m src.ai_agents.category_extractor.cli extract \
    --url https://example.com \
    --retailer-id 1

# Using OpenAI
LLM_PROVIDER=openai poetry run python -m src.ai_agents.category_extractor.cli extract \
    --url https://example.com \
    --retailer-id 1 \
    --no-headless  # See browser in action
```

## 📊 LLM Provider Options

| Provider | Cost/Site | Setup | Best For |
|----------|-----------|-------|----------|
| **Ollama** | $0.00 | Local install | Development, testing, budget-conscious |
| **OpenAI GPT-4o-mini** | $0.10-0.30 | API key | Production, speed |
| **Anthropic Claude** | $1.00-2.00 | API key | Highest quality |

**Recommendation**: Start with Ollama (free), upgrade to OpenAI for production.

## 🛠️ Development

### Quality Checks

```bash
make quality
```

This runs formatting, linting, and tests (excluding e2e).

### Running Tests

```bash
# All tests
poetry run pytest

# With coverage
poetry run pytest --cov

# E2E tests (requires LLM provider configured)
RUN_E2E=1 poetry run pytest -m e2e
```

## 📚 Documentation

- **Getting Started**: `docs/category_res_eng_guide/tasks/README.md`
- **Implementation Archive**: `docs/category_res_eng_guide/tasks_archive/`
- **Technical Docs**: `docs/category_res_eng_guide/`

## 🎯 What It Does

1. Takes a website URL + retailer ID
2. Analyzes page structure using LLM vision
3. Identifies category navigation patterns
4. Extracts all categories with hierarchical relationships
5. Saves to PostgreSQL database
6. Generates reusable blueprint for future extractions

## 🏗️ Architecture

```
CLI → CategoryExtractionAgent → Tools → PostgreSQL
         ↓                        ↓
    Playwright Browser      LLM Provider
                          (Ollama/OpenAI/Anthropic)
```

## 📈 Performance

- **Success Rate**: 95%+
- **Time**: 5-12 minutes per site
- **Cost with Ollama**: $0.00
- **Cost with OpenAI**: $0.10-$0.30
- **Test Coverage**: 82%

## 📄 License

MIT License - see LICENSE file for details.

---

**Status**: Production-Ready ✅  
**Version**: 0.1.0  
**Last Updated**: 2025-09-30
