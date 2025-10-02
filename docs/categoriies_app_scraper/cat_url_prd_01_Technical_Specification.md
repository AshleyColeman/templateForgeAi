# Technical Specification: scrape:cp Module

## System Entry Point

### CLI Entry Point: `src/scrappers/category_url_products/cli.ts`

**Purpose**: Main entry point for category URL products scraper

**Responsibilities**:
- Command-line argument parsing (Commander.js)
- Interactive menu interface (Inquirer.js)
- Retailer validation
- Mode selection (Enhanced/Legacy/Queue)
- Process spawning for concurrent execution
- Graceful shutdown handling

**Key Command Structure**:
```bash
# Interactive mode
npm run scrape:cp

# Direct scraping
npm run scrape:cp scrape --retailer <retailer-name>

# List retailers
npm run scrape:cp list
```

## Module Architecture

### Directory Structure

```
src/scrappers/category_url_products/
├── cli.ts                                    # Main CLI entry point
├── cli-worker.ts                             # Legacy worker (IPC)
├── worker.ts                                 # Queue-based worker (Enhanced mode)
│
├── cli/
│   └── index.ts                              # CLI commands implementation
│
├── legacy/
│   └── scraper.ts                            # Legacy single-threaded scraper
│
├── modules/
│   └── queueBasedScraper.ts                  # Queue-based scraper
│
├── EnhancedConcurrentCategoryUrlProductsManager.ts  # Multi-worker manager
│
├── orchestrator.ts                           # Main product extraction orchestrator
├── categoryProcessor.ts                      # Single category processing logic
├── categoryLoop.ts                           # Category iteration loop
├── runner.ts                                 # Scraper runner coordination
├── scraper.ts                                # Scraper entry/wrapper
│
├── config/
│   ├── index.ts                              # Config aggregator
│   ├── clicks/                               # Clicks-specific selectors
│   ├── dischem/                              # Dis-Chem selectors
│   ├── faithfulToNature/                     # Faithful to Nature selectors
│   └── wellnessWarehouse/                    # Wellness Warehouse selectors
│
├── extractor/
│   ├── index.ts                              # Main extractor entry
│   ├── productLinkExtractor.ts               # Generic product link extraction
│   ├── pageNavigator.ts                      # Page navigation & anti-bot
│   ├── urlParser.ts                          # URL parsing/normalization
│   ├── errorHandler.ts                       # Error handling strategies
│   ├── debugUtils.ts                         # Debugging utilities
│   ├── retailerExtractors.ts                 # Retailer extractor factory
│   │
│   ├── common/
│   │   └── baseExtractor.ts                  # Base extractor class
│   │
│   ├── retailers/
│   │   ├── clicks/
│   │   │   └── clicksExtractor.ts
│   │   ├── dischem/
│   │   │   └── dischemExtractor.ts
│   │   ├── faithfulToNature/
│   │   │   ├── productExtractor.ts
│   │   │   ├── paginationHandler.ts
│   │   │   ├── debugUtils.ts
│   │   │   └── utils/cloudflare/            # Cloudflare challenge solvers
│   │   │       ├── solver.ts
│   │   │       └── handlers/
│   │   │           └── RecaptchaHandler.ts
│   │   └── wellnessWarehouse/
│   │       └── wellnessWarehouseExtractor.ts
│   │
│   └── helpers/
│       └── extractionHelpers.ts
│
├── repositories/
│   ├── categoryRepository.ts                 # Category data access
│   ├── productRepository.ts                  # Product URL data access
│   └── index.ts
│
├── queue/
│   └── CategoryUrlProductsQueueManager.ts    # Database queue management
│
├── db/
│   └── connection.ts                         # Database connection
│
├── db_handler.ts                             # Database operations wrapper
├── checkpoint_handler.ts                     # Checkpoint save/load
│
├── types/
│   └── types.ts                              # TypeScript interfaces
│
├── utils/
│   ├── logger.ts                             # Logger configuration
│   ├── botDetectionHelper.ts                 # Bot detection utilities
│   └── [15 files total]                      # Various utilities
│
├── helpers/
│   └── orchestratorHelpers.ts                # Orchestrator helper functions
│
└── retailerHandlers/
    └── [retailer-specific handlers]
```

