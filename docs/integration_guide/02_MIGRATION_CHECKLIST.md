# Migration Checklist: Replacing scrape:c with AI Agent

## Overview

This checklist guides you through replacing the TypeScript `scrape:c` category scraper with the Python AI Agent system.

**Estimated Time:** 2-4 hours for full migration (all 4 retailers)  
**Risk Level:** Low (backward compatible, parallel operation supported)

## Prerequisites

### ✅ Before You Start

- [ ] Python 3.11+ installed
- [ ] PostgreSQL database accessible
- [ ] `categories` table exists with correct schema
- [ ] LLM provider configured (Ollama/OpenAI/Anthropic)
- [ ] AI Agent code installed and tested
- [ ] scrape:cp and scrape:p working with current scrape:c data

### Verify Current Setup

```bash
# 1. Check Python version
python --version  # Should be 3.11+

# 2. Check database connection
psql -d products -c "\dt categories"

# 3. Check AI Agent installation
python -m src.ai_agents.category_extractor.cli --help

# 4. Verify scrape:c works (baseline)
npm run scrape:c scrape --retailer clicks
```

## Phase 1: Parallel Operation (Recommended)

Run both systems simultaneously to validate AI Agent output.

### Step 1.1: Run AI Agent (Test Retailer)

```bash
# Choose one retailer for initial test (Clicks recommended)
python -m src.ai_agents.category_extractor.cli \
  --url https://clicks.co.za \
  --retailer-id 1

# Monitor execution
tail -f logs/ai_agent.log
```

**Expected Duration:** 5-10 minutes  
**Expected Output:** 
- Categories extracted: 3000+
- Max depth: 4-5
- Blueprint generated: `retailer_1_*.json`

### Step 1.2: Backup Existing Categories

```bash
# Create backup of current categories (from scrape:c)
pg_dump -d products -t categories > backups/categories_before_ai_agent_$(date +%Y%m%d).sql

# Or just the Clicks data
psql -d products -c "COPY (SELECT * FROM categories WHERE retailer_id = 1) 
  TO '/tmp/categories_clicks_backup.csv' CSV HEADER;"
```

### Step 1.3: Compare Results

```sql
-- Save AI Agent results temporarily
CREATE TABLE categories_ai_agent AS 
SELECT * FROM categories WHERE retailer_id = 1;

-- Clear AI Agent data
DELETE FROM categories WHERE retailer_id = 1;

-- Run scrape:c again
-- (npm run scrape:c scrape --retailer clicks)

-- Compare counts
SELECT 
  'scrape:c' as source,
  COUNT(*) as total,
  MAX(depth) as max_depth,
  COUNT(DISTINCT parent_id) as unique_parents
FROM categories
WHERE retailer_id = 1

UNION ALL

SELECT 
  'AI Agent' as source,
  COUNT(*) as total,
  MAX(depth) as max_depth,
  COUNT(DISTINCT parent_id) as unique_parents
FROM categories_ai_agent;
```

**Expected Comparison:**

| Source | Total Categories | Max Depth | Unique Parents |
|--------|-----------------|-----------|----------------|
| scrape:c | 3000+ | 4-5 | 500+ |
| AI Agent | 3000+ | 4-5 | 500+ |

**✅ PASS if:**
- AI Agent total >= scrape:c total
- AI Agent max depth >= scrape:c max depth
- No major discrepancies in hierarchy

**⚠️ INVESTIGATE if:**
- AI Agent total < 80% of scrape:c
- Max depth = 0 (no subcategories found)
- Significant hierarchy differences

### Step 1.4: Validate Data Quality

```bash
# Run validation script
psql -d products -f docs/integration_guide/scripts/validate_ai_agent_output.sql
```

See `01_SCHEMA_VALIDATION.md` for validation queries.

### Step 1.5: Test scrape:cp Integration

```bash
# Use AI Agent categories with scrape:cp
npm run scrape:cp scrape --retailer clicks

# Monitor logs
tail -f logs/category_url_products.log
```

**✅ PASS if:**
- scrape:cp reads categories successfully
- Product URLs extracted without errors
- `category_url_products` table populated

**❌ FAIL if:**
- scrape:cp errors on reading categories
- No product URLs extracted
- Database constraint violations

## Phase 2: Single Retailer Migration

Once validation passes, migrate one retailer completely.

### Step 2.1: Choose Migration Retailer

**Recommended Order:**
1. **Wellness Warehouse** (simplest, ~300 categories)
2. **Faithful to Nature** (~400 categories)
3. **Dis-Chem** (~500 categories)
4. **Clicks** (most complex, 3000+ categories)

