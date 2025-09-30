# Task 11: Comprehensive Testing

**Status**: 🔒 Blocked (depends on Tasks 1-10)  
**Estimated Time**: 10-15 hours  
**Dependencies**: All prior tasks  
**Priority**: High (production readiness)

---

## 📋 Objective

Design and implement the complete automated test suite covering unit, integration, and end-to-end layers for the AI Category Extractor. Ensure coverage targets, linting, and type-checking gates are met, and document test execution workflows.

## 🎯 Success Criteria

- [ ] Unit tests for utilities (`utils/`), validators, config, and blueprint helpers
- [ ] Unit tests for tool logic using Playwright/Strands mocks
- [ ] Integration tests hitting real PostgreSQL (test database) and Playwright (headless) flows
- [ ] E2E smoke test using a public demo site (with environment guard)
- [ ] Coverage ≥ 80% (`pytest --cov`)
- [ ] Static analysis gates: `ruff`, `black --check`, `mypy`
- [ ] CI-ready script (Makefile target or Poetry script) to run full quality suite
- [ ] Testing section added to README documenting commands

## 📝 Specifications

### Test Layout

```
tests/
├── conftest.py
├── fixtures/
│   ├── blueprint_valid.json
│   ├── blueprint_invalid.json
│   └── mock_categories.json
├── test_config.py
├── test_database.py
├── test_agent.py
├── test_cli.py
├── tools/
│   ├── test_page_analyzer.py
│   ├── test_category_extractor.py
│   └── test_blueprint_generator.py
└── blueprints/
    └── test_blueprint_executor.py
```

### Pytest Configuration

Update or create `pyproject.toml` tooling section:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
addopts = "-ra --strict-markers --disable-warnings"
markers = [
    "e2e: marks end-to-end tests that hit external websites",
    "slow: marks tests that take longer than 30s",
]
```

### Example Unit Test (Category Extractor Post-Processing)

```python
"""Unit tests for category post-processing."""
import pytest

from src.ai_agents.category_extractor.tools.category_extractor import CategoryExtractorTool


class DummyAgent:
    def __init__(self):
        self.state = {"analysis": {"navigation_type": "generic", "selectors": {"category_links": "a"}}}
        self.page = None
        self.site_url = "https://example.com"
        self.config = type("Cfg", (), {"browser_timeout": 5000})


def test_post_process_deduplicates(monkeypatch):
    tool = CategoryExtractorTool(DummyAgent())

    categories = [
        {"id": 1, "name": "A", "url": "https://example.com/a", "depth": 0, "parent_id": None},
        {"id": 2, "name": "A Duplicate", "url": "https://example.com/a", "depth": 0, "parent_id": None},
    ]

    result = tool._post_process(categories, "https://example.com")
    assert len(result) == 1
```

### Integration Test (Database)

```python
"""Integration tests for database layer."""
import asyncio
import pytest

from src.ai_agents.category_extractor.database import CategoryDatabase


@pytest.fixture
async def db():
    database = CategoryDatabase()
    await database.connect()
    yield database
    await database.delete_categories_by_retailer(999)
    await database.disconnect()


@pytest.mark.asyncio
async def test_save_and_fetch_categories(db):
    categories = [
        {"id": 1, "name": "Root", "url": "https://example.com/root", "depth": 0, "parent_id": None},
        {"id": 2, "name": "Child", "url": "https://example.com/root/child", "depth": 1, "parent_id": 1},
    ]

    stats = await db.save_categories(categories, retailer_id=999)
    assert stats["saved"] == 2

    fetched = await db.get_categories_by_retailer(999)
    assert len(fetched) >= 2
```

### End-to-End Test (Optional/Guarded)

```python
"""End-to-end smoke test (opt-in)."""
import os

import pytest

from src.ai_agents.category_extractor.agent import CategoryExtractionAgent


