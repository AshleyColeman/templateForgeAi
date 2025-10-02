# Adding a New Retailer - Step-by-Step Guide

## Overview

This guide walks you through adding a brand-new retailer to the category scraper. Follow these steps in order to ensure proper integration with the existing system.

---

## Prerequisites

Before starting, gather the following information about the new retailer:

- [ ] Website URL (homepage and category pages)
- [ ] Browser access to the website (to inspect DOM)
- [ ] Understanding of the site's category navigation structure
- [ ] Decision on retailer identifier (lowercase, no spaces)

---

## Step 1: Add Retailer to Enum

### Location: `src/scrappers/shared/types.ts`

Add the new retailer to the `Retailer` enum:

```typescript
export enum Retailer {
  CLICKS = "clicks",
  DISCHEM = "dischem",
  FAITHFUL_TO_NATURE = "faithful-to-nature",
  WELLNESS_WAREHOUSE = "wellnesswarehouse",
  NEW_RETAILER = "newretailer",  // ← ADD THIS
}
```

**Naming Convention:**
- Use lowercase
- Replace spaces with hyphens or remove them
- Keep it short and recognizable

### Update Retailer Mappings

In the same file, update the mapping objects:

```typescript
export const RETAILER_DB_MAP: { [key in Retailer]: string } = {
  [Retailer.CLICKS]: "Clicks",
  [Retailer.DISCHEM]: "Dis-Chem",
  [Retailer.FAITHFUL_TO_NATURE]: "faithful-to-nature",
  [Retailer.WELLNESS_WAREHOUSE]: "wellnesswarehouse",
  [Retailer.NEW_RETAILER]: "NewRetailer",  // ← ADD THIS (display name)
};

export const RETAILER_DB_MAP_NORMALIZED: { [key in Retailer]: string } = {
  [Retailer.CLICKS]: "clicks",
  [Retailer.DISCHEM]: "dischem",
  [Retailer.FAITHFUL_TO_NATURE]: "faithfultonature",
  [Retailer.WELLNESS_WAREHOUSE]: "wellnesswarehouse",
  [Retailer.NEW_RETAILER]: "newretailer",  // ← ADD THIS (normalized)
};
```

### Update Normalizer Function

```typescript
export function normalizeRetailerKey(retailer: string): Retailer | undefined {
  switch (retailer.toLowerCase().replace(/_/g, "").replace(/-/g, "")) {
    case "clicks":
      return Retailer.CLICKS;
    case "dischem":
      return Retailer.DISCHEM;
    case "faithfultonature":
      return Retailer.FAITHFUL_TO_NATURE;
    case "wellnesswarehouse":
      return Retailer.WELLNESS_WAREHOUSE;
    case "newretailer":  // ← ADD THIS
      return Retailer.NEW_RETAILER;
    default:
      return undefined;
  }
}
```

---

## Step 2: Add Retailer to Database

### Insert into `retailers` Table

Run this SQL query to add the retailer to your database:

```sql
INSERT INTO retailers (name, website_url, normalize)
VALUES (
  'NewRetailer',                      -- Display name
  'https://www.newretailer.com',      -- Website URL
  'newretailer'                       -- Normalized name (lowercase)
);
```

### Get the Retailer ID

```sql
SELECT id FROM retailers WHERE normalize = 'newretailer';
```

Note this ID (e.g., `5`) - you'll need it for the configuration.

---

## Step 3: Update Retailer ID Mapping

### Location: `src/scrappers/category_scraper/config.ts`

Add the retailer to the `RETAILER_NAME_TO_ID` map:

```typescript
export const RETAILER_NAME_TO_ID: Record<Retailer, number> = {
  [Retailer.CLICKS]: 1,
  [Retailer.DISCHEM]: 2,
  [Retailer.FAITHFUL_TO_NATURE]: 3,
  [Retailer.WELLNESS_WAREHOUSE]: 4,
  [Retailer.NEW_RETAILER]: 5,  // ← ADD THIS (use the ID from database)
};
```

---

## Step 4: Inspect the Website's DOM Structure

Open the retailer's website in a browser and inspect the category navigation:

### Questions to Answer:

1. **Where are categories located?**
   - Top navigation bar?
   - Sidebar menu?
   - Dedicated categories page?

2. **How do categories appear?**
   - Static list?
   - Flyout/dropdown on hover?
   - Click-to-expand menu?
   - Lazy-loaded/paginated?

3. **What DOM structure is used?**
   - `<ul>` with `<li>` items?
   - `<div>` grid layout?
   - Table structure?
   - Custom component?

4. **What information is available?**
   - Category names?
   - URLs (in `href` attributes)?
   - Product counts?
   - Images?

### Example DOM Inspection

For a typical navigation menu:

```html
<nav class="main-navigation">
  <ul class="category-list">
    <li class="category-item">
      <a href="/health" class="category-link">
        <span class="category-name">Health</span>
        <span class="product-count">(245 items)</span>
      </a>
    </li>
    <li class="category-item">
      <a href="/beauty" class="category-link">
        <span class="category-name">Beauty</span>
        <span class="product-count">(189 items)</span>
      </a>
    </li>
  </ul>
</nav>
```

**Record the CSS selectors:**
- Container: `.main-navigation .category-list`
- Item: `li.category-item`
- Link: `a.category-link`
- Name: `span.category-name`
- Count: `span.product-count`

---

## Step 5: Create Configuration File

### Location: `src/scrappers/category_scraper/config/newretailer.ts`

Create a new file with the retailer's configuration:

```typescript
import { CategorySelectors, ScraperConfig } from "../types";
import { Retailer } from "../../shared/types";

/**
 * Category selectors for NewRetailer website
 */
export const newRetailerCategorySelectors: CategorySelectors = {
  // Container for the category list
  CATEGORY_LIST_CONTAINER: ".main-navigation .category-list",
  
  // Individual category items
  CATEGORY_ITEM: "li.category-item",
  
  // Category name element
  CATEGORY_NAME_TEXT: "span.category-name",
  
  // Category link/anchor element
  CATEGORY_URL_ANCHOR: "a.category-link",
  
  // Product count (optional)
  CATEGORY_PRODUCT_COUNT: "span.product-count",
  
  // Selector to confirm page has loaded (not Cloudflare challenge)
  expectedPageLoadedSelector: ".main-navigation",
  
  // === Navigation-specific selectors (if flyout menu exists) ===
  // Top-level navigation items that trigger flyouts
  MAIN_NAV_TOP_LEVEL_LINK_PATTERN: "nav.main-nav > ul > li > a",
  
  // The flyout panel that appears on hover/click
  MAIN_NAV_FLYOUT_PANEL_SELECTOR: "div.flyout-submenu",
  
  // Container for subcategory links within flyout
  MAIN_NAV_SUBLIST_CONTAINER: "ul.submenu-items",
  
  // Individual subcategory items
  MAIN_NAV_SUB_ITEM: "li.submenu-item",
  
  // Subcategory name
  MAIN_NAV_SUB_NAME_TEXT: "a.submenu-link",
  
  // Subcategory URL
  MAIN_NAV_SUB_URL_ANCHOR: "a.submenu-link",
  
  // === Expansion buttons (if categories are lazy-loaded) ===
  SEE_MORE_BUTTON: "button.show-more-categories",
  SEE_LESS_BUTTON: "button.show-less-categories",
  
  // === Leave empty if not applicable ===
  EXPAND_CATEGORY_SECTION_TOGGLE: "",
  CATEGORY_URL_INPUT: "",
  CATEGORY_LINK_SELECTOR: "",
  SUB_CATEGORY_SELECTOR: "",
};

/**
 * Scraper configuration for NewRetailer
 */
export const newRetailerScraperConfig: ScraperConfig = {
  // === URLs ===
  baseUrl: "https://www.newretailer.com",
  startUrl: "https://www.newretailer.com/categories",
  
  // === Identifiers ===
  siteId: "newretailer",
  retailerId: Retailer.NEW_RETAILER,
  
  // === Selectors ===
  categorySelectors: newRetailerCategorySelectors,
  
  // === Traversal Limits ===
  maxDepth: 3,  // Adjust based on site's category depth
  maxProductsPerCategory: 0,
  
  // === Rate Limiting ===
  maxConcurrentRequests: 3,
  delayBetweenRequests: 1500,  // 1.5 seconds
  
  // === Browser Configuration ===
  headless: "new",
  userAgent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
  viewport: { width: 1920, height: 1080 },
  launchArgs: ["--no-sandbox", "--disable-setuid-sandbox"],
  useStealthPlugin: true,
  
  // === Timeouts and Retries ===
  retryAttempts: 3,
  retryDelay: 5000,  // 5 seconds
  pageLoadTimeout: 60000,  // 60 seconds
  navigationTimeout: 60000,  // 60 seconds
  elementTimeout: 30000,  // 30 seconds
  cloudflareChallengeTimeout: 120000,  // 2 minutes
  
  // === Checkpointing ===
  checkpointFilePath: "./checkpoints/newretailer_checkpoint.json",
  saveCheckpointCategoryCount: 10,
  saveCheckpointIntervalMs: 300000,  // 5 minutes
  
  // === Logging ===
  debugMode: false,
  logLevel: "info",
  saveSnapshotsOnError: true,
  snapshotDirectory: "./debug_snapshots/newretailer",
  
  // === Interaction Configuration ===
  interactionConfig: {
    mainNavInteraction: "hover",  // or "click" or "none"
    mainNavTriggerSelectorPattern: "nav.main-nav > ul > li > a",
    mainNavFlyoutPanelToWaitFor: "div.flyout-submenu",
    delayAfterMainNavInteraction: 500,  // 0.5 seconds
  },
};
```

