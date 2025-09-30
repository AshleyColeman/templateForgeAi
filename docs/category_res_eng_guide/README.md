# AI-Powered Category Extractor: Complete Documentation

## 📋 Table of Contents

This directory contains comprehensive documentation for building an AI-powered category extraction system for e-commerce websites using Python and Strands Agents SDK.

### Documents

1. **[00_Project_Overview.md](./00_Project_Overview.md)**
   - Executive summary
   - Problem statement and vision
   - System advantages over current TypeScript scraper
   - Technology stack
   - Architecture overview
   - Success criteria and use cases

2. **[01_Technical_Specification.md](./01_Technical_Specification.md)**
   - System architecture diagrams
   - Core component specifications
   - CategoryExtractionAgent class
   - PageAnalyzerTool implementation
   - CategoryExtractorTool implementation
   - DatabaseSaverTool implementation

3. **[02_Architecture_Design.md](./02_Architecture_Design.md)**
   - Complete project structure
   - Configuration management
   - Error handling strategy
   - Dependencies (pyproject.toml)
   - Workflow diagrams

4. **[03_Implementation_Guide.md](./03_Implementation_Guide.md)**
   - Step-by-step setup instructions
   - Environment configuration
   - Ollama/OpenAI/Anthropic setup
   - Core module implementation
   - CLI interface creation
   - First extraction walkthrough

5. **[04_Testing_Strategy.md](./04_Testing_Strategy.md)**
   - Testing pyramid
   - Unit tests
   - Integration tests
   - End-to-end tests
   - Performance testing
   - CI/CD configuration
   - Test coverage goals

6. **[05_Blueprint_Schema.md](./05_Blueprint_Schema.md)**
   - Blueprint purpose and structure
   - Complete JSON schema
   - Field descriptions
   - Example blueprints
   - Using blueprints for extraction
   - Validation and versioning

7. **[06_FAQ_and_Troubleshooting.md](./06_FAQ_and_Troubleshooting.md)**
   - Frequently asked questions
   - Common issues and solutions
   - Debugging tips
   - Performance optimization
   - Best practices

8. **[07_Prompt_Engineering_Guide.md](./07_Prompt_Engineering_Guide.md)**
   - Prompt design principles
   - Vision API prompts for screenshot analysis
   - HTML analysis prompts
   - Validation and blueprint prompts
   - Few-shot learning examples
   - Prompt optimization techniques

9. **[08_Real_World_Examples.md](./08_Real_World_Examples.md)**
   - Case study: Clicks.co.za (complex sidebar)
   - Case study: Wellness Warehouse (simple grid)
   - Case study: Faithful to Nature (hover menu)
   - Case study: Dis-Chem (mega menu)
   - Comparison and lessons learned
   - Blueprint reuse examples

10. **[09_Cost_Analysis_and_ROI.md](./09_Cost_Analysis_and_ROI.md)**
    - Detailed cost breakdown (LLM, infrastructure, development)
    - ROI comparison vs TypeScript approach
    - Cost optimization strategies
    - Total cost of ownership (5-year analysis)
    - Financial recommendations

11. **[10_Quick_Reference.md](./10_Quick_Reference.md)**
    - One-page cheat sheet
    - Common commands and patterns
    - Quick troubleshooting
    - Code snippets
    - Database queries
    - Performance tips

12. **[11_Migration_Strategy.md](./11_Migration_Strategy.md)**
    - Phased migration plan (TypeScript → Python)
    - Parallel operation strategy
    - Validation and rollback procedures
    - Communication plan
    - Success metrics
    - Post-migration monitoring

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL database
- LLM Provider: Ollama (free, local) OR OpenAI API key OR Anthropic API key
- Poetry for dependency management

### Installation

```bash
# Clone repository
cd /home/ashleycoleman/Projects/product_scraper

# Create project structure
mkdir -p src/ai_agents/category_extractor/{tools,utils,blueprints}

# Install dependencies
poetry add strands-agents playwright asyncpg pydantic click rich loguru openai anthropic httpx

# Install Playwright browsers
poetry run playwright install chromium

# Configure environment
cp .env.example .env
# Edit .env with your credentials
```

### First Extraction

```bash
# Set environment variables
export OPENAI_API_KEY (if using OpenAI)=your_key
export ANTHROPIC_API_KEY (if using Anthropic)=your_secret
export DB_PASSWORD=your_password

# Run extraction
python -m src.ai_agents.category_extractor.cli \
    --url https://example.com \
    --retailer-id 1
```

## 📊 How It Works

```
1. User provides URL and retailer ID
   ↓
2. Agent initializes Playwright browser
   ↓
3. PageAnalyzerTool captures screenshot and HTML
   ↓
4. LLM (Claude Vision) analyzes page structure
   ↓
5. Agent generates extraction strategy
   ↓
6. CategoryExtractorTool executes strategy
   ↓
7. Categories extracted with hierarchy
   ↓
8. Data validated and saved to PostgreSQL
   ↓
9. Blueprint generated for future use
   ↓
10. Results and statistics returned
```

