# Migration Strategy: TypeScript to Python AI Agent

## Overview

This document provides a step-by-step plan for migrating from your current TypeScript category scraper to the Python AI agent, with minimal disruption and risk.

## Migration Philosophy

**Parallel Operation → Validation → Gradual Cutover**

- Run both systems simultaneously initially
- Validate AI agent results against TypeScript baseline
- Gradually shift retailers to AI agent
- Keep TypeScript as safety net during transition

## Pre-Migration Checklist

### 1. Current System Documentation

**Capture baseline metrics:**
```bash
# For each retailer, document:
- Total categories currently extracted
- Category hierarchy depth
- Extraction frequency (daily, weekly?)
- Known issues or quirks
- Average extraction time
- Last successful extraction date
```

**Example baseline for Clicks:**
```json
{
  "retailer": "Clicks",
  "retailer_id": 1,
  "baseline_date": "2025-09-30",
  "total_categories": 85,
  "max_depth": 3,
  "extraction_time_avg": "45 seconds",
  "known_issues": [
    "Cloudflare challenges occasionally",
    "See More button sometimes missing"
  ],
  "last_successful": "2025-09-29T14:30:00Z"
}
```

### 2. Environment Preparation

```bash
# 1. LLM Provider Setup (choose one)

# Option A: Ollama (FREE)
curl -fsSL https://ollama.com/install.sh | sh
ollama pull gemma3:1b
ollama serve

# Option B: OpenAI
# Get API key from platform.openai.com

# Option C: Anthropic  
# Get API key from console.anthropic.com

# 2. Python Environment
poetry init
poetry add strands-agents playwright asyncpg pydantic
poetry run playwright install chromium

# 3. Database Backup
pg_dump -U postgres product_scraper > backup_pre_migration_$(date +%Y%m%d).sql

# 4. Test Environment
# Create separate test database if needed
createdb product_scraper_test
```

### 3. Validation Criteria

Define success criteria:
- **Accuracy**: ≥95% match with TypeScript results
- **Completeness**: Find ≥95% of categories
- **Reliability**: ≤5% error rate
- **Performance**: Complete within 15 minutes
- **Cost**: ≤$2 per retailer

## Migration Phases

### Phase 0: Proof of Concept (Week 1)

**Goal**: Validate approach with one retailer

**Steps:**

1. **Choose simplest retailer** (Wellness Warehouse recommended)

2. **Run baseline extraction** with TypeScript:
   ```bash
   npm run scrape:c scrape --retailer wellnesswarehouse
   # Record: categories found, time taken, any issues
   ```

3. **Implement AI agent** (following implementation guide)

4. **Run AI extraction** to separate test table:
   ```sql
   CREATE TABLE categories_ai_test AS 
   SELECT * FROM categories WHERE 1=0;
   ```

5. **Compare results**:
   ```python
   # comparison_script.py
   async def compare_extractions(retailer_id):
       # Get TypeScript results
       ts_categories = await get_categories_typescript(retailer_id)
       
       # Get AI results
       ai_categories = await get_categories_ai(retailer_id)
       
       # Compare
       comparison = {
           'ts_count': len(ts_categories),
           'ai_count': len(ai_categories),
           'missing_in_ai': find_missing(ts_categories, ai_categories),
           'extra_in_ai': find_extra(ts_categories, ai_categories),
           'name_differences': compare_names(ts_categories, ai_categories),
           'url_differences': compare_urls(ts_categories, ai_categories),
       }
       
       return comparison
   ```

6. **Analyze differences**:
   - Are missing categories legitimate (outdated in TypeScript)?
   - Are extra categories valid (new categories found)?
   - Investigate any significant discrepancies

**Success Criteria**:
- ≥90% category match
- All major categories found
- No critical errors
- Cost <$1

**Decision Point**: Proceed to Phase 1 if POC successful

### Phase 1: Parallel Operation (Weeks 2-4)

**Goal**: Run both systems in parallel, validate thoroughly

**Implementation:**

