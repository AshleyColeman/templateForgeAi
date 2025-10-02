# Project Overview: scrape:cp (Category URL Products Scraper)

## Executive Summary

**scrape:cp** is the second stage in the 3-stage product scraping pipeline:

1. **scrape:c** → Discovers category structure
2. **scrape:cp** → **Extracts product URLs from category listing pages** ← THIS DOCUMENT
3. **scrape:p** → Scrapes detailed product information

**Purpose**: Visit each category page and extract all product URLs found on that page, mapping products to categories.

## What scrape:cp Does

### Primary Function
Visits category listing pages (discovered by scrape:c) and extracts product URLs.

**Example**:
- scrape:c found category: "https://clicks.co.za/vitamins"
- scrape:cp visits that URL and extracts:
  - Product 1: https://clicks.co.za/product/vitamin-c-1000mg
  - Product 2: https://clicks.co.za/product/vitamin-d3-500iu
  - Product 3: https://clicks.co.za/product/multivitamin-pack
  - ... (handles pagination to get all products)

### Core Responsibilities

1. **Product URL Extraction**
   - Navigate to each category URL from database
   - Extract product links from listing pages
   - Handle pagination (next button, page numbers)
   - Deduplicate URLs

2. **Product-Category Mapping**
   - Store which products belong to which categories
   - Handle products appearing in multiple categories
   - Track extraction metadata

3. **Data Persistence**
   - Save to `category_url_products` table
   - Link products to categories via `category_id`
   - Prepare URLs for detailed scraping (scrape:p)

## Commands

### Interactive Mode
```bash
npm run scrape:cp
```
Menu-driven interface to select retailers and modes.

### Direct Scraping
```bash
npm run scrape:cp scrape --retailer clicks
npm run scrape:cp scrape --retailer dischem
npm run scrape:cp scrape --retailer faithful-to-nature
npm run scrape:cp scrape --retailer wellnesswarehouse
```

### Operational Modes

| Mode | Command | Description |
|------|---------|-------------|
| **Enhanced** | `npm run scrape:cp:enhanced` | Multi-threaded with database queue |
| **Legacy** | `npm run scrape:cp` | Single-threaded with checkpoints |
| **Queue** | `npm run scrape:cp:queue` | Single process, database queue |

### Convenience Commands
```bash
npm run scrape:cp:clicks       # Scrape Clicks products
npm run scrape:cp:dischem      # Scrape Dis-Chem products
npm run scrape:cp:faithful     # Scrape Faithful to Nature products
npm run scrape:cp:wellness     # Scrape Wellness Warehouse products
```

## Supported Retailers

| Retailer | ID | Base URL |
|----------|-----|----------|
| Clicks | clicks | https://clicks.co.za |
| Dis-Chem | dischem | https://www.dischem.co.za |
| Faithful to Nature | faithful-to-nature | https://www.faithful-to-nature.co.za |
| Wellness Warehouse | wellnesswarehouse | https://www.wellnesswarehouse.com |

## Technology Stack

- **Runtime**: Node.js 20+, TypeScript, tsx
- **Browser Automation**: Puppeteer 24.7.2 with stealth plugin
- **Database**: PostgreSQL via Prisma ORM
- **CLI**: Commander.js, Inquirer.js
- **Logging**: Winston (centralized to `logs/category_url_products.log`)

## Entry Point

**File**: `src/scrappers/category_url_products/cli.ts`

Defined in `package.json`:
```json
{
  "scripts": {
    "scrape:cp": "tsx src/scrappers/category_url_products/cli.ts"
  }
}
```

## Workflow

```
1. User runs: npm run scrape:cp scrape --retailer clicks
2. CLI loads Clicks configuration
3. Fetches categories from database (from scrape:c)
4. For each category:
   a. Navigate to category URL
   b. Extract product links from page
   c. Handle pagination (next button)
   d. Save product URLs to database
5. Complete: Product URLs ready for scrape:p
```

## Data Flow

```
scrape:c (categories)
    ↓
  Database: categories table
    ↓
scrape:cp (reads categories, extracts product URLs)
    ↓
  Database: category_url_products table
    ↓
scrape:p (reads product URLs, extracts details)
```

## Key Features

### Pagination Handling
- **Next Button**: Clicks "Next" until no more pages
- **Page Numbers**: Extracts all page links (1, 2, 3...)
- **Infinite Scroll**: (if implemented by retailer)

