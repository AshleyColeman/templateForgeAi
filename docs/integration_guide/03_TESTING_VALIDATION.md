# Testing & Validation: AI Agent Integration

## Overview

This document provides comprehensive testing procedures to validate that the AI Agent successfully replaces scrape:c and integrates seamlessly with scrape:cp and scrape:p.

## Test Suite Structure

```
Integration Tests
├── Unit Tests (AI Agent standalone)
├── Schema Validation (Database compatibility)
├── Data Quality Tests (Output validation)
├── Pipeline Integration Tests (scrape:cp + scrape:p)
└── Performance Tests (Speed, resource usage)
```

## Unit Tests: AI Agent Standalone

### Test 1: AI Agent Executes Successfully

```bash
# Test Command
python -m src.ai_agents.category_extractor.cli \
  --url https://clicks.co.za \
  --retailer-id 1

# Expected Output
# ✅ Categories extracted: 3000+
# ✅ Max depth: 4-5
# ✅ Blueprint generated: retailer_1_*.json
# ✅ Exit code: 0
```

**Pass Criteria:**
- Process completes without exceptions
- Exit code = 0
- Log file created in `logs/`
- Blueprint JSON file created

### Test 2: Database Insertion

```sql
-- Verify categories were inserted
SELECT COUNT(*) as total_inserted
FROM categories
WHERE retailer_id = 1
  AND created_at > (NOW() - INTERVAL '1 hour');

-- Expected: > 100 (should be 3000+)
```

**Pass Criteria:**
- Categories inserted into database
- Count > minimum threshold (100+)
- Timestamps recent (within last hour)

### Test 3: Hierarchy Structure

```sql
-- Verify hierarchy was built
SELECT 
  depth,
  COUNT(*) as count,
  ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) as percentage
FROM categories
WHERE retailer_id = 1
GROUP BY depth
ORDER BY depth;

-- Expected distribution example:
-- depth | count | percentage
-- ------|-------|------------
--   0   |   12  |   0.40%
--   1   |  150  |   5.00%
--   2   |  800  |  26.67%
--   3   | 1500  |  50.00%
--   4   |  480  |  16.00%
--   5   |   58  |   1.93%
```

**Pass Criteria:**
- Multiple depth levels exist (depth 0, 1, 2+)
- Reasonable distribution across depths
- Max depth >= 2

## Schema Validation Tests

### Test 4: Required Fields Populated

```sql
-- Check for NULL values in required fields
SELECT 
  COUNT(*) FILTER (WHERE name IS NULL) as null_names,
  COUNT(*) FILTER (WHERE url IS NULL) as null_urls,
  COUNT(*) FILTER (WHERE retailer_id IS NULL) as null_retailer_ids,
  COUNT(*) FILTER (WHERE depth IS NULL) as null_depths
FROM categories
WHERE retailer_id = 1;

-- Expected: All zeros
```

**Pass Criteria:**
- Zero NULL values in required fields
- `name`, `url`, `retailer_id`, `depth` all populated

### Test 5: Parent-Child Integrity

```sql
-- Validate parent_id references
SELECT COUNT(*) as broken_references
FROM categories c1
WHERE c1.retailer_id = 1
  AND c1.parent_id IS NOT NULL
  AND NOT EXISTS (
    SELECT 1 FROM categories c2 WHERE c2.id = c1.parent_id
  );

-- Expected: 0
```

**Pass Criteria:**
- Zero orphan categories
- All `parent_id` values reference existing categories

### Test 6: URL Format Validation

```sql
-- Check URL format
SELECT 
  COUNT(*) as total,
  COUNT(*) FILTER (WHERE url LIKE 'http%') as valid_urls,
  COUNT(*) FILTER (WHERE url NOT LIKE 'http%') as invalid_urls
FROM categories
WHERE retailer_id = 1;

-- Expected: invalid_urls = 0
```

**Pass Criteria:**
- All URLs start with `http://` or `https://`
- No empty or malformed URLs

