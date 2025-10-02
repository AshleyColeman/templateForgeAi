# How to Add a New Retailer to the Category Scraper

This guide walks you through adding a new retailer to the category scraper system.

## Prerequisites

- Basic understanding of CSS selectors
- Chrome DevTools familiarity
- Access to the target retailer's website
- Development environment set up

## Step-by-Step Guide

### Step 1: Analyze the Website Structure

**Goal**: Understand how the target site organizes its categories.

#### 1.1 Visit the Homepage
Navigate to the retailer's website and observe:
- Where are categories displayed? (Top nav, sidebar, footer)
- How do they appear? (Hover menu, click menu, static links)
- Are they hierarchical? (Categories → Subcategories → Sub-subcategories)

#### 1.2 Identify UI Patterns
Common patterns:
- **Hover flyout menu**: Hover over top-level item → submenu appears
- **Click-to-expand**: Click category → accordion expands
- **Sidebar filters**: Categories displayed as filters on category pages
- **Dropdown menu**: Multi-column dropdown with grouped categories
- **Grid layout**: Category cards in a grid

#### 1.3 Inspect with DevTools
Open Chrome DevTools (F12) and:
1. Right-click on a category link → Inspect
2. Note the HTML structure
3. Identify patterns in class names and IDs
4. Check for dynamic loading (JavaScript-rendered content)

### Step 2: Create Configuration File

**Location**: `src/scrappers/category_scraper/config/<retailer>.ts`

#### 2.1 Define Category Selectors

```typescript
import { CategorySelectors, ScraperConfig } from "../types";
import { Retailer } from "../../shared/types";

export const newRetailerCategorySelectors: CategorySelectors = {
  // --- Navigation Menu Selectors ---
  
  // Top-level menu item selector
  TOP_LEVEL_MENU_ITEM: "ul.main-nav > li.menu-item",
  
  // Link inside top-level item
  TOP_LEVEL_MENU_ITEM_LINK: "a.menu-link",
  
  // Flyout/submenu panel that appears on hover/click
  MAIN_NAV_FLYOUT_PANEL_SELECTOR: "div.submenu-panel",
  
  // --- Category List Selectors ---
  
  // Container holding all category items
  CATEGORY_LIST_CONTAINER: "div.category-list",
  
  // Individual category item
  CATEGORY_ITEM: "div.category-card",
  
  // Category name text
  CATEGORY_NAME_TEXT: "h3.category-name",
  
  // Category URL anchor
  CATEGORY_URL_ANCHOR: "a.category-link",
  
  // --- Optional Selectors ---
  
  // "See more" button to expand categories
  SEE_MORE_BUTTON: "button.show-more",
  
  // Product count (if displayed)
  CATEGORY_PRODUCT_COUNT: "span.product-count",
  
  // Selector to wait for to confirm page loaded
  expectedPageLoadedSelector: "div.category-list"
};
```

#### 2.2 Define Scraper Configuration

```typescript
export const newRetailerScraperConfig: ScraperConfig = {
  // Base URL (home page or category listing page)
  baseUrl: "https://www.newretailer.com",
  
  // Unique site identifier
  siteId: "newretailer",
  
  // Retailer enum value (add to shared/types.ts if needed)
  retailerId: Retailer.NEW_RETAILER,
  
  // Category selectors defined above
  categorySelectors: newRetailerCategorySelectors,
  
  // --- Scraping Behavior ---
  maxDepth: 50,                      // Maximum category depth
  maxConcurrentRequests: 3,           // Concurrent requests
  delayBetweenRequests: 2000,         // Delay between requests (ms)
  
  // --- Browser Settings ---
  headless: "new",                    // Headless mode
  userAgent: "Mozilla/5.0 ...",       // User agent string
  viewport: { width: 1920, height: 1080 },
  launchArgs: ["--no-sandbox"],
  useStealthPlugin: true,
  
  // --- Timeouts ---
  cloudflareChallengeTimeout: 60000,  // Cloudflare timeout (ms)
  navigationTimeout: 60000,           // Page navigation timeout
  elementTimeout: 30000,              // Element wait timeout
  
  // --- Retry & Error Handling ---
  retryAttempts: 3,
  retryDelay: 5000,
  
  // --- Checkpoint ---
  checkpointFilePath: "./checkpoints/newretailer_checkpoint.json",
  saveCheckpointIntervalMs: 60000,
  saveCheckpointCategoryCount: 20,
  
  // --- Debug ---
  debugMode: false,
  logLevel: "info",
  saveSnapshotsOnError: true,
  snapshotDirectory: "./debug_snapshots/newretailer",
  
  // --- Interaction Strategy (optional) ---
  interactionConfig: {
    mainNavInteraction: "hover",      // "hover" | "click"
    mainNavTriggerSelectorPattern: "ul.main-nav > li",
    mainNavFlyoutPanelToWaitFor: "div.submenu-panel",
    delayAfterMainNavInteraction: 1000
  }
};
```

