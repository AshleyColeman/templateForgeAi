# AI-Powered Category Extractor: Project Overview

## Executive Summary

This project aims to build an **AI-powered Python agent** that can automatically discover, analyze, and extract product categories from e-commerce websites **without manual configuration**. Unlike the current TypeScript scraper which requires hand-coded CSS selectors for each retailer, this AI agent will:

1. **Automatically analyze** any given website's structure
2. **Identify category elements** using visual and semantic understanding
3. **Extract hierarchical category relationships** 
4. **Generate reusable templates/blueprints** for future scraping
5. **Adapt to website changes** without code modifications

## Problem Statement

### Current State (TypeScript Scraper)
The existing `category_scraper` system has several limitations:

- **Manual Configuration Required**: Each retailer needs a hand-coded configuration file with specific CSS selectors
- **Brittle**: Website changes break the scraper, requiring developer intervention
- **Time-Consuming**: Adding a new retailer takes hours of HTML inspection and testing
- **Maintenance Overhead**: Each site update may require selector updates
- **Not Scalable**: Adding 100 new retailers would require 100 manual configurations

**Example of Manual Configuration** (`clicks.ts`):
```typescript
export const clicksCategorySelectors: CategorySelectors = {
  MAIN_NAV_TOP_LEVEL_LINK_PATTERN: "a.refinementToggle[title='Hide Refinement']",
  MAIN_NAV_FLYOUT_PANEL_SELECTOR: "div.panel.panel-default.bg-white",
  CATEGORY_ITEM: "li",
  CATEGORY_NAME_TEXT: 'span[id^="facetName_"]',
  // ... 15+ more selectors
};
```

### Desired State (AI Agent)
The AI-powered agent should:

1. **Accept a URL** as input (e.g., `https://newretailer.com`)
2. **Autonomously discover** where categories are located
3. **Extract all categories** and their relationships
4. **Store results** in the PostgreSQL database
5. **Generate a template** for future efficient scraping

## Vision: How It Should Work

### User Flow
```bash
# Simple CLI command
python scrape_categories.py --url https://newretailer.com --retailer-id 5

# The agent:
# 1. Opens the website with Puppeteer/Playwright
# 2. Uses GPT-4/Claude to analyze the page structure
# 3. Identifies navigation menus, category links, etc.
# 4. Extracts all categories and saves to database
# 5. Generates a JSON blueprint for future use
```

### Expected Output

**Console Output:**
```
[AI Agent] Opening https://newretailer.com...
[AI Agent] Analyzing page structure with Claude...
[AI Agent] Detected navigation menu at: nav.main-menu
[AI Agent] Found 12 top-level categories
[AI Agent] Extracting category hierarchy...
[AI Agent] Discovered 156 total categories (depth: 3)
[AI Agent] Saving to database...
[AI Agent] Categories saved successfully
[AI Agent] Generating blueprint...
[AI Agent] Blueprint saved to: blueprints/newretailer_com.json
```

**Blueprint Output** (`newretailer_com.json`):
```json
{
  "site_url": "https://newretailer.com",
  "retailer_id": 5,
  "analyzed_at": "2025-09-30T19:10:00Z",
  "category_structure": {
    "type": "hover_menu",
    "navigation_selector": "nav.main-menu",
    "top_level_items": "li.menu-item",
    "category_link": "a.category-link",
    "flyout_panel": "div.submenu",
    "subcategory_list": "ul.subcategories"
  },
  "extraction_strategy": "hover_and_extract",
  "categories_found": 156,
  "max_depth": 3,
  "confidence_score": 0.92
}
```

## Key Advantages Over Current System

| Aspect | Current (TypeScript) | AI Agent (Python) |
|--------|---------------------|-------------------|
| **Setup Time** | 2-4 hours per site | ~5 minutes per site |
| **Configuration** | Manual CSS selectors | Automatic discovery |
| **Adaptability** | Breaks on site changes | Self-healing |
| **Scalability** | Linear (1 dev per site) | Exponential (agent scales) |
| **Maintenance** | High (constant updates) | Low (agent adapts) |
| **Learning** | No learning | Improves over time |
| **Blueprint Generation** | Manual documentation | Automatic templates |

