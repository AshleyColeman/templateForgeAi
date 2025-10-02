import { FaithfulToNatureCategorySelectors, FaithfulToNatureScraperConfig } from "../types";
import { Retailer } from "../../shared/types";

export const faithfulToNatureCategorySelectors: FaithfulToNatureCategorySelectors = {
  // Top-level navigation menu (e.g., "Food", "Health")
  TOP_LEVEL_MENU_CONTAINER: "ul#ms-topmenu",
  TOP_LEVEL_MENU_ITEM: "li.ms-level0",
  TOP_LEVEL_MENU_ITEM_LINK: "a.ms-label",

  // Submenu that appears on hover/interaction with a top-level item
  SUBMENU_PANEL: "div.ms-submenu",
  SUBMENU_COLUMN_LAYOUT_CONTAINER: "div.ms-content > div.ms-maincontent > div.row.ms-category",
  SUBMENU_INDIVIDUAL_COLUMN: "div.col-category",

  // Category links within the submenu columns
  LEVEL_1_CATEGORY_ANCHOR: "a.form-group.level1",
  GENERAL_SUB_CATEGORY_ANCHOR: "a.form-group",

  // --- Standard/Common Selectors (from base CategorySelectors) ---
  MAIN_NAV_TOP_LEVEL_LINK_PATTERN: "", // Not directly used in the same way as Clicks
  MAIN_NAV_FLYOUT_PANEL_SELECTOR: "",  // Covered by SUBMENU_PANEL
  MAIN_NAV_SUBLIST_CONTAINER: "",     // Covered by SUBMENU_COLUMN_LAYOUT_CONTAINER and SUBMENU_INDIVIDUAL_COLUMN
  MAIN_NAV_SUB_ITEM: "",              // Covered by LEVEL_1_CATEGORY_ANCHOR and GENERAL_SUB_CATEGORY_ANCHOR
  MAIN_NAV_SUB_NAME_TEXT: "",         // Name is part of the anchor text
  MAIN_NAV_SUB_URL_ANCHOR: "",        // URL is part of the anchor href
  CATEGORY_LIST_CONTAINER: "",        // Specific structure, not a generic list
  CATEGORY_ITEM: "",                  // Specific structure
  CATEGORY_NAME_TEXT: "",             // Name is part of the anchor text
  CATEGORY_URL_INPUT: "",             // No hidden input for URL observed
  CATEGORY_URL_ANCHOR: "",            // Covered by specific anchors
  CATEGORY_PRODUCT_COUNT: "",         // No product count observed in nav
  SEE_MORE_BUTTON: "",                // No "see more" observed in this nav structure
  SEE_LESS_BUTTON: "",                // No "see less" observed
  EXPAND_CATEGORY_SECTION_TOGGLE: "", // No general expand toggle observed
};

export const faithfulToNatureScraperConfig: FaithfulToNatureScraperConfig = {
  baseUrl: "https://www.faithful-to-nature.co.za",
  startUrl: "https://www.faithful-to-nature.co.za/", 
  siteId: "faithfultonature",
  retailerId: Retailer.FAITHFUL_TO_NATURE,
  
  categorySelectors: faithfulToNatureCategorySelectors,
  
  maxDepth: 3, 
  
  maxConcurrentRequests: 3,
  delayBetweenRequests: 1500,

  headless: "new",
  userAgent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36",
  viewport: { width: 1920, height: 1080 },
  launchArgs: ["--no-sandbox", "--disable-setuid-sandbox"],
  useStealthPlugin: true,

  retryAttempts: 3,
  retryDelay: 5000,
  pageLoadTimeout: 60000,
  navigationTimeout: 60000,
  elementTimeout: 30000,

  checkpointFilePath: "./checkpoints/faithfultonature_checkpoint.json",
  saveCheckpointCategoryCount: 10, 
  saveCheckpointIntervalMs: 300000, 

  debugMode: false,
  logLevel: "info",
  saveSnapshotsOnError: false,
  snapshotDirectory: "./debug_snapshots/faithfultonature",

  interactionConfig: {
    mainNavInteraction: "hover", 
    mainNavTriggerSelectorPattern: faithfulToNatureCategorySelectors.TOP_LEVEL_MENU_ITEM_LINK,
    mainNavFlyoutPanelToWaitFor: faithfulToNatureCategorySelectors.SUBMENU_PANEL,
    delayAfterMainNavInteraction: 500, 
  },
};
