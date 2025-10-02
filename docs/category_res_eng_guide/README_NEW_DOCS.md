# New Documentation Guide

## Overview

This directory contains comprehensive documentation for the AI-Powered Web Scraping System. This system uses AI agents to automatically extract data from e-commerce websites without manual configuration.

## Documentation Structure

### 📘 Getting Started

1. **[SYSTEM_OVERVIEW.md](./SYSTEM_OVERVIEW.md)** - **START HERE**
   - High-level explanation of what the system is
   - How it works in simple terms
   - Key advantages and use cases
   - Technology stack overview

### 📗 Core System Documentation

2. **[00_Project_Overview.md](./00_Project_Overview.md)**
   - Detailed project overview
   - Problem statement and vision
   - Success criteria and phases

3. **[01_Technical_Specification.md](./01_Technical_Specification.md)**
   - Technical architecture
   - Component specifications
   - Tool implementations

4. **[02_Architecture_Design.md](./02_Architecture_Design.md)**
   - Project structure
   - Configuration management
   - Dependencies and integrations

5. **[03_Implementation_Guide.md](./03_Implementation_Guide.md)**
   - Step-by-step setup instructions
   - Environment configuration
   - First extraction walkthrough

### 📙 Extensibility Guides

6. **[AGENT_FRAMEWORK_GUIDE.md](./AGENT_FRAMEWORK_GUIDE.md)** - **IMPORTANT**
   - Understanding the agent pattern
   - How to create custom agents
   - Tool development guide
   - Best practices

7. **[PRODUCT_EXTRACTOR_GUIDE.md](./PRODUCT_EXTRACTOR_GUIDE.md)** - **COMPLETE EXAMPLE**
   - Full implementation of a Product Extractor Agent
   - Database schema for products
   - All tools (analyzer, extractor, pagination)
   - CLI interface and usage examples
   - **Use this as a template for new agents**

8. **[MULTI_AGENT_ORCHESTRATION.md](./MULTI_AGENT_ORCHESTRATION.md)**
   - Coordinating multiple agents
   - Master orchestrator pattern
   - Running agents in parallel
   - Complete retailer extraction workflow

### 📕 Reference Documentation

9. **[05_Blueprint_Schema.md](./05_Blueprint_Schema.md)**
   - Blueprint file format specification
   - Example blueprints
   - Validation rules
   - Using blueprints for fast extraction

10. **[07_Prompt_Engineering_Guide.md](./07_Prompt_Engineering_Guide.md)**
    - System prompts for agents
    - Prompt optimization techniques
    - Examples and best practices

## Quick Navigation

### I want to...

#### **Understand what this system does**
→ Read [SYSTEM_OVERVIEW.md](./SYSTEM_OVERVIEW.md)

#### **Set up the system for the first time**
→ Follow [03_Implementation_Guide.md](./03_Implementation_Guide.md)

#### **Create a new type of scraping agent** (e.g., for products, prices, reviews)
→ Read [AGENT_FRAMEWORK_GUIDE.md](./AGENT_FRAMEWORK_GUIDE.md) then use [PRODUCT_EXTRACTOR_GUIDE.md](./PRODUCT_EXTRACTOR_GUIDE.md) as a template

#### **Scrape products from category pages**
→ Implement from [PRODUCT_EXTRACTOR_GUIDE.md](./PRODUCT_EXTRACTOR_GUIDE.md)

#### **Run multiple agents together** (e.g., categories → products → prices)
→ Follow [MULTI_AGENT_ORCHESTRATION.md](./MULTI_AGENT_ORCHESTRATION.md)

#### **Understand the technical architecture**
→ Read [01_Technical_Specification.md](./01_Technical_Specification.md) and [02_Architecture_Design.md](./02_Architecture_Design.md)

#### **Learn about blueprints**
→ Read [05_Blueprint_Schema.md](./05_Blueprint_Schema.md)

## Key Concepts

### AI Agent
A Python class that uses LLMs (like GPT or Claude) to make decisions about how to scrape a website. Each agent has:
- A **goal** (e.g., "extract all categories")
- **Tools** it can use (browser automation, HTML parsing, data saving)
- **AI brain** that decides which tools to use and when

### Tools
Functions that an agent can call to perform specific actions:
- `analyze_page()` - Understand website structure
- `extract_data()` - Extract specific data
- `save_to_database()` - Persist data
- `generate_blueprint()` - Create reusable template

### Blueprint
A JSON template generated after successful extraction that captures:
- What selectors worked
- What interactions were needed
- How to extract the data

Future extractions can use the blueprint instead of AI (faster, cheaper).

