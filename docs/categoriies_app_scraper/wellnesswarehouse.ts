import { CategorySelectors, ScraperConfig } from "../types";
import { Retailer } from "../../shared/types";

/**
 * Specific category selectors for the Wellness Warehouse site.
 * These selectors target the grid-based category layout with image tiles.
 */
export const wellnessWarehouseCategorySelectors: CategorySelectors = {
  // Main container for the category grid
  CATEGORY_LIST_CONTAINER: "div.iis340o.mgz-element-row .inner-content",
  
  // Individual category items (columns in the grid)
  CATEGORY_ITEM: "div[class*='mgz-element-column'].new-link",
  
  // Category name and URL (from the link)
  CATEGORY_NAME_TEXT: "p.fs-4 a.my-link",
  CATEGORY_URL_ANCHOR: "p.fs-4 a.my-link",
  
  // Category image is available in the same item container as the link
  // Can be accessed via: itemContainer.querySelector('img.mgz-hover-main')
  
  // Show more button (for lazy-loaded categories)
  SEE_MORE_BUTTON: "button#toggle-all-button",
  
  // Standard selectors (not all may be applicable)
  MAIN_NAV_TOP_LEVEL_LINK_PATTERN: "",
  MAIN_NAV_FLYOUT_PANEL_SELECTOR: "",
  MAIN_NAV_SUBLIST_CONTAINER: "",
  MAIN_NAV_SUB_ITEM: "",
  MAIN_NAV_SUB_NAME_TEXT: "",
  MAIN_NAV_SUB_URL_ANCHOR: "",
  CATEGORY_URL_INPUT: "",
  CATEGORY_PRODUCT_COUNT: "",
  SEE_LESS_BUTTON: "",
  EXPAND_CATEGORY_SECTION_TOGGLE: "",
};

/**
 * Configuration for the Wellness Warehouse category scraper.
 */
export const wellnessWarehouseScraperConfig: ScraperConfig = {
  // Base configuration
  baseUrl: "https://www.wellnesswarehouse.com",
  startUrl: "https://www.wellnesswarehouse.com/shop-by-solution",
  siteId: "wellnesswarehouse",
  retailerId: Retailer.WELLNESS_WAREHOUSE,
  
  // Category selection
  categorySelectors: wellnessWarehouseCategorySelectors,
  
  // Navigation and depth
  maxDepth: 2, // Adjust based on actual category depth
  
  // Rate limiting
  maxConcurrentRequests: 3,
  delayBetweenRequests: 1500, // 1.5 seconds between requests
  
  // Browser configuration
  headless: "new",
  userAgent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36",
  viewport: { width: 1920, height: 1080 },
  launchArgs: ["--no-sandbox", "--disable-setuid-sandbox"],
  useStealthPlugin: true,
  
  // Retry and timeout settings
  retryAttempts: 3,
  retryDelay: 5000, // 5 seconds
  pageLoadTimeout: 60000, // 60 seconds
  navigationTimeout: 60000, // 60 seconds
  elementTimeout: 30000, // 30 seconds
  
  // Checkpoint and state management
  checkpointFilePath: "./checkpoints/wellnesswarehouse_checkpoint.json",
  saveCheckpointCategoryCount: 10, // Save after every 10 categories
  saveCheckpointIntervalMs: 300000, // 5 minutes
  
  // Debugging and logging
  debugMode: false,
  logLevel: "info",
  saveSnapshotsOnError: true,
  snapshotDirectory: "./debug_snapshots/wellnesswarehouse",
  
  // Interaction configuration
  interactionConfig: {
    mainNavInteraction: "click", // Default interaction type
    delayAfterMainNavInteraction: 1000, // 1 second delay after interaction
  },
};