## Technology Stack

### Core Technologies

**Runtime & Language:**
- **Python 3.11+**: Modern Python with type hints
- **Strands Agents SDK**: AI agent framework (Amazon Bedrock backend)

**Web Automation:**
- **Playwright for Python**: Modern browser automation (preferred over Puppeteer)
- **BeautifulSoup4**: HTML parsing for static content
- **lxml**: Fast XML/HTML processing

**AI/LLM:**
- **Amazon Bedrock**: Claude 4 Sonnet (via Strands)
- **Anthropic Claude**: Vision capabilities for page analysis
- **OpenAI GPT-4 Vision**: Alternative for visual understanding

**Data Persistence:**
- **PostgreSQL**: Existing database (via psycopg3)
- **SQLAlchemy**: ORM for database operations
- **Prisma Client Python**: Alternative ORM option

**Utilities:**
- **Pydantic**: Data validation and settings management
- **loguru**: Enhanced logging
- **tenacity**: Retry logic
- **rich**: Beautiful CLI output

### Development Tools
- **Poetry**: Dependency management
- **pytest**: Testing framework
- **black**: Code formatting
- **mypy**: Type checking
- **ruff**: Fast linting

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      USER INPUT                                  │
│        python scrape_categories.py --url <site>                  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   AI AGENT ORCHESTRATOR                          │
│              (Strands Agent Framework)                           │
│                                                                  │
│  • Initialize Playwright browser                                │
│  • Load agent configuration                                     │
│  • Create agent tools and context                               │
└────────────────────────┬────────────────────────────────────────┘
                         │
            ┌────────────┼────────────┐
            │            │            │
            ▼            ▼            ▼
    ┌───────────┐  ┌──────────┐  ┌──────────────┐
    │ PAGE      │  │ AI       │  │ EXTRACTION   │
    │ ANALYZER  │  │ REASONING│  │ EXECUTOR     │
    │ TOOL      │  │ ENGINE   │  │ TOOL         │
    └─────┬─────┘  └────┬─────┘  └──────┬───────┘
          │             │                │
          └─────────────┼────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                   WORKFLOW STAGES                                │
