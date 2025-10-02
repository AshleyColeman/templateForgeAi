# Selectors Guide: Finding and Defining CSS Selectors

This guide teaches you how to find the right CSS selectors for extracting categories from any retailer website.

## What Are Selectors?

CSS selectors are patterns used to select elements in a web page. The category scraper uses them to locate and extract category information.

**Example**:
```css
div.category-card > h3.title  /* Select h3 with class "title" inside div with class "category-card" */
a[href*="/category/"]         /* Select all links containing "/category/" in href */
ul.menu > li:first-child      /* Select first li in ul with class "menu" */
```

## Using Chrome DevTools

### Step 1: Open DevTools

1. Navigate to the retailer's website
2. Press `F12` or right-click → "Inspect"
3. DevTools panel opens

### Step 2: Inspect Elements

1. Click the "Select element" tool (or press `Ctrl+Shift+C`)
2. Hover over a category link
3. Click to inspect
4. The HTML element is highlighted in the Elements panel

### Step 3: Identify Patterns

Look for:
- **Consistent class names**: `category-card`, `menu-item`, `nav-link`
- **Unique IDs**: `#main-nav`, `#categories-list`
- **Data attributes**: `data-category`, `data-id`
- **Semantic HTML**: `<nav>`, `<article>`, `<section>`

### Step 4: Test Selectors

In the DevTools Console, test your selector:

```javascript
// Test if selector finds elements
document.querySelectorAll('div.category-card')

// Count how many it finds
document.querySelectorAll('div.category-card').length

// Get first element
document.querySelector('div.category-card')
```

### Step 5: Copy Selector

Right-click the element in Elements panel → "Copy" → "Copy selector"

**⚠️ Warning**: DevTools generates verbose selectors like:
```css
#root > div > div.container > div:nth-child(3) > div > ul > li:nth-child(2) > a
```

These are **fragile** and break easily. Simplify them!

## Selector Strategies

### Strategy 1: Use Stable Classes

**Good**:
```css
.category-card
.menu-item
.nav-link
```

**Bad** (likely to change):
```css
.css-1a2b3c4
.sc-fzXfMD
.jsx-2947562893
```

### Strategy 2: Combine Multiple Attributes

If a single class isn't unique:

```css
/* Combine element type + class */
a.category-link

/* Combine classes */
.sidebar .category-item

/* Use data attributes */
[data-type="category"]
```

### Strategy 3: Use Hierarchical Selectors

Navigate the DOM tree:

```css
/* Direct child */
nav.main > ul > li

/* Descendant */
div.menu a.link

/* Multiple levels */
nav.main ul.submenu li.item a
```

### Strategy 4: Use Attribute Selectors

When classes aren't reliable:

```css
/* Exact match */
a[href="/categories"]

/* Contains */
a[href*="/category/"]

/* Starts with */
a[href^="/shop/"]

/* Ends with */
a[href$=".html"]
```

### Strategy 5: Pseudo-Selectors

For specific positions or states:

```css
/* First/last child */
li:first-child
li:last-child

/* Nth child */
li:nth-child(2)

/* Not */
a:not(.disabled)
```

## Selector Types Needed

### 1. Top-Level Menu Items

**What**: Main navigation items (usually in header)

**Example HTML**:
```html
<nav class="main-navigation">
  <ul>
    <li class="menu-item">
      <a href="/beauty">Beauty</a>
    </li>
    <li class="menu-item">
      <a href="/health">Health</a>
    </li>
  </ul>
</nav>
```

**Selectors**:
```typescript
TOP_LEVEL_MENU_ITEM: "nav.main-navigation > ul > li.menu-item"
TOP_LEVEL_MENU_ITEM_LINK: "a"
```

### 2. Flyout/Submenu Panel

**What**: Dropdown or flyout that appears on hover/click

**Example HTML**:
```html
<div class="mega-menu" style="display: block;">
  <!-- Submenu content -->
</div>
```

**Selector**:
```typescript
MAIN_NAV_FLYOUT_PANEL_SELECTOR: "div.mega-menu"
```

### 3. Category List Container

**What**: Container holding all category items

**Example HTML**:
```html
<div class="categories-list">
  <div class="category-card">...</div>
  <div class="category-card">...</div>
  <div class="category-card">...</div>
</div>
```

