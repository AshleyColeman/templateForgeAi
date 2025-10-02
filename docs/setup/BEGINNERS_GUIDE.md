# 🎓 Complete Beginner's Guide - Extract Categories from Wellness Warehouse

**Your First Category Extraction in 15 Minutes**

This guide walks you through extracting categories from [Wellness Warehouse](https://www.wellnesswarehouse.com/) from scratch. No prior knowledge needed!

---

## 📋 What You'll Learn

By the end of this guide, you'll:
- ✅ Have the system fully set up
- ✅ Extract categories from Wellness Warehouse
- ✅ See categories saved in PostgreSQL database
- ✅ Understand where logs are
- ✅ Know how to verify everything worked
- ✅ Have a reusable blueprint for future extractions

**Time Required**: 15-20 minutes  
**Cost**: $0 (using FREE Ollama)

---

## 🎯 Prerequisites Check

Before starting, verify you have:

```bash
# 1. Python 3.11+ (check version)
python3 --version
# Should show: Python 3.11.x or 3.12.x ✅

# 2. PostgreSQL running
psql -U postgres -c "SELECT version();"
# Should connect and show PostgreSQL version ✅

# 3. Database exists
psql -U postgres -c "\l" | grep products
# Should show 'products' database ✅
```

If any fail, see **"Prerequisites Setup"** section at the end.

---

## 🚀 Step 1: Install Ollama (FREE LLM - 5 minutes)

Ollama gives you a FREE local AI that works without API keys.

### On Linux/Mac:

```bash
# Download and install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull the model (downloads ~2GB - takes 2-5 minutes)
ollama pull gemma3:1b

# Start Ollama server (leave this running)
ollama serve
```

**You'll see**:
```
Downloading gemma3:1b... 100%
✅ Model downloaded successfully
```

**Keep this terminal open!** Ollama needs to stay running.

### Verify Ollama is Working:

Open a **new terminal** and test:

```bash
curl http://localhost:11434/api/tags
```

**You'll see**:
```json
{"models":[{"name":"gemma3:1b",...}]}
```

✅ **Success!** Ollama is ready.

---

## 📦 Step 2: Install Project Dependencies (2 minutes)

In a **new terminal**:

```bash
# Navigate to project
cd /home/ashleycoleman/Projects/templateForgeAi

# Install all Python packages (takes 1-2 minutes)
pip install -e .
# OR if you have Poetry:
poetry install

# Install Playwright browser
python3 -m playwright install chromium

# You'll see progress bars and "✓ chromium installed"
```

**Verify installation**:

```bash
python3 verify_setup.py
```

**You'll see**:
```
🔍 Verifying Environment Setup

✅ Python version: 3.12.4
✅ playwright installed
✅ asyncpg installed
✅ pydantic installed
✅ click installed
✅ rich installed
✅ loguru installed
✅ openai installed
✅ anthropic installed
✅ httpx installed
✅ tenacity installed
✅ Directory exists: src/ai_agents/category_extractor
✅ Directory exists: src/ai_agents/category_extractor/tools
✅ Directory exists: src/ai_agents/category_extractor/utils
✅ Directory exists: src/ai_agents/category_extractor/blueprints
✅ Directory exists: tests/test_category_extractor
✅ Directory exists: logs
✅ .env file exists

==================================================
✅ All checks passed! Environment is ready.
```

---

## ⚙️ Step 3: Configure Environment (3 minutes)

### Create your .env file:

```bash
# Copy the example
cp .env.example .env

# Edit with your favorite editor
nano .env
# OR
code .env
# OR
vim .env
```

### What to set in .env:

**Required Settings** (you MUST change these):

```bash
# Database password (replace with your actual password)
DB_PASSWORD=your_actual_postgres_password_here
```

**LLM Provider** (default is Ollama - FREE):

```bash
# Use Ollama (already set as default - FREE!)
LLM_PROVIDER=ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=gemma3:1b
```

**Leave everything else as default!** The file already has good defaults.

### Your .env should look like:

```bash
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=products
DB_USER=postgres
DB_PASSWORD=your_actual_password_here  # ← CHANGE THIS!

# LLM Provider Configuration
LLM_PROVIDER=ollama  # ← Using FREE Ollama

# Ollama Configuration (Default - FREE)
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=gemma3:1b

# Everything else can stay as default...
```

**Save and close** the file.

### Verify configuration:

```bash
python3 -c "from src.ai_agents.category_extractor.config import get_config; c=get_config(); print(f'✅ Provider: {c.llm_provider}'); print(f'✅ Database: {c.db_name}'); c.validate_config(); print('✅ Config valid!')"
```

**You'll see**:
```
✅ Provider: ollama
✅ Database: products
✅ Config valid!
```

---

## 🎯 Step 4: Set Up Database for Wellness Warehouse (2 minutes)

### Create a retailer entry:

```bash
# Connect to PostgreSQL
psql -U postgres -d products

# Or if you have a password:
psql -U postgres -d products -W
```

**In psql**, run:

```sql
-- Check if retailers table exists
\dt retailers

-- Check existing retailers
SELECT * FROM retailers;

-- Add Wellness Warehouse (if not exists)
INSERT INTO retailers (id, name, base_url, enabled)
VALUES (99, 'Wellness Warehouse', 'https://www.wellnesswarehouse.com', true)
ON CONFLICT (id) DO NOTHING;

-- Verify it was added
SELECT * FROM retailers WHERE id = 99;

-- Exit psql
\q
```

**You'll see**:
```
INSERT 0 1
 id |        name         |            base_url            | enabled
----+---------------------+--------------------------------+---------
 99 | Wellness Warehouse  | https://www.wellnesswarehouse.com | t
```

✅ **Database ready!**

---

## 🚀 Step 5: Run Your First Extraction! (5-10 minutes)

### Terminal 1: Make sure Ollama is running

```bash
# If not still running from Step 1:
ollama serve
```

### Terminal 2: Run the extraction

```bash
cd /home/ashleycoleman/Projects/templateForgeAi

# Run extraction with visible browser (so you can watch!)
python3 -m src.ai_agents.category_extractor.cli extract \
    --url https://www.wellnesswarehouse.com/ \
    --retailer-id 99 \
    --no-headless
```

**What flags mean**:
- `extract` - Command to extract categories
- `--url` - Website to analyze
- `--retailer-id 99` - Database ID we just created
- `--no-headless` - Show browser so you can watch (remove this for silent mode)

---

## 👀 What You'll See Happening

### 1. Initial Output:

```
╭─ AI Category Extractor ──────────────────────╮
│ Retailer 99                                  │
│ URL: https://www.wellnesswarehouse.com/      │
╰──────────────────────────────────────────────╯

⠋ Initialising...
```

### 2. Browser Opens:

You'll see a Chrome window open and navigate to Wellness Warehouse.

**Watch for**:
- Page loads
- Cookie consent might be auto-accepted
- Screenshot is captured
- Browser might scroll or interact with menus

### 3. Progress Updates:

```
⠙ Analyzing navigation...
⠹ Extracting categories...
⠸ Saving categories...
⠼ Generating blueprint...
```

### 4. Success Output:

```
╭─────────────── Extraction Complete ───────────────╮
│ Categories discovered: 156                        │
│ Database -> saved: 142, updated: 14              │
│ Blueprint saved to: src/ai_agents/category_extractor/blueprints/retailer_99_20250930_220000.json │
╰───────────────────────────────────────────────────╯
```

**Extraction time**: 5-12 minutes depending on site complexity

---

## 📁 Step 6: Where to Find Everything

### 1. Logs (Real-time Extraction Details)

```bash
# View the log file
cat logs/category_extractor.log

# Or follow it in real-time (open before running extraction)
tail -f logs/category_extractor.log
```

**What you'll see in logs**:

```
2025-09-30 22:00:15 | INFO     | retailer=99 | agent:initialize_browser - Browser initialised for https://www.wellnesswarehouse.com/
2025-09-30 22:00:18 | INFO     | retailer=99 | page_analyzer:analyze - Analyzing page: https://www.wellnesswarehouse.com/
2025-09-30 22:00:25 | INFO     | retailer=99 | page_analyzer:_handle_cookie_consent - Accepted cookies via button:has-text('Allow Cookies')
2025-09-30 22:01:42 | INFO     | retailer=99 | category_extractor:extract - Starting category extraction
2025-09-30 22:02:55 | INFO     | retailer=99 | category_extractor:extract - Extracted 156 categories
2025-09-30 22:03:10 | INFO     | retailer=99 | database:save_categories - Saved 142 categories, updated 14
2025-09-30 22:03:15 | INFO     | retailer=99 | blueprint_generator:generate - Blueprint saved to: .../retailer_99_20250930_220000.json
2025-09-30 22:03:20 | INFO     | retailer=99 | agent:cleanup - Cleanup complete
```

**Log levels**:
- `INFO` - Normal operations
- `WARNING` - Potential issues
- `ERROR` - Something failed
- `DEBUG` - Detailed debugging (enable with `LOG_LEVEL=DEBUG` in .env)

### 2. Database (Extracted Categories)

```bash
# Connect to database
psql -U postgres -d products

# Check how many categories were saved
SELECT COUNT(*) FROM categories WHERE retailer_id = 99;
```

**You'll see**:
```
 count
-------
   156
```

**See the actual categories**:

```sql
-- View first 10 categories
SELECT id, name, url, depth, parent_id 
FROM categories 
WHERE retailer_id = 99 
ORDER BY depth, name 
LIMIT 10;
```

**You'll see**:
```
  id  |       name        |                    url                     | depth | parent_id
------+-------------------+--------------------------------------------+-------+-----------
 1001 | Beauty            | https://www.wellnesswarehouse.com/beauty   |     0 |
 1002 | Clean Fitness     | https://www.wellnesswarehouse.com/fitness  |     0 |
 1003 | Gut Health        | https://www.wellnesswarehouse.com/gut      |     0 |
 1004 | Immunity          | https://www.wellnesswarehouse.com/immunity |     0 |
 1005 | AHA               | https://www.wellnesswarehouse.com/aha      |     1 |      1001
 1006 | Bakuchiol         | https://www.wellnesswarehouse.com/...      |     1 |      1001
```

**Check hierarchy**:

```sql
-- See parent-child relationships
SELECT 
    c1.name as parent,
    c2.name as child
FROM categories c1
JOIN categories c2 ON c2.parent_id = c1.id
WHERE c1.retailer_id = 99
LIMIT 10;
```

**You'll see**:
```
    parent     |        child
---------------+----------------------
 Beauty        | AHA
 Beauty        | Bakuchiol
 Beauty        | Collagen
 Beauty        | Hair, Skin & Nail Support
 Gut Health    | Amino Acids
 Gut Health    | Apple Cider Vinegar
```

**Check depth distribution**:

```sql
-- How many categories at each level?
SELECT depth, COUNT(*) as count
FROM categories
WHERE retailer_id = 99
GROUP BY depth
ORDER BY depth;
```

**You'll see**:
```
 depth | count
-------+-------
     0 |    11  (top-level categories)
     1 |   145  (subcategories)
```

### 3. Generated Blueprint

```bash
# Find the blueprint file
ls -lh src/ai_agents/category_extractor/blueprints/

# You'll see:
# retailer_99_20250930_220000.json

# View the blueprint
cat src/ai_agents/category_extractor/blueprints/retailer_99_*.json
```

**Blueprint contents** (simplified):

```json
{
  "version": "1.0",
  "metadata": {
    "site_url": "https://www.wellnesswarehouse.com/",
    "retailer_id": 99,
    "retailer_name": "Wellness Warehouse",
    "generated_at": "2025-09-30T22:03:15Z",
    "confidence_score": 0.85
  },
  "extraction_strategy": {
    "navigation_type": "hover_menu",
    "complexity": "medium"
  },
  "selectors": {
    "nav_container": "nav.navigation",
    "top_level_items": "li.level0",
    "category_links": "a.level0",
    "flyout_panel": "div.submenu",
    "subcategory_list": "div.col-category a"
  },
  "extraction_stats": {
    "total_categories": 156,
    "max_depth": 1
  }
}
```

**This blueprint can be reused** for future extractions (costs $0!).

---

## 🔍 Step 7: Verify Everything Worked

### Checklist:

```bash
# 1. Check logs exist
ls -lh logs/category_extractor.log
# Should show a log file with recent timestamp

# 2. Check log has no errors
grep ERROR logs/category_extractor.log
# Should show nothing (or only minor warnings)

# 3. Check categories in database
psql -U postgres -d products -c "SELECT COUNT(*) FROM categories WHERE retailer_id = 99;"
# Should show: 156 (or similar - number of categories found)

# 4. Check blueprint was created
ls -1 src/ai_agents/category_extractor/blueprints/retailer_99_*.json
# Should show the blueprint file

# 5. Verify hierarchy is correct
psql -U postgres -d products -c "
SELECT depth, COUNT(*) 
FROM categories 
WHERE retailer_id = 99 
GROUP BY depth 
ORDER BY depth;"
# Should show categories at different depth levels
```

**All checks pass?** ✅ **Success!** Your first extraction worked perfectly!

---

## 🎓 Understanding What Happened

### The Workflow:

```
1. YOU run CLI command
   ↓
2. System opens browser (Chromium)
   ↓
3. Navigates to https://www.wellnesswarehouse.com/
   ↓
4. Captures screenshot
   ↓
5. Sends screenshot + HTML to Ollama (local AI)
   ↓
6. Ollama analyzes and identifies:
   - Navigation type: "hover_menu"
   - Where categories are: "Top navigation bar"
   - Selectors needed: "li.level0", "a.level0", etc.
   ↓
7. System executes extraction strategy:
   - Hovers over menu items
   - Waits for flyouts to appear
   - Extracts category names and URLs
   - Builds parent-child hierarchy
   ↓
8. Validates extracted data:
   - Removes duplicates
   - Verifies URLs are valid
   - Checks hierarchy makes sense
   ↓
9. Saves to PostgreSQL:
   - Inserts categories with parent_id relationships
   - Sets retailer_id = 99
   - Marks as enabled
   ↓
10. Generates blueprint:
    - Saves extraction strategy to JSON
    - Can be reused for $0 future extractions
    ↓
11. Shows success message
    ↓
12. Cleanup (closes browser, connections)
```

### Files Created:

```
logs/
└── category_extractor.log ............ Detailed execution log

src/ai_agents/category_extractor/blueprints/
└── retailer_99_20250930_220000.json .. Reusable blueprint

PostgreSQL database:
└── categories table ................... 156 new rows with retailer_id=99
```

---

## 📊 Understanding the Database

### Categories Table Structure:

```sql
-- View table structure
\d categories
```

```
 Column      |  Type   | Description
-------------+---------+----------------------------------
 id          | int     | Unique category ID (auto-generated)
 name        | text    | Category name (e.g., "Beauty")
 url         | text    | Category URL
 parent_id   | int     | Parent category ID (NULL for root)
 retailer_id | int     | Your retailer ID (99)
 depth       | int     | Hierarchy level (0=root, 1=child, etc.)
 enabled     | bool    | Is category active?
 created_at  | timestamp | When it was extracted
```

### Example Data from Wellness Warehouse:

```sql
SELECT id, name, url, depth, parent_id 
FROM categories 
WHERE retailer_id = 99 
ORDER BY depth, name 
LIMIT 20;
```

**You'll see categories like**:

```
Root Categories (depth=0, parent_id=NULL):
  - Beauty
  - Clean Fitness
  - Concentration & Memory
  - Energy
  - Fitness
  - Gut Health
  - Immunity
  - Shop by Diet
  - Sleep Support
  - Stress Management
  - Women's Health

Subcategories (depth=1, parent_id=1001):
  Under "Beauty":
    - AHA (parent_id points to Beauty)
    - Bakuchiol
    - Collagen
    - Hair, Skin & Nail Support
    - Hyaluronic Acid
    - etc.
```

---

## 🔍 Understanding the Logs

### Log File Location:

```bash
logs/category_extractor.log
```

### Log Format:

```
[Timestamp] | [Level] | retailer=[ID] | [Module]:[Function] - [Message]
```

### Example Log Entries:

```
2025-09-30 22:00:15 | INFO  | retailer=99 | agent:initialize_browser - Browser initialised
# ↑ Timestamp      ↑ Level  ↑ Retailer  ↑ Module & function  ↑ What happened

2025-09-30 22:00:18 | INFO  | retailer=99 | page_analyzer:analyze - Analyzing page: https://www.wellnesswarehouse.com/
# Started analyzing the page

2025-09-30 22:00:25 | DEBUG | retailer=99 | page_analyzer:_handle_cookie_consent - Accepted cookies via button:has-text('Allow')
# Auto-accepted cookie banner

2025-09-30 22:01:42 | INFO  | retailer=99 | category_extractor:extract - Starting category extraction
# Started extracting categories

2025-09-30 22:02:55 | INFO  | retailer=99 | category_extractor:extract - Extracted 156 categories
# Finished extraction - found 156 categories

2025-09-30 22:03:10 | INFO  | retailer=99 | database:save_categories - Saved 142 new, updated 14 existing
# Saved to database

2025-09-30 22:03:15 | INFO  | retailer=99 | blueprint_generator:generate - Blueprint saved
# Blueprint created

2025-09-30 22:03:20 | INFO  | retailer=99 | agent:cleanup - Cleanup complete
# Finished successfully
```

### If Something Goes Wrong:

**Look for ERROR lines**:

```bash
grep ERROR logs/category_extractor.log
```

**Common errors and what they mean**:

```
ERROR ... NavigationError: Failed to load page
→ Website didn't load. Check internet connection.

ERROR ... AnalysisError: Ollama API error
→ Ollama not running. Run: ollama serve

ERROR ... DatabaseError: password authentication failed
→ Wrong DB_PASSWORD in .env file

ERROR ... TimeoutError: Waiting for selector timed out
→ Page structure different than expected (not a problem, AI will adapt)
```

---

## 🎨 Advanced: Enable Debug Logging

Want to see **everything** that's happening?

### Edit .env:

```bash
# Change log level
LOG_LEVEL=DEBUG
```

### Re-run extraction:

```bash
python3 -m src.ai_agents.category_extractor.cli extract \
    --url https://www.wellnesswarehouse.com/ \
    --retailer-id 99
```

**Now logs show EVERYTHING**:

```
2025-09-30 22:00:15 | DEBUG | retailer=99 | agent:__init__ - Initializing agent with provider: ollama
2025-09-30 22:00:16 | DEBUG | retailer=99 | agent:_create_strands_agent - Creating Ollama model
2025-09-30 22:00:17 | DEBUG | retailer=99 | agent:_register_tools - Registering PageAnalyzerTool
2025-09-30 22:00:17 | DEBUG | retailer=99 | agent:_register_tools - Registering CategoryExtractorTool
2025-09-30 22:00:17 | DEBUG | retailer=99 | agent:_register_tools - Registering BlueprintGeneratorTool
2025-09-30 22:00:18 | DEBUG | retailer=99 | page_analyzer:_capture_screenshot - Screenshot captured: 234KB
2025-09-30 22:00:19 | DEBUG | retailer=99 | page_analyzer:_simplified_html - HTML simplified: 45KB
2025-09-30 22:00:30 | DEBUG | retailer=99 | llm_client:analyze_page - Sending request to Ollama
2025-09-30 22:01:15 | DEBUG | retailer=99 | llm_client:_parse_response - Parsed LLM response
... much more detail ...
```

---

## 🔄 Step 8: Reuse the Blueprint (FREE!)

### Extract Again Using Blueprint (No LLM Cost):

```bash
# Use the blueprint from your first extraction
python3 -m src.ai_agents.category_extractor.cli execute-blueprint \
    --blueprint src/ai_agents/category_extractor/blueprints/retailer_99_20250930_220000.json
```

**This runs in ~2 minutes instead of 10 minutes and costs $0!**

**Why?**
- No AI analysis needed (uses saved strategy)
- Just executes the blueprint instructions
- Updates categories if site changed
- Perfect for daily/weekly updates

---

## 🎯 Quick Reference Commands

### View Categories in Database:

```sql
-- All Wellness Warehouse categories
SELECT name, url, depth FROM categories WHERE retailer_id = 99 ORDER BY depth, name;

-- Count by depth
SELECT depth, COUNT(*) FROM categories WHERE retailer_id = 99 GROUP BY depth;

-- Root categories only
SELECT name FROM categories WHERE retailer_id = 99 AND parent_id IS NULL;

-- Categories under "Beauty"
SELECT c2.name as subcategory
FROM categories c1
JOIN categories c2 ON c2.parent_id = c1.id
WHERE c1.retailer_id = 99 AND c1.name = 'Beauty';
```

### Check Logs:

```bash
# Last 50 lines
tail -50 logs/category_extractor.log

# Search for errors
grep -i error logs/category_extractor.log

# Follow in real-time
tail -f logs/category_extractor.log

# Show only INFO level
grep INFO logs/category_extractor.log
```

### List Blueprints:

```bash
ls -lh src/ai_agents/category_extractor/blueprints/

# View a blueprint
cat src/ai_agents/category_extractor/blueprints/retailer_99_*.json | head -50
```

---

## 🐛 Troubleshooting Common Issues

### Issue 1: "Ollama connection refused"

**Error**:
```
AnalysisError: Ollama API error: Connection refused
```

**Solution**:
```bash
# Start Ollama in another terminal
ollama serve

# Verify it's running
curl http://localhost:11434/api/tags
```

### Issue 2: "Database password authentication failed"

**Error**:
```
DatabaseError: password authentication failed for user "postgres"
```

**Solution**:
```bash
# Check your password
psql -U postgres -d products -W
# Enter password manually - does it work?

# If it works, update .env file with correct password
nano .env
# Change: DB_PASSWORD=your_correct_password_here
```

### Issue 3: "No categories found"

**Possible causes**:
1. Website structure changed
2. Bot detection blocked access
3. Selectors were incorrect

**Solutions**:
```bash
# 1. Run in visible mode to see what's happening
--no-headless

# 2. Check logs for details
grep -A 5 -B 5 ERROR logs/category_extractor.log

# 3. Re-run - AI will adapt to changes
python3 -m src.ai_agents.category_extractor.cli extract --url https://www.wellnesswarehouse.com/ --retailer-id 99
```

### Issue 4: "Browser crashes or hangs"

**Solution**:
```bash
# Kill any stuck browser processes
pkill -f chromium

# Run again
python3 -m src.ai_agents.category_extractor.cli extract --url https://www.wellnesswarehouse.com/ --retailer-id 99
```

### Issue 5: Want to see the AI's analysis?

**Check the log for the analysis**:

```bash
grep -A 30 "navigation_type" logs/category_extractor.log
```

**You'll see what the AI detected**:
```
{
  "navigation_type": "hover_menu",
  "selectors": {
    "nav_container": "nav.navigation",
    "top_level_items": "li.level0",
    ...
  },
  "confidence": 0.85
}
```

---

## 📸 What to Expect: Wellness Warehouse Specifics

### Based on Website Analysis:

**Navigation Type**: Hover menu  
**Categories Found**: ~150-200 (site has many!)  
**Hierarchy Depth**: 2 levels  
**Extraction Time**: 8-12 minutes  

### Top-Level Categories You'll See:

```
Shop by Products:
  - Clean Supplements
  - Natural Foods
  - Natural Beauty
  - Eco Home
  - Moms & Tots
  - Clean Fitness

Shop by Solution:
  - Beauty
  - Concentration & Memory
  - Energy
  - Fitness
  - Gut Health
  - Immunity
  - Shop by Diet
  - Sleep Support
  - Stress Management
  - Women's Health
  - Shop by Skin Type
```

### Subcategories Example (under "Beauty"):

```
- AHA
- Bakuchiol
- Collagen
- Hair, Skin & Nail Support
- Hyaluronic Acid
- Lactic Acid
- Longevity
- Niacinamide
- PHA
- Retinol
- Salicylic Acid
- Vitamin C
```

---

## 🎯 Next Steps After First Extraction

### 1. Review the Categories:

```sql
-- Open database and browse
psql -U postgres -d products

-- See all Wellness Warehouse categories nicely formatted
SELECT 
    REPEAT('  ', depth) || name as category_hierarchy,
    url
FROM categories 
WHERE retailer_id = 99 
ORDER BY name;
```

### 2. Test Blueprint Reuse:

```bash
# Delete the extracted categories (for testing)
psql -U postgres -d products -c "DELETE FROM categories WHERE retailer_id = 99;"

# Extract again using the blueprint (much faster!)
python3 -m src.ai_agents.category_extractor.cli execute-blueprint \
    --blueprint src/ai_agents/category_extractor/blueprints/retailer_99_*.json

# Check - categories are back!
psql -U postgres -d products -c "SELECT COUNT(*) FROM categories WHERE retailer_id = 99;"
```

**Time comparison**:
- First extraction with AI: ~10 minutes
- Blueprint extraction: ~2 minutes
- **5x faster!**

### 3. Try Another Retailer:

```bash
# Add another retailer
psql -U postgres -d products -c "
INSERT INTO retailers (id, name, base_url, enabled)
VALUES (100, 'Clicks', 'https://clicks.co.za', true);"

# Extract from Clicks
python3 -m src.ai_agents.category_extractor.cli extract \
    --url https://clicks.co.za/products/c/OH1 \
    --retailer-id 100

# Now you have 2 retailers in your database!
```

---

## 💡 Pro Tips

### Tip 1: Run Extractions in Background

```bash
# Run without showing browser (faster)
python3 -m src.ai_agents.category_extractor.cli extract \
    --url https://www.wellnesswarehouse.com/ \
    --retailer-id 99 \
    --headless

# Even run in background
nohup python3 -m src.ai_agents.category_extractor.cli extract \
    --url https://www.wellnesswarehouse.com/ \
    --retailer-id 99 \
    --headless > extraction.log 2>&1 &

# Check progress
tail -f extraction.log
```

### Tip 2: Schedule Regular Updates

```bash
# Add to crontab (daily at 2 AM)
crontab -e

# Add this line:
0 2 * * * cd /home/ashleycoleman/Projects/templateForgeAi && /usr/bin/python3 -m src.ai_agents.category_extractor.cli execute-blueprint --blueprint src/ai_agents/category_extractor/blueprints/retailer_99_latest.json >> logs/cron.log 2>&1
```

### Tip 3: Monitor Costs (Even Though Ollama is FREE)

```bash
# Check log file size (Ollama uses no API, but logs grow)
du -sh logs/category_extractor.log

# Ollama is FREE - no API costs to worry about!
# If you switch to OpenAI, track token usage in logs
grep "tokens" logs/category_extractor.log
```

### Tip 4: Compare Extractions Over Time

```sql
-- Add extraction metadata
ALTER TABLE categories ADD COLUMN IF NOT EXISTS extraction_date timestamptz;

-- Track when categories change
SELECT 
    c1.name,
    c1.url,
    c1.created_at as first_seen,
    MAX(c2.created_at) as last_updated
FROM categories c1
LEFT JOIN categories c2 ON c1.id = c2.id
WHERE c1.retailer_id = 99
GROUP BY c1.id, c1.name, c1.url, c1.created_at;
```

---

## 🎓 Understanding Costs

### Wellness Warehouse Extraction Costs:

**Using Ollama (Default)**:
- LLM Cost: **$0.00** (FREE!)
- Infrastructure: **$0.00** (runs on your machine)
- **Total: $0.00**

**Using OpenAI (Alternative)**:
- LLM Cost: ~$0.15-0.25 (small site, simple structure)
- Infrastructure: $0.00
- **Total: ~$0.20**

**Using Blueprint (Reuse)**:
- LLM Cost: **$0.00** (no AI needed)
- **Total: $0.00**

### Cost Comparison Table:

| Extraction Type | First Run | 2nd Run | 10th Run | Annual (52 weeks) |
|-----------------|-----------|---------|----------|-------------------|
| **Ollama** | $0.00 | $0.00 | $0.00 | **$0.00** |
| **OpenAI + Blueprint** | $0.20 | $0.00 | $0.00 | **$0.20** |
| **Anthropic + Blueprint** | $1.50 | $0.00 | $0.00 | **$1.50** |

**Key Insight**: After first extraction, all providers cost $0 (blueprint reuse)!

---

## 🎯 Summary Checklist

After completing this guide, you should have:

- [x] Ollama installed and running
- [x] Project dependencies installed
- [x] .env file configured
- [x] Database retailer entry created
- [x] First extraction completed successfully
- [x] Categories in database (verified)
- [x] Blueprint generated
- [x] Logs reviewed
- [x] Understanding of the workflow

**If all checked**: 🎉 **Congratulations! You're now a category extraction expert!**

---

## 📚 Quick Command Reference

### Run extraction:
```bash
python3 -m src.ai_agents.category_extractor.cli extract --url <URL> --retailer-id <ID>
```

### Use blueprint:
```bash
python3 -m src.ai_agents.category_extractor.cli execute-blueprint --blueprint <path>
```

### Check logs:
```bash
tail -f logs/category_extractor.log
```

### Check database:
```bash
psql -U postgres -d products -c "SELECT COUNT(*) FROM categories WHERE retailer_id = 99;"
```

### Verify setup:
```bash
python3 verify_setup.py
```

---

## 🆘 Need Help?

### If Extraction Fails:

1. **Check Ollama is running**:
   ```bash
   curl http://localhost:11434/api/tags
   ```

2. **Check database connection**:
   ```bash
   psql -U postgres -d products -c "SELECT version();"
   ```

3. **Review logs**:
   ```bash
   grep -i error logs/category_extractor.log
   ```

4. **Run in debug mode**:
   ```bash
   LOG_LEVEL=DEBUG python3 -m src.ai_agents.category_extractor.cli extract ...
   ```

5. **Check detailed QA report**:
   ```bash
   cat QUALITY_ASSURANCE_REPORT.md
   ```

---

## 🎉 You Did It!

You've successfully:
- ✅ Set up a production-quality AI system
- ✅ Extracted categories from a real e-commerce site
- ✅ Saved data to PostgreSQL database
- ✅ Generated a reusable blueprint
- ✅ Understood the complete workflow

**This same process works for ANY e-commerce site!**

Try it on:
- Clicks: https://clicks.co.za
- Takealot: https://www.takealot.com
- Makro: https://www.makro.co.za
- Any online store!

---

**Cost**: $0 with Ollama 💰  
**Time**: 5-10 minutes per site ⚡  
**Reusability**: Blueprints = $0 forever 🔄  
**Scalability**: Unlimited retailers! 🚀

**Now go extract some categories!** 🎊

---

