# Required Templates Per Retailer

## Overview

Each retailer requires **one main configuration file** to work with the category scraper. This file contains:
- CSS selectors for extracting categories from the DOM
- Scraper configuration (timeouts, URLs, browser settings)
- Retailer-specific extraction logic parameters

---

## Mandatory Files Per Retailer

### 1. Configuration File (REQUIRED)

**Location:** `src/scrappers/category_scraper/config/<retailer>.ts`

**Examples:**
- `config/clicks.ts`
- `config/dischem.ts`
- `config/faithfultonature.ts`
- `config/wellnesswarehouse.ts`

This is the **ONLY required file** for basic functionality.

---

## Configuration File Structure

Every retailer configuration file **must export** two objects:

### 1. Category Selectors Object

Defines CSS selectors for finding category elements in the DOM.

```typescript
export const <retailer>CategorySelectors: CategorySelectors = {
  // Main container for category list
  CATEGORY_LIST_CONTAINER: "ul.category-menu",
  
  // Individual category items
  CATEGORY_ITEM: "li.category-item",
  
  // Category name element
  CATEGORY_NAME_TEXT: "span.category-name",
  
  // Category link element
  CATEGORY_URL_ANCHOR: "a.category-link",
  
  // Product count (optional)
  CATEGORY_PRODUCT_COUNT: "span.product-count",
  
  // Expected element after page load
  expectedPageLoadedSelector: "div.main-content",
  
  // Navigation-specific selectors (if using flyout menus)
  MAIN_NAV_TOP_LEVEL_LINK_PATTERN: "nav > ul > li > a",
  MAIN_NAV_FLYOUT_PANEL_SELECTOR: "div.flyout-menu",
  
  // Expansion buttons (if categories are lazy-loaded)
  SEE_MORE_BUTTON: "button.show-more",
  SEE_LESS_BUTTON: "button.show-less",
  
  // ... other selectors as needed
};
```

### 2. Scraper Configuration Object

Defines runtime parameters and behavior.

```typescript
export const <retailer>ScraperConfig: ScraperConfig = {
  // URLs
  baseUrl: "https://www.example.com",
  startUrl: "https://www.example.com/categories",
  
  // Identifiers
  siteId: "<retailer>",
  retailerId: Retailer.<RETAILER_ENUM>,
  
  // Selectors reference
  categorySelectors: <retailer>CategorySelectors,
  
  // Traversal limits
  maxDepth: 3,
  maxProductsPerCategory: 0,
  
  // Rate limiting
  maxConcurrentRequests: 3,
  delayBetweenRequests: 1500,
  
  // Browser settings
  headless: "new",
  userAgent: "Mozilla/5.0 ...",
  viewport: { width: 1920, height: 1080 },
  launchArgs: ["--no-sandbox", "--disable-setuid-sandbox"],
  useStealthPlugin: true,
  
  // Timeouts
  retryAttempts: 3,
  retryDelay: 5000,
  pageLoadTimeout: 60000,
  navigationTimeout: 60000,
  elementTimeout: 30000,
  cloudflareChallengeTimeout: 120000,
  
  // Checkpointing
  checkpointFilePath: "./checkpoints/<retailer>_checkpoint.json",
  saveCheckpointCategoryCount: 10,
  saveCheckpointIntervalMs: 300000,
  
  // Logging
  debugMode: false,
  logLevel: "info",
  saveSnapshotsOnError: true,
  snapshotDirectory: "./debug_snapshots/<retailer>",
  
  // Interaction configuration
  interactionConfig: {
    mainNavInteraction: "hover", // or "click" or "none"
    mainNavTriggerSelectorPattern: "nav > ul > li > a",
    mainNavFlyoutPanelToWaitFor: "div.flyout-menu",
    delayAfterMainNavInteraction: 500,
  },
};
```

---

## Retailer-Specific Extractor (OPTIONAL)

For complex websites with unique DOM structures, you may need a custom extractor.

**Location:** `src/scrappers/category_scraper/extractor/<retailer>/categoryLinkExtractor.ts`

**Examples:**
- `extractor/clicks/categoryLinkExtractor.ts`
- `extractor/dischem/dischemCategoryLinkExtractor.ts`
- `extractor/faithfultonature/categoryLinkExtractor.ts`
- `extractor/wellnesswarehouse/categoryLinkExtractor.ts`

**When to Create:**
- The website has a unique category navigation structure
- Standard DOM traversal doesn't work
- Categories are loaded via JavaScript/AJAX
- Special interaction patterns are needed (carousel, infinite scroll, etc.)

---

## Complete Template Checklist

### Minimum Required (Basic Retailer)

- [ ] **Configuration File:** `config/<retailer>.ts`
  - [ ] Export `<retailer>CategorySelectors` object
  - [ ] Export `<retailer>ScraperConfig` object
  - [ ] Define all required CSS selectors
  - [ ] Set timeouts and browser configuration
  - [ ] Specify `retailerId` from `Retailer` enum

### Optional (Complex Retailer)

- [ ] **Custom Extractor:** `extractor/<retailer>/categoryLinkExtractor.ts`
  - [ ] Implement category extraction logic
  - [ ] Handle retailer-specific DOM structure
  - [ ] Export extractor function

- [ ] **Orchestrator Handler:** `orchestrator/handlers/<retailer>/categoryExtractor.ts`
  - [ ] Only needed if extraction requires multi-step orchestration

---

## Comparison: What's in Each File