### Step 3: Create Retailer-Specific Extractor

**Location**: `src/scrappers/category_scraper/extractor/<retailer>/categoryLinkExtractor.ts`

#### 3.1 Choose Your Base Pattern

You can either:
1. **Implement `ICategoryLinkExtractor` interface** (recommended)
2. **Use a standalone function** (simpler, for basic cases)

#### 3.2 Implement the Extractor (Interface Method)

```typescript
import { Page } from 'puppeteer';
import { ScraperConfig, CategoryInfo } from '../../scraper/core/types';
import { ICategoryLinkExtractor } from '../../scraper/core/iCategoryLinkExtractor';
import { UrlParser } from '../urlParser';
import { categoryScraperLogger as logger } from '../../logging';

export class NewRetailerCategoryLinkExtractor implements ICategoryLinkExtractor {
  async extract(
    page: Page,
    config: ScraperConfig,
    currentCategory?: CategoryInfo
  ): Promise<CategoryInfo[]> {
    const { categorySelectors, baseUrl, siteId, retailerId } = config;
    const extractedCategories: CategoryInfo[] = [];
    const urlParser = new UrlParser();
    
    try {
      // Wait for category container to load
      await page.waitForSelector(
        categorySelectors.CATEGORY_LIST_CONTAINER,
        { visible: true, timeout: 10000 }
      );
      
      // Get all category items
      const categoryItems = await page.$$(categorySelectors.CATEGORY_ITEM);
      
      logger.info(`[NewRetailer] Found ${categoryItems.length} category items`);
      
      for (const item of categoryItems) {
        try {
          // Extract category name
          const nameElement = await item.$(categorySelectors.CATEGORY_NAME_TEXT);
          const name = await nameElement?.evaluate(el => el.textContent?.trim());
          
          // Extract category URL
          const urlElement = await item.$(categorySelectors.CATEGORY_URL_ANCHOR);
          const url = await urlElement?.evaluate(el => (el as HTMLAnchorElement).href);
          
          if (!name || !url) {
            logger.warn(`[NewRetailer] Skipping category with missing data`);
            continue;
          }
          
          // Normalize URL
          const absoluteUrl = urlParser.normalizeUrl(url, baseUrl);
          
          // Calculate depth
          const depth = currentCategory ? (currentCategory.depth || 0) + 1 : 0;
          
          // Create category info object
          const categoryInfo: CategoryInfo = {
            id: `${siteId}-${name.toLowerCase().replace(/[^a-z0-9]+/g, '-')}-${Date.now()}`,
            name,
            url: absoluteUrl,
            parentId: currentCategory?.id || null,
            depth,
            siteId,
            retailerId,
            children: []
          };
          
          extractedCategories.push(categoryInfo);
          
          logger.debug(`[NewRetailer] Extracted: ${name} | ${absoluteUrl}`);
          
        } catch (error) {
          logger.error(`[NewRetailer] Error processing category item:`, error);
          continue;
        }
      }
      
      logger.info(`[NewRetailer] Successfully extracted ${extractedCategories.length} categories`);
      
    } catch (error) {
      logger.error('[NewRetailer] Error in extractor:', error);
      throw error;
    }
    
    return extractedCategories;
  }
}
```

#### 3.3 Alternative: Standalone Function (Simpler)