@pytest.mark.e2e
@pytest.mark.skipif(os.getenv("RUN_E2E") != "1", reason="Set RUN_E2E=1 to run E2E test")
async def test_full_extraction_flow():
    agent = CategoryExtractionAgent(retailer_id=999, site_url="https://example.com")
    await agent.initialize_browser()

    analysis = await agent.page_analyzer.analyze("https://example.com")
    extraction = await agent.category_extractor.extract()
    assert extraction["total"] > 0

    blueprint_path = await agent.blueprint_generator.generate(extraction["categories"], analysis)
    assert blueprint_path

    await agent.cleanup()
```

### Coverage + Quality Targets

Add scripts (example `Makefile` or Poetry script):

```bash
poetry run ruff check src tests
poetry run black --check src tests
poetry run mypy src
poetry run pytest --cov=src --cov-report=term-missing
```

Document command (e.g., `poetry run task quality`) that performs all of the above sequentially.

## 🔧 Implementation Steps

1. **Set up fixtures**: Mock data for categories, blueprint JSONs, fake Bedrock responses. Use `pytest` fixtures and `monkeypatch` to isolate external services.
2. **Write unit tests**: Cover utility functions, URL normalization, validators, blueprint generator logic, CLI argument parsing (via `CliRunner`).
3. **Write integration tests**: Run against local PostgreSQL (create/destroy test retailer data). Use Playwright in headless mode for analyzer/extractor tests with local HTML fixtures if possible.
4. **Implement E2E guard**: Provide optional test hitting a real site; skip by default to avoid flaky CI.
5. **Configure coverage**: Add `pytest-cov` to dev dependencies (already in Task 1 spec). Ensure coverage threshold enforced via `pytest.ini` or CLI (`--cov-fail-under=80`).
6. **Static analysis**: Add Poetry scripts or Makefile targets to run `ruff`, `black`, `mypy`, `pytest` sequentially. Document usage.
7. **Update documentation**: README testing instructions and `MASTER_TASKLIST.md` completion notes.

## ✅ Validation Checklist

- [ ] `poetry run pytest` passes locally
- [ ] `poetry run pytest --cov --cov-fail-under=80` passes with ≥80% coverage
- [ ] `poetry run ruff check .` and `poetry run black --check .` succeed
- [ ] `poetry run mypy src` succeeds
- [ ] E2E test runs successfully when `RUN_E2E=1` set (optional but recommended once before release)
- [ ] CI (if configured) green on new quality pipeline

## 🧪 Manual Testing

```bash
# Quick unit + integration tests
poetry run pytest -m "not e2e"

# Full quality gate
poetry run pytest --cov --cov-report=term-missing --cov-fail-under=80
poetry run ruff check src tests
poetry run black --check src tests
poetry run mypy src

# Optional E2E (requires credentials + stable network)
RUN_E2E=1 poetry run pytest -m e2e -s
```

## 📝 Deliverables

1. Complete `tests/` suite with unit/integration/E2E coverage
2. Updated `pyproject.toml` (pytest config, scripts) and optional Makefile
3. README testing instructions
4. Final updates to `MASTER_TASKLIST.md`

## 🚨 Common Issues & Solutions

| Issue | Symptom | Fix |
|-------|---------|-----|
| Playwright fails in CI | `Executable doesn't exist` | Run `poetry run playwright install chromium` in CI setup step |
| Slow/flaky tests | Random timeouts | Use fixtures to host static HTML snapshots; mark slow tests with `@pytest.mark.slow` |
| Coverage below threshold | <80% | Add tests for uncovered modules, e.g., blueprint executor fallback |
| E2E hitting live site fails | Captcha/bot detection | Keep E2E optional (skipped by default), document need for manual verification |

## 📚 Next Steps

After completing Task 11:
1. Update `MASTER_TASKLIST.md` (mark ✅, note coverage numbers).
2. Commit test suite and quality scripts.
3. Prepare final documentation and deployment readiness checklist.

**Last Updated**: 2025-09-30
