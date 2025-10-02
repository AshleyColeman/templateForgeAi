# What is `scrape:c`? - Complete Guide

## Overview

`scrape:c` is the **Category Scraper** command - the first and most critical phase of the product scraping pipeline. It discovers and maps the entire category hierarchy of e-commerce websites, saving this structure to a PostgreSQL database for later product scraping.

## Purpose

The category scraper serves three primary functions:

### 1. **Category Discovery**
- Navigate retailer websites to identify all product categories
- Extract category metadata (names, URLs, product counts)
- Map hierarchical relationships (parent-child category structures)

### 2. **Data Persistence**
- Store discovered categories in PostgreSQL (`categories` table)
- Maintain parent-child relationships using adjacency list pattern
- Track processing status for each category

### 3. **Pipeline Foundation**
- Create the foundation for downstream product scraping
- Generate a complete sitemap of product categories
- Enable targeted scraping of specific category branches

---

## What Does `scrape:c` Do?

### High-Level Workflow

```
1. START: User runs npm run scrape:c
   ↓
2. SELECT RETAILER: Choose which retailer to scrape (Clicks, Dis-Chem, etc.)
   ↓
3. LOAD CONFIGURATION: Load retailer-specific config (selectors, timeouts, etc.)
   ↓
4. INITIALIZE BROWSER: Launch Puppeteer with stealth plugins
   ↓
5. NAVIGATE TO START URL: Open retailer's homepage or category page
   ↓
6. EXTRACT ROOT CATEGORIES: Find top-level categories in navigation menu
   ↓
7. ADD TO QUEUE: Place discovered categories in processing queue
   ↓
8. PROCESS QUEUE (Recursive):
   ├─ Fetch next category from queue
   ├─ Navigate to category page
   ├─ Extract subcategories from DOM
   ├─ Save subcategories to database
   ├─ Add subcategories to queue (if depth limit not reached)
   └─ Repeat until queue is empty
   ↓
9. COMPLETE: Generate statistics, close browser, exit
```

### Detailed Step-by-Step Process

#### **Step 1: Initialization**
```bash
npm run scrape:c scrape --retailer clicks
```
- CLI parses command-line arguments using Commander.js
- Validates retailer selection
- Loads retailer-specific configuration from `config/<retailer>.ts`
- Initializes Winston logger (console + file logging)

#### **Step 2: Browser Setup**
- Launches headless Chromium via Puppeteer
- Applies stealth plugins to avoid bot detection
- Sets viewport size (1920x1080 by default)
- Configures custom user agent

#### **Step 3: Root Category Extraction**
- Navigates to the configured `startUrl` or `baseUrl`
- Waits for page load and handles anti-bot challenges (Cloudflare, etc.)
- Interacts with main navigation (hover/click as configured)
- Extracts all top-level categories from the navigation menu
- Saves root categories to database with `depth: 0`

#### **Step 4: Recursive Category Processing**
For each category in the queue:

1. **Navigate to Category**
   - Open category URL
   - Wait for page elements to load
   - Handle any flyout menus or dynamic content

2. **Extract Subcategories**
   - Use retailer-specific CSS selectors
   - Parse category names, URLs, and product counts
   - Handle pagination ("See More" buttons, etc.)

3. **Save to Database**
   - Insert new categories into `categories` table
   - Set `parent_id` to establish hierarchy
   - Update status: `pending` → `in_progress` → `processed`

4. **Enqueue Children**
   - Add discovered subcategories to processing queue
   - Increment depth counter
   - Continue until `maxDepth` reached or no more subcategories

#### **Step 5: Completion**
- Save final statistics (categories found, processing time)
- Update category statuses to `processed_no_children` or `pending_children`
- Close browser and database connections
- Log summary report

---

## How Far Down Does It Go?

### Depth Traversal

The scraper traverses the category tree **recursively until it reaches leaf nodes** (categories with no subcategories). The depth is controlled by:

#### 1. **Configuration Limit: `maxDepth`**
Each retailer config specifies a maximum depth:

```typescript
// clicks.ts
maxDepth: 50  // Virtually unlimited

// dischem.ts
maxDepth: 3   // Stop after 3 levels

// faithfultonature.ts
maxDepth: 3   // Stop after 3 levels
```

#### 2. **Natural Leaf Nodes**
The scraper stops when a category has no subcategories, regardless of depth.

### Example: Category Tree Traversal

```
Root (depth: 0)
├─ Health & Beauty (depth: 1)
│  ├─ Skincare (depth: 2)
│  │  ├─ Face Creams (depth: 3)
│  │  │  ├─ Moisturizers (depth: 4)
│  │  │  └─ Anti-Aging (depth: 4) ← Leaf node (no children)
│  │  └─ Body Lotions (depth: 3) ← Leaf node (no children)
│  └─ Hair Care (depth: 2)
│     └─ Shampoos (depth: 3) ← Leaf node (no children)
└─ Food & Supplements (depth: 1)
   └─ Vitamins (depth: 2) ← Leaf node (no children)
```

