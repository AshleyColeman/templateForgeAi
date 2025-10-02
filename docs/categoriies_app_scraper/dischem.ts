import { DischemCategorySelectors, DischemScraperConfig } from "../types";
import { Retailer } from "../../shared/types";

export const dischemCategorySelectors: DischemCategorySelectors = {
  CATEGORY_LIST_CONTAINER: 'div.sub-navigation.sub-nav-desktop ul.menu-items',
  CATEGORY_ITEM: 'li.menu-item', // Selector for an individual category item
  SUB_CATEGORY_SELECTOR: ".sub-category-item a",
  expectedPageLoadedSelector: "main#maincontent", // Main content area for Dischem pages
  CATEGORY_LINK_ANCHOR: 'a',
  // Selectors for Clicks that are not applicable to Dischem, kept for interface compatibility
  MAIN_NAV_TOP_LEVEL_LINK_PATTERN: '',
  MAIN_NAV_FLYOUT_PANEL_SELECTOR: '',
  MAIN_NAV_SUBLIST_CONTAINER: '',
  MAIN_NAV_SUB_ITEM: '',
  MAIN_NAV_SUB_NAME_TEXT: '',
  MAIN_NAV_SUB_URL_ANCHOR: '',
  CATEGORY_PRODUCT_COUNT: '',
  SEE_MORE_BUTTON: '',
  SEE_LESS_BUTTON: '',
  EXPAND_CATEGORY_SECTION_TOGGLE: '',

  // Updated selectors for Dischem Brand Page Carousels (e.g., Avene page, 'bp-carousel' type)
  BRAND_PAGE_CAROUSEL_BLOCK: 'div.bp-brands-block', // The main widget block for the carousel
  BRAND_PAGE_CAROUSEL_ITEMS_CONTAINER: 'div.bp-carousel', // The container holding the sliding items
  BRAND_PAGE_CAROUSEL_ITEM: 'div.inline-bp[data-thumb-alt], p[data-thumb-alt]', // Updated to support both div and p
  BRAND_PAGE_CAROUSEL_ITEM_LINK: 'a', // The link is directly inside the <p> item
  BRAND_PAGE_CAROUSEL_ITEM_NAME_SELECTOR: 'img', // Name might be on the title of the <img> tag inside the <a>
  BRAND_PAGE_CAROUSEL_NEXT_BUTTON: 'a.flex-next', // The 'Next' button for carousel pagination

  // Selectors for 'v-navigation' type menus (e.g., Almay brand page)
  V_NAVIGATION_CONTAINER: 'div.nav-container ul.v-navigation',
  V_NAVIGATION_ITEM: 'li.v-navigation__item.category-item', 
  V_NAVIGATION_LINK_ANCHOR: 'a.v-navigation__link',
};

export const dischemScraperConfig: DischemScraperConfig = {
  baseUrl: "https://www.dischem.co.za",
  startUrl: "https://www.dischem.co.za/shop-by-department",
  siteId: "dischem",
  retailerId: Retailer.DISCHEM, 
  categorySelectors: dischemCategorySelectors,
  maxDepth: 3, 
  maxProductsPerCategory: 0,
  maxConcurrentRequests: 3,
  delayBetweenRequests: 2000,
  headless: "new",
  userAgent:
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36",
  viewport: { width: 1920, height: 1080 },
  launchArgs: ["--no-sandbox", "--disable-setuid-sandbox"],
  useStealthPlugin: true,
  cloudflareChallengeTimeout: 120000, // 2 minutes
  retryAttempts: 3,
  retryDelay: 7000,
  pageLoadTimeout: 90000,
  navigationTimeout: 90000,
  elementTimeout: 45000,
  checkpointFilePath: "./checkpoints/dischem_checkpoint.json",
  saveCheckpointCategoryCount: 5,
  saveCheckpointIntervalMs: 300000, // Save every 5 minutes
  debugMode: false,
  logLevel: "info",
  saveSnapshotsOnError: true,
  snapshotDirectory: "./debug_snapshots/dischem",
  interactionConfig: {
    mainNavInteraction: "none",
    mainNavTriggerSelectorPattern: "", 
    mainNavFlyoutPanelToWaitFor: "",
    delayAfterMainNavInteraction: 0,
  },
};