### Step 2.2: Clear Old Data

```sql
-- Example: Migrating Wellness Warehouse (retailer_id = 4)

-- 1. Backup first!
COPY (SELECT * FROM categories WHERE retailer_id = 4) 
  TO '/tmp/categories_wellness_backup.csv' CSV HEADER;

-- 2. Clear old scrape:c data
DELETE FROM categories WHERE retailer_id = 4;

-- 3. Verify clean state
SELECT COUNT(*) FROM categories WHERE retailer_id = 4;
-- Expected: 0
```

### Step 2.3: Run AI Agent

```bash
python -m src.ai_agents.category_extractor.cli \
  --url https://www.wellnesswarehouse.com \
  --retailer-id 4
```

### Step 2.4: Validate & Test Pipeline

```bash
# 1. Validate categories
psql -d products -c "
  SELECT depth, COUNT(*) 
  FROM categories 
  WHERE retailer_id = 4 
  GROUP BY depth 
  ORDER BY depth;
"

# 2. Run full pipeline
npm run scrape:cp scrape --retailer wellnesswarehouse
npm run scrape:p scrape --retailer wellnesswarehouse

# 3. Verify products extracted
psql -d products -c "
  SELECT COUNT(*) as total_products
  FROM products 
  WHERE retailer_id = 4;
"
```

**✅ PASS if:** Full pipeline completes without errors

### Step 2.5: Monitor for 1 Week

```bash
# Run daily checks
psql -d products -c "
  SELECT 
    'Categories' as type, 
    COUNT(*) as count 
  FROM categories 
  WHERE retailer_id = 4
  
  UNION ALL
  
  SELECT 
    'Products' as type, 
    COUNT(*) 
  FROM products 
  WHERE retailer_id = 4;
"
```

**✅ If stable after 1 week:** Proceed to next retailer

## Phase 3: Full Migration (All Retailers)

Once one retailer is stable, migrate remaining retailers.

### Step 3.1: Migration Schedule

| Week | Retailer | Retailer ID | URL |
|------|----------|-------------|-----|
| 1 | Wellness Warehouse | 4 | https://www.wellnesswarehouse.com |
| 2 | Faithful to Nature | 3 | https://www.faithful-to-nature.co.za |
| 3 | Dis-Chem | 2 | https://www.dischem.co.za |
| 4 | Clicks | 1 | https://clicks.co.za |

### Step 3.2: Per-Retailer Migration

For each retailer, repeat Phase 2 steps:

```bash
# Template command
python -m src.ai_agents.category_extractor.cli \
  --url <RETAILER_URL> \
  --retailer-id <RETAILER_ID>
```

### Step 3.3: Automation Script

Create a migration script:

```bash
#!/bin/bash
# migrate_all_retailers.sh

RETAILERS=(
  "4|https://www.wellnesswarehouse.com|wellnesswarehouse"
  "3|https://www.faithful-to-nature.co.za|faithful-to-nature"
  "2|https://www.dischem.co.za|dischem"
  "1|https://clicks.co.za|clicks"
)

for retailer in "${RETAILERS[@]}"; do
  IFS='|' read -r id url name <<< "$retailer"
  
  echo "Migrating $name (ID: $id)..."
  
  # Backup
  psql -d products -c "COPY (SELECT * FROM categories WHERE retailer_id = $id) 
    TO '/tmp/categories_${name}_backup.csv' CSV HEADER;"
  
  # Clear
  psql -d products -c "DELETE FROM categories WHERE retailer_id = $id;"
  
  # Run AI Agent
  python -m src.ai_agents.category_extractor.cli \
    --url $url \
    --retailer-id $id
  
  # Validate
  psql -d products -c "SELECT COUNT(*) as categories_extracted 
    FROM categories WHERE retailer_id = $id;"
  
  # Test scrape:cp
  npm run scrape:cp scrape --retailer $name
  
  echo "Completed $name migration!"
  echo "---"
done
```

### Step 3.4: Final Validation

```bash
# Run comprehensive validation
psql -d products -f docs/integration_guide/scripts/validate_all_retailers.sql
```

## Phase 4: Deprecate scrape:c

Once all retailers migrated and stable:

### Step 4.1: Update Documentation

- [ ] Update README.md with AI Agent commands
- [ ] Update operational runbooks
- [ ] Archive scrape:c documentation

### Step 4.2: Update Scripts