1. **Set up parallel extraction**:
   ```bash
   # Cron job to run both systems
   # TypeScript (existing)
   0 2 * * * cd /path/to/project && npm run scrape:c
   
   # Python AI (new)
   0 3 * * * cd /path/to/project && poetry run python -m ai_agent.cli
   ```

2. **Create comparison dashboard**:
   ```sql
   CREATE VIEW category_comparison AS
   SELECT 
       t.retailer_id,
       t.category_count as ts_count,
       a.category_count as ai_count,
       t.last_run as ts_last_run,
       a.last_run as ai_last_run,
       ABS(t.category_count - a.category_count) as difference,
       CASE 
           WHEN ABS(t.category_count - a.category_count) <= 5 THEN 'OK'
           WHEN ABS(t.category_count - a.category_count) <= 20 THEN 'WARNING'
           ELSE 'ERROR'
       END as status
   FROM typescript_stats t
   JOIN ai_stats a ON t.retailer_id = a.retailer_id;
   ```

3. **Automated validation script**:
   ```python
   # validation_job.py
   import asyncio
   from datetime import datetime
   
   async def daily_validation():
       retailers = [1, 2, 3, 4]  # Clicks, DisChem, FTN, Wellness
       
       results = []
       for retailer_id in retailers:
           comparison = await compare_extractions(retailer_id)
           
           # Alert if significant difference
           if comparison['accuracy'] < 0.90:
               await send_alert(
                   f"Low accuracy for retailer {retailer_id}: "
                   f"{comparison['accuracy']:.2%}"
               )
           
           results.append(comparison)
       
       # Generate daily report
       await generate_report(results, datetime.now())
   
   if __name__ == "__main__":
       asyncio.run(daily_validation())
   ```

4. **Monitor for 2-3 weeks**:
   - Daily review of comparison reports
   - Investigate any discrepancies
   - Refine AI agent based on findings
   - Document patterns and issues

**Success Criteria**:
- 95%+ accuracy across all retailers
- No critical failures
- Cost within budget (<$10/week total)
- Issues understood and documented

### Phase 2: Selective Cutover (Weeks 5-6)

**Goal**: Switch 1-2 retailers to AI agent exclusively

**Strategy**: Start with highest-confidence retailers

1. **Rank retailers by confidence**:
   ```python
   retailer_confidence = {
       'wellnesswarehouse': 0.95,  # Simple, high confidence
       'faithfultonature': 0.88,   # Medium complexity
       'dischem': 0.85,            # Medium-high complexity
       'clicks': 0.80,             # Complex, lower confidence
   }
   ```

2. **Cutover process per retailer**:

   **Step 1: Final validation run**
   ```bash
   # Run both systems one last time
   npm run scrape:c scrape --retailer wellnesswarehouse
   poetry run python -m ai_agent.cli --retailer-id 4
   
   # Compare and verify
   python validation_job.py --retailer 4 --detailed
   ```

   **Step 2: Disable TypeScript scraper**
   ```typescript
   // In config
   const DISABLED_RETAILERS = [4]; // Wellness Warehouse
   
   if (DISABLED_RETAILERS.includes(retailerId)) {
       console.log(`Retailer ${retailerId} migrated to AI agent`);
       return;
   }
   ```

   **Step 3: Update cron to use AI agent**
   ```bash
   # Replace TypeScript job for this retailer
   0 2 * * * poetry run python -m ai_agent.cli --retailer-id 4
   ```

   **Step 4: Monitor closely for 1 week**
   - Daily checks of extraction results
   - Compare with historical TypeScript data
   - Watch for any anomalies

   **Step 5: Rollback plan ready**
   ```bash
   # If issues arise, quick rollback:
   # 1. Re-enable TypeScript scraper
   # 2. Restore from backup if needed
   # 3. Investigate AI agent issue
   ```

3. **Cutover schedule**:
   - **Week 5**: Wellness Warehouse (simplest)
   - **Week 6**: Faithful to Nature (medium complexity)
   - Review and adjust before continuing

