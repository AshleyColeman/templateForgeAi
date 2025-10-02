# Category Scraper Architecture

## System Overview

The category scraper is built with a modular, layered architecture that separates concerns and allows for easy extension and maintenance.

```
┌─────────────────────────────────────────────────────┐
│                   CLI Layer                          │
│  (cli.ts, cli/index.ts)                             │
│  • Command parsing                                   │
│  • Mode selection                                    │
│  • Worker management                                 │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────┐
│              Execution Modes                         │
├──────────────────────────────────────────────────────┤
│  Legacy Mode        Enhanced Mode      Queue Mode    │
│  (legacy/scraper)   (Enhanced...)      (modules/...) │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────┐
│              Core Components                         │
├──────────────────────────────────────────────────────┤
│  • ScraperRunner    • CategoryOrchestrator           │
│  • QueueManager     • PageNavigator                  │
│  • Extractors       • BrowserManager                 │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────┐
│         Data Access & Persistence                    │
│  • Database queries                                  │
│  • Checkpoint handler                                │
│  • Queue manager                                     │
└─────────────────────────────────────────────────────┘
```

## Directory Structure

```
src/scrappers/category_scraper/
├── cli.ts                                # Main CLI entry point
├── cli-worker.ts                         # Legacy worker process
├── worker.ts                             # Enhanced worker process
├── scraper.ts                            # Main scraper orchestration
│
├── cli/
│   └── index.ts                          # CLI commands implementation
│
├── legacy/
│   └── scraper.ts                        # Legacy single-threaded scraper
│
├── modules/
│   ├── queueBasedScraper.ts              # Queue-based scraper
│   └── singleThreadScraper.ts            # Single-threaded variant
│
├── scraper/
│   └── core/
│       ├── runner.ts                     # Main scraping loop
│       ├── types.ts                      # TypeScript interfaces
│       ├── iCategoryLinkExtractor.ts     # Extractor interface
│       └── runner/
│           ├── queue_manager.ts          # In-memory queue
│           ├── initializer.ts            # Initialization logic
│           ├── checkpoint_manager.ts     # Checkpoint handling
│           ├── category_processor.ts     # Category processing
│           ├── error_manager.ts          # Error handling
│           └── status_updater.ts         # Status updates
│
├── orchestrator/
│   ├── index.ts                          # Category orchestrator
│   └── handlers/
│       ├── navigationHandler.ts          # Page navigation
│       ├── flyoutHandler.ts              # Flyout interaction
│       └── categoryExtractor.ts          # Category extraction
│
├── extractor/
│   ├── index.ts                          # Extractor exports
│   ├── pageNavigator.ts                  # Page navigation utilities
│   ├── browserManager.ts                 # Browser lifecycle
│   ├── urlParser.ts                      # URL normalization
│   ├── errorHandler.ts                   # Error handling
│   ├── debugUtils.ts                     # Debugging tools
│   │
│   ├── clicks/
│   │   └── categoryLinkExtractor.ts      # Clicks-specific logic
│   ├── dischem/
│   │   └── dischemCategoryLinkExtractor.ts
│   ├── faithfultonature/
│   │   └── categoryLinkExtractor.ts
│   └── wellnesswarehouse/
│       └── categoryLinkExtractor.ts
│
├── config/
│   ├── concurrency.json                  # Worker configuration
│   ├── retailerConfig.ts                 # Centralized config
│   ├── clicks.ts                         # Clicks selectors
│   ├── dischem.ts                        # Dis-Chem selectors
│   ├── faithfultonature.ts               # FTN selectors
│   └── wellnesswarehouse.ts              # WW selectors
│
├── db/
│   ├── connection.ts                     # Database connection
│   ├── queries.ts                        # Query functions
│   ├── category/                         # Category operations
│   └── helpers/                          # Helper functions
│
├── queue/
│   └── CategoryQueueManager.ts           # Database queue manager
│
├── signal_handler/
│   ├── index.ts                          # Signal handling
│   └── error_handler.ts                  # Error coordination
│
├── utils/
│   └── memoryMonitor.ts                  # Memory monitoring
│
├── types.ts                              # Global type definitions
├── constants.ts                          # Constants
├── logging.ts                            # Logger configuration
├── checkpointHandler.ts                  # Checkpoint logic
└── EnhancedConcurrentCategoryManager.ts  # Multi-worker manager
```