## Core Components

### 1. CLI Layer

#### `cli.ts` (Main Entry Point)
- Parses commands and options
- Validates retailer selection
- Routes to appropriate mode
- Manages worker processes

**Key Classes**:
- `ConcurrentCategoryUrlProductsScraperManager`: Spawns multiple legacy workers
- `RetailerUtils`: Retailer validation and display names

#### `cli/index.ts`
- Implements CLI commands
- Interactive menus
- Enhanced/Queue mode launchers

### 2. Execution Modes

#### Legacy Mode: `legacy/scraper.ts`
**Function**: `runCategoryUrlProductsScraper(retailer)`
- Single-threaded execution
- JSON checkpoint-based resume
- In-memory queue management

#### Enhanced Mode: `EnhancedConcurrentCategoryUrlProductsManager.ts`
- Multi-worker architecture
- Database task queue
- Worker lifecycle management
- Real-time monitoring

#### Queue Mode: `modules/queueBasedScraper.ts`
**Class**: `CategoryUrlProductsQueueBasedScraper`
- Single process with database queue
- Task assignment and locking
- Retry logic

### 3. Workers

#### `cli-worker.ts` (Legacy Worker)
- Spawned by `ConcurrentCategoryUrlProductsScraperManager`
- Simple IPC messaging
- Calls `runCategoryUrlProductsScraper()`
- Used in Legacy concurrent mode

#### `worker.ts` (Queue Worker)
- Spawned by `EnhancedConcurrentCategoryUrlProductsManager`
- Complex queue management
- Uses `CategoryUrlProductsQueueManager`
- Database task coordination

### 4. Orchestration Layer

#### `orchestrator.ts`
**Main Function**: `scrapeCategoryProductUrlsForRetailer()`

**Responsibilities**:
- Coordinates product URL extraction from category pages
- Handles pagination (multiple strategies)
- Manages per-page product saving
- Deduplication of product URLs

**Pagination Strategies**:
1. **Advanced**: Extracts all pagination links upfront
2. **Next Button**: Clicks "Next" iteratively
3. **Custom**: Retailer-specific implementations

#### `categoryProcessor.ts`
**Function**: `processCategory()`
- Processes single category
- Calls orchestrator for product extraction
- Handles errors and retries
- Saves products to database

#### `categoryLoop.ts`
- Iterates through categories
- Queue management
- Progress tracking

### 5. Extractor Layer

#### `extractor/index.ts`
Main extraction coordination

#### `productLinkExtractor.ts`
Generic product link extraction using CSS selectors

#### `pageNavigator.ts`
**Class**: `PageNavigator`

**Responsibilities**:
- Navigate to URLs
- Handle Cloudflare challenges
- Cookie consent automation
- Anti-bot checks
- Timeout management

**Key Methods**:
- `navigateToPage(url)`: Navigate with retry logic
- `performAntiBotChecks()`: Detect and handle challenges
- `handleCloudflareChallenge()`: Wait for Cloudflare resolution

#### `retailerExtractors.ts`
**Function**: `getExtractorForRetailer()`

Returns retailer-specific extractor instance

#### Retailer-Specific Extractors

**Base**: `common/baseExtractor.ts`
- Abstract base class
- Common extraction patterns
- Pagination handling

**Implementations**:
- `clicks/clicksExtractor.ts`: Clicks-specific logic
- `dischem/dischemExtractor.ts`: Dis-Chem logic
- `faithfulToNature/productExtractor.ts`: FTN logic (most complex)
- `wellnessWarehouse/wellnessWarehouseExtractor.ts`: WW logic

**Special**: Faithful to Nature
- Most complex implementation
- Custom Cloudflare solver
- Recaptcha handler
- Extensive debugging utilities

### 6. Data Access Layer

#### `repositories/categoryRepository.ts`
**Functions**:
- `fetchCategories(retailerId)`: Get categories to scrape
- `getCategoryById(id)`: Fetch single category

#### `repositories/productRepository.ts`
**Functions**:
- `saveProducts(products)`: Save product-category mappings
- `productExists(url)`: Check if product already scraped