│                                                                  │
│  STAGE 1: PAGE ANALYSIS                                         │
│  • Screenshot capture                                            │
│  • HTML structure extraction                                    │
│  • LLM analyzes page layout                                     │
│  • Identifies navigation patterns                               │
│                                                                  │
│  STAGE 2: CATEGORY DISCOVERY                                    │
│  • LLM generates extraction strategy                            │
│  • Execute browser interactions (hover, click)                  │
│  • Extract category elements                                    │
│  • Build category hierarchy                                     │
│                                                                  │
│  STAGE 3: DATA VALIDATION                                       │
│  • Validate extracted data                                      │
│  • Check for duplicates                                         │
│  • Verify parent-child relationships                            │
│                                                                  │
│  STAGE 4: PERSISTENCE                                           │
│  • Save categories to PostgreSQL                                │
│  • Update retailer metadata                                     │
│  • Generate blueprint JSON                                      │
│                                                                  │
│  STAGE 5: BLUEPRINT GENERATION                                  │
│  • Create reusable template                                     │
│  • Document extraction strategy                                 │
│  • Save for future fast extraction                              │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   OUTPUT                                         │
│                                                                  │
│  • PostgreSQL Database: categories table populated              │
│  • Blueprint File: JSON extraction template                     │
│  • Logs: Detailed execution logs                                │
│  • Statistics: Categories found, depth, confidence              │
└─────────────────────────────────────────────────────────────────┘
```

## How the AI Agent Works

### Phase 1: Initial Page Analysis

**Goal**: Understand the website's structure and identify where categories are located.

**Process**:
1. **Navigate** to the target URL
2. **Capture** a full-page screenshot
3. **Extract** the HTML structure (cleaned, minified)
4. **Send to LLM** with prompt:
   ```
   You are a web scraping expert. Analyze this e-commerce website and:
   1. Identify where product categories are located
   2. Describe the navigation pattern (hover menu, sidebar, etc.)
   3. Suggest CSS selectors for category elements
   4. Identify any dynamic elements (flyouts, lazy loading)
   ```

**LLM Response Example**:
```json
{
  "navigation_type": "hover_menu",
  "category_location": "Main navigation bar at top",
  "selectors": {
    "nav_container": "nav.navbar-primary",
    "top_level_items": "li.nav-item",
    "category_links": "a.nav-link",
    "flyout_trigger": "hover",
    "submenu": "div.dropdown-menu"
  },
  "interaction_required": true,
  "confidence": 0.88
}
```

### Phase 2: Category Extraction

**Goal**: Execute the extraction strategy and gather all categories.

**Process**:
1. **Use LLM-generated selectors** to find category elements
2. **Execute interactions** (hover, click) as needed
3. **Extract** category names, URLs, hierarchy
4. **Handle pagination** or "Show More" buttons
5. **Recursively process** subcategories

**Pseudo-code**:
```python
async def extract_categories(page, strategy):
    categories = []
    
    # Find top-level items
    nav_items = await page.query_selector_all(strategy.selectors.top_level_items)
    
    for item in nav_items:
        # Hover to reveal submenu
        if strategy.interaction_required:
            await item.hover()
            await page.wait_for_selector(strategy.selectors.submenu)
        
        # Extract category info
        name = await item.text_content()
        url = await item.get_attribute('href')
        
        # Extract subcategories
        subcategories = await extract_subcategories(page, item, strategy)
        
        categories.append({
            'name': name,
            'url': url,
            'children': subcategories
        })
    
    return categories
```

### Phase 3: Blueprint Generation

**Goal**: Create a reusable template for future fast extraction.

**Output**: A JSON file that can be used for non-AI extraction:
```json
{
  "version": "1.0",
  "site_url": "https://example.com",
  "extraction_method": "hover_menu",
  "selectors": {
    "navigation": "nav.main-menu",
    "top_level": "li.menu-item > a",
    "flyout": "div.submenu",
    "subcategories": "ul.subcategories > li > a"
  },
  "interactions": [
    {"type": "hover", "target": "top_level"},
    {"type": "wait", "selector": "flyout", "timeout": 2000},
    {"type": "extract", "target": "subcategories"}
  ]
}
```

## Database Integration

The agent will use the existing PostgreSQL schema:

```sql
-- Existing categories table
CREATE TABLE public.categories (
    id serial4 PRIMARY KEY,
    name text NOT NULL,
    parent_id int4 NULL,
    url text NULL,
    retailer_id int4 NOT NULL,
    depth int4 NULL,
    enabled bool DEFAULT false NOT NULL,
    created_at timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL,
    -- ... additional fields
    CONSTRAINT categories_unique_retailer_name_parent 
        UNIQUE (retailer_id, name, parent_id)
);
```

**Insertion Strategy**:
- Start with root categories (depth=0, parent_id=NULL)
- Recursively insert children, maintaining parent_id references
- Use UPSERT logic to handle duplicates
- Track extraction metadata in `extraction_state` JSON field

## Success Criteria

The AI agent project will be considered successful when:

1. **Automation**: Can extract categories from a new site with zero manual configuration
2. **Accuracy**: Achieves >95% accuracy in category extraction vs manual review
3. **Completeness**: Finds all categories including nested ones (up to depth 5)
4. **Speed**: Completes extraction in <10 minutes for sites with <500 categories
5. **Reliability**: Success rate >90% across diverse e-commerce platforms
6. **Blueprint Quality**: Generated blueprints work for subsequent fast extractions
7. **Cost Efficiency**: LLM costs <$1 per site extraction

## Use Cases

### Use Case 1: New Retailer Onboarding
**Scenario**: Adding a new South African retailer to the system

**Current Flow** (TypeScript):
1. Developer inspects website HTML (30 min)
2. Write configuration file with selectors (1 hour)
3. Test and debug (1-2 hours)
4. Total: 2.5-3.5 hours

**AI Agent Flow**:
1. Run command: `python scrape_categories.py --url https://newsite.com --retailer-id 5`
2. Agent analyzes and extracts (5-10 min)
3. Review extracted data (5 min)
4. Total: 10-15 minutes