## Core Components

### 1. CLI Layer

#### `cli.ts` (Main Entry Point)
**Responsibilities**:
- Parse command-line arguments
- Validate retailer selection
- Route to appropriate execution mode
- Manage worker processes (Enhanced mode)
- Handle graceful shutdown

**Key Functions**:
```typescript
// Main CLI entry
program
  .command('scrape')
  .option('--retailer <name>', 'Retailer to scrape')
  .option('--mode <mode>', 'Execution mode')
  .action(async (options) => {
    // Route to appropriate scraper
  });
```

#### `cli/index.ts`
**Responsibilities**:
- Interactive menu interface
- Enhanced/Queue mode launchers
- Monitor mode implementation

### 2. Execution Modes

#### Legacy Mode: `legacy/scraper.ts`
**Function**: `runCategoryScraper(retailer, options)`

**Flow**:
1. Initialize configuration
2. Launch browser
3. Create ScraperRunner
4. Process categories sequentially
5. Save checkpoints periodically

**Pros**:
- Simple, easy to debug
- Checkpoint-based resume
- Lower memory usage

**Cons**:
- Slower (single-threaded)
- No parallelization

#### Enhanced Mode: `EnhancedConcurrentCategoryManager.ts`
**Class**: `EnhancedConcurrentCategoryManager`

**Flow**:
1. Initialize queue from database
2. Spawn multiple worker processes
3. Workers pull tasks from database queue
4. Coordinate task assignment
5. Monitor worker health

**Pros**:
- Fast (multi-worker)
- Scalable
- Fault-tolerant

**Cons**:
- Higher memory usage
- More complex debugging

#### Queue Mode: `modules/queueBasedScraper.ts`
**Class**: `CategoryQueueBasedScraper`

**Flow**:
1. Connect to database queue
2. Pull tasks one at a time
3. Process and mark complete
4. Automatic retry on failure

**Pros**:
- Balanced performance
- Database-backed
- Easy to monitor

**Cons**:
- Not as fast as Enhanced mode

### 3. Scraper Core

#### `scraper/core/runner.ts`
**Class**: `ScraperRunner`

**Main Responsibilities**:
- Orchestrate the scraping process
- Manage category queue
- Handle initialization and checkpoints
- Coordinate specialized modules

**Key Methods**:
```typescript
class ScraperRunner {
  async initialize(): Promise<void>
  async run(): Promise<void>
  async saveCheckpoint(): Promise<void>
  getCategoryQueue(): CategoryInfo[]
  getProcessedUrls(): Set<string>
}
```

**Specialized Modules**:
- **QueueManager**: In-memory queue management
- **Initializer**: Initial category setup
- **CheckpointManager**: Checkpoint save/restore
- **CategoryProcessor**: Process individual categories
- **ErrorManager**: Error handling strategies
- **StatusUpdater**: Database status updates

#### `orchestrator/index.ts`
**Class**: `CategoryOrchestrator`

**Responsibilities**:
- Process a single category
- Navigate to category page
- Interact with flyout menus
- Extract subcategories
- Handle errors gracefully

**Flow**:
```typescript
async processCategory(categoryInfo, page) {
  // 1. Navigate to category page
  await navigationHandler.navigateToCategory(page, categoryInfo);
  
  // 2. Interact with flyout menu
  const flyout = await flyoutHandler.interactWithFlyout(page, categoryInfo);
  
  // 3. Extract subcategories
  const subcategories = await categoryExtractor.extractSubcategories(
    page, 
    categoryInfo, 
    flyout
  );
  
  // 4. Return discovered subcategories
  return subcategories;
}
```

### 4. Extractor Layer

#### `extractor/pageNavigator.ts`
**Class**: `PageNavigator`

**Responsibilities**:
- Navigate to URLs with retry logic
- Handle Cloudflare challenges
- Detect and bypass bot protection
- Cookie consent automation
- Set user agents and viewports