#### `db_handler.ts`
**Class**: `DatabaseHandler`
- Wraps Prisma client
- Connection pooling
- Error handling

### 7. Queue Management

#### `queue/CategoryUrlProductsQueueManager.ts`
**Class**: `CategoryUrlProductsQueueManager`

**Methods**:
- `getNextTask(workerId, retailerId)`: Atomic task assignment
- `markTaskCompleted(taskId)`: Mark task done
- `markTaskFailed(taskId, error)`: Mark task failed
- `resetQueue()`: Clear queue for restart

**Database Table**: `category_url_products_queue`
- Task assignment
- Worker coordination
- Retry tracking
- Status management

### 8. Configuration System

#### `config/<retailer>/index.ts`
**Exports**: `<retailer>Config`

**Structure**:
```typescript
{
  selectors: {
    PRODUCT_LINK_SELECTOR: string,
    PRODUCT_CONTAINER: string,
    PAGINATION_CONTAINER: string,
    PAGINATION_LINK_SELECTOR: string,
    NEXT_BUTTON_SELECTOR: string,
    // ... more selectors
  },
  scraperConfig: {
    baseUrl: string,
    timeouts: {
      navigation: number,
      pageLoad: number,
      // ...
    },
    retry: {
      maxAttempts: number,
      delayMs: number,
    }
  }
}
```

### 9. Utilities

#### `utils/logger.ts`
Logger configuration (Winston)

**⚠️ Critical Issue**: Multiple logger instances, no centralization
- Should be: Single `categoryUrlProductsLogger` (like category_scraper)
- Currently: Each file creates own logger

#### `utils/botDetectionHelper.ts`
Bot detection utilities

**⚠️ Critical Issue**: 23 console.log statements

#### Other Utilities
- URL validation
- String normalization
- Date formatting
- etc.

## Data Flow

### Detailed Flow

```
1. USER INVOCATION
   npm run scrape:cp scrape --retailer clicks
   
2. CLI ENTRY (cli.ts)
   - Parse arguments
   - Load Clicks configuration
   - Select mode (Legacy/Enhanced/Queue)
   
3. MODE SELECTION
   
   A. Legacy Mode:
      cli.ts → legacy/scraper.ts → categoryLoop → orchestrator
      
   B. Enhanced Mode:
      cli.ts → EnhancedConcurrentCategoryUrlProductsManager
      → spawn worker.ts × N
      → each worker: CategoryUrlProductsQueueManager → orchestrator
      
   C. Queue Mode:
      cli.ts → modules/queueBasedScraper.ts
      → CategoryUrlProductsQueueManager → orchestrator

4. ORCHESTRATION (orchestrator.ts)
   - scrapeCategoryProductUrlsForRetailer()
   - Get effective category URL (with pagination settings)
   - Navigate to category page
   - Extract pagination links (if available)
   
5. EXTRACTION (per page)
   - Get extractor for retailer
   - Extract product links using selectors
   - Deduplicate URLs
   - Call savePerPageCallback
   
6. PAGINATION
   - Visit next page
   - Repeat extraction
   - Continue until no more pages
   
7. PERSISTENCE (productRepository)
   - Save product URLs to database
   - Link to category via category_id
   - Track metadata (page number, position, timestamp)
   
8. COMPLETION
   - Update category status
   - Save checkpoint (Legacy mode)
   - Mark queue task complete (Enhanced/Queue mode)
   - Log statistics
```

## Key Interfaces

### CategoryInfo
```typescript
interface CategoryInfo {
  id: number;
  name: string;
  url: string;
  parent_id?: number;
  retailer_id: number;
  depth: number;
}
```

### ProductUrlInfo
```typescript
interface ProductUrlInfo {
  url: string;
  position?: number;
  categoryId: number;
}
```

### ProductExtractionResult
```typescript
interface ProductExtractionResult {
  productLinks: ProductUrlInfo[];
  totalPages: number;
  totalProducts: number;
  errors?: string[];
}
```

### Task (Queue System)
```typescript
interface CategoryUrlProductsTask {
  id: number;
  category_id: number;
  category_url: string;
  retailer_id: number;
  status: 'queued' | 'in_progress' | 'completed' | 'failed';
  assigned_worker_id?: string;
  attempts: number;
  error_message?: string;
}
```