### Configuration Tips:

**Timeouts:**
- Start conservative (60s page load, 30s elements)
- Increase if site is slow
- Decrease for fast-loading sites

**Max Depth:**
- Set to 3 for most sites
- Increase to 5+ if deep category trees
- Set to 2 for shallow hierarchies

**Interaction Type:**
- `"hover"`: For flyout menus triggered by mouse hover
- `"click"`: For menus that need explicit clicking
- `"none"`: For static category pages (no interaction needed)

**Delays:**
- Increase if site is slow to load dynamic content
- Decrease for fast sites (but stay >1000ms to avoid rate limiting)

---

## Step 6: Register Configuration

### Location: `src/scrappers/category_scraper/config.ts`

Import and register the new configuration:

```typescript
import { Retailer } from "../shared/types";
import type { ScraperConfig } from "./types";
import { clicksScraperConfig, clicksCategorySelectors } from "./config/clicks";
import { dischemScraperConfig, dischemCategorySelectors } from "./config/dischem";
import { faithfulToNatureScraperConfig, faithfulToNatureCategorySelectors } from "./config/faithfultonature";
import { wellnessWarehouseScraperConfig, wellnessWarehouseCategorySelectors } from "./config/wellnesswarehouse";
import { newRetailerScraperConfig, newRetailerCategorySelectors } from "./config/newretailer";  // ← ADD THIS

export const RETAILER_NAME_TO_ID: Record<Retailer, number> = {
  [Retailer.CLICKS]: 1,
  [Retailer.DISCHEM]: 2,
  [Retailer.FAITHFUL_TO_NATURE]: 3,
  [Retailer.WELLNESS_WAREHOUSE]: 4,
  [Retailer.NEW_RETAILER]: 5,
};

export const RETAILER_SCRAPER_CONFIGS: Record<Retailer, ScraperConfig> = {
  [Retailer.CLICKS]: clicksScraperConfig,
  [Retailer.DISCHEM]: dischemScraperConfig,
  [Retailer.FAITHFUL_TO_NATURE]: faithfulToNatureScraperConfig,
  [Retailer.WELLNESS_WAREHOUSE]: wellnessWarehouseScraperConfig,
  [Retailer.NEW_RETAILER]: newRetailerScraperConfig,  // ← ADD THIS
};

export {
  clicksScraperConfig,
  clicksCategorySelectors,
  dischemScraperConfig,
  dischemCategorySelectors,
  faithfulToNatureScraperConfig,
  faithfulToNatureCategorySelectors,
  wellnessWarehouseScraperConfig,
  wellnessWarehouseCategorySelectors,
  newRetailerScraperConfig,  // ← ADD THIS
  newRetailerCategorySelectors,  // ← ADD THIS
};
```