**Key Methods**:
```typescript
class PageNavigator {
  async navigateToUrl(page: Page, url: string): Promise<void>
  async performAntiBotChecks(page: Page): Promise<void>
  async waitForSelector(page: Page, selector: string): Promise<ElementHandle>
  async click(page: Page, selector: string): Promise<void>
  async scrollPageToBottom(page: Page): Promise<void>
}
```

**Anti-Bot Features**:
- Cloudflare challenge detection
- Challenge resolution with polling
- Realistic delays and timeouts
- User-agent spoofing
- HTTP header customization

#### `extractor/browserManager.ts`
**Class**: `BrowserManager`

**Responsibilities**:
- Launch Puppeteer browser
- Configure stealth plugin
- Manage browser lifecycle
- Handle browser shutdown

**Key Methods**:
```typescript
class BrowserManager {
  async launch(options: BrowserLaunchOptions): Promise<Browser>
  getBrowserInstance(): Browser | null
  async shutdown(): Promise<void>
}
```

### 5. Retailer-Specific Extractors

Each retailer has a custom extractor that implements the extraction logic specific to that site's structure.

#### Common Pattern: `ICategoryLinkExtractor` Interface

```typescript
interface ICategoryLinkExtractor {
  extract(
    page: Page,
    config: ScraperConfig,
    currentCategory?: CategoryInfo
  ): Promise<CategoryInfo[]>;
}
```

#### Clicks Extractor: `extractor/clicks/categoryLinkExtractor.ts`

**Strategy**: Sidebar filter interaction

**Process**:
1. Click "See more" button to expand all categories
2. Extract category items from sidebar list
3. Parse category name, URL, product count
4. Handle nested categories

**Key Selectors**:
```typescript
MAIN_NAV_SUBLIST_CONTAINER: "div.facetValues ul.facet_block"
MAIN_NAV_SUB_ITEM: "li"
MAIN_NAV_SUB_NAME_TEXT: 'span[id^="facetName_"]'
```

#### Dis-Chem Extractor: `extractor/dischem/dischemCategoryLinkExtractor.ts`

**Strategy**: Multi-strategy extraction

**Strategies (in order)**:
1. **Sidebar strategy**: Extract from sidebar category list
2. **Dropdown menu strategy**: Extract from multi-column dropdown
3. **Fallback**: Other strategies as needed

**Key Features**:
- Smart name derivation from URLs
- Generic name detection and replacement
- Group category handling
- Prevents duplicate categories

#### Faithful to Nature Extractor: `extractor/faithfultonature/categoryLinkExtractor.ts`

**Strategy**: Hover menu with explicit L1/L2 classification

**Process**:
1. Find all top-level menu items (L0)
2. Hover over each L0 item
3. Wait for submenu panel to appear
4. Extract L1 categories (marked with `.level1` class)
5. Extract L2 categories (following L1 in same column)
6. Maintain parent-child relationships

**Key Features**:
- Explicit L1/L2 classification
- Column-based extraction
- Mouse movement to reset hover state
- Robust timeout handling

#### Wellness Warehouse Extractor: `extractor/wellnesswarehouse/categoryLinkExtractor.ts`

**Strategy**: Grid-based category cards

**Process**:
1. Handle "Show More" button if present
2. Wait for category items to load
3. Extract name, URL, and image from each card
4. Calculate depth based on parent category

**Key Features**:
- Image URL extraction
- Simple card-based layout
- Optional "Show More" handling

### 6. Configuration System

#### `config/retailerConfig.ts`
**Centralized Configuration**

Eliminates hardcoded retailer checks throughout the codebase.

**Structure**:
```typescript
interface RetailerScraperConfig {
  retailerId: string;
  displayName: string;
  baseUrl: string;
  antiBotConfig: AntiBotConfig;
  navigationTimeout: number;
  elementTimeout: number;
  requestDelay: number;
  maxRetries: number;
  hasAggressiveAntiBot: boolean;
}
```

**Registry**:
```typescript
const RETAILER_CONFIGS: Record<string, RetailerScraperConfig> = {
  'clicks': CLICKS_CONFIG,
  'dischem': DISCHEM_CONFIG,
  'faithful-to-nature': FAITHFUL_TO_NATURE_CONFIG,
  'wellnesswarehouse': WELLNESS_WAREHOUSE_CONFIG
};
```