## Database Schema

### category_url_products Table
```sql
CREATE TABLE category_url_products (
  id SERIAL PRIMARY KEY,
  url TEXT NOT NULL,
  category_id INTEGER REFERENCES categories(id),
  product_id INTEGER REFERENCES products(id),
  extraction_date TIMESTAMP DEFAULT NOW(),
  page_number INTEGER,
  position_in_page INTEGER,
  retailer_id INTEGER,
  
  UNIQUE(url, category_id)  -- Product can be in category once
);
```

### category_url_products_queue Table
```sql
CREATE TABLE category_url_products_queue (
  id SERIAL PRIMARY KEY,
  category_id INTEGER REFERENCES categories(id),
  category_url TEXT NOT NULL,
  retailer_id INTEGER,
  status TEXT DEFAULT 'queued',
  assigned_worker_id TEXT,
  locked_at TIMESTAMP,
  attempts INTEGER DEFAULT 0,
  max_attempts INTEGER DEFAULT 3,
  error_message TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

## Configuration Files

### Global Concurrency Config
`config/concurrency.json`

```json
{
  "clicks": {
    "maxWorkers": 2,
    "requestDelayMs": 1500,
    "retryAttempts": 3
  },
  "dischem": {
    "maxWorkers": 3,
    "requestDelayMs": 2000,
    "retryAttempts": 3
  }
}
```

### Retailer Selector Config
`config/<retailer>/index.ts`

Contains all CSS selectors for:
- Product link elements
- Product containers
- Pagination elements
- Next/Previous buttons
- Page numbers

## Error Handling

### Error Types
1. **Navigation Errors**: Page load timeout, connection refused
2. **Extraction Errors**: Selectors not found, no products
3. **Bot Detection**: Cloudflare challenge, rate limiting
4. **Database Errors**: Connection issues, constraint violations

### Retry Strategy
```typescript
{
  maxAttempts: 3,
  backoff: exponential,  // 5s, 10s, 20s
  retryableErrors: [
    'TimeoutError',
    'NetworkError',
    'BotDetectionError'
  ]
}
```

## Performance Characteristics

### Legacy Mode
- **Throughput**: ~50-100 products/min
- **Memory**: ~300 MB
- **CPU**: ~40%
- **Browsers**: 1

### Enhanced Mode
- **Throughput**: ~200-400 products/min
- **Memory**: ~1-3 GB
- **CPU**: ~200% (multi-core)
- **Browsers**: 2-4 (one per worker)
- **Workers**: 2-4 (configurable)

### Queue Mode
- **Throughput**: ~100-200 products/min
- **Memory**: ~500 MB
- **CPU**: ~80%
- **Browsers**: 1

## Critical Issues

### Logging
- ❌ 150+ console.log statements across 17 files
- ❌ No centralized logger (should be `categoryUrlProductsLogger`)
- ❌ Logs not captured in log files

### Workers
- ⚠️ Two worker implementations (cli-worker.ts vs worker.ts)
- ⚠️ Confusion about which is used when
- ⚠️ Duplicate IPC handling code

### Bot Detection
- ⚠️ 23 console.log in botDetectionHelper.ts
- ⚠️ Excessive logging in Cloudflare solver

See `04_Critical_Warnings_&_Red_Flags.md` for complete list.

## Testing

### Manual Testing
```bash
# Test single category
npm run scrape:cp scrape --retailer wellnesswarehouse

# Monitor logs
tail -f logs/category_url_products.log

# Check database
psql -d product_scraper -c "SELECT COUNT(*) FROM category_url_products;"
```

### Integration Points
1. **Input**: Categories from `categories` table (from scrape:c)
2. **Output**: Product URLs in `category_url_products` table (for scrape:p)

## Next Steps

- **02_Code_Analysis_&_Bugs.md**: Known issues and bugs
- **03_Ownership_&_Maintenance_Checklist.md**: Operational procedures
- **04_Critical_Warnings_&_Red_Flags.md**: Priority fixes
- **07_Immediate_Action_Plan.md**: Step-by-step improvement plan