## Data Quality Tests

### Test 7: Category Name Quality

```sql
-- Check for suspicious category names
SELECT name, url
FROM categories
WHERE retailer_id = 1
  AND (
    LENGTH(name) < 2 OR               -- Too short
    LENGTH(name) > 100 OR             -- Too long
    name LIKE '%<%' OR                -- Contains HTML
    name LIKE '%undefined%' OR        -- JavaScript error
    name LIKE '%null%'                -- Null placeholder
  )
LIMIT 10;

-- Expected: 0 rows or very few edge cases
```

**Pass Criteria:**
- Category names are meaningful
- No HTML tags or JavaScript errors
- Names between 2-100 characters

### Test 8: URL Accessibility

```bash
# Sample URL test (manual or automated)
psql -d products -t -c "
  SELECT url FROM categories 
  WHERE retailer_id = 1 
  ORDER BY RANDOM() 
  LIMIT 5;
" | while read url; do
  echo "Testing: $url"
  curl -I "$url" 2>&1 | grep "HTTP/"
done

# Expected: HTTP 200 OK for most URLs
```

**Pass Criteria:**
- Sample of URLs return HTTP 200
- No 404 errors on category pages
- URLs are accessible

### Test 9: Depth Consistency

```sql
-- Verify depth = parent.depth + 1
SELECT 
  c1.id,
  c1.name,
  c1.depth as child_depth,
  c2.depth as parent_depth,
  c1.depth - c2.depth as depth_difference
FROM categories c1
JOIN categories c2 ON c1.parent_id = c2.id
WHERE c1.retailer_id = 1
  AND c1.depth != c2.depth + 1;

-- Expected: 0 rows
```

**Pass Criteria:**
- All child categories have `depth = parent.depth + 1`
- Zero depth inconsistencies

## Pipeline Integration Tests

### Test 10: scrape:cp Reads Categories

```bash
# Run scrape:cp with AI Agent data
npm run scrape:cp scrape --retailer clicks

# Monitor logs
tail -f logs/category_url_products.log

# Expected output:
# ✅ Categories loaded: 3000+
# ✅ Processing category 1/3000...
# ✅ Product URLs found: X
```

**Pass Criteria:**
- scrape:cp starts without errors
- Categories are read from database
- Processing begins for each category

### Test 11: Product URL Extraction

```sql
-- After scrape:cp completes
SELECT 
  COUNT(DISTINCT cup.category_id) as categories_processed,
  COUNT(*) as total_product_urls
FROM category_url_products cup
JOIN categories c ON cup.category_id = c.id
WHERE c.retailer_id = 1
  AND cup.extraction_date > (NOW() - INTERVAL '1 hour');

-- Expected:
-- categories_processed: 100+ (sample or all)
-- total_product_urls: 1000+ (depends on retailer)
```

**Pass Criteria:**
- Product URLs extracted for multiple categories
- `category_url_products` table populated
- Foreign key constraints satisfied

### Test 12: scrape:p Reads Product URLs

```bash
# Run scrape:p with AI Agent→scrape:cp data
npm run scrape:p scrape --retailer clicks

# Expected:
# ✅ Product URLs loaded from database
# ✅ Processing products...
# ✅ Products scraped: X
```

**Pass Criteria:**
- scrape:p reads from `category_url_products`
- Products are scraped successfully
- `products` table populated

### Test 13: Full Pipeline End-to-End

```bash
#!/bin/bash
# Full pipeline test

echo "=== STAGE 1: AI Agent (Categories) ==="
python -m src.ai_agents.category_extractor.cli \
  --url https://www.wellnesswarehouse.com \
  --retailer-id 4

echo "=== Validate Stage 1 ==="
psql -d products -c "SELECT COUNT(*) as categories FROM categories WHERE retailer_id = 4;"

echo "=== STAGE 2: scrape:cp (Product URLs) ==="
npm run scrape:cp scrape --retailer wellnesswarehouse

echo "=== Validate Stage 2 ==="
psql -d products -c "SELECT COUNT(*) as product_urls FROM category_url_products 
  WHERE category_id IN (SELECT id FROM categories WHERE retailer_id = 4);"

echo "=== STAGE 3: scrape:p (Products) ==="
npm run scrape:p scrape --retailer wellnesswarehouse

echo "=== Validate Stage 3 ==="
psql -d products -c "SELECT COUNT(*) as products FROM products WHERE retailer_id = 4;"

echo "=== Pipeline Complete ==="
```