### Orchestrator
A master coordinator that runs multiple agents in sequence or parallel to accomplish complex tasks.

## Example: Building a Product Scraper

Following the documentation:

1. **Read** [AGENT_FRAMEWORK_GUIDE.md](./AGENT_FRAMEWORK_GUIDE.md) to understand the pattern
2. **Study** [PRODUCT_EXTRACTOR_GUIDE.md](./PRODUCT_EXTRACTOR_GUIDE.md) complete implementation
3. **Copy** the product extractor structure to your new agent
4. **Customize** the tools and prompts for your specific use case
5. **Test** your new agent on a sample website
6. **Integrate** with orchestrator if you want multi-agent workflows

## Common Patterns

### Pattern 1: Single Agent Extraction
```bash
# Run category extractor
python -m src.ai_agents.category_extractor.cli \
  --url https://example.com \
  --retailer-id 1
```

### Pattern 2: Sequential Agent Pipeline
```python
# 1. Extract categories
category_result = await category_agent.run()

# 2. For each category, extract products
for category in category_result.categories:
    product_agent = ProductAgent(category.url, category.id)
    await product_agent.run()
```

### Pattern 3: Orchestrated Multi-Agent
```bash
# Run all agents at once (orchestrator handles workflow)
python -m src.ai_agents.orchestrator.cli \
  --retailer-id 5 \
  --url https://example.com \
  --categories \
  --products \
  --prices
```

## Available Agents

### Currently Implemented
- ✅ **CategoryExtractionAgent** - Extracts hierarchical categories
- ✅ Blueprint executor for fast re-extraction

### Documented but Not Yet Implemented
- 📝 **ProductExtractionAgent** - Extracts products (complete guide available)
- 📝 **PriceMonitorAgent** - Tracks price changes
- 📝 **ReviewScraperAgent** - Collects customer reviews
- 📝 **MasterOrchestrator** - Coordinates multiple agents

### Easy to Add (following the pattern)
- 💡 **ImageDownloaderAgent** - Downloads product images
- 💡 **StockCheckerAgent** - Monitors availability
- 💡 **SpecificationExtractorAgent** - Extracts product specs
- 💡 **VariantExtractorAgent** - Handles sizes, colors, etc.

## Technology Requirements

- **Python 3.11+**
- **PostgreSQL** - Data storage
- **Playwright** - Browser automation
- **Strands Agents SDK** - AI agent framework
- **LLM Provider** (choose one):
  - Ollama (free, local)
  - OpenAI (cloud, cheap)
  - Anthropic (cloud, high quality)

## Getting Help

### Documentation Issues
If something is unclear in the docs, please:
1. Check if there's a related document
2. Look for code examples in the guides
3. Review the existing implementation in `src/ai_agents/category_extractor/`

### Implementation Issues
If you're stuck implementing:
1. Start with [PRODUCT_EXTRACTOR_GUIDE.md](./PRODUCT_EXTRACTOR_GUIDE.md) - it's complete
2. Copy the pattern and modify for your needs
3. Test each tool independently before integrating
4. Use the existing category extractor as a reference

### Agent Not Working
If your agent isn't extracting correctly:
1. Run with `--no-headless` to see what's happening
2. Check the logs for errors
3. Test the selectors manually in browser DevTools
4. Simplify the task - start with one page before handling pagination

## Next Steps

### For Beginners
1. Read [SYSTEM_OVERVIEW.md](./SYSTEM_OVERVIEW.md)
2. Follow [03_Implementation_Guide.md](./03_Implementation_Guide.md) setup
3. Run the category extractor on a test site
4. Study the code to understand how it works

### For Developers Adding New Agents
1. Read [AGENT_FRAMEWORK_GUIDE.md](./AGENT_FRAMEWORK_GUIDE.md)
2. Study [PRODUCT_EXTRACTOR_GUIDE.md](./PRODUCT_EXTRACTOR_GUIDE.md)
3. Copy the structure and customize
4. Test thoroughly
5. Add to orchestrator if needed

### For Advanced Users
1. Review [MULTI_AGENT_ORCHESTRATION.md](./MULTI_AGENT_ORCHESTRATION.md)
2. Build custom orchestration workflows
3. Optimize with parallel processing
4. Create domain-specific agents

## Contributing

When adding new agents or features:
1. Follow the established patterns
2. Document your agent thoroughly
3. Include usage examples
4. Add tests
5. Update this README if adding new docs

---

**Questions?** Start with [SYSTEM_OVERVIEW.md](./SYSTEM_OVERVIEW.md) - it explains everything in simple terms!