**Helper Functions**:
```typescript
getRetailerConfig(retailerId: string): RetailerScraperConfig
getCloudflareTimeout(retailerId: string): number
hasAggressiveAntiBot(retailerId: string): boolean
getAllRetailerIds(): string[]
```

#### Per-Retailer Configurations

Example: `config/clicks.ts`

```typescript
export const clicksScraperConfig: ScraperConfig = {
  baseUrl: "https://clicks.co.za",
  siteId: "clicks",
  retailerId: Retailer.CLICKS,
  categorySelectors: clicksCategorySelectors,
  maxDepth: 50,
  headless: "new",
  cloudflareChallengeTimeout: 120000,
  navigationTimeout: 90000,
  elementTimeout: 60000,
  // ... more settings
};
```

### 7. Data Access Layer

#### Database Operations

**Location**: `db/` directory

**Categories**:
```typescript
// Save a category
await saveCategory(categoryInfo);

// Update category status
await updateCategoryStatus(categoryId, 'completed');

// Find category by URL
const category = await findCategoryByUrl(url, retailerId);

// Get pending categories
const pending = await getPendingCategories(retailerId, siteId);
```

#### Checkpoint Handler

**Location**: `checkpointHandler.ts`

**Responsibilities**:
- Save scraping progress to file
- Load and restore from checkpoint
- Detect checkpoint corruption

**Checkpoint Structure**:
```typescript
interface ScraperCheckpoint {
  retailerId: string;
  siteId: string;
  timestamp: number;
  currentCategory: CategoryInfo | null;
  queue: CategoryInfo[];
  processedUrls: string[];
  categoriesProcessed: number;
}
```

### 8. Queue Management

#### `queue/CategoryQueueManager.ts`
**Class**: `CategoryQueueManager`

**Responsibilities**:
- Manage database-backed task queue
- Atomic task assignment to workers
- Track task status and retries
- Handle task failures

**Key Methods**:
```typescript
class CategoryQueueManager {
  async getNextTask(workerId: string, retailerId: number): Promise<Task>
  async markTaskCompleted(taskId: number): Promise<void>
  async markTaskFailed(taskId: number, error: string): Promise<void>
  async resetQueue(retailerId: number): Promise<void>
  async getQueueStats(): Promise<QueueStats>
}
```

### 9. Error Handling

#### `extractor/errorHandler.ts`
**Class**: `ErrorHandler`

**Responsibilities**:
- Classify errors by type
- Implement retry strategies
- Save debug snapshots on error
- Log error details

**Error Types**:
- **Network errors**: Timeout, connection refused
- **Selector errors**: Element not found
- **Bot detection**: Cloudflare challenge
- **Business logic errors**: Invalid data

**Retry Strategy**:
```typescript
interface RetryConfig {
  maxAttempts: 3;
  backoff: exponential;  // 5s, 10s, 20s
  retryableErrors: [
    'TimeoutError',
    'NetworkError',
    'BotDetectionError'
  ];
}
```

### 10. Logging System

#### `logging.ts`
**Centralized Logger**: `categoryScraperLogger`

**Configuration**:
```typescript
const categoryScraperLogger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  transports: [
    new winston.transports.File({ 
      filename: 'logs/category_scraper.log' 
    }),
    new winston.transports.Console({
      format: winston.format.simple()
    })
  ]
});
```

**Usage**:
```typescript
import { categoryScraperLogger as logger } from './logging';

logger.info('Category processing started', { categoryId });
logger.warn('Selector not found', { selector });
logger.error('Navigation failed', { error, url });
logger.debug('Flyout interaction', { flyoutSelector });
```

## Data Flow Diagram

### Complete End-to-End Flow