```typescript
import { Page } from "puppeteer";
import { CategoryInfo } from "../../types";
import { categoryScraperLogger as logger } from "../../logging";

export async function extractNewRetailerCategoryLinks(
  page: Page,
  selectors: any,
  currentCategory: CategoryInfo
): Promise<CategoryInfo[]> {
  const extractedCategories: CategoryInfo[] = [];
  
  // Your extraction logic here
  const categoryItems = await page.$$(selectors.CATEGORY_ITEM);
  
  for (const item of categoryItems) {
    // Extract name, URL, etc.
    // Build CategoryInfo object
    // Add to extractedCategories
  }
  
  return extractedCategories;
}
```

### Step 4: Register the Retailer

#### 4.1 Update Retailer Enum

**File**: `src/scrappers/shared/types.ts` (or equivalent)

```typescript
export enum Retailer {
  CLICKS = 'clicks',
  DISCHEM = 'dischem',
  FAITHFUL_TO_NATURE = 'faithful-to-nature',
  WELLNESSWAREHOUSE = 'wellnesswarehouse',
  NEW_RETAILER = 'newretailer'  // Add this
}
```

#### 4.2 Update Retailer Configuration Registry

**File**: `src/scrappers/category_scraper/config/retailerConfig.ts`

```typescript
import { NEW_RETAILER_CONFIG } from './newretailer';

export const RETAILER_CONFIGS: Record<string, RetailerScraperConfig> = {
  'clicks': CLICKS_CONFIG,
  'dischem': DISCHEM_CONFIG,
  'faithful-to-nature': FAITHFUL_TO_NATURE_CONFIG,
  'wellnesswarehouse': WELLNESS_WAREHOUSE_CONFIG,
  'newretailer': NEW_RETAILER_CONFIG  // Add this
};
```

#### 4.3 Update Config Index

**File**: `src/scrappers/category_scraper/config.ts` or `config/index.ts`

```typescript
import { newRetailerScraperConfig } from './config/newretailer';

export function getConfigForRetailer(retailer: string): ScraperConfig {
  switch (retailer.toLowerCase()) {
    case 'clicks':
      return clicksScraperConfig;
    case 'dischem':
      return dischemScraperConfig;
    case 'faithful-to-nature':
    case 'faithfultonature':
      return faithfulToNatureScraperConfig;
    case 'wellnesswarehouse':
    case 'wellness-warehouse':
      return wellnessWarehouseScraperConfig;
    case 'newretailer':  // Add this
      return newRetailerScraperConfig;
    default:
      throw new Error(`Unknown retailer: ${retailer}`);
  }
}
```

#### 4.4 Update Orchestrator (if needed)

**File**: `src/scrappers/category_scraper/orchestrator/handlers/categoryExtractor.ts`

If your extractor uses the interface pattern, add it to the extraction logic:

```typescript
import { NewRetailerCategoryLinkExtractor } from '../../extractor/newretailer/categoryLinkExtractor';

// In the extraction method:
if (this.config.siteId === 'newretailer') {
  const extractor = new NewRetailerCategoryLinkExtractor();
  const categories = await extractor.extract(page, this.config, categoryInfo);
  return categories;
}
```

### Step 5: Add Database Mapping

**File**: `src/scrappers/category_scraper/config.ts` or database helpers

```typescript
export const RETAILER_NAME_TO_ID: Record<string, number> = {
  'clicks': 1,
  'dischem': 2,
  'faithful-to-nature': 3,
  'wellnesswarehouse': 4,
  'newretailer': 5  // Add this with next available ID
};
```

### Step 6: Test Your Implementation

#### 6.1 Enable Debug Mode

```bash
npm run scrape:c scrape --retailer newretailer --debug
```

#### 6.2 Check Logs

Monitor the logs for errors:
```bash
tail -f logs/category_scraper.log
```

#### 6.3 Verify Database

Check if categories were saved:
```sql
SELECT * FROM categories WHERE retailer_id = 5 ORDER BY depth, id;
```

#### 6.4 Common Issues and Solutions

**Issue**: Selectors not found
- **Solution**: Double-check selectors in DevTools, site may have changed

**Issue**: Cloudflare challenge not resolving
- **Solution**: Increase `cloudflareChallengeTimeout`, check anti-bot settings

**Issue**: Categories not hierarchical
- **Solution**: Verify `parentId` is set correctly in extractor

