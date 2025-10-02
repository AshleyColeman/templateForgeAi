# 🚀 TemplateForgeAI - Quick Start Guide

## ⚡ 1-Minute Setup Checklist

```powershell
# 1. Update database password
notepad .env  # Change DB_PASSWORD

# 2. Install Ollama (FREE option)
# Download from: https://ollama.com/download/windows
ollama pull gemma3:1b
ollama serve  # Keep running in background

# 3. Verify setup
python verify_setup.py
```

---

## 📋 Common Commands

### Verify Environment
```powershell
python verify_setup.py
```

### Extract Categories (First Time)
```powershell
# With Ollama (FREE)
python -m src.ai_agents.category_extractor.cli extract `
    --url https://www.wellnesswarehouse.com `
    --retailer-id 1

# With visible browser (for debugging)
python -m src.ai_agents.category_extractor.cli extract `
    --url https://www.wellnesswarehouse.com `
    --retailer-id 1 `
    --no-headless
```

### Reuse Blueprint (Fast & FREE)
```powershell
python -m src.ai_agents.category_extractor.cli execute-blueprint `
    --blueprint src/ai_agents/category_extractor/blueprints/retailer_1_*.json
```

### Run Tests
```powershell
# All tests
pytest tests/

# Specific test
pytest tests/test_category_extractor/test_agent.py -v

# With coverage
pytest --cov=src tests/
```

### View Logs
```powershell
# Real-time log viewing
Get-Content logs/category_extractor.log -Wait -Tail 50

# Search for errors
Select-String -Path logs/category_extractor.log -Pattern "ERROR"
```

---

## 🗄️ Database Quick Reference

```sql
-- Connect to database
psql -U postgres -d products

-- View all categories for retailer
SELECT id, name, url, depth, parent_id 
FROM categories 
WHERE retailer_id = 1 
ORDER BY depth, name 
LIMIT 20;

-- Count categories by depth
SELECT depth, COUNT(*) as count 
FROM categories 
WHERE retailer_id = 1 
GROUP BY depth 
ORDER BY depth;

-- Find root categories
SELECT name, url 
FROM categories 
WHERE retailer_id = 1 AND parent_id IS NULL;

-- View category hierarchy
WITH RECURSIVE cat_tree AS (
    SELECT id, name, url, 0 as level, name as path
    FROM categories 
    WHERE retailer_id = 1 AND parent_id IS NULL
    
    UNION ALL
    
    SELECT c.id, c.name, c.url, ct.level + 1, ct.path || ' > ' || c.name
    FROM categories c
    JOIN cat_tree ct ON c.parent_id = ct.id
)
SELECT REPEAT('  ', level) || name as hierarchy, url
FROM cat_tree
ORDER BY path;

-- Delete all categories for a retailer (for testing)
DELETE FROM categories WHERE retailer_id = 1;
```

---

## 🔧 Configuration Quick Reference

### .env File Sections

```ini
# Database (REQUIRED - Update DB_PASSWORD!)
DB_HOST=localhost
DB_NAME=products
DB_PASSWORD=your_password_here

# LLM Provider (Choose one)
LLM_PROVIDER=ollama          # or openai, anthropic

# Ollama (FREE)
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=gemma3:1b

# OpenAI (Alternative)
# OPENAI_API_KEY=sk-...
# OPENAI_MODEL=gpt-4o-mini

# Anthropic (Alternative)
# ANTHROPIC_API_KEY=sk-ant-...
# ANTHROPIC_MODEL=claude-3-5-sonnet-20241022

# Logging
LOG_LEVEL=INFO              # or DEBUG for verbose
```

---

## 🐛 Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError: strands` | `pip install -r requirements.txt` |
| `Database connection failed` | Check `.env` DB_PASSWORD & PostgreSQL running |
| `Ollama connection refused` | `ollama serve` in another terminal |
| `Playwright browser not found` | `python -m playwright install chromium` |
| No categories extracted | Run with `--no-headless` to see browser |
| Import errors | Check Python path: `$env:PYTHONPATH="."` |

