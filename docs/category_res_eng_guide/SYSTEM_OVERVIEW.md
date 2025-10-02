# AI-Powered Web Scraping System: High-Level Overview

## What Is This System?

This is an **intelligent web scraping platform** that uses AI agents to automatically extract structured data from e-commerce websites **without manual configuration**. Instead of writing custom code for each website, you simply point the AI agent at a URL, and it figures out how to extract the data on its own.

## The Core Problem It Solves

### Traditional Web Scraping (Manual)
```
Developer inspects website → 
Writes CSS selectors → 
Codes extraction logic → 
Tests and debugs → 
Maintains when site changes
```
**Time per website**: 2-4 hours  
**Maintenance**: High (breaks when sites change)  
**Scalability**: Poor (linear effort per site)

### AI-Powered Scraping (This System)
```
Developer runs command → 
AI analyzes website → 
AI extracts data → 
AI generates reusable template
```
**Time per website**: 5-10 minutes  
**Maintenance**: Low (AI adapts to changes)  
**Scalability**: Excellent (AI scales automatically)

## How It Works in Simple Terms

### 1. **You Tell It What to Scrape**
```bash
python scrape_categories.py --url https://newstore.com --retailer-id 5
```

### 2. **AI Analyzes the Website**
- Opens the website in a browser
- Takes screenshots
- Examines the HTML structure
- Uses GPT/Claude vision to understand the layout
- Identifies where categories (or products, or any data) are located

### 3. **AI Extracts the Data**
- Generates a strategy (hover here, click there, extract this)
- Executes browser interactions
- Extracts all the data with hierarchical relationships
- Validates what it found

### 4. **AI Saves Results**
- Stores data in PostgreSQL database
- Generates a "blueprint" (reusable template)
- Provides statistics and confidence scores

### 5. **Future Extractions Are Fast**
- Next time, uses the blueprint instead of AI
- Falls back to AI if blueprint doesn't work
- Continuously learns and improves

## System Architecture

```
┌──────────────────────────────────────────────────┐
│              USER INTERFACE                       │
│    CLI Commands / API / Web Dashboard             │
└────────────────────┬─────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────┐
│         AI AGENT FRAMEWORK                        │
│  • Category Extractor Agent                       │
│  • Product Extractor Agent (future)               │
│  • Price Scraper Agent (future)                   │
│  • Review Scraper Agent (future)                  │
└────────┬─────────────────┬─────────────┬─────────┘
         │                 │             │
         ▼                 ▼             ▼
  ┌───────────┐    ┌─────────────┐   ┌──────────┐
  │ Browser   │    │ AI/LLM      │   │ Database │
  │ (Playwright)│   │ (GPT/Claude)│   │ (Postgres)│
  └───────────┘    └─────────────┘   └──────────┘
```

## Current Implementation: Category Extractor Agent

The **first agent** we built extracts product categories from e-commerce sites.

### What It Extracts
- Category names (e.g., "Health & Beauty", "Electronics")
- Category URLs
- Hierarchical relationships (parent → child → grandchild)
- Metadata (product counts, depth levels)

### Example Output
```json
{
  "categories": [
    {
      "id": 1,
      "name": "Health & Beauty",
      "url": "https://example.com/health",
      "depth": 0,
      "parent_id": null,
      "children": [
        {
          "id": 2,
          "name": "Skincare",
          "url": "https://example.com/health/skincare",
          "depth": 1,
          "parent_id": 1
        }
      ]
    }
  ],
  "total": 156,
  "max_depth": 3,
  "confidence": 0.92
}
```

## Key Components

### 1. **Agent Orchestrator**
- Main coordinator that manages the entire workflow
- Talks to the LLM to make decisions
- Manages browser automation
- Handles errors and retries

### 2. **Specialized Tools**
Each agent has a set of tools it can use:
- **PageAnalyzerTool**: Analyzes website structure
- **CategoryExtractorTool**: Extracts category data
- **BlueprintGeneratorTool**: Creates reusable templates
- **DatabaseSaverTool**: Persists to database

### 3. **Browser Automation**
- Uses Playwright to control a real browser
- Handles interactions (clicks, hovers, scrolls)
- Manages cookies, popups, bot detection

### 4. **AI/LLM Integration**
- Uses Claude, GPT, or Ollama models
- Vision capabilities for screenshot analysis
- Generates extraction strategies
- Adapts to different site patterns

### 5. **Blueprint System**
- Saves successful extraction strategies as JSON templates
- Enables fast re-extraction without AI costs
- Acts as documentation of site structure

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Language** | Python 3.11+ | Modern, async-capable |
| **AI Framework** | Strands Agents SDK | Agent orchestration |
| **LLM Providers** | Ollama, OpenAI, Anthropic | AI reasoning |
| **Browser** | Playwright | Web automation |
| **Database** | PostgreSQL | Data persistence |
| **Validation** | Pydantic | Data models |
| **Logging** | Loguru | Beautiful logs |
| **CLI** | Click | Command interface |

