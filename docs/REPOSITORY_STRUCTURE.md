# 📁 TemplateForgeAI Repository Structure

**Last Updated**: 2025-10-02

---

## 🎯 Root Directory (Clean!)

```
templateForgeAi/
├── README.md              # Main documentation & project overview
├── QUICK_START.md         # Quick reference for common commands
├── requirements.txt       # Python dependencies (pip install -r requirements.txt)
├── pyproject.toml         # Poetry configuration (alternative to requirements.txt)
├── Makefile               # Build and test commands
├── .env                   # Your configuration (gitignored)
└── .gitignore             # Git ignore rules
```

---

## 📚 Documentation (`docs/`)

### Setup Guides (`docs/setup/`)
- **`SETUP_COMPLETE.md`** - Comprehensive setup guide with troubleshooting
- **`BEGINNERS_GUIDE.md`** - Complete walkthrough with Wellness Warehouse example
- **`OLLAMA_FIX.md`** - Ollama model configuration and troubleshooting

### Usage Guides (`docs/usage/`)
- **`BLUEPRINT_ONLY_MODE.md`** - How to generate templates without saving to database
- **`TEST_WELLNESS_WAREHOUSE.md`** - Testing guide for Wellness Warehouse extraction

### Fix Documentation (`docs/fixes/`)
- **`SIDEBAR_FIX_APPLIED.md`** - Technical explanation of sidebar navigation fix
- **`TIMEOUT_FIX.md`** - Technical explanation of Ollama timeout fix

### Engineering Guides (`docs/category_res_eng_guide/`)
- Detailed technical documentation
- Architecture and design decisions
- Implementation guides
- Prompt engineering
- FAQ and troubleshooting

---

## 🔧 Scripts (`scripts/`)

- **`test_ollama.py`** - Diagnostic tool to test Ollama connectivity and performance
- **`verify_setup.py`** - Verify all dependencies and configuration are correct

**Usage:**
```bash
python scripts/verify_setup.py
python scripts/test_ollama.py
```

---

## 💻 Source Code (`src/`)

```
src/ai_agents/category_extractor/
├── agent.py                    # Main AI agent orchestrator
├── cli.py                      # Command-line interface
├── config.py                   # Configuration management
├── database.py                 # PostgreSQL integration
├── llm_client.py               # LLM provider abstraction
├── errors.py                   # Custom exceptions
│
├── tools/                      # Agent tools
│   ├── page_analyzer.py        # Page analysis with LLM
│   ├── category_extractor.py   # Category extraction logic
│   ├── blueprint_generator.py  # Template generation
│   └── validators.py           # Data validation
│
├── utils/                      # Utilities
│   ├── logger.py               # Logging configuration
│   ├── url_utils.py            # URL normalization
│   └── browser_manager.py      # Playwright wrapper
│
└── blueprints/                 # Generated extraction templates
    └── *.json                  # Blueprint files (gitignored)
```

---

## 🧪 Tests (`tests/`)

```
tests/test_category_extractor/
├── test_agent.py               # Agent tests
├── test_config.py              # Configuration tests
├── test_database.py            # Database tests
├── test_tools.py               # Tool tests
└── fixtures/                   # Test fixtures
```

**Run tests:**
```bash
pytest tests/
pytest tests/ -v                # Verbose
pytest tests/ --cov            # With coverage
```

---

## 📝 Logs (`logs/`)

- **`category_extractor.log`** - Runtime logs from extractions
- Automatically rotated (10 MB max, 30 days retention)

**View logs:**
```bash
# Real-time
Get-Content logs/category_extractor.log -Wait -Tail 50

# Search for errors
Select-String -Path logs/category_extractor.log -Pattern "ERROR"
```

---

## 🎯 Quick Navigation

### I want to...

**Get started:**
→ Read `README.md` then `QUICK_START.md`

**Set up the project:**
→ Follow `docs/setup/SETUP_COMPLETE.md`

**Learn how it works:**
→ Read `docs/setup/BEGINNERS_GUIDE.md`

**Generate a blueprint/template:**
→ See `docs/usage/BLUEPRINT_ONLY_MODE.md`

**Understand the fixes:**
→ Check `docs/fixes/SIDEBAR_FIX_APPLIED.md` and `TIMEOUT_FIX.md`

**Troubleshoot issues:**
→ Run `python scripts/test_ollama.py`
→ Check `docs/setup/OLLAMA_FIX.md`

**Understand the architecture:**
→ Read `docs/category_res_eng_guide/00_Project_Overview.md`

**Run tests:**
→ `pytest tests/`

**View logs:**
→ `logs/category_extractor.log`

---

## 📊 File Count Summary

| Location | Files | Purpose |
|----------|-------|---------|
| **Root** | 7 | Essential project files only |
| **docs/setup/** | 3 | Setup and installation guides |
| **docs/usage/** | 2 | Usage documentation |
| **docs/fixes/** | 2 | Technical fix explanations |
| **docs/category_res_eng_guide/** | ~20 | Detailed engineering docs |
| **scripts/** | 2 | Utility scripts |
| **src/** | ~15 | Source code |
| **tests/** | ~10 | Test suite |

**Total**: ~60 files (down from 90+)

---

## 🎉 Benefits of Clean Structure

✅ **Easy to navigate** - Everything has a logical place
✅ **Clear separation** - Setup vs usage vs technical docs
✅ **Quick access** - Essential files in root
✅ **Maintainable** - Easy to find and update docs
✅ **Professional** - Clean, organized repository

---

## 🔄 Maintenance

### Adding New Documentation
- Setup guides → `docs/setup/`
- Usage guides → `docs/usage/`
- Fix explanations → `docs/fixes/`
- Engineering docs → `docs/category_res_eng_guide/`

### Adding New Scripts
- Utility scripts → `scripts/`
- Test scripts → `tests/`

### Adding New Features
- Source code → `src/ai_agents/category_extractor/`
- Tests → `tests/test_category_extractor/`
- Documentation → Appropriate `docs/` subfolder

---

**Repository is now clean and organized!** 🎉
