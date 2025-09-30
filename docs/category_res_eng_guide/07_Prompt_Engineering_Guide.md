# Prompt Engineering Guide for Category Extraction

## Overview

The success of the AI agent heavily depends on well-crafted prompts. This guide provides best practices, examples, and optimization techniques for prompting Claude to analyze and extract categories.

## Core Principles

### 1. Be Specific and Structured

**Bad Prompt:**
```
Look at this website and find the categories.
```

**Good Prompt:**
```
Analyze this e-commerce website to identify product categories.

Your task:
1. Locate the main navigation menu
2. Identify all category links
3. Determine the hierarchy (parent-child relationships)
4. Generate CSS selectors for extraction

Return your analysis as JSON with this structure: {...}
```

### 2. Provide Context and Examples

**Enhanced Prompt:**
```
You are analyzing an e-commerce website to extract product categories.

Context:
- Website: {url}
- Industry: Health & Beauty
- Expected categories: 50-200
- Navigation type: Unknown (you need to identify)

Common patterns in e-commerce sites:
1. Hover menus in header navigation
2. Sidebar category lists
3. Footer category links
4. Mega menus with multiple columns

Your goal: Identify which pattern this site uses and provide extraction selectors.
```

### 3. Request Structured Output

Always ask for JSON responses for easy parsing:

```
Return your analysis as valid JSON (no markdown code blocks):
{
  "navigation_type": "hover_menu|sidebar|dropdown|mega_menu|grid|other",
  "selectors": {
    "nav_container": "CSS selector",
    "top_level_items": "CSS selector",
    ...
  },
  "confidence": 0.0-1.0,
  "reasoning": "Your explanation"
}
```

## Page Analysis Prompts

### Vision API Prompt (Screenshot Analysis)

**Purpose**: Analyze a screenshot to identify category navigation.

**Prompt Template:**

```python
VISION_ANALYSIS_PROMPT = """
Analyze this e-commerce website screenshot to identify where product categories are located.

Website URL: {url}
Website Name: {retailer_name}

HTML Structure Excerpt (first 2000 chars):
```html
{html_excerpt}
```

Your Task:
1. VISUAL ANALYSIS
   - Locate the primary navigation menu (header, sidebar, footer)
   - Identify category links visually
   - Note any expandable menus, dropdowns, or hover effects
   - Identify "Shop by Category" or similar sections

2. NAVIGATION PATTERN
   Determine which pattern this site uses:
   - hover_menu: Categories appear on hover
   - sidebar: Static sidebar with category list
   - dropdown: Click-based dropdown menus
   - mega_menu: Large multi-column menu
   - grid: Grid of category tiles/cards
   - accordion: Expandable accordion sections
   - tabs: Tab-based navigation
   - other: Describe the custom pattern

3. CSS SELECTORS
   Provide accurate CSS selectors for:
   - Main navigation container
   - Top-level category items
   - Category link anchors
   - Flyout/submenu panels (if applicable)
   - Subcategory lists
   - Category names (text elements)
   - Product counts (if visible)

4. INTERACTION REQUIREMENTS
   What interactions are needed?
   - Hover over elements
   - Click to expand
   - Scroll to load more
   - Click "Show More" buttons

5. DYNAMIC BEHAVIOR
   - Is content loaded dynamically (AJAX)?
   - Lazy loading present?
   - Infinite scroll?

Return your analysis as JSON:
{
  "navigation_type": "...",
  "category_location": "Describe where categories are (e.g., 'Top navigation bar, center-left')",
  "selectors": {
    "nav_container": "CSS selector for main nav container",
    "top_level_items": "CSS selector for top-level category items (li, div, etc.)",
    "category_links": "CSS selector for <a> tags",
    "category_name": "CSS selector for category name text (span, p, etc.)",
    "flyout_panel": "CSS selector for submenu panel (or null if none)",
    "subcategory_list": "CSS selector for subcategory list (ul, div, etc.)",
    "subcategory_items": "CSS selector for individual subcategory items",
    "product_count": "CSS selector for product count (or null if not visible)",
    "show_more_button": "CSS selector for 'Show More' button (or null)"
  },
  "interactions": [
    {
      "type": "hover|click|scroll|wait",
      "target": "which selector to interact with",
      "wait_for": "selector to wait for after interaction",
      "timeout": 3000,
      "optional": false,
      "description": "Why this interaction is needed"
    }
  ],
  "dynamic_loading": {
    "enabled": true|false,
    "type": "lazy_load|ajax|infinite_scroll|click_more|none",
    "trigger": "scroll|click|auto|none",
    "additional_selectors": {
      "loading_indicator": "selector for loading spinner (or null)",
      "load_more_trigger": "selector for trigger element"
    }
  },
  "complexity": "simple|medium|complex",
  "confidence": 0.0-1.0,
  "reasoning": "Brief explanation of your analysis",
  "warnings": ["Any potential issues or edge cases you noticed"],
  "notes": ["Additional observations"]
}

IMPORTANT:
- Selectors must be specific and unique
- Test mentally if selectors would work
- Consider multiple levels of hierarchy
- Note any unusual patterns
- Be honest about confidence level
"""
```