**Pass Criteria:**
- All 3 stages complete without errors
- Data flows through all tables
- Final product count > 0

## Comparison Tests: AI Agent vs scrape:c

### Test 14: Category Count Comparison

```sql
-- Run both systems and compare

-- AI Agent results (table: categories_ai_agent)
CREATE TEMP TABLE ai_stats AS
SELECT 
  COUNT(*) as total,
  MAX(depth) as max_depth,
  COUNT(DISTINCT parent_id) as unique_parents
FROM categories
WHERE retailer_id = 1;

-- scrape:c results (after running scrape:c)
-- Compare manually or via saved data
SELECT * FROM ai_stats;

-- Expected: AI Agent total >= scrape:c total
```

**Pass Criteria:**
- AI Agent extracts >= categories than scrape:c
- Depth levels similar or greater
- No significant loss of data

### Test 15: Hierarchy Depth Comparison

```bash
# Compare depth distributions

# AI Agent
psql -d products -c "SELECT depth, COUNT(*) FROM categories 
  WHERE retailer_id = 1 GROUP BY depth ORDER BY depth;"

# scrape:c (from backup or previous run)
# Manual comparison

# Expected: Similar distribution
```

**Pass Criteria:**
- Similar depth distribution
- AI Agent reaches same or deeper max depth
- No significant structural differences

### Test 16: URL Coverage Comparison

```bash
# Compare which URLs were discovered

# Export AI Agent URLs
psql -d products -t -c "SELECT url FROM categories WHERE retailer_id = 1 
  ORDER BY url;" > ai_agent_urls.txt

# Export scrape:c URLs (from backup)
psql -d products -t -c "SELECT url FROM categories_backup WHERE retailer_id = 1 
  ORDER BY url;" > scrape_c_urls.txt

# Find differences
comm -3 <(sort ai_agent_urls.txt) <(sort scrape_c_urls.txt)

# Investigate any missing URLs
```

**Pass Criteria:**
- AI Agent finds most/all scrape:c URLs
- Any missing URLs are investigated
- New URLs discovered by AI Agent are valid

## Performance Tests

### Test 17: Execution Time

```bash
# Time AI Agent execution
time python -m src.ai_agents.category_extractor.cli \
  --url https://www.wellnesswarehouse.com \
  --retailer-id 4

# Expected: < 10 minutes for Wellness Warehouse
# Expected: < 30 minutes for Clicks
```

**Pass Criteria:**
- Completes within reasonable time
- Faster than manual scrape:c configuration time
- No infinite loops or hangs

### Test 18: Resource Usage

```bash
# Monitor during execution
# In another terminal:
watch -n 5 'ps aux | grep "python.*category_extractor" | grep -v grep'

# Check:
# - CPU usage reasonable (<100% sustained)
# - Memory usage acceptable (<2GB)
# - No memory leaks
```

**Pass Criteria:**
- Resource usage within acceptable limits
- No memory leaks
- Process completes and exits cleanly

### Test 19: Database Load

```sql
-- Monitor database connections during AI Agent run
SELECT 
  COUNT(*) as active_connections,
  state
FROM pg_stat_activity
WHERE datname = 'products'
GROUP BY state;

-- Expected: < 10 connections
```

**Pass Criteria:**
- Connection count reasonable
- No connection leaks
- Connections closed after execution

## Regression Tests

### Test 20: Existing scrape:cp Functionality