**Time Saved**: ~3 hours per retailer

### Use Case 2: Website Redesign Handling
**Scenario**: Existing retailer changes their website design

**Current Flow** (TypeScript):
1. Scraper starts failing
2. Developer investigates broken selectors (30 min)
3. Update configuration file (30 min)
4. Test and deploy (30 min)
5. Total: 1.5 hours + downtime

**AI Agent Flow**:
1. Scraper detects failure
2. Agent re-analyzes website (5 min)
3. Updates blueprint automatically
4. Extraction resumes
5. Total: 5 minutes + minimal downtime

### Use Case 3: One-Time Data Collection
**Scenario**: Client wants data from 50 competitor websites

**Current Flow** (TypeScript):
- Not feasible (50 × 3 hours = 150 hours of work)

**AI Agent Flow**:
- Run agent on all 50 sites (50 × 10 min = 8.3 hours automated)
- Manual review of results (10 hours)
- Total: ~18 hours mostly automated

## Project Phases

### Phase 1: Proof of Concept (Week 1-2)
- Set up Python environment with Strands Agents
- Implement basic page analysis tool
- Test LLM integration with Claude
- Extract categories from 1 simple site
- **Deliverable**: Working POC with 1 retailer

### Phase 2: Core Development (Week 3-5)
- Implement full agent workflow
- Add database integration
- Handle complex navigation patterns
- Blueprint generation
- **Deliverable**: Agent working on 3-4 diverse sites

### Phase 3: Testing & Refinement (Week 6-7)
- Test on all existing 4 retailers
- Compare accuracy with TypeScript scraper
- Performance optimization
- Error handling improvements
- **Deliverable**: Production-ready agent

### Phase 4: Documentation & Deployment (Week 8)
- Complete documentation
- CLI tool refinement
- Deployment scripts
- User guide
- **Deliverable**: Deployed system with docs

## Next Steps

To proceed with implementation, review the following documents in order:

1. **01_Technical_Specification.md** - Detailed technical design
2. **02_Architecture_Design.md** - System architecture and components
3. **03_Implementation_Guide.md** - Step-by-step implementation
4. **04_Agent_Tools_Reference.md** - Custom tools for the agent
5. **05_Testing_Strategy.md** - Testing approach and validation
6. **06_Blueprint_Schema.md** - Blueprint file format specification
7. **07_Deployment_Guide.md** - Production deployment instructions

## Questions & Considerations

Before proceeding, consider these key questions:

1. **LLM Costs**: What's the acceptable cost per extraction? (Claude 4: ~$0.50-2 per site)
2. **Accuracy Requirements**: Is 95% accuracy acceptable, or do we need 99%?
3. **Fallback Strategy**: Should we keep TypeScript scraper as fallback for critical retailers?
4. **Human Review**: Should extractions be reviewed before database insertion?
5. **Rate Limiting**: How do we handle sites with aggressive rate limiting?
6. **Authentication**: Do any retailers require login to see categories?
7. **Multi-language**: Do we need to handle non-English sites?

## Resources

- **Strands Agents Documentation**: https://strandsagents.com/latest/
- **Playwright Python**: https://playwright.dev/python/
- **Claude Vision API**: https://docs.anthropic.com/claude/docs/vision
- **Current TypeScript Scraper**: `/src/scrappers/category_scraper/`
- **Database Schema**: See PostgreSQL schema in project root