### HTML-Only Analysis Prompt

**Purpose**: Analyze HTML when screenshot is unavailable.

```python
HTML_ANALYSIS_PROMPT = """
Analyze this HTML structure from an e-commerce website to identify category navigation.

URL: {url}
Retailer: {retailer_name}

HTML Structure:
```html
{html_content}
```

Task: Identify the category navigation structure.

Look for common patterns:
1. <nav> elements with category links
2. <ul><li> structures for menu items
3. Sidebar elements with class names like "category", "menu", "nav"
4. Elements with aria-label="Categories" or similar
5. Links with href patterns like "/category/", "/shop/", "/products/"

Analyze the HTML attributes:
- Class names (look for: menu, nav, category, sidebar, dropdown)
- ID attributes
- Data attributes (data-category, data-menu, etc.)
- ARIA attributes (aria-label, role="navigation")

Return JSON with the same structure as vision analysis, but:
- Be more conservative with confidence (HTML-only is less reliable)
- Note if you need visual confirmation for certain elements
- Suggest alternative selectors when uncertain

{JSON structure...}
"""
```

## Extraction Validation Prompts

### Validate Extracted Data

```python
VALIDATION_PROMPT = """
Review these extracted categories and identify any issues.

Extraction Results:
- Total categories: {total}
- Max depth: {max_depth}
- Categories by depth: {depth_distribution}

Sample categories:
```json
{sample_categories}
```

Check for:
1. DUPLICATES
   - Same name appearing multiple times
   - Same URL with different names
   - Similar names (typos, case differences)

2. HIERARCHY ISSUES
   - Orphaned children (parent_id references non-existent parent)
   - Circular references
   - Inconsistent depth values

3. DATA QUALITY
   - Empty or null names
   - Invalid URLs
   - Missing required fields
   - Suspiciously generic names ("Home", "Search", "Cart")

4. COMPLETENESS
   - Are all major categories likely present?
   - Reasonable depth distribution?
   - Product counts make sense?

5. FALSE POSITIVES
   - Non-category links (Login, Contact, About, etc.)
   - Navigation elements (Previous, Next, Home)
   - Filter options mistaken as categories

Return JSON:
{
  "valid": true|false,
  "issues": [
    {
      "type": "duplicate|hierarchy|quality|completeness|false_positive",
      "severity": "critical|warning|info",
      "description": "Issue description",
      "affected_items": ["category names or IDs"],
      "suggested_fix": "How to fix this"
    }
  ],
  "statistics": {
    "duplicates_found": 0,
    "orphaned_categories": 0,
    "invalid_urls": 0,
    "likely_false_positives": []
  },
  "recommendations": [
    "Suggestions for improving extraction"
  ]
}
"""
```