### Example: Clicks vs Dis-Chem

| Aspect | Clicks | Dis-Chem |
|--------|--------|----------|
| **Config File** | `config/clicks.ts` | `config/dischem.ts` |
| **Custom Extractor** | `extractor/clicks/categoryLinkExtractor.ts` | `extractor/dischem/dischemCategoryLinkExtractor.ts` |
| **Reason for Extractor** | Uses sidebar filter structure (not standard menu) | Uses mega menu with brand carousels |
| **Complexity** | High (filter toggles, hidden inputs) | Medium (carousel pagination, v-navigation) |

### Example: Faithful to Nature vs Wellness Warehouse

| Aspect | Faithful to Nature | Wellness Warehouse |
|--------|-------------------|-------------------|
| **Config File** | `config/faithfultonature.ts` | `config/wellnesswarehouse.ts` |
| **Custom Extractor** | `extractor/faithfultonature/categoryLinkExtractor.ts` | `extractor/wellnesswarehouse/categoryLinkExtractor.ts` |
| **Reason for Extractor** | Hierarchical submenu with hover interaction | Grid-based category layout with images |
| **Complexity** | Medium (multi-column flyout) | Low (simple grid parsing) |

---

## Selector Types Explained

### Basic Selectors (Universal)

These work for most standard e-commerce sites:

```typescript
CATEGORY_LIST_CONTAINER: "ul.categories"     // Container for all categories
CATEGORY_ITEM: "li.category"                 // Individual category item
CATEGORY_NAME_TEXT: "span.name"              // Category name
CATEGORY_URL_ANCHOR: "a.link"                // Category link
```

### Navigation Selectors (Flyout Menus)

For sites with dropdown/flyout navigation:

```typescript
MAIN_NAV_TOP_LEVEL_LINK_PATTERN: "nav > ul > li > a"  // Top-level nav items
MAIN_NAV_FLYOUT_PANEL_SELECTOR: "div.submenu"         // Flyout panel
MAIN_NAV_SUBLIST_CONTAINER: "ul.submenu-items"        // List within flyout
MAIN_NAV_SUB_ITEM: "li"                               // Subcategory item
```

### Clicks-Specific Selectors (Sidebar Filters)

```typescript
EXPAND_CATEGORY_SECTION_TOGGLE: "a.refinementToggle"
SEE_MORE_BUTTON: "button.read-more-facet"
CATEGORY_URL_INPUT: "input.hidden-lg"  // Hidden input with URL
CATEGORY_PRODUCT_COUNT: "span.facetValueCount"
```

### Dis-Chem-Specific Selectors (Carousels)

```typescript
BRAND_PAGE_CAROUSEL_BLOCK: "div.bp-brands-block"
BRAND_PAGE_CAROUSEL_ITEMS_CONTAINER: "div.bp-carousel"
BRAND_PAGE_CAROUSEL_ITEM: "div.inline-bp[data-thumb-alt]"
BRAND_PAGE_CAROUSEL_NEXT_BUTTON: "a.flex-next"
```

### Faithful to Nature-Specific Selectors (Mega Menu)

```typescript
TOP_LEVEL_MENU_CONTAINER: "ul#ms-topmenu"
SUBMENU_PANEL: "div.ms-submenu"
SUBMENU_COLUMN_LAYOUT_CONTAINER: "div.row.ms-category"
LEVEL_1_CATEGORY_ANCHOR: "a.form-group.level1"
```

---

## Configuration Priority

When multiple config sources exist, they are loaded in this order:

1. **Retailer-specific config** from `RETAILER_SCRAPER_CONFIGS[retailer]`
2. **Default config** (Clicks-based fallback)
3. **Runtime overrides** (command-line options)

Example:
```typescript
const baseConfig = RETAILER_SCRAPER_CONFIGS[Retailer.DISCHEM];
const effectiveConfig = { 
  ...baseConfig, 
  ...runtimeOptions  // Override with CLI args
};
```

---

## Shared Configuration File

The global concurrency settings are shared across all retailers:

**File:** `config/concurrency.json`

```json
{
  "maxGlobalConcurrent": 4,
  "retailerConcurrency": {
    "clicks": 2,
    "dischem": 2,
    "faithfultonature": 1,
    "wellnesswarehouse": 1,
    "default": 1
  },
  "database": {
    "maxBatchSize": 5,
    "lockTimeoutMs": 300000,
    "poolSize": 10
  },
  "scraping": {
    "maxItemsPerTask": 1000,
    "taskTimeoutMs": 1800000,
    "browserConcurrency": 1
  }
}
```

**This file is OPTIONAL** - only needed for Enhanced Mode (multi-threaded).

---

## Summary

### Minimum Required Per Retailer:
1. **One configuration file:** `config/<retailer>.ts`
   - Contains selectors and scraper config
   - ~70-90 lines of code

### Optional (if needed):
2. **Custom extractor:** `extractor/<retailer>/categoryLinkExtractor.ts`
   - Only for complex DOM structures
   - ~100-500 lines of code

### Shared (All Retailers):
3. **Concurrency config:** `config/concurrency.json`
   - Only for Enhanced Mode
   - Shared across all retailers

**Answer to your question:** 
The config files you listed (`clicks.ts`, `dischem.ts`, `faithfultonature.ts`, `wellnesswarehouse.ts`, and `concurrency.json`) are the **core templates** needed. Custom extractors are only created when the standard extraction logic doesn't work for a retailer's unique DOM structure.