**Success Criteria per Retailer**:
- 7 days of successful AI-only extractions
- No data quality issues
- Cost as expected
- No emergency rollbacks needed

### Phase 3: Full Migration (Weeks 7-8)

**Goal**: Migrate remaining retailers, decommission TypeScript scraper

1. **Migrate remaining retailers**:
   - Week 7: Dis-Chem
   - Week 8: Clicks (most complex, save for last)

2. **Update all documentation**:
   ```markdown
   # Update README
   - Mark TypeScript scraper as deprecated
   - Link to AI agent docs
   - Update commands and examples
   
   # Update runbooks
   - New troubleshooting procedures
   - AI agent maintenance guide
   - Cost monitoring procedures
   ```

3. **Archive TypeScript code**:
   ```bash
   # Don't delete yet, just archive
   git checkout -b archive/typescript-scraper
   git add src/scrappers/category_scraper/
   git commit -m "Archive TypeScript category scraper"
   git push origin archive/typescript-scraper
   
   # Keep in main branch but mark deprecated
   echo "DEPRECATED: See docs/migration.md" > src/scrappers/category_scraper/DEPRECATED.md
   ```

4. **Final validation**:
   ```bash
   # Run all retailers with AI agent
   for retailer in 1 2 3 4; do
       poetry run python -m ai_agent.cli --retailer-id $retailer
   done
   
   # Verify results
   psql -d product_scraper -c "
   SELECT retailer_id, COUNT(*), MAX(depth), MAX(created_at)
   FROM categories
   GROUP BY retailer_id
   ORDER BY retailer_id;
   "
   ```

**Success Criteria**:
- All 4 retailers successfully migrated
- 2 weeks of stable AI-only operation
- Cost tracking in place
- Team trained on new system

### Phase 4: Optimization & Cleanup (Weeks 9-10)

**Goal**: Optimize AI agent, remove TypeScript dependencies

1. **Generate blueprints for all retailers**:
   ```bash
   # Each retailer should have a blueprint now
   ls -la blueprints/
   # clicks_v1_2025-09-30.json
   # dischem_v1_2025-09-30.json
   # faithfultonature_v1_2025-09-30.json
   # wellnesswarehouse_v1_2025-09-30.json
   ```

2. **Implement blueprint-first strategy**:
   ```python
   # Updated CLI
   async def extract(retailer_id):
       blueprint_path = f"blueprints/{get_retailer_slug(retailer_id)}_v1.json"
       
       # Try blueprint first
       if os.path.exists(blueprint_path):
           try:
               return await extract_with_blueprint(blueprint_path)
           except ExtractionError:
               # Blueprint failed, fall back to AI
               pass
       
       # Use AI agent
       return await extract_with_ai(retailer_id)
   ```

3. **Optimize costs**:
   - Blueprint usage reduces LLM costs to near-zero
   - Monitor actual costs vs estimates
   - Tune prompts if needed

4. **Remove TypeScript scraper** (if stable):
   ```bash
   # After 4 weeks of successful AI operation
   git rm -r src/scrappers/category_scraper/
   git commit -m "Remove deprecated TypeScript category scraper"
   
   # Keep archive branch for reference
   ```

5. **Update infrastructure**:
   - Remove TypeScript cron jobs
   - Clean up old logs
   - Archive old checkpoints

## Rollback Procedures

### Scenario 1: AI Agent Completely Fails

**Symptoms**: No categories extracted, consistent errors

**Rollback**:
```bash
# 1. Immediately re-enable TypeScript
npm run scrape:c scrape --retailer <retailer-name>

# 2. Restore cron job
crontab -e
# Add back: 0 2 * * * cd /path && npm run scrape:c

# 3. Investigate AI agent issue
tail -f logs/ai_agent.log

# 4. File bug report with details
```

### Scenario 2: AI Agent Produces Incorrect Data

**Symptoms**: Categories found but many are wrong