## Blueprint Generation Prompts

```python
BLUEPRINT_GENERATION_PROMPT = """
Generate a reusable blueprint for extracting categories from this website.

Extraction Context:
- URL: {url}
- Retailer: {retailer_name}
- Navigation type: {nav_type}
- Categories found: {total_categories}
- Max depth: {max_depth}
- Extraction duration: {duration_ms}ms

Successful Strategy Used:
```json
{strategy}
```

Observed Edge Cases:
{edge_cases}

Create a comprehensive blueprint that includes:
1. All selectors that worked
2. Required interaction steps in order
3. Handling for edge cases encountered
4. Validation rules based on this extraction
5. Notes for future extractions

The blueprint should be detailed enough that a non-AI scraper could use it.

Return JSON following the blueprint schema:
{blueprint_schema}

Add detailed notes about:
- Any timing-sensitive interactions
- Elements that may change seasonally
- Promotional content to ignore
- Rate limiting observed
- Bot detection measures
"""
```

## Prompt Optimization Techniques

### 1. Iterative Refinement

Start simple, then add details:

**Iteration 1 (Basic):**
```
Identify categories on this e-commerce site.
```

**Iteration 2 (Structured):**
```
Analyze this site and:
1. Find category navigation
2. Provide CSS selectors
3. Return as JSON
```

**Iteration 3 (Detailed):**
```
Analyze this e-commerce site's category structure.
- Identify navigation pattern
- Provide precise selectors
- Note interaction requirements
- Return structured JSON
[Include full prompt details]
```

### 2. Few-Shot Learning

Provide examples for better results:

```python
FEW_SHOT_PROMPT = """
Here are examples of category structures from similar sites:

Example 1 - Sidebar Navigation:
{
  "navigation_type": "sidebar",
  "selectors": {
    "nav_container": "aside.category-sidebar",
    "category_links": "ul.categories > li > a"
  }
}

Example 2 - Hover Menu:
{
  "navigation_type": "hover_menu",
  "selectors": {
    "nav_container": "nav.main-menu",
    "top_level_items": "li.menu-item",
    "flyout_panel": "div.submenu"
  }
}

Now analyze this website following the same pattern:
[Screenshot and HTML]
```

### 3. Chain-of-Thought

Guide the model through reasoning steps:

```
Let's analyze this step by step:

Step 1: Visual Inspection
Look at the screenshot and describe what you see in the navigation area.

Step 2: HTML Correlation
Match what you see visually with the HTML structure provided.

Step 3: Pattern Recognition
Which navigation pattern does this match (hover menu, sidebar, etc.)?

Step 4: Selector Generation
Based on the pattern, generate CSS selectors.

Step 5: Interaction Planning
What interactions are needed to extract all categories?

Step 6: Validation
Review your analysis and rate your confidence.

Now provide your complete analysis as JSON.
```

### 4. Confidence Calibration

Ask the model to assess its own confidence:

```
After providing your analysis, rate your confidence:

Confidence Score (0.0-1.0):
- 0.9-1.0: Very confident, selectors tested mentally, clear pattern
- 0.7-0.8: Confident, but some ambiguity exists
- 0.5-0.6: Moderate confidence, may need validation
- 0.3-0.4: Low confidence, complex or unclear structure
- 0.0-0.2: Very uncertain, manual inspection recommended

Also provide:
- "certain_about": ["aspects you're confident in"]
- "uncertain_about": ["aspects that need validation"]
- "needs_human_review": true|false
```

## Error Handling Prompts

### When Extraction Fails