```
┌─────────────────────┐
│ User runs CLI       │
│ npm run scrape:c    │
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│ cli.ts              │
│ • Parse arguments   │
│ • Load config       │
│ • Select mode       │
└──────────┬──────────┘
           │
     ┌─────┴─────┐
     │           │
┌────▼────┐ ┌───▼────┐
│ Legacy  │ │Enhanced│
│  Mode   │ │  Mode  │
└────┬────┘ └───┬────┘
     │          │
     │     ┌────▼────────────┐
     │     │ Spawn Workers   │
     │     │ worker.ts × N   │
     │     └────┬────────────┘
     │          │
┌────▼──────────▼────┐
│ ScraperRunner      │
│ • initialize()     │
│ • run()            │
└────────┬───────────┘
         │
┌────────▼───────────┐
│ Initialize         │
│ • Load checkpoint  │
│ • Setup queue      │
│ • Get categories   │
└────────┬───────────┘
         │
┌────────▼───────────┐
│ Main Loop          │
│ while (queue) {    │
│   processCategory()│
│ }                  │
└────────┬───────────┘
         │
┌────────▼───────────┐
│ CategoryProcessor  │
│ • Get next cat     │
│ • Call orchestrator│
│ • Save results     │
└────────┬───────────┘
         │
┌────────▼───────────┐
│ Orchestrator       │
│ • Navigate         │
│ • Interact flyout  │
│ • Extract subs     │
└────────┬───────────┘
         │
┌────────▼───────────┐
│ Extractor          │
│ • Clicks           │
│ • Dischem          │
│ • FTN              │
│ • WW               │
└────────┬───────────┘
         │
┌────────▼───────────┐
│ Database           │
│ • Save categories  │
│ • Update status    │
│ • Store hierarchy  │
└────────────────────┘
```

## Component Interaction Patterns

### Pattern 1: Category Processing

```
CategoryProcessor
  ↓ calls
CategoryOrchestrator.processCategory()
  ↓ uses
NavigationHandler.navigateToCategory()
  ↓ uses
PageNavigator.navigateToUrl()
  ↓ handles
Anti-bot checks, Cloudflare, cookies
  ↓ then
FlyoutHandler.interactWithFlyout()
  ↓ extracts
CategoryExtractor.extractSubcategories()
  ↓ delegates to
Retailer-specific extractor
  ↓ returns
CategoryInfo[]
  ↓ saved by
Database operations
```

### Pattern 2: Error Handling Flow

```
Error occurs in extractor
  ↓
ErrorHandler catches error
  ↓
Classify error type
  ↓
Is error retryable?
  ├─ Yes → Retry with backoff
  └─ No  → Log and skip
  ↓
Save debug snapshot
  ↓
Update category status
  ↓
Continue with next category
```

### Pattern 3: Checkpoint Flow

```
Main loop running
  ↓
Process N categories
  ↓
Check if checkpoint needed
  ├─ By count (e.g., every 20 cats)
  └─ By time (e.g., every 60s)
  ↓
Create checkpoint object
  ↓
Serialize to JSON
  ↓
Save to file
  ↓
Continue processing
```

## Performance Characteristics

### Legacy Mode
- **Throughput**: ~3-5 categories/min
- **Memory**: ~300 MB
- **CPU**: ~40%
- **Browsers**: 1

### Enhanced Mode (4 workers)
- **Throughput**: ~12-20 categories/min
- **Memory**: ~1-2 GB
- **CPU**: ~200% (multi-core)
- **Browsers**: 4 (one per worker)

### Queue Mode
- **Throughput**: ~5-8 categories/min
- **Memory**: ~400 MB
- **CPU**: ~60%
- **Browsers**: 1

## Extension Points

### Adding a New Retailer

1. **Create config file**: `config/newretailer.ts`
2. **Create extractor**: `extractor/newretailer/categoryLinkExtractor.ts`
3. **Update registry**: Add to `RETAILER_CONFIGS`
4. **Test and iterate**: Run in debug mode

See **02_How_To_Add_Retailer.md** for detailed guide.

### Adding a New Extraction Strategy

1. **Implement interface**: `ICategoryLinkExtractor`
2. **Add to orchestrator**: Update fallback logic
3. **Test**: Verify on target site

### Customizing Anti-Bot Handling

1. **Update `pageNavigator.ts`**: Add detection logic
2. **Configure per-retailer**: Set timeout, delays
3. **Test**: Verify challenge resolution

## Summary

The category scraper is a sophisticated, modular system designed for reliability and extensibility. Its layered architecture separates concerns, making it easy to:
- Add new retailers
- Customize extraction logic
- Handle errors gracefully
- Scale horizontally
- Debug effectively

The combination of multiple execution modes, robust error handling, and flexible configuration makes it suitable for both development and production use.