**Selector**:
```typescript
CATEGORY_LIST_CONTAINER: "div.categories-list"
```

### 4. Category Item

**What**: Individual category element

**Example HTML**:
```html
<div class="category-card">
  <a href="/skincare">
    <h3 class="category-name">Skincare</h3>
    <img src="skincare.jpg" alt="Skincare">
  </a>
</div>
```

**Selector**:
```typescript
CATEGORY_ITEM: "div.category-card"
```

### 5. Category Name

**What**: Element containing the category name text

**Example HTML**:
```html
<h3 class="category-name">Skincare</h3>
```

**Selector**:
```typescript
CATEGORY_NAME_TEXT: "h3.category-name"
```

### 6. Category URL

**What**: Link element with category URL

**Example HTML**:
```html
<a href="/skincare" class="category-link">Skincare</a>
```

**Selector**:
```typescript
CATEGORY_URL_ANCHOR: "a.category-link"
```

### 7. Optional Elements

**"See More" Button**:
```html
<button class="show-more">Show More</button>
```

```typescript
SEE_MORE_BUTTON: "button.show-more"
```

**Product Count**:
```html
<span class="product-count">(42 products)</span>
```

```typescript
CATEGORY_PRODUCT_COUNT: "span.product-count"
```

**Expected Page Loaded Selector**:
```typescript
expectedPageLoadedSelector: "div.categories-list"  // Confirms page loaded
```

## Common Patterns by UI Type

### Pattern 1: Sidebar Filter (Clicks)

```html
<div class="facetValues">
  <ul class="facet_block">
    <li>
      <label class="facet_block-label">
        <input type="hidden" value="/url">
        <span id="facetName_123">Category Name</span>
        <span class="facetValueCount">(15)</span>
      </label>
    </li>
  </ul>
</div>
```

**Selectors**:
```typescript
CATEGORY_LIST_CONTAINER: "div.facetValues ul.facet_block"
CATEGORY_ITEM: "li"
CATEGORY_NAME_TEXT: 'span[id^="facetName_"]'
CATEGORY_URL_ANCHOR: "label.facet_block-label"
CATEGORY_PRODUCT_COUNT: "span.facetValueCount"
```

### Pattern 2: Dropdown Menu (Dis-Chem)

```html
<div class="dropdown-menu">
  <div class="dropdown-column-3">
    <h6>Group Name</h6>
    <a href="/category1" class="dropdown-item">Category 1</a>
    <a href="/category2" class="dropdown-item">Category 2</a>
  </div>
</div>
```

**Selectors**:
```typescript
CATEGORY_LIST_CONTAINER: ".dropdown-menu"
CATEGORY_ITEM: ".dropdown-column-3"
CATEGORY_URL_ANCHOR: "a.dropdown-item"
```

### Pattern 3: Hover Menu (Faithful to Nature)

```html
<li class="ms-level0" id="nav-26">
  <a class="ms-label">Beauty</a>
</li>

<div id="submenu-26" class="ms-flyout">
  <div class="col-category">
    <a class="form-group level1" href="/skincare">Skincare</a>
    <a class="form-group" href="/face">Face</a>
    <a class="form-group" href="/body">Body</a>
  </div>
</div>
```

**Selectors**:
```typescript
TOP_LEVEL_MENU_ITEM: "li.ms-level0"
TOP_LEVEL_MENU_ITEM_LINK: "a.ms-label"
SUBMENU_INDIVIDUAL_COLUMN: "div.col-category"
GENERAL_SUB_CATEGORY_ANCHOR: "a.form-group"
```

### Pattern 4: Grid Layout (Wellness Warehouse)

```html
<div class="categories-grid">
  <div class="category-card">
    <a href="/vitamins">
      <img class="mgz-hover-main" src="vitamins.jpg">
      <h3 class="category-title">Vitamins</h3>
    </a>
  </div>
</div>
```

**Selectors**:
```typescript
CATEGORY_LIST_CONTAINER: "div.categories-grid"
CATEGORY_ITEM: "div.category-card"
CATEGORY_NAME_TEXT: "h3.category-title"
CATEGORY_URL_ANCHOR: "a"
```

## Advanced Selector Techniques

### Using `:has()` Pseudo-Class

Select parents based on children:

```css
/* Select li that has an anchor with specific class */
li:has(a.category-link)

/* Select div that contains an h3 */
div:has(h3.title)
```

### Using `:not()` Pseudo-Class

Exclude certain elements:

```css
/* Select all links except those with class 'disabled' */
a:not(.disabled)

/* Select li that doesn't have class 'hidden' */
li:not(.hidden)
```

### Using Attribute Prefix/Suffix

```css
/* ID starts with 'category' */
[id^="category"]

/* ID ends with 'item' */
[id$="item"]

/* Class contains 'nav' */
[class*="nav"]
```

### Using Multiple Selectors

```css
/* Select any of these */
.class1, .class2, .class3

/* Select all that match both */
.class1.class2

/* Select descendants */
.parent .child
```

## Selector Testing Workflow

### 1. Test in Console

```javascript
// Test selector
const elements = document.querySelectorAll('div.category-card');
console.log('Found:', elements.length);

// Inspect first element
console.log(elements[0]);

// Check if elements have expected properties
elements.forEach(el => {
  const name = el.querySelector('h3')?.textContent;
  const url = el.querySelector('a')?.href;
  console.log({ name, url });
});
```

### 2. Test in Puppeteer

```typescript
// Test selector in Puppeteer context
const elements = await page.$$('div.category-card');
console.log(`Found ${elements.length} elements`);

// Extract data
for (const el of elements) {
  const name = await el.$eval('h3', node => node.textContent);
  const url = await el.$eval('a', node => node.href);
  console.log({ name, url });
}
```

### 3. Validate Stability

Check if selectors work across different:
- Pages (home, category pages)
- Times (visit at different times)
- States (logged in/out)

## Common Pitfalls

### Pitfall 1: Using Generated Classes

**Bad**:
```typescript
CATEGORY_ITEM: "div.css-1a2b3c4d"  // Generated by CSS-in-JS
```

These change on every build!

**Solution**: Use semantic classes or data attributes.

### Pitfall 2: Too Specific Selectors

**Bad**:
```typescript
CATEGORY_ITEM: "body > div#root > div > div > div:nth-child(3) > ul > li"
```

Breaks easily when structure changes.

**Solution**: Use stable, shorter selectors.

### Pitfall 3: Selecting Hidden Elements

Some elements might be hidden or not visible:

```typescript
// Bad: Selects hidden elements too
CATEGORY_ITEM: "div.category"

// Better: Only visible elements
CATEGORY_ITEM: "div.category:not([style*='display: none'])"
```

Or use `{ visible: true }` in `waitForSelector()`.

### Pitfall 4: Assuming Single Element

Always expect multiple elements even if you think there's only one:

```typescript
// Bad: Assumes one element
const element = await page.$('nav.main');

// Good: Handle multiple
const elements = await page.$$('nav.main');
if (elements.length === 0) {
  throw new Error('Nav not found');
}
```

## Selector Maintenance

### When Selectors Break

Symptoms:
- "Selector not found" errors
- No categories extracted
- Timeout waiting for elements

Solutions:
1. Visit the website manually
2. Inspect the HTML structure
3. Update selectors in config file
4. Test with `--debug` flag
5. Save HTML snapshot for comparison

### Version Control for Selectors

Document selector changes:

```typescript
// config/retailer.ts

export const retailerCategorySelectors: CategorySelectors = {
  // Updated 2024-01-15: Site redesign changed class names
  CATEGORY_ITEM: "div.category-card",  // Was: "div.product-category"
  
  // Updated 2024-02-01: Added new container
  CATEGORY_LIST_CONTAINER: "section.categories",  // Was: "div.category-section"
};
```

## Summary

**Key Principles**:
1. Use stable, semantic selectors
2. Test selectors before implementation
3. Keep selectors simple and readable
4. Document selector choices
5. Handle edge cases (hidden elements, dynamic content)
6. Plan for selector breakage (it will happen!)

**Tools**:
- Chrome DevTools (F12)
- Console for testing (`document.querySelectorAll()`)
- Puppeteer for automation testing
- Debug mode for troubleshooting

**Remember**: Good selectors are:
- **Stable**: Don't change often
- **Specific**: Target the right elements
- **Simple**: Easy to understand
- **Documented**: Explain non-obvious choices
