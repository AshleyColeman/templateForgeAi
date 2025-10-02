import { CategorySelectors, ScraperConfig } from "../types";
import { Retailer } from "../../shared/types";

export const clicksCategorySelectors: CategorySelectors = {
  // Selectors for sidebar category filters (the actual structure on the page)
  MAIN_NAV_TOP_LEVEL_LINK_PATTERN:
    "a.refinementToggle[title='Hide Refinement']", // The "Category" link at the top of the filter
  MAIN_NAV_FLYOUT_PANEL_SELECTOR: "div.panel.panel-default.bg-white", // The panel containing the categories
  MAIN_NAV_SUBLIST_CONTAINER: "div.facetValues ul.facet_block", // The <ul> containing category items
  MAIN_NAV_SUB_ITEM: "li", // Category list items
  MAIN_NAV_SUB_NAME_TEXT: 'span[id^="facetName_"]', // The span containing the category name
  MAIN_NAV_SUB_URL_ANCHOR: "label.facet_block-label", // The label that can be clicked for navigation

  // Important selectors for extracting data
  CATEGORY_LIST_CONTAINER: "div.facetValues ul.facet_block", // The ul containing all category items
  CATEGORY_ITEM: "li", // Each category list item
  CATEGORY_NAME_TEXT: 'span[id^="facetName_"]', // The span with category name
  CATEGORY_LINK_SELECTOR: ".category-item__link", // Selector for the direct category link
  // Wait for the actual facet list to be present instead of relying on body class
  expectedPageLoadedSelector: "div.facetValues ul.facet_block",
  CATEGORY_URL_ANCHOR: "label.facet_block-label", // The clickable label
  CATEGORY_URL_INPUT: "input.hidden-lg.hidden-sm.hidden-xs.hidden-md", // Hidden input containing the category URL
  CATEGORY_PRODUCT_COUNT: "span.facetcountDiv.facetValueCount", // Span containing product count

  // Buttons for expanding/collapsing category lists
  SEE_MORE_BUTTON: "button.read-more-facet", // "See more" button to show more categories
  SEE_LESS_BUTTON: "button.read-less-facet", // "See less" button to collapse category list
  EXPAND_CATEGORY_SECTION_TOGGLE: "a.refinementToggle", // Toggle to expand/collapse category section
};

export const clicksScraperConfig: ScraperConfig = {
  baseUrl:
    "https://clicks.co.za/products/c/OH1?q=%3Arelevance%3Acategory%3AOH10010&text=&count=12",
  siteId: "clicks",
  startUrl: undefined,
  targetCategory: { name: "Toiletries" },
  retailerId: Retailer.CLICKS,
  categorySelectors: clicksCategorySelectors,
  maxDepth: 50,
  maxProductsPerCategory: 0,
  maxConcurrentRequests: 5,
  delayBetweenRequests: 1000,
  headless: "new",
  userAgent:
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36",
  viewport: { width: 1920, height: 1080 },
  launchArgs: ["--no-sandbox", "--disable-setuid-sandbox"],
  useStealthPlugin: true,
  cloudflareChallengeTimeout: 120000, // 2 minutes
  retryAttempts: 3,
  retryDelay: 5000,
  // Increase timeouts to accommodate slower loads observed recently
  pageLoadTimeout: 90000,
  navigationTimeout: 90000,
  elementTimeout: 60000,
  checkpointFilePath: "./checkpoints/clicks_checkpoint.json",
  saveCheckpointIntervalMs: 60000,
  saveCheckpointCategoryCount: 20,
  debugMode: false,
  logLevel: "info",
  saveSnapshotsOnError: false,
  snapshotDirectory: "./debug_snapshots/clicks",
  interactionConfig: {
    mainNavInteraction: "click",
    mainNavTriggerSelectorPattern: "ul.nav-list > li.La.parent > a",
    mainNavFlyoutPanelToWaitFor: "section",
    delayAfterMainNavInteraction: 3000,
  },
};