---

## 📁 Important Files

| File | Purpose |
|------|---------|
| `.env` | **YOUR CONFIG** - Update DB_PASSWORD! |
| `verify_setup.py` | Check if everything is installed |
| `BEGINNERS_GUIDE.md` | Complete walkthrough (30 min read) |
| `SETUP_COMPLETE.md` | Detailed setup documentation |
| `src/ai_agents/category_extractor/cli.py` | CLI entry point |
| `src/ai_agents/category_extractor/agent.py` | Main agent logic |
| `logs/category_extractor.log` | Execution logs |
| `blueprints/*.json` | Generated extraction templates |

---

## 🎯 Development Workflow

```powershell
# 1. Make changes to code
notepad src/ai_agents/category_extractor/agent.py

# 2. Run tests
pytest tests/ -v

# 3. Test on real site
python -m src.ai_agents.category_extractor.cli extract `
    --url https://example.com --retailer-id 999 --no-headless

# 4. Check logs
Get-Content logs/category_extractor.log -Tail 100

# 5. Verify database
psql -U postgres -d products -c "SELECT COUNT(*) FROM categories WHERE retailer_id = 999;"
```

---

## 💰 Cost Reference

| Provider | First Run | With Blueprint | Monthly (4 sites) |
|----------|-----------|----------------|-------------------|
| **Ollama** | $0.00 | $0.00 | **$0.00** |
| **OpenAI** | $0.20-0.50 | $0.00 | **~$1-2** |
| **Anthropic** | $1-2 | $0.00 | **~$4-8** |

*Blueprint reuse = $0 for all providers!*

---

## 📚 Learning Path

### Beginner (1 hour)
1. Read `START_HERE.md` (5 min)
2. Read `BEGINNERS_GUIDE.md` (30 min)
3. Run first extraction (15 min)
4. Review logs and database (10 min)

### Intermediate (3 hours)
1. Read `docs/category_res_eng_guide/00_Project_Overview.md`
2. Read `docs/category_res_eng_guide/01_Technical_Specification.md`
3. Study existing code in `src/ai_agents/category_extractor/`
4. Run tests and understand test structure

### Advanced (1 day)
1. Read all engineering guides in `docs/category_res_eng_guide/`
2. Understand blueprint generation process
3. Optimize prompts for your use cases
4. Add new tools or features
5. Deploy to production

---

## 🎓 Key Concepts

### Agent Tools
- **PageAnalyzerTool**: Analyzes webpage structure
- **CategoryExtractorTool**: Executes extraction strategy
- **DatabaseSaverTool**: Saves to PostgreSQL
- **BlueprintGeneratorTool**: Creates reusable templates

### Extraction Flow
```
1. Navigate to URL
2. Analyze page (screenshot + HTML → LLM)
3. LLM identifies navigation type & selectors
4. Extract categories using strategy
5. Build hierarchy (parent-child relationships)
6. Validate data
7. Save to database
8. Generate blueprint for future use
```

### Blueprint Benefits
- **Speed**: 5x faster than AI analysis
- **Cost**: $0 (no LLM calls)
- **Reliability**: Tested strategy
- **Reusability**: Use forever until site changes

---

## 🔗 Quick Links

- **Ollama Download**: https://ollama.com/download/windows
- **OpenAI API Keys**: https://platform.openai.com/api-keys
- **Anthropic Console**: https://console.anthropic.com/
- **Strands Agents Docs**: https://strandsagents.com/latest/
- **Playwright Docs**: https://playwright.dev/python/

---

**Ready to extract?** 🚀

1. Update `.env` with DB password
2. Start Ollama: `ollama serve`
3. Run: `python verify_setup.py`
4. Extract: Follow `BEGINNERS_GUIDE.md`

**Need help?** Check `SETUP_COMPLETE.md` for detailed troubleshooting.