**Issue**: Duplicate categories
- **Solution**: Check URL normalization, ensure unique constraint in DB

### Step 7: Optimize and Refine

#### 7.1 Fine-tune Timeouts

Based on testing, adjust:
- `navigationTimeout`: How long to wait for page load
- `elementTimeout`: How long to wait for elements
- `delayBetweenRequests`: Prevent rate limiting

#### 7.2 Handle Edge Cases

- Empty category lists
- Categories without URLs
- Categories with generic names ("Click here", "View all")
- Pagination within category lists
- Dynamic loading (AJAX)

#### 7.3 Add Error Handling

```typescript
try {
  // Extraction logic
} catch (error) {
  logger.error(`[NewRetailer] Extraction failed:`, error);
  
  // Save debug snapshot
  const snapshot = await page.content();
  fs.writeFileSync(`debug_${Date.now()}.html`, snapshot);
  
  // Return empty array or throw based on criticality
  return [];
}
```

### Step 8: Document Your Implementation

Create a README for your retailer:

**File**: `src/scrappers/category_scraper/extractor/newretailer/README.md`

```markdown
# New Retailer Category Extractor

## Site Structure
- UI Pattern: Sidebar filter
- Hierarchy: 2 levels (L1 → L2)
- Dynamic loading: No

## Selectors
- Category list: `div.category-list`
- Category item: `div.category-card`
- Category name: `h3.category-name`
- Category URL: `a.category-link`

## Special Considerations
- Requires "See more" button click to show all categories
- URLs are relative, need baseUrl for normalization
- Some categories have product counts

## Known Issues
- None

## Testing
```bash
npm run scrape:c scrape --retailer newretailer --debug
```
```

## Complete Example: Adding "Example Pharmacy"

Let's walk through a complete example for a fictional retailer "Example Pharmacy".

### Site Analysis
- **URL**: https://www.examplepharmacy.com
- **Pattern**: Hover menu with dropdown
- **Hierarchy**: 3 levels
- **Selectors identified**:
  - Main nav: `nav.main-navigation`
  - Top-level items: `nav.main-navigation > ul > li`
  - Submenu: `div.mega-menu`
  - Category links: `div.mega-menu a.category-link`

### Configuration File

```typescript
// src/scrappers/category_scraper/config/examplepharmacy.ts

import { CategorySelectors, ScraperConfig } from "../types";
import { Retailer } from "../../shared/types";

export const examplePharmacyCategorySelectors: CategorySelectors = {
  TOP_LEVEL_MENU_ITEM: "nav.main-navigation > ul > li",
  TOP_LEVEL_MENU_ITEM_LINK: "a.nav-link",
  MAIN_NAV_FLYOUT_PANEL_SELECTOR: "div.mega-menu",
  
  CATEGORY_LIST_CONTAINER: "div.mega-menu",
  CATEGORY_ITEM: "div.category-column",
  CATEGORY_NAME_TEXT: "h4.category-title",
  CATEGORY_URL_ANCHOR: "a.category-link",
  
  expectedPageLoadedSelector: "nav.main-navigation"
};

export const examplePharmacyScraperConfig: ScraperConfig = {
  baseUrl: "https://www.examplepharmacy.com",
  siteId: "examplepharmacy",
  retailerId: Retailer.EXAMPLE_PHARMACY,
  categorySelectors: examplePharmacyCategorySelectors,
  maxDepth: 50,
  delayBetweenRequests: 2000,
  headless: "new",
  userAgent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
  viewport: { width: 1920, height: 1080 },
  useStealthPlugin: true,
  navigationTimeout: 60000,
  elementTimeout: 30000,
  checkpointFilePath: "./checkpoints/examplepharmacy_checkpoint.json",
  interactionConfig: {
    mainNavInteraction: "hover",
    delayAfterMainNavInteraction: 1000
  }
};
```

### Extractor Implementation