```bash
# After AI Agent migration, verify scrape:cp still works with old data

# Use a retailer that hasn't been migrated yet
npm run scrape:cp scrape --retailer dischem

# Expected: Works exactly as before
```

**Pass Criteria:**
- scrape:cp works with both AI Agent and scrape:c data
- No breaking changes introduced
- Backward compatible

### Test 21: Existing scrape:p Functionality

```bash
# Verify scrape:p unchanged
npm run scrape:p scrape --retailer dischem

# Expected: Works exactly as before
```

**Pass Criteria:**
- scrape:p works with both data sources
- No regression in product scraping
- Data quality maintained

## Test Automation

### Automated Test Suite Script

```bash
#!/bin/bash
# run_integration_tests.sh

RETAILER_ID=4  # Wellness Warehouse for testing
RETAILER_NAME="wellnesswarehouse"
RETAILER_URL="https://www.wellnesswarehouse.com"

echo "=== Integration Test Suite ==="
echo "Retailer: $RETAILER_NAME (ID: $RETAILER_ID)"

# Clean slate
echo "Cleaning previous data..."
psql -d products -c "DELETE FROM categories WHERE retailer_id = $RETAILER_ID;"

# Run AI Agent
echo "Running AI Agent..."
python -m src.ai_agents.category_extractor.cli \
  --url $RETAILER_URL \
  --retailer-id $RETAILER_ID

# Run validation SQL
echo "Running validation tests..."
psql -d products -f docs/integration_guide/scripts/validate_ai_agent_output.sql

# Test scrape:cp integration
echo "Testing scrape:cp integration..."
npm run scrape:cp scrape --retailer $RETAILER_NAME

# Validate product URLs
echo "Validating product URL extraction..."
psql -d products -c "SELECT COUNT(*) as product_urls FROM category_url_products 
  WHERE category_id IN (SELECT id FROM categories WHERE retailer_id = $RETAILER_ID);"

echo "=== Test Suite Complete ==="
```

### Continuous Integration

```yaml
# .github/workflows/integration-test.yml
name: Integration Test - AI Agent

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_DB: products
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      
      - name: Run AI Agent
        run: |
          python -m src.ai_agents.category_extractor.cli \
            --url https://www.wellnesswarehouse.com \
            --retailer-id 4
      
      - name: Validate output
        run: |
          psql -h localhost -U postgres -d products \
            -f docs/integration_guide/scripts/validate_ai_agent_output.sql
```

## Test Results Documentation

### Test Report Template

```markdown
# Integration Test Report

**Date:** 2025-10-03
**Tester:** [Name]
**Retailer:** Clicks (ID: 1)

## Test Results Summary

| Test ID | Test Name | Status | Notes |
|---------|-----------|--------|-------|
| Test 1 | AI Agent Execution | ✅ PASS | Completed in 8 minutes |
| Test 2 | Database Insertion | ✅ PASS | 3,142 categories inserted |
| Test 3 | Hierarchy Structure | ✅ PASS | Max depth: 5 |
| Test 4 | Required Fields | ✅ PASS | All fields populated |
| Test 5 | Parent-Child Integrity | ✅ PASS | Zero broken references |
| ... | ... | ... | ... |

## Issues Found

1. **Issue:** Some category names contain extra whitespace
   **Severity:** Low
   **Status:** Fixed with TRIM() in extraction

2. **Issue:** 3 URLs returned 404
   **Severity:** Medium
   **Status:** Investigating with retailer

## Recommendations

- Proceed with migration
- Monitor for 1 week
- Schedule follow-up validation

**Overall Status:** ✅ PASS - Ready for production
```

## Next Steps

After all tests pass:

1. ✅ Document test results
2. ✅ Proceed with migration (see `02_MIGRATION_CHECKLIST.md`)
3. ✅ Set up monitoring
4. ✅ Train team on AI Agent system

---

**Test Coverage:** 21 tests across 5 categories  
**Pass Threshold:** 95% of tests must pass  
**Last Updated:** October 3, 2025