---

## Step 7: Update Concurrency Settings (Optional)

### Location: `config/concurrency.json`

Add the retailer to the concurrency configuration:

```json
{
  "maxGlobalConcurrent": 4,
  "retailerConcurrency": {
    "clicks": 2,
    "dischem": 2,
    "faithfultonature": 1,
    "wellnesswarehouse": 1,
    "newretailer": 2,  ← ADD THIS
    "default": 1
  }
}
```

**Concurrency Recommendations:**
- Start with `1` for testing
- Increase to `2-3` for production
- Never exceed `5` to avoid overwhelming the server

---

## Step 8: Update Types (If Needed)

### Location: `src/scrappers/category_scraper/types.ts`

If your retailer uses standard selectors, no changes are needed. If it requires custom selectors, create an interface:

```typescript
/**
 * Specific category selectors for NewRetailer
 */
export interface NewRetailerCategorySelectors extends CategorySelectors {
  // Add any custom selectors here
  CUSTOM_SELECTOR_1?: string;
  CUSTOM_SELECTOR_2?: string;
}

/**
 * Specific scraper configuration for NewRetailer
 */
export interface NewRetailerScraperConfig extends ScraperConfig {
  categorySelectors: NewRetailerCategorySelectors;
  siteId: "newretailer";
  retailerId: Retailer.NEW_RETAILER;
}
```

Then update your config file to use these types:

```typescript
export const newRetailerCategorySelectors: NewRetailerCategorySelectors = { ... };
export const newRetailerScraperConfig: NewRetailerScraperConfig = { ... };
```

---

## Step 9: Test the Configuration

### Run in Legacy Mode First

```bash
npm run scrape:c scrape --retailer newretailer --mode legacy
```

**Why Legacy Mode?**
- Single-threaded = easier to debug
- Checkpoint files = can resume after failures
- Detailed logging

### Watch for Issues:

1. **Selectors not found**
   - Error: "Element not found: .category-list"
   - Fix: Inspect DOM again, update selectors

2. **Cloudflare challenges**
   - Error: "Cloudflare challenge detected"
   - Fix: Increase `cloudflareChallengeTimeout`

3. **Timeouts**
   - Error: "Navigation timeout"
   - Fix: Increase `pageLoadTimeout` and `navigationTimeout`

4. **No categories found**
   - Error: "Discovered 0 subcategories"
   - Fix: Check `CATEGORY_LIST_CONTAINER` and `CATEGORY_ITEM` selectors

### Enable Debug Mode

If issues persist, enable debugging:

```typescript
// In config/newretailer.ts
debugMode: true,
saveSnapshotsOnError: true,
logLevel: "debug",
```

This will save HTML snapshots to `debug_snapshots/newretailer/`.

---

## Step 10: Create Custom Extractor (If Needed)

If the standard extraction logic doesn't work, create a custom extractor.

### Location: `src/scrappers/category_scraper/extractor/newretailer/categoryLinkExtractor.ts`