```python
ERROR_ANALYSIS_PROMPT = """
The category extraction failed with this error:
{error_message}

Context:
- URL: {url}
- Strategy attempted: {strategy}
- Stage failed: {stage}

Analyze what went wrong:

1. LIKELY CAUSE
   What probably caused this failure?
   - Invalid selectors?
   - Dynamic content not loaded?
   - Bot detection?
   - Unexpected page structure?

2. DIAGNOSTIC STEPS
   What should we check?

3. ALTERNATIVE APPROACHES
   Suggest 2-3 different strategies to try.

4. RISK ASSESSMENT
   Is this a temporary issue or fundamental problem?

Return JSON:
{
  "likely_cause": "...",
  "diagnostic_steps": ["step 1", "step 2"],
  "alternative_strategies": [
    {
      "approach": "...",
      "selectors": {...},
      "confidence": 0.0-1.0
    }
  ],
  "risk_level": "low|medium|high",
  "recommendation": "retry|try_alternative|manual_intervention"
}
"""
```

## Testing Prompts

### Test Selector Validity

```python
SELECTOR_TEST_PROMPT = """
Given this HTML snippet, validate if these selectors would work:

HTML:
```html
{html_sample}
```

Selectors to test:
{selectors_json}

For each selector:
1. Would it match any elements?
2. How many elements would it match?
3. Are the matched elements what we expect?
4. Any potential issues (too broad, too specific, fragile)?

Return JSON:
{
  "results": [
    {
      "selector_name": "...",
      "selector": "...",
      "would_match": true|false,
      "match_count": 0,
      "matched_elements_sample": ["<a>Category 1</a>"],
      "issues": ["too broad", "fragile ID selector"],
      "recommendation": "use|modify|replace",
      "alternative_selector": "..." or null
    }
  ]
}
"""
```

## Prompt Variables Reference

Common variables to inject into prompts:

```python
PROMPT_VARIABLES = {
    "url": "Website URL",
    "retailer_name": "Retailer name",
    "retailer_id": "Database ID",
    "html_content": "Page HTML",
    "html_excerpt": "First N chars of HTML",
    "screenshot_b64": "Base64 screenshot",
    "nav_type": "Navigation type",
    "total_categories": "Count of categories",
    "max_depth": "Maximum depth",
    "strategy": "Extraction strategy JSON",
    "edge_cases": "Observed edge cases",
    "error_message": "Error details",
    "duration_ms": "Extraction time",
    "confidence": "Confidence score",
}
```

## Prompt Templates Library

Store reusable prompts:

```python
# prompts.py

PROMPTS = {
    "vision_analysis": VISION_ANALYSIS_PROMPT,
    "html_analysis": HTML_ANALYSIS_PROMPT,
    "validation": VALIDATION_PROMPT,
    "blueprint": BLUEPRINT_GENERATION_PROMPT,
    "error_analysis": ERROR_ANALYSIS_PROMPT,
    "selector_test": SELECTOR_TEST_PROMPT,
}

def get_prompt(prompt_name: str, **kwargs) -> str:
    """Get and format a prompt template."""
    template = PROMPTS[prompt_name]
    return template.format(**kwargs)
```

## Best Practices Summary

1. **Be Explicit**: Don't assume the model knows what you want
2. **Structure Output**: Always request JSON for programmatic parsing
3. **Provide Context**: Include website type, industry, expectations
4. **Use Examples**: Show what good output looks like
5. **Request Confidence**: Ask model to assess its own certainty
6. **Handle Uncertainty**: Allow model to express what it doesn't know
7. **Iterate**: Refine prompts based on results
8. **Version Prompts**: Track changes and improvements
9. **Test Thoroughly**: Validate prompts across different sites
10. **Monitor Costs**: Shorter prompts = lower costs

## Measuring Prompt Effectiveness

Track metrics:
- **Accuracy**: % of correct extractions
- **Precision**: False positives rate
- **Recall**: False negatives rate
- **Confidence Correlation**: Do high-confidence results perform better?
- **Token Usage**: Prompt length vs. result quality
- **Cost**: Total $ spent per extraction

Optimize based on data!