## 🎯 Key Features

- **Automatic Discovery**: No manual selector configuration required
- **Visual Understanding**: Uses Claude Vision API to analyze pages
- **Adaptive**: Handles different navigation patterns (hover, sidebar, dropdown, etc.)
- **Blueprint Generation**: Creates reusable templates for fast extraction
- **Error Handling**: Manages bot detection, popups, dynamic loading
- **Database Integration**: Saves to existing PostgreSQL schema
- **Cost Effective**: $0.50-$2 per site extraction

## 🏗️ Architecture

```
CLI Interface
    ↓
CategoryExtractionAgent (Orchestrator)
    ↓
┌───────────────┬──────────────────┬─────────────────┐
│               │                  │                 │
PageAnalyzer   Category          Database        Blueprint
Tool           Extractor         Saver           Generator
               Tool              Tool            Tool
```

## 💾 Database Schema

Uses existing `categories` table:

```sql
CREATE TABLE categories (
    id serial4 PRIMARY KEY,
    name text NOT NULL,
    url text NULL,
    parent_id int4 NULL,
    retailer_id int4 NOT NULL,
    depth int4 NULL,
    enabled bool DEFAULT false,
    created_at timestamptz DEFAULT CURRENT_TIMESTAMP
);
```

## 🧪 Testing

```bash
# Run all tests
poetry run pytest

# Run specific test category
poetry run pytest -m unit
poetry run pytest -m integration
poetry run pytest -m e2e

# With coverage
poetry run pytest --cov
```

## 📈 Comparison with TypeScript Scraper

| Aspect | TypeScript (Current) | Python AI Agent (New) |
|--------|---------------------|----------------------|
| Setup Time | 2-4 hours | 5-10 minutes |
| Configuration | Manual CSS selectors | Automatic discovery |
| Adaptability | Breaks on changes | Self-healing |
| Scalability | Linear | Exponential |
| Cost | Developer time | ~$1-2 per site |
| Maintenance | High | Low |

## 🔧 Configuration

Key settings in `.env`:

```bash
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=product_scraper
DB_USER=postgres
DB_PASSWORD=your_password

# Ollama/OpenAI/Anthropic
LLM_PROVIDER=ollama
OPENAI_API_KEY (if using OpenAI)=your_key
ANTHROPIC_API_KEY (if using Anthropic)=your_secret

# Model
MODEL_ID=gemma3:1b (Ollama) or gpt-4o-mini (OpenAI)

# Browser
BROWSER_HEADLESS=true
BROWSER_TIMEOUT=60000
```

## 🎓 Learning Path

### For Beginners
1. Read **00_Project_Overview.md** for context
2. Review **03_Implementation_Guide.md** for setup
3. Run first extraction with example code
4. Check **06_FAQ_and_Troubleshooting.md** for issues

### For Developers
1. Study **01_Technical_Specification.md** for architecture
2. Review **02_Architecture_Design.md** for components
3. Implement tools following the specifications
4. Add tests from **04_Testing_Strategy.md**

### For DevOps
1. Review **03_Implementation_Guide.md** for deployment
2. Set up CI/CD from **04_Testing_Strategy.md**
3. Monitor costs via AWS Cost Explorer
4. Configure alerts and logging

## 🚨 Common Issues

| Issue | Solution |
|-------|----------|
| LLM Provider Error | Check Ollama running or API key valid |
| Database Connection Failed | Verify PostgreSQL running and credentials |
| Browser Not Found | Run `playwright install chromium` |
| Bot Detection | Increase timeout, use stealth mode |
| No Categories Found | Run in non-headless mode to debug |

See **06_FAQ_and_Troubleshooting.md** for detailed solutions.

## 📚 Additional Resources

- **Strands Agents**: https://strandsagents.com/latest/
- **Playwright Python**: https://playwright.dev/python/
- **Claude API**: https://docs.anthropic.com/claude/
- **Ollama**: https://ollama.com/
- **OpenAI**: https://platform.openai.com/docs
- **Anthropic**: https://docs.anthropic.com/

## 🤝 Contributing

When extending this system:

1. Follow the existing architecture patterns
2. Add tests for new features
3. Update blueprints when changing extraction logic
4. Document new edge cases
5. Update this README with new sections

## 📝 License

See main project LICENSE file.

## 💬 Support

For questions or issues:

1. Check **06_FAQ_and_Troubleshooting.md**
2. Review relevant documentation sections
3. Search existing issues
4. Create new issue with details

## 🎯 Next Steps

After reviewing this documentation:

1. Set up your development environment
2. Configure Ollama/OpenAI/Anthropic access
3. Run your first extraction
4. Generate a blueprint
5. Test with multiple retailers
6. Deploy to production

**Start with**: [00_Project_Overview.md](./00_Project_Overview.md)

---

**Last Updated**: 2025-09-30

**Version**: 1.0

**Maintainer**: Ashley Coleman
