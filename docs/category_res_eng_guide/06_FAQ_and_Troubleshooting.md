# FAQ and Troubleshooting Guide

## Frequently Asked Questions

### General Questions

**Q: How is this different from the existing TypeScript scraper?**

A: The AI agent automatically discovers category structure without manual configuration. The TypeScript scraper requires hand-coded selectors for each retailer.

**Q: How much does it cost to extract categories from one website?**

A: Approximately $0.50-$2 per site, depending on:
- Number of LLM calls (typically 3-5)
- Use of vision API (screenshot analysis)
- Site complexity
- Token usage

Claude 4 Sonnet pricing (via Bedrock):
- Input: $3 per 1M tokens
- Output: $15 per 1M tokens

**Q: How long does extraction take?**

A: Typically 5-15 minutes per site, depending on:
- Site complexity
- Number of categories
- Dynamic loading requirements
- Network speed

**Q: Can it handle websites that require login?**

A: Not currently. The agent is designed for publicly accessible category pages. Authentication would need to be added as a separate feature.

**Q: What happens if the website structure changes?**

A: The AI agent can be re-run to analyze the new structure. Unlike the hardcoded TypeScript scraper, it will adapt automatically.

**Q: Can I use the generated blueprints instead of running the AI agent every time?**

A: Yes! Once a blueprint is generated, you can use it for fast, non-AI extractions. This saves both time and costs.

### Technical Questions

**Q: Why use Strands Agents instead of LangChain or other frameworks?**

A: Strands Agents provides:
- Native Amazon Bedrock integration
- Simpler code-first approach
- Better observability
- Production-ready features

You can adapt the code to LangChain if preferred.

**Q: Why Playwright over Puppeteer for Python?**

A: Playwright offers:
- Better async support in Python
- More reliable selector engine
- Better network interception
- Multi-browser support
- Active maintenance

**Q: How does the agent handle dynamic content?**

A: The agent can:
- Detect lazy loading patterns
- Handle infinite scroll
- Click "Show More" buttons
- Wait for AJAX requests
- Interact with dynamic menus

**Q: Can it extract from JavaScript-heavy SPAs?**

A: Yes, Playwright renders JavaScript before extraction. However, very complex SPAs may require additional wait strategies.

**Q: How accurate is the extraction?**

A: Typically 90-95% accurate. The agent includes confidence scores. Manual review is recommended for critical data.

## Common Issues and Solutions

### Issue 1: AWS Bedrock Access Denied

**Error**:
```
botocore.exceptions.ClientError: An error occurred (AccessDeniedException) 
when calling the InvokeModel operation: User is not authorized to perform: 
bedrock:InvokeModel
```

**Solution**:
1. Verify AWS credentials are configured:
   ```bash
   aws configure
   aws sts get-caller-identity
   ```

2. Enable model access in Bedrock console:
   - Go to AWS Console → Bedrock → Model Access
   - Request access to Claude 4 Sonnet
   - Wait for approval (usually instant)

3. Verify IAM permissions include:
   ```json
   {
     "Effect": "Allow",
     "Action": [
       "bedrock:InvokeModel",
       "bedrock:InvokeModelWithResponseStream"
     ],
     "Resource": "*"
   }
   ```

### Issue 2: Database Connection Failed

**Error**:
```
asyncpg.exceptions.InvalidCatalogNameError: database "product_scraper" does not exist
```

**Solution**:
1. Create the database:
   ```bash
   psql -U postgres
   CREATE DATABASE product_scraper;
   ```

2. Run migrations:
   ```bash
   # If using Prisma
   npx prisma migrate deploy
   ```

3. Verify connection:
   ```bash
   psql -h localhost -U postgres -d product_scraper -c "SELECT version();"
   ```

### Issue 3: Playwright Browser Not Found

**Error**:
```
playwright._impl._api_types.Error: Executable doesn't exist at 
/home/user/.cache/ms-playwright/chromium-1234/chrome-linux/chrome
```

**Solution**:
```bash
# Install browsers
poetry run playwright install chromium

# Or with system dependencies
poetry run playwright install --with-deps chromium
```

### Issue 4: Bot Detection / Cloudflare Challenge

**Error**:
```
BotDetectionError: Cloudflare challenge detected
```

**Solution**:
1. Increase timeout in config:
   ```python
   CLOUDFLARE_CHALLENGE_TIMEOUT = 120000  # 2 minutes
   ```

2. Use stealth mode (already enabled in agent)

3. Add delays between requests:
   ```python
   await page.wait_for_timeout(random.randint(2000, 5000))
   ```

4. Use residential proxies (if needed):
   ```python
   context = await browser.new_context(
       proxy={
           "server": "http://proxy.example.com:8080",
           "username": "user",
           "password": "pass"
       }
   )
   ```

### Issue 5: Categories Not Found

**Error**:
```
ExtractionError: No categories found on page
```

**Solution**:
1. Check if page loaded correctly:
   ```bash
   # Run with --no-headless to see browser
   python -m cli --url https://example.com --retailer-id 1 --no-headless
   ```

2. Take screenshot for debugging:
   ```python
   await page.screenshot(path="debug.png", full_page=True)
   ```

3. Inspect HTML structure:
   ```python
   html = await page.content()
   print(html[:5000])
   ```

4. Try manual selector inspection:
   ```python
   # Test selectors directly
   nav = await page.query_selector("nav")
   print(f"Nav found: {nav is not None}")
   ```

### Issue 6: Memory Leaks in Long Extractions

**Symptoms**: Memory usage grows continuously, eventually crashes