### Anti-Bot Measures
- Puppeteer stealth plugin
- Cloudflare challenge detection
- Rate limiting with delays
- User-agent rotation

### Fault Tolerance
- Checkpoint system (Legacy mode)
- Database queue with retry (Enhanced/Queue modes)
- Graceful shutdown (SIGINT/SIGTERM)
- Error logging

## Operating Modes Comparison

| Feature | Legacy | Enhanced | Queue |
|---------|--------|----------|-------|
| Concurrency | Single-threaded | Multi-worker | Single process |
| State | JSON checkpoints | Database queue | Database queue |
| Speed | Slow | Fast (3-4x) | Medium (2x) |
| Resume | Yes (checkpoint) | Yes (queue) | Yes (queue) |
| Memory | ~300 MB | ~1-3 GB | ~500 MB |
| Best For | Debugging | Production | Balanced |

## Configuration

### Global Config
Location: `config/concurrency.json`

Per-retailer settings:
- Max workers
- Request delays
- Retry attempts
- Timeouts

### Retailer-Specific Config
Location: `src/scrappers/category_url_products/config/<retailer>/`

Contains:
- Product link selectors (CSS/XPath)
- Pagination selectors
- Container elements
- Anti-bot settings

## Database Schema

### Main Table: `category_url_products`
```sql
CREATE TABLE category_url_products (
  id SERIAL PRIMARY KEY,
  url TEXT NOT NULL,
  category_id INTEGER REFERENCES categories(id),
  product_id INTEGER REFERENCES products(id),
  extraction_date TIMESTAMP DEFAULT NOW(),
  page_number INTEGER,
  position_in_page INTEGER
);
```

**Key Relationships**:
- Links to `categories` (from scrape:c)
- Links to `products` (for scrape:p)
- Many-to-many: Products can be in multiple categories

## Logging

**File**: `logs/category_url_products.log`

**Centralized Logger**: `categoryUrlProductsLogger`

**Log Levels**:
- ERROR: Critical failures
- WARN: Unexpected conditions
- INFO: Standard progress
- DEBUG: Detailed troubleshooting

**Note**: Currently has 150+ console.log statements that need replacement with proper logger (see 04_Critical_Warnings_&_Red_Flags.md).

## Known Issues

### Critical
1. **150+ console.log statements** - Not captured in log files
2. **No sequential scraping mode** - Cannot automate "scrape all retailers"
3. **Two worker implementations** - Confusion between worker.ts and cli-worker.ts

### High Priority
4. **Excessive HTML logging** - Logs full HTML of products
5. **No centralized logger** - Multiple logger instances
6. **Bot detection logging** - 23 console statements in one file

See `04_Critical_Warnings_&_Red_Flags.md` for complete list and fixes.

## Performance

**Approximate Duration** (Legacy mode, single retailer):
- Clicks: ~2-4 hours (~10,000 products)
- Dis-Chem: ~1-3 hours (~5,000 products)  
- Faithful to Nature: ~1-2 hours (~3,000 products)
- Wellness Warehouse: ~1-2 hours (~3,000 products)

**Enhanced Mode**: 2-4 hours for all retailers (parallel)

## Next Steps

To understand the system in detail, see:

- **01_Technical_Specification.md**: Module structure and code organization
- **02_Code_Analysis_&_Bugs.md**: Known issues and testing strategies
- **03_Ownership_&_Maintenance_Checklist.md**: Operational procedures
- **04_Critical_Warnings_&_Red_Flags.md**: Priority issues to fix
- **05_Sequential_Scraping_Guide.md**: How to automate sequential execution
- **06_Dead_Code_&_Optimization_Opportunities.md**: Performance improvements
- **07_Immediate_Action_Plan.md**: 7-day sprint to production ready

## Quick Start

```bash
# 1. Ensure scrape:c has run first (need categories in database)
npm run scrape:c scrape --retailer clicks

# 2. Run category URL products scraper
npm run scrape:cp scrape --retailer clicks

# 3. Monitor progress
tail -f logs/category_url_products.log

# 4. Check results
psql -d product_scraper -c "SELECT COUNT(*) FROM category_url_products WHERE category_id IN (SELECT id FROM categories WHERE retailer_id = 1);"
```

## Summary

**scrape:cp** is the bridge between category discovery (scrape:c) and product detail extraction (scrape:p). It maps products to categories by visiting category listing pages and extracting product URLs. The extracted URLs are stored in the database and used by scrape:p for detailed product information extraction.