```typescript
// src/scrappers/category_scraper/extractor/examplepharmacy/categoryLinkExtractor.ts

import { Page } from 'puppeteer';
import { ScraperConfig, CategoryInfo } from '../../scraper/core/types';
import { ICategoryLinkExtractor } from '../../scraper/core/iCategoryLinkExtractor';
import { UrlParser } from '../urlParser';
import { categoryScraperLogger as logger } from '../../logging';

export class ExamplePharmacyCategoryLinkExtractor implements ICategoryLinkExtractor {
  async extract(
    page: Page,
    config: ScraperConfig,
    currentCategory?: CategoryInfo
  ): Promise<CategoryInfo[]> {
    const { categorySelectors, baseUrl, siteId, retailerId } = config;
    const extractedCategories: CategoryInfo[] = [];
    const urlParser = new UrlParser();
    let categoryIdCounter = Date.now();
    
    try {
      // Find all top-level menu items
      const topLevelItems = await page.$$(categorySelectors.TOP_LEVEL_MENU_ITEM);
      
      for (const topLevelItem of topLevelItems) {
        const topLevelLink = await topLevelItem.$(categorySelectors.TOP_LEVEL_MENU_ITEM_LINK);
        if (!topLevelLink) continue;
        
        // Get top-level name
        const topLevelName = await topLevelLink.evaluate(el => el.textContent?.trim());
        if (!topLevelName) continue;
        
        // Hover to reveal mega menu
        await topLevelLink.hover();
        await page.waitForTimeout(1000);
        
        // Check if mega menu appeared
        const megaMenu = await page.$(categorySelectors.MAIN_NAV_FLYOUT_PANEL_SELECTOR);
        if (!megaMenu) continue;
        
        // Extract categories from mega menu
        const categoryColumns = await megaMenu.$$(categorySelectors.CATEGORY_ITEM);
        
        for (const column of categoryColumns) {
          const nameElement = await column.$(categorySelectors.CATEGORY_NAME_TEXT);
          const urlElement = await column.$(categorySelectors.CATEGORY_URL_ANCHOR);
          
          const name = await nameElement?.evaluate(el => el.textContent?.trim());
          const url = await urlElement?.evaluate(el => (el as HTMLAnchorElement).href);
          
          if (!name || !url) continue;
          
          const absoluteUrl = urlParser.normalizeUrl(url, baseUrl);
          
          const categoryInfo: CategoryInfo = {
            id: `examplepharmacy-${name.toLowerCase().replace(/[^a-z0-9]+/g, '-')}-${categoryIdCounter++}`,
            name,
            url: absoluteUrl,
            parentId: null,  // Top-level for now
            depth: 0,
            siteId,
            retailerId,
            children: []
          };
          
          extractedCategories.push(categoryInfo);
        }
        
        // Move mouse away to close menu
        await page.mouse.move(0, 0);
        await page.waitForTimeout(500);
      }
      
      logger.info(`[ExamplePharmacy] Extracted ${extractedCategories.length} categories`);
      
    } catch (error) {
      logger.error('[ExamplePharmacy] Error in extractor:', error);
      throw error;
    }
    
    return extractedCategories;
  }
}
```

### Registration

```typescript
// Update Retailer enum
export enum Retailer {
  // ... existing retailers
  EXAMPLE_PHARMACY = 'examplepharmacy'
}

// Update config registry
export const RETAILER_CONFIGS = {
  // ... existing configs
  'examplepharmacy': EXAMPLE_PHARMACY_CONFIG
};

// Update ID mapping
export const RETAILER_NAME_TO_ID = {
  // ... existing mappings
  'examplepharmacy': 6
};
```

### Test

```bash
npm run scrape:c scrape --retailer examplepharmacy --debug
```

## Troubleshooting Checklist

- [ ] Selectors are correct and elements exist
- [ ] URLs are being normalized properly
- [ ] Parent-child relationships are set correctly
- [ ] Depth is calculated correctly
- [ ] No duplicate categories in database
- [ ] Cloudflare challenges are handled
- [ ] Logs show expected behavior
- [ ] Database contains categories after run

## Summary

Adding a new retailer involves:
1. **Analyze** the website structure
2. **Create** configuration file with selectors
3. **Implement** extractor logic
4. **Register** retailer in the system
5. **Test** and debug
6. **Optimize** timeouts and error handling
7. **Document** your implementation

With this guide, you should be able to add any new retailer to the category scraper system. The modular architecture makes it straightforward to extend without modifying core logic.