```bash
# Replace in package.json or wrapper scripts

# OLD:
npm run scrape:c scrape --retailer clicks

# NEW:
python -m src.ai_agents.category_extractor.cli \
  --url https://clicks.co.za \
  --retailer-id 1
```

### Step 4.3: Archive scrape:c Code

```bash
# Move scrape:c to archive (don't delete yet!)
mkdir -p archive/scrape_c_typescript
mv src/scrappers/category_scraper archive/scrape_c_typescript/

# Keep for 3-6 months as safety backup
```

### Step 4.4: Monitor Post-Migration

```bash
# Daily monitoring for 1 month
psql -d products -c "
  SELECT 
    retailer_id,
    COUNT(*) as categories,
    MAX(depth) as max_depth,
    MAX(created_at) as last_updated
  FROM categories
  GROUP BY retailer_id
  ORDER BY retailer_id;
"
```

## Rollback Procedures

### If Issues Found During Migration

```bash
# 1. Stop AI Agent processing
# (Ctrl+C or kill process)

# 2. Restore from backup
psql -d products < backups/categories_before_ai_agent_20251003.sql

# Or for specific retailer:
psql -d products -c "DELETE FROM categories WHERE retailer_id = 1;"
psql -d products -c "\copy categories FROM '/tmp/categories_clicks_backup.csv' CSV HEADER;"

# 3. Resume with scrape:c
npm run scrape:c scrape --retailer clicks
```

### If scrape:cp Fails with AI Agent Data

```sql
-- Restore scrape:c data
\copy categories FROM '/tmp/categories_clicks_backup.csv' CSV HEADER;

-- Investigate schema differences
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'categories';
```

## Success Criteria Checklist

### Per-Retailer Success

- [ ] AI Agent completes extraction without errors
- [ ] Categories count >= previous scrape:c results
- [ ] Hierarchy depth > 0 (subcategories exist)
- [ ] Parent-child relationships valid
- [ ] URLs are accessible
- [ ] scrape:cp reads categories successfully
- [ ] Product URLs extracted
- [ ] scrape:p completes product scraping
- [ ] No regression in product data quality

### Full Migration Success

- [ ] All 4 retailers migrated
- [ ] Pipeline stable for 1+ month
- [ ] No manual intervention required
- [ ] Performance acceptable (<10 min per retailer)
- [ ] Team trained on AI Agent system
- [ ] Documentation updated
- [ ] scrape:c code archived

## Timeline Estimate

| Phase | Duration | Description |
|-------|----------|-------------|
| **Phase 1: Parallel** | 1-2 days | Validate AI Agent with one retailer |
| **Phase 2: Single Retailer** | 1 week | Migrate + monitor one retailer |
| **Phase 3: Full Migration** | 4 weeks | Migrate all retailers (1/week) |
| **Phase 4: Deprecation** | 1 week | Update docs, archive scrape:c |
| **Monitoring** | 1 month | Post-migration stability check |
| **Total** | ~6-7 weeks | Conservative timeline |

**Aggressive Timeline:** 2-3 weeks (parallel migration of multiple retailers)

## Common Issues & Solutions

### Issue: AI Agent extracts fewer categories than scrape:c

**Cause:** Recursive discovery not enabled or misconfigured

**Solution:**
```bash
# Ensure recursive discovery is implemented
# See: docs/category_res_eng_guide/RECURSIVE_DISCOVERY_IMPLEMENTATION.md

# Check max depth setting
python -m src.ai_agents.category_extractor.cli \
  --url https://clicks.co.za \
  --retailer-id 1 \
  --max-depth 5
```

### Issue: scrape:cp doesn't find categories

**Cause:** Missing `retailer_id` or wrong ID used

**Solution:**
```sql
-- Verify retailer_id in database
SELECT DISTINCT retailer_id FROM categories;

-- Should match what scrape:cp expects (1, 2, 3, 4)
```

### Issue: Duplicate categories

**Cause:** AI Agent ran multiple times without clearing

**Solution:**
```sql
-- Remove duplicates, keep latest
DELETE FROM categories a USING categories b
WHERE a.id < b.id 
  AND a.url = b.url 
  AND a.retailer_id = b.retailer_id;
```

## Next Steps

1. ✅ Complete Phase 1 (Parallel Operation)
2. ✅ Validate results with `01_SCHEMA_VALIDATION.md`
3. ✅ Test integration with `03_TESTING_VALIDATION.md`
4. ✅ Proceed to Phase 2 (Single Retailer Migration)

---

**Migration Status:** Ready to begin  
**Recommended Start:** Wellness Warehouse (simplest)  
**Last Updated:** October 3, 2025