**Processing Order:**
1. Start at Health & Beauty (depth: 1)
2. Navigate to Skincare (depth: 2), extract children
3. Navigate to Face Creams (depth: 3), extract children
4. Navigate to Moisturizers (depth: 4) - no children found → mark as leaf
5. Navigate to Anti-Aging (depth: 4) - no children found → mark as leaf
6. Back to Body Lotions (depth: 3) - no children found → mark as leaf
7. Continue with Hair Care branch...

### Depth Limits by Retailer

| Retailer | Max Depth | Typical Actual Depth |
|----------|-----------|---------------------|
| Clicks | 50 (unlimited) | 3-5 levels |
| Dis-Chem | 3 | 2-3 levels |
| Faithful to Nature | 3 | 2-3 levels |
| Wellness Warehouse | 2 | 2 levels |

---

## Database Integration

### Categories Table Structure

```sql
CREATE TABLE categories (
  id                    SERIAL PRIMARY KEY,
  name                  VARCHAR(255) NOT NULL,
  url                   VARCHAR(500) UNIQUE,
  parent_id             INTEGER REFERENCES categories(id),
  retailer_id           INTEGER REFERENCES retailers(id),
  depth                 INTEGER,
  queue_status          VARCHAR(20) DEFAULT 'pending',
  processed             BOOLEAN DEFAULT false,
  created_at            TIMESTAMP DEFAULT NOW()
);
```

### Category Status Flow

```
pending → in_progress → processed_no_children (leaf node)
                    ↓
                    → pending_children → hierarchy_completed
```

### Example Database Records

After scraping Clicks "Skincare" category:

| id | name | url | parent_id | depth | queue_status |
|----|------|-----|-----------|-------|--------------|
| 1 | Health & Beauty | /health-beauty | NULL | 0 | hierarchy_completed |
| 2 | Skincare | /health-beauty/skincare | 1 | 1 | hierarchy_completed |
| 3 | Face Creams | /health-beauty/skincare/face-creams | 2 | 2 | hierarchy_completed |
| 4 | Moisturizers | /health-beauty/skincare/face-creams/moisturizers | 3 | 3 | processed_no_children |
| 5 | Anti-Aging | /health-beauty/skincare/face-creams/anti-aging | 3 | 3 | processed_no_children |

---

## Operating Modes

The category scraper supports three execution modes:

### 1. Legacy Mode (Single-Threaded)
**Best for:** Debugging, small sites, development

```bash
npm run scrape:c scrape --retailer clicks --mode legacy
```

**Characteristics:**
- Single-threaded sequential processing
- Checkpoint-based resume capability (JSON files)
- Slower but more stable
- Lower resource usage

**When to Use:**
- Testing new retailer configurations
- Debugging selector issues
- Small websites (<1000 categories)

### 2. Enhanced Mode (Multi-Threaded)
**Best for:** Production, large-scale operations

```bash
npm run scrape:c scrape --retailer clicks --mode enhanced
```

**Characteristics:**
- Multi-threaded worker pool (configurable concurrency)
- Database queue management (no checkpoint files)
- Fastest execution
- High resource usage (parallel browsers)

**When to Use:**
- Production scraping
- Large websites (>5000 categories)
- When speed is critical

**Configuration:**
```json
// config/concurrency.json
{
  "maxGlobalConcurrent": 4,
  "retailerConcurrency": {
    "clicks": 2,
    "dischem": 2,
    "faithfultonature": 1
  }
}
```

### 3. Queue-Based Mode (Hybrid)
**Best for:** Balanced operation

```bash
npm run scrape:c scrape --retailer clicks --mode queue
```

**Characteristics:**
- Single process with database-backed queue
- Medium speed and resource usage
- Good for moderate-sized sites

---

## Key Features

### 1. **Anti-Bot Detection Handling**
- Automatic Cloudflare challenge detection
- Wait for challenge resolution (configurable timeout)
- Retry logic for failed requests

### 2. **Checkpoint System**
- Resume from interruption (Legacy/Queue modes)
- Periodic state snapshots to JSON files
- Configurable checkpoint frequency

### 3. **Error Handling**
- Classify errors (network, selector, Cloudflare)
- Automatic retry with exponential backoff
- HTML snapshot saving on error (debug mode)

### 4. **Progress Tracking**
- Real-time console logging with colors
- Persistent log files (daily rotation)
- Statistics (categories found, processing time)

### 5. **Graceful Shutdown**
- SIGINT/SIGTERM signal handling
- Save checkpoint on interruption
- Clean browser and database closure

---

## Next Steps

For more detailed information, see:
- **04_Required_Templates_Per_Retailer.md** - What files are needed per retailer
- **05_Adding_A_New_Retailer.md** - Step-by-step guide to add a new site
- **06_How_Category_Scraping_Works.md** - Deep dive into extraction logic
- **07_Subcategory_Discovery.md** - Recursive traversal algorithm
