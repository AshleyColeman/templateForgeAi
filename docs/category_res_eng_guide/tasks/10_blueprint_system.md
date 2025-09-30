# Task 10: Blueprint Execution System

**Status**: 🔒 Blocked (depends on Task 7)  
**Estimated Time**: 5-6 hours  
**Dependencies**: Task 4 (Agent), Task 5 (Analyzer), Task 6 (Extractor), Task 7 (Blueprints)  
**Priority**: Medium-High

---

## 📋 Objective

Implement a blueprint execution flow that loads previously generated JSON blueprints, validates them, and replays the recorded interactions/selectors to extract categories without invoking the LLM. Include a fallback path that reverts to AI-driven extraction if the blueprint fails or becomes stale.

## 🎯 Success Criteria

- [ ] `src/ai_agents/category_extractor/blueprints/loader.py` (or similar) created with `load_blueprint(path: str) -> BlueprintModel`
- [ ] Validation step ensures blueprint matches schema version and required selectors
- [ ] Execution helper `async execute_blueprint(page: Page, blueprint: BlueprintModel) -> List[Dict[str, Any]]`
- [ ] Supports navigation actions defined in blueprint `interactions`
- [ ] Returns category list identical in structure to Task 6 output
- [ ] Fallback triggers AI extraction when blueprint execution fails, with logged reason
- [ ] CLI gains optional flag `--blueprint` to run from stored file before contacting LLM (optional but recommended)

## 📝 Specifications

### File: `src/ai_agents/category_extractor/blueprints/loader.py`

```python
"""Blueprint loading, validation, and execution helpers."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from pydantic import ValidationError

from ..errors import BlueprintError
from ..tools.category_extractor import CategoryExtractorTool
from ..utils.logger import log
from .models import BlueprintModel  # Create in Task 7 or reuse existing model


def load_blueprint(path: str) -> BlueprintModel:
    file_path = Path(path)
    if not file_path.exists():
        raise BlueprintError(f"Blueprint not found: {path}")

    try:
        payload = json.loads(file_path.read_text(encoding="utf-8"))
        blueprint = BlueprintModel.model_validate(payload)
    except (OSError, json.JSONDecodeError) as exc:
        raise BlueprintError(f"Failed to read blueprint {path}: {exc}") from exc
    except ValidationError as exc:
        raise BlueprintError(f"Blueprint validation error: {exc}") from exc

    if blueprint.version != "1.0":
        raise BlueprintError(f"Unsupported blueprint version: {blueprint.version}")

    return blueprint
```

### File: `src/ai_agents/category_extractor/blueprints/executor.py`

```python
"""Execute blueprint extraction without LLM involvement."""
from __future__ import annotations

from typing import Any, Dict, List

from playwright.async_api import Page

from ..errors import BlueprintError
from ..utils.logger import log
from ..utils.url_utils import ensure_absolute, normalize_url


async def execute_blueprint(page: Page, blueprint, base_url: str) -> List[Dict[str, Any]]:
    selectors = blueprint.selectors
    interactions = blueprint.interactions

    await _perform_interactions(page, interactions, selectors)
    categories = await _extract_categories(page, selectors, base_url)
    return categories


async def _perform_interactions(page: Page, interactions, selectors):
    for step in interactions:
        action = step.get("action")
        target_key = step.get("target")
        target_selector = selectors.get(target_key, target_key)
        wait_for = step.get("wait_for")
        timeout = step.get("timeout", 2000)

        if action == "hover":
            element = await page.wait_for_selector(target_selector, timeout=timeout)
            await element.hover()
        elif action == "click":
            element = await page.wait_for_selector(target_selector, timeout=timeout)
            await element.click()
        elif action == "wait":
            await page.wait_for_timeout(step.get("duration", 500))
        elif action == "scroll":
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
        else:
            log.debug("Skipping unknown action %s", action)

        if wait_for:
            await page.wait_for_selector(selectors.get(wait_for, wait_for), timeout=timeout)
```

### Execution Fallback

Add helper in agent or CLI:

```python
async def run_with_blueprint(agent, blueprint_path: str):
    try:
        blueprint = load_blueprint(blueprint_path)
        categories = await execute_blueprint(agent.page, blueprint, agent.site_url)
        return {"categories": categories, "source": "blueprint"}
    except BlueprintError as exc:
        log.warning("Blueprint execution failed: %s -- falling back to AI", exc)
        return await agent.category_extractor.extract()
```

## 🔧 Implementation Steps

1. **Create blueprint models module** (reuse from Task 7) to avoid duplication.
2. **Implement loader**: Validate JSON against `BlueprintModel`, check version, handle errors.
3. **Implement executor**: Replay recorded interactions, then run category extraction similar to Task 6 but using selectors from blueprint rather than LLM.
4. **Normalize output**: Use `ensure_absolute` + `normalize_url` to produce consistent categories.
5. **Integrate fallback**: Update agent/CLI to attempt blueprint execution when `--blueprint` flag provided or when blueprint exists for retailer.
6. **Log metrics**: Provide info-level logs summarizing blueprint used, counts, fallback triggers.

## ✅ Validation Checklist

- [ ] `load_blueprint` rejects missing/invalid files with clear message
- [ ] `execute_blueprint` returns >0 categories on a stored blueprint
- [ ] Fallback path reverts to AI extraction and logs warning once
- [ ] CLI option works (`--blueprint path/to/file.json`)
- [ ] Tests cover happy path + failure path for loader/executor

## 🧪 Manual Testing

```bash
poetry run python -m src.ai_agents.category_extractor.cli extract \
    --url https://retailer.com \
    --retailer-id 7 \
    --blueprint ./src/ai_agents/category_extractor/blueprints/retailer_7_20250930_191000.json
```

Ensure CLI prints `source=blueprint` or similar indicator, and run again with intentionally corrupted blueprint to confirm fallback.

## 📝 Deliverables

1. Loader + executor modules
2. CLI integration (new flag/branch)
3. Tests covering blueprint loading/execution/fallback
4. `MASTER_TASKLIST.md` update

## 🚨 Common Issues & Solutions

| Issue | Symptom | Fix |
|-------|---------|-----|
| Selectors outdated | Elements not found | Log failure, fallback to AI, regenerate blueprint |
| Blueprint path wrong | `FileNotFoundError` | Provide helpful error (BlueprintError) and exit early |
| Interaction loop fails | Timeout waiting for element | Use optional flag in blueprint (`optional: true`) to skip gracefully |
| Version mismatch | Execution aborted | Document upgrade path; implement migration if needed |

## 📚 Next Steps

After Task 10:
1. Update `MASTER_TASKLIST.md`.
2. Commit blueprint execution modules + tests.
3. Proceed to **Task 11: Comprehensive Testing**.

**Last Updated**: 2025-09-30