**Solution**:
1. Ensure browser cleanup:
   ```python
   async def cleanup(self):
       if self.page:
           await self.page.close()
       if self.browser:
           await self.browser.close()
       if self.playwright:
           await self.playwright.stop()
   ```

2. Use context managers:
   ```python
   async with async_playwright() as p:
       browser = await p.chromium.launch()
       # ... work ...
       # Automatically cleaned up
   ```

3. Close pages between extractions:
   ```python
   for url in urls:
       page = await context.new_page()
       # ... extract ...
       await page.close()  # Important!
   ```

### Issue 7: Selectors Invalid After Site Update

**Error**:
```
ValidationError: Selector 'nav.main-menu' not found
```

**Solution**:
1. Re-run the AI agent to analyze new structure:
   ```bash
   python -m cli --url https://example.com --retailer-id 1
   ```

2. Generate new blueprint

3. Update database with new blueprint

4. Compare old vs new blueprint:
   ```bash
   diff blueprints/site_v1.json blueprints/site_v2.json
   ```

### Issue 8: Rate Limiting

**Error**:
```
HTTP 429: Too Many Requests
```

**Solution**:
1. Add delays between requests:
   ```python
   await page.wait_for_timeout(random.randint(1000, 3000))
   ```

2. Implement exponential backoff:
   ```python
   from tenacity import retry, stop_after_attempt, wait_exponential
   
   @retry(
       stop=stop_after_attempt(3),
       wait=wait_exponential(multiplier=1, min=4, max=10)
   )
   async def fetch_with_retry(page, url):
       return await page.goto(url)
   ```

3. Use multiple IP addresses (proxy rotation)

### Issue 9: Vision API Errors

**Error**:
```
anthropic.APIError: Invalid image format
```

**Solution**:
1. Verify image encoding:
   ```python
   import base64
   screenshot = await page.screenshot()
   b64 = base64.b64encode(screenshot).decode('utf-8')
   ```

2. Check image size (max 5MB for Anthropic):
   ```python
   if len(screenshot) > 5 * 1024 * 1024:
       # Resize or compress
       screenshot = await page.screenshot(
           full_page=False,  # Viewport only
           quality=80  # For JPEG
       )
   ```

3. Fallback to HTML-only analysis:
   ```python
   try:
       analysis = await analyze_with_vision(screenshot)
   except Exception:
       analysis = await analyze_html_only(html)
   ```

## Debugging Tips

### Enable Debug Logging

```python
# In config
LOG_LEVEL=DEBUG

# Or in code
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Save Debug Screenshots

```python
# After each major step
await page.screenshot(path=f"debug_{step}.png")
```

### Inspect Network Traffic

```python
# Log all requests
page.on("request", lambda req: print(f"→ {req.method} {req.url}"))
page.on("response", lambda res: print(f"← {res.status} {res.url}"))
```

### Test Selectors in Browser Console

```javascript
// In browser DevTools console
document.querySelectorAll('nav.main-menu li')
// Check if elements are found
```

### Use Playwright Inspector

```bash
# Launch with inspector
PWDEBUG=1 python -m cli --url https://example.com --retailer-id 1
```

### Check Database State

```sql
-- Count categories by retailer
SELECT retailer_id, COUNT(*) 
FROM categories 
GROUP BY retailer_id;

-- Check for orphaned categories
SELECT * FROM categories 
WHERE parent_id IS NOT NULL 
  AND parent_id NOT IN (SELECT id FROM categories);

-- Verify hierarchy
WITH RECURSIVE cat_tree AS (
    SELECT id, name, parent_id, 0 AS depth
    FROM categories
    WHERE parent_id IS NULL AND retailer_id = 1
    
    UNION ALL
    
    SELECT c.id, c.name, c.parent_id, ct.depth + 1
    FROM categories c
    JOIN cat_tree ct ON c.parent_id = ct.id
)
SELECT depth, COUNT(*) 
FROM cat_tree 
GROUP BY depth 
ORDER BY depth;
```

## Performance Optimization

### 1. Reduce LLM Calls

- Use blueprint after first successful extraction
- Cache analysis results
- Batch multiple pages if possible

### 2. Optimize Browser Usage

```python
# Disable unnecessary features
await browser.new_context(
    java_script_enabled=True,  # Keep JS
    images_enabled=False,      # Skip images
    has_touch=False,
    is_mobile=False
)
```

### 3. Parallel Extractions

```python
# Extract multiple retailers in parallel
import asyncio

async def extract_all(retailers):
    tasks = [
        extract_retailer(r) for r in retailers
    ]
    return await asyncio.gather(*tasks)
```

### 4. Database Connection Pooling

```python
# Use connection pool
pool = await asyncpg.create_pool(
    min_size=5,
    max_size=20,
    command_timeout=60
)
```

## Getting Help

If you're still stuck:

1. **Check logs**: Review full logs for error details
2. **Search issues**: Check GitHub issues for similar problems
3. **Enable debug mode**: Run with maximum logging
4. **Ask for help**: Open an issue with:
   - Full error message
   - Log excerpt
   - Steps to reproduce
   - Environment details (OS, Python version, etc.)

## Best Practices

1. **Always test in non-headless mode first** to see what's happening
2. **Save screenshots** at each major step for debugging
3. **Use blueprints** for repeated extractions to save costs
4. **Monitor LLM costs** via AWS Cost Explorer
5. **Validate extracted data** before assuming it's correct
6. **Keep blueprints versioned** as sites change
7. **Set reasonable timeouts** (60-120 seconds for complex pages)
8. **Handle errors gracefully** with retries and fallbacks
9. **Log everything** during development
10. **Test with multiple retailers** before deploying
