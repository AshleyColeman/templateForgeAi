# Strands 1.10 Tool Registration Fix

## ✅ What I Fixed

### The Problem
Strands 1.10 rejected bound methods with:
```
tool=<<bound method PageAnalyzerTool.analyze...>>> | unrecognized tool specification
```

### The Solution
Strands 1.10 uses the **`@agent.tool()` decorator pattern**. Tools must be:
1. Standalone functions (not bound methods)
2. Decorated with `@agent.tool()`
3. Have proper type hints and docstrings

### Changes Made

**File**: `src/ai_agents/category_extractor/agent.py`

**Before** (broken):
```python
# Trying to pass bound methods to constructor
tools = [
    self.page_analyzer.analyze,
    self.category_extractor.extract,
    self.blueprint_generator.generate
]
return StrandsAgent(model=model, tools=tools)  # ❌ Doesn't work
```

**After** (fixed):
```python
# Create agent first
self.agent = StrandsAgent(model=model)

# Then register tools with @agent.tool() decorator
@self.agent.tool()
async def analyze_page(url: str, force_refresh: bool = False) -> dict:
    """Analyze webpage structure..."""
    return await self.page_analyzer.analyze(url, force_refresh)

@self.agent.tool()
async def extract_categories(url: str, parent_id: int = None, depth: int = 0) -> dict:
    """Extract categories..."""
    return await self.category_extractor.extract(url, parent_id, depth)

@self.agent.tool()
async def generate_blueprint(analysis: dict, categories: list) -> dict:
    """Generate blueprint..."""
    return await self.blueprint_generator.generate(analysis, categories)
```

## 🧪 Test It

```bash
cd ~/Projects/templateForgeAi

# Run test
python3 test_strands_update.py

# Run actual extraction
python3 -m src.ai_agents.category_extractor.cli extract \
  --url https://www.wellnesswarehouse.com/ \
  --retailer-id 999 \
  --blueprint-only
```

## 📋 What You'll See

### ✅ Success Output
No more "unrecognized tool specification" errors!

### ⚠️ LLM Response Issue
You may still see:
```
Ollama API error: Failed to parse LLM response
```

**This is a different issue**: The `gemma3:1b` model is returning template JSON instead of real data. This happens because:
1. The model is very small (1 billion parameters)
2. It's returning example/placeholder JSON with comments
3. Our parser expects valid, clean JSON

**Fix**: Try a better model like `llama3.2:3b` or `qwen2.5:7b`:

```bash
# In your .env file, change:
OLLAMA_MODEL=llama3.2:3b
# or
OLLAMA_MODEL=qwen2.5:7b
```

## 🔍 Verification

The tool registration is now fixed. You should see in logs:
- Tools registered with proper function names
- No "unrecognized tool specification" errors
- Agent can actually call the tools

---

**Status**: Tool registration **FIXED** ✅  
**Next**: Improve model quality for better LLM responses