```typescript
import { Page, ElementHandle } from "puppeteer";
import { CategoryInfo, ScraperConfig } from "../../types";
import { categoryScraperLogger as logger } from "../../logging";

/**
 * Custom category link extractor for NewRetailer
 */
export async function extractNewRetailerCategoryLinks(
  page: Page,
  parentCategory: CategoryInfo,
  config: ScraperConfig,
  sectionHandle?: ElementHandle<Element> | null
): Promise<CategoryInfo[]> {
  const categories: CategoryInfo[] = [];
  
  try {
    // Your custom extraction logic here
    // Example: Extract from grid layout
    const categoryElements = await page.$$(
      config.categorySelectors.CATEGORY_ITEM || "div.category-card"
    );
    
    for (const element of categoryElements) {
      const nameElement = await element.$(
        config.categorySelectors.CATEGORY_NAME_TEXT || "h3.category-title"
      );
      const linkElement = await element.$(
        config.categorySelectors.CATEGORY_URL_ANCHOR || "a.category-link"
      );
      
      if (nameElement && linkElement) {
        const name = await nameElement.evaluate(el => el.textContent?.trim() || "");
        const url = await linkElement.evaluate(el => el.getAttribute("href") || "");
        
        if (name && url) {
          categories.push({
            id: `temp_${Date.now()}_${categories.length}`,
            name,
            url: new URL(url, config.baseUrl).href,
            parentId: parentCategory.id,
            parentUrl: parentCategory.url,
            depth: (parentCategory.depth || 0) + 1,
            siteId: config.siteId,
            retailerId: config.retailerId,
            status: "pending",
          });
        }
      }
      
      await element.dispose();
    }
    
    logger.info(`[NewRetailer Extractor] Extracted ${categories.length} categories`);
  } catch (error: any) {
    logger.error(`[NewRetailer Extractor] Error:`, error);
  }
  
  return categories;
}
```

### Register Custom Extractor

Update the orchestrator to use your custom extractor for this retailer.

---

## Step 11: Final Testing

### Test All Scenarios:

1. **Root category extraction**
   ```bash
   npm run scrape:c scrape --retailer newretailer --mode legacy
   ```

2. **Subcategory traversal**
   - Check that depth increases correctly
   - Verify parent-child relationships in database

3. **Error handling**
   - Simulate network failures
   - Test Cloudflare challenges

4. **Resume capability**
   - Stop scraper mid-run (Ctrl+C)
   - Restart and verify it resumes from checkpoint

### Verify Database Records:

```sql
SELECT 
  id, name, url, parent_id, depth, queue_status
FROM categories
WHERE retailer_id = 5  -- NewRetailer's ID
ORDER BY depth, id
LIMIT 20;
```

---

## Step 12: Production Run

Once testing is successful, run in Enhanced Mode for faster execution:

```bash
npm run scrape:c scrape --retailer newretailer --mode enhanced
```

Monitor logs for any issues.

---

## Checklist Summary

- [ ] **Step 1:** Add to `Retailer` enum and mappings
- [ ] **Step 2:** Insert into `retailers` database table
- [ ] **Step 3:** Update `RETAILER_NAME_TO_ID` mapping
- [ ] **Step 4:** Inspect website DOM structure
- [ ] **Step 5:** Create `config/newretailer.ts` file
- [ ] **Step 6:** Register in `config.ts`
- [ ] **Step 7:** Add to `concurrency.json` (optional)
- [ ] **Step 8:** Create custom types (if needed)
- [ ] **Step 9:** Test in Legacy Mode
- [ ] **Step 10:** Create custom extractor (if needed)
- [ ] **Step 11:** Final testing and validation
- [ ] **Step 12:** Production run in Enhanced Mode

---

## Troubleshooting Common Issues

### Issue: No categories found

**Possible causes:**
- Incorrect selectors
- Page not fully loaded
- Cloudflare blocking

**Solutions:**
- Enable `debugMode` and check HTML snapshots
- Increase timeouts
- Verify selectors in browser DevTools

### Issue: Duplicate categories in database

**Possible causes:**
- Unique constraint violation
- Same category found via different paths

**Solutions:**
- Check `UNIQUE(retailer_id, name, parent_id)` constraint
- Verify URL normalization

### Issue: Categories not being processed

**Possible causes:**
- `maxDepth` limit reached
- Categories marked as `skip_processing`
- Queue status stuck

**Solutions:**
- Increase `maxDepth` in config
- Check `queue_status` in database
- Reset stuck categories:
  ```sql
  UPDATE categories
  SET queue_status = 'pending'
  WHERE retailer_id = 5 AND queue_status = 'in_progress';
  ```

---

## Next Steps

After successfully adding a retailer, you may want to:

1. **Optimize selectors** - Fine-tune for better accuracy
2. **Add product scraping** - Extend to scrape products from categories
3. **Schedule regular runs** - Set up cron jobs for updates
4. **Monitor performance** - Track scraping speed and error rates
