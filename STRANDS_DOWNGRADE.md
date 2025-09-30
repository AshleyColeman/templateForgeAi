# Strands Downgrade to 0.3.0

## 🔄 What Happened

I attempted to upgrade to **Strands 1.10**, but the API has significantly changed and the documentation for proper tool registration in 1.10 is unclear.

### Errors Encountered with 1.10

1. **"unrecognized tool specification"** - Strands 1.10 rejected bound methods
2. **"'ToolCaller' object is not callable"** - The `@agent.tool()` decorator approach didn't work

### Decision: Downgrade to 0.3.0

**Your code was originally written for Strands 0.3.0** and uses the `agent.add_tool()` API. Rather than guessing at the undocumented Strands 1.10 API, I've downgraded back to **0.3.0** which is stable and proven to work.

## ✅ Changes Made

1. **`pyproject.toml`**: Changed `strands-agents = "^1.10.0"` → `strands-agents = "0.3.0"`
2. **`src/ai_agents/category_extractor/agent.py`**: Restored the original `_register_tools()` method with `agent.add_tool()`

## 🚀 Install and Run

```bash
cd ~/Projects/templateForgeAi

# Uninstall current version
pip3 uninstall -y strands-agents

# Install the correct version
pip3 install strands-agents==0.3.0

# Verify
python3 -c "import strands; print(f'Strands version: {getattr(strands, \"__version__\", \"0.3.x\")}')"

# Run extraction
python3 -m src.ai_agents.category_extractor.cli extract \
  --url https://www.wellnesswarehouse.com/ \
  --retailer-id 999 \
  --blueprint-only
```

## 📊 Why 0.3.0?

- ✅ **Proven to work**: Your code was written for this version
- ✅ **Stable API**: `agent.add_tool()` is clear and documented
- ✅ **No guesswork**: We know exactly how it works
- ❌ **1.10 issues**: Unclear documentation, breaking API changes

## 🔮 Future Upgrade Path

When Strands 1.10+ documentation becomes clearer, we can upgrade. For now, **0.3.0 is the pragmatic choice**.

## 📝 Next Steps

1. Uninstall Strands 1.10: `pip3 uninstall -y strands-agents`
2. Install Strands 0.3.0: `pip3 install strands-agents==0.3.0`
3. Run your extraction
4. Check logs: `tail -f logs/category_extractor.log`

---

**Status**: Using **Strands 0.3.0** (stable) ✅