## Real-World Use Cases

### Use Case 1: Competitor Analysis
**Scenario**: Analyze 50 competitor websites to see what categories they offer

**Traditional Approach**: Not feasible (50 × 3 hours = 150 hours)

**AI Approach**: 
```bash
# Create a list of competitors
for url in competitors.txt; do
  python scrape_categories.py --url $url --retailer-id auto
done
# Total time: ~8 hours automated + 2 hours review
```

### Use Case 2: Website Monitoring
**Scenario**: Monitor when retailers add new categories

**Traditional Approach**: Manual checking or brittle scrapers that break

**AI Approach**:
```bash
# Daily cron job
0 2 * * * python scrape_categories.py --url https://store.com --compare-with-previous
# AI detects changes automatically
```

### Use Case 3: New Retailer Onboarding
**Scenario**: Add a new retailer to your platform

**Traditional Approach**: 2-4 hours of developer time

**AI Approach**:
```bash
python scrape_categories.py --url https://newretailer.com --retailer-id 99
# Done in 10 minutes
```

## What Makes This System Powerful

### 1. **Zero Manual Configuration**
No need to write CSS selectors or extraction rules. The AI figures it out.

### 2. **Self-Healing**
When websites change their layout, the AI adapts automatically.

### 3. **Learning & Improving**
Each extraction generates a blueprint that makes future extractions faster.

### 4. **Scalable**
Can handle hundreds of websites without proportional increase in effort.

### 5. **Flexible**
The agent framework can be extended to scrape anything:
- Product listings
- Prices
- Reviews
- Stock availability
- Images
- Specifications

### 6. **Cost-Effective**
- Uses local LLMs (Ollama) or cheap cloud models (GPT-4o-mini)
- Blueprints reduce AI costs on subsequent runs
- Typical cost: $0.50-2 per new site analysis

## Success Metrics

The system is successful when:
- ✅ **95%+ accuracy** in data extraction
- ✅ **< 10 minutes** per site extraction
- ✅ **90%+ success rate** across diverse sites
- ✅ **< $1 per site** in LLM costs
- ✅ **Zero manual configuration** required

## Extensibility

The beauty of this system is that it's **easily extensible**. The Category Extractor Agent is just the first example. You can create:

- **Product Extractor Agent**: Extract products that belong to categories
- **Price Scraper Agent**: Monitor price changes
- **Review Aggregator Agent**: Collect customer reviews
- **Stock Checker Agent**: Track availability
- **Image Scraper Agent**: Download product images
- **Specification Parser Agent**: Extract technical specs

**All agents follow the same pattern** (see `AGENT_FRAMEWORK_GUIDE.md` for details).

## Current Status

### ✅ Implemented
- Category Extractor Agent (fully functional)
- Blueprint generation and execution
- PostgreSQL database integration
- CLI interface
- Support for Ollama, OpenAI, Anthropic
- Error handling and retry logic
- Comprehensive logging

### 🚧 In Progress
- Vision API integration for better analysis
- Advanced blueprint validation
- Multi-site batch processing
- Web dashboard

### 📋 Planned
- Product Extractor Agent
- Price Monitoring Agent
- Automated blueprint updates
- Machine learning for selector prediction
- Cloud deployment templates

## Getting Started

### Quick Start
```bash
# 1. Set up environment
pip install -r requirements.txt
playwright install chromium

# 2. Configure (set API keys, database)
cp .env.example .env
nano .env

# 3. Run your first extraction
python -m src.ai_agents.category_extractor.cli \
  --url https://example.com \
  --retailer-id 1
```

See `docs/setup/BEGINNERS_GUIDE.md` for detailed setup instructions.

## Learn More

- **[01_Technical_Specification.md](./01_Technical_Specification.md)** - Detailed technical design
- **[02_Architecture_Design.md](./02_Architecture_Design.md)** - System architecture
- **[03_Implementation_Guide.md](./03_Implementation_Guide.md)** - Step-by-step implementation
- **[AGENT_FRAMEWORK_GUIDE.md](./AGENT_FRAMEWORK_GUIDE.md)** - How to create new agents
- **[PRODUCT_EXTRACTOR_GUIDE.md](./PRODUCT_EXTRACTOR_GUIDE.md)** - Example: Building a product scraper

## Summary

This is an **AI-powered web scraping system** that:
1. Uses AI agents to understand website structure
2. Extracts structured data automatically
3. Generates reusable templates for efficiency
4. Scales to hundreds of websites
5. Can be extended to scrape any type of data

**Key Innovation**: Instead of writing code to scrape each website, we teach AI agents how to scrape, and they figure out each website on their own.

---

For questions or contributions, see the main [README.md](../../README.md).