**Rollback**:
```bash
# 1. Restore from last good TypeScript extraction
psql product_scraper < backup_typescript_$(date +%Y%m%d).sql

# 2. Disable AI agent for this retailer
# Edit config to skip retailer

# 3. Re-run TypeScript scraper
npm run scrape:c scrape --retailer <retailer-name>

# 4. Investigate AI agent issue
# Check prompts, selectors, validation
```

### Scenario 3: Cost Overruns

**Symptoms**: AWS bill unexpectedly high

**Immediate Actions**:
```bash
# 1. Stop all AI agent cron jobs
crontab -e
# Comment out AI agent jobs

# 2. Check AWS costs
aws ce get-cost-and-usage \
    --time-period Start=2025-09-01,End=2025-09-30 \
    --granularity DAILY \
    --metrics BlendedCost

# 3. Investigate cause
# - Are we using blueprints?
# - Excessive retries?
# - Prompt too long?

# 4. Implement cost controls
# - Add cost limits in code
# - Use blueprints exclusively
# - Reduce extraction frequency
```

## Data Validation Checklist

After each migration step:

- [ ] Category count matches baseline (±5%)
- [ ] No orphaned categories (parent_id references valid parent)
- [ ] Depth distribution reasonable (not all depth 0)
- [ ] URLs are valid and absolute
- [ ] Names are clean (no HTML, proper capitalization)
- [ ] No duplicates (same name + parent)
- [ ] Hierarchy makes logical sense
- [ ] Product counts reasonable (if applicable)
- [ ] All major categories present
- [ ] No suspicious categories (Login, Search, etc.)

## Communication Plan

### Internal Team

**Before Migration**:
- Email to team: "Category scraper migration planned"
- Brown bag session: Demo AI agent
- Documentation sharing: Migration plan

**During Migration**:
- Daily Slack updates during parallel operation
- Weekly progress reports
- Immediate notification of issues

**After Migration**:
- Success announcement
- Updated documentation shared
- Training session on new system

### Stakeholders

**Before**:
- Brief stakeholders on benefits and risks
- Get approval for migration plan
- Set expectations on timeline

**During**:
- Weekly status updates
- Flag any significant issues early
- Provide comparison reports

**After**:
- Final report with results and savings
- Document lessons learned
- Celebrate success

## Success Metrics

Track throughout migration:

| Metric | Target | Actual |
|--------|--------|--------|
| Accuracy vs TypeScript | ≥95% | ___ |
| Extraction Success Rate | ≥95% | ___ |
| Average Extraction Time | ≤15 min | ___ |
| Cost per Retailer | ≤$2 | ___ |
| Zero-Day Rollbacks | 0 | ___ |
| Days to Full Migration | ≤56 days | ___ |

## Lessons Learned Template

Document after migration:

```markdown
# Category Scraper Migration - Lessons Learned

## What Went Well
- 
- 
- 

## What Could Be Improved
- 
- 
- 

## Unexpected Challenges
- 
- 
- 

## Recommendations for Future Migrations
- 
- 
- 

## Cost Analysis
- Estimated: $___
- Actual: $___
- Variance: ___

## Timeline
- Estimated: ___ weeks
- Actual: ___ weeks
- Variance: ___
```

## Post-Migration Monitoring

For first 30 days after full migration:

**Daily**:
- Check extraction success rate
- Review error logs
- Verify category counts

**Weekly**:
- Cost analysis (AWS bills)
- Comparison with historical TypeScript data
- Performance metrics review

**Monthly**:
- Blueprint updates if needed
- Deep dive on any recurring issues
- ROI calculation update

## Conclusion

This migration strategy balances risk and speed:
- **Parallel operation** ensures safety
- **Phased approach** allows learning
- **Clear rollback plans** minimize risk
- **Validation at each step** ensures quality

Expected timeline: **8-10 weeks** from start to full migration
Expected effort: **40-60 hours** total
Expected cost: **$50-100** (mostly LLM costs during parallel operation)

The investment in careful migration pays off with a more maintainable, scalable system.
