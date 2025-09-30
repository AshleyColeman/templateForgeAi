# Task 7: Blueprint Generator Tool

**Status**: 🔒 Blocked (depends on Task 6)  
**Estimated Time**: 5-6 hours  
**Dependencies**: Task 4 (Core Agent), Task 5 (Page Analyzer), Task 6 (Category Extractor)  
**Priority**: High

---

## 📋 Objective

Create the `BlueprintGeneratorTool` that transforms successful extraction runs into reusable JSON blueprints aligned with `docs/category_res_eng_guide/05_Blueprint_Schema.md`. The blueprint will capture selectors, interactions, metadata, and validation information for fast future executions.

## 🎯 Success Criteria

- [ ] `src/ai_agents/category_extractor/tools/blueprint_generator.py` implemented
- [ ] Tool exposes `async generate(categories: List[Dict[str, Any]], strategy: Dict[str, Any]) -> str`
- [ ] Blueprint adheres to schema fields (`metadata`, `extraction_strategy`, `selectors`, `interactions`, `validation_rules`, `extraction_stats`, `edge_cases`, `notes`)
- [ ] Uses Pydantic model to validate output before writing
- [ ] Serializes JSON with indentation and UTF-8 encoding under `config.blueprint_dir`
- [ ] File name deterministic (e.g., `retailer_{id}_{timestamp}.json`)
- [ ] Records blueprint path in `agent.state["blueprint_path"]`
- [ ] Returns path string for downstream usage

## 📝 Specifications

### File: `src/ai_agents/category_extractor/tools/blueprint_generator.py`

```python
"""Tool that generates reusable extraction blueprints."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from pydantic import BaseModel, Field

from ..config import get_config
from ..errors import BlueprintError
from ..utils.logger import log


class BlueprintMetadata(BaseModel):
    site_url: str
    retailer_id: int
    retailer_name: str | None = None
    generated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    generated_by: str = "ai_category_extractor"
    agent_version: str = "0.1.0"
    confidence_score: float


class BlueprintModel(BaseModel):
    version: str = "1.0"
    metadata: BlueprintMetadata
    extraction_strategy: Dict[str, Any]
    selectors: Dict[str, Any]
    interactions: List[Dict[str, Any]]
    validation_rules: Dict[str, Any]
    extraction_stats: Dict[str, Any]
    edge_cases: List[Dict[str, Any]] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)


class BlueprintGeneratorTool:
    """Generate JSON blueprints after successful extraction."""

    def __init__(self, agent: "CategoryExtractionAgent") -> None:
        self.agent = agent
        self.config = get_config()

    async def generate(self, categories: List[Dict[str, Any]], strategy: Dict[str, Any]) -> str:
        if not categories:
            raise BlueprintError("Cannot generate blueprint with zero categories")
        if not strategy:
            raise BlueprintError("Strategy data missing. Ensure PageAnalyzer ran successfully")

        retailer = await self.agent.db.get_retailer_info(self.agent.retailer_id)
        metadata = BlueprintMetadata(
            site_url=self.agent.site_url,
            retailer_id=self.agent.retailer_id,
            retailer_name=retailer.get("name") if retailer else None,
            confidence_score=strategy.get("confidence", 0.5),
        )

        blueprint = BlueprintModel(
            metadata=metadata,
            extraction_strategy={
                "navigation_type": strategy.get("navigation_type", "unknown"),
                "complexity": strategy.get("complexity", "unknown"),
                "requires_javascript": True,
                "dynamic_loading": strategy.get("dynamic_loading", {}),
            },
            selectors=strategy.get("selectors", {}),
            interactions=strategy.get("interactions", []),
            validation_rules=self._build_validation_rules(categories, strategy),
            extraction_stats=self._build_stats(categories),
            notes=strategy.get("notes", []),
        )

        path = self._write_blueprint(blueprint)
        self.agent.state["blueprint_path"] = str(path)
        return str(path)

    def _build_validation_rules(self, categories: List[Dict[str, Any]], strategy: Dict[str, Any]) -> Dict[str, Any]:
        total = len(categories)
        max_depth = max(category.get("depth", 0) for category in categories)
        return {
            "min_categories": max(1, total // 4),
            "max_categories": total * 2,
            "max_depth": max_depth,
            "required_fields": ["name", "url"],
            "url_pattern": strategy.get("url_pattern", ""),
        }

    def _build_stats(self, categories: List[Dict[str, Any]]) -> Dict[str, Any]:
        depth_counts: Dict[int, int] = {}
        for category in categories:
            depth = int(category.get("depth", 0))
            depth_counts[depth] = depth_counts.get(depth, 0) + 1
        return {
            "total_categories": len(categories),
            "max_depth": max(depth_counts) if depth_counts else 0,
            "categories_by_depth": {str(depth): count for depth, count in depth_counts.items()},
        }

    def _write_blueprint(self, blueprint: BlueprintModel) -> Path:
        output_dir = Path(self.config.blueprint_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        filename = f"retailer_{self.agent.retailer_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        path = output_dir / filename

        try:
            with path.open("w", encoding="utf-8") as handle:
                json.dump(blueprint.model_dump(mode="json"), handle, indent=2)
        except OSError as exc:
            raise BlueprintError(f"Failed to write blueprint to {path}: {exc}") from exc

        log.info("Blueprint saved to %s", path)
        return path
```

> The Pydantic models ensure that future schema changes are centralized. Keep field names in sync with `05_Blueprint_Schema.md`.

## 🔧 Implementation Steps

1. **Create module + models**: Define `BlueprintMetadata` and `BlueprintModel` inside the tool file or a dedicated `schemas.py` if preferred.
2. **Gather context**: Pull retailer info via `CategoryDatabase.get_retailer_info` (Task 3). Use strategy output (`selectors`, `interactions`, etc.) captured in agent state.
3. **Derive validation rules**: Build heuristics for `min_categories`, `max_categories`, `max_depth`, and `url_pattern` (if provided by the analyzer).
4. **Compute stats**: Summaries by depth, total categories, optional duration metrics (if available from state).
5. **Serialize blueprint**: Write JSON with indentation=2, ensure directory exists, and handle exceptions cleanly.
6. **Update state + return path**: Record path for CLI output and blueprint execution task.
7. **Logging**: Log blueprint creation start/end, number of categories included, and file path.

## ✅ Validation Checklist

- [ ] Blueprint file created in `src/ai_agents/category_extractor/blueprints/`
- [ ] JSON validates against schema (optional automated check using `jsonschema`)
- [ ] `poetry run python -c` snippet instantiates tool and generates blueprint without raising
- [ ] Pydantic ensures missing required fields raise `ValidationError`
- [ ] Agent state includes `blueprint_path`

## 🧪 Manual Testing

```python
import asyncio

from src.ai_agents.category_extractor.agent import CategoryExtractionAgent

async def main() -> None:
    agent = CategoryExtractionAgent(retailer_id=5, site_url="https://example.com")
    categories = [
        {"id": 1, "name": "Root", "url": "https://example.com/root", "depth": 0, "parent_id": None},
        {"id": 2, "name": "Child", "url": "https://example.com/root/child", "depth": 1, "parent_id": 1},
    ]
    strategy = {
        "navigation_type": "hover_menu",
        "selectors": {"nav_container": "nav.main"},
        "interactions": [],
        "confidence": 0.9,
    }
    path = await agent.blueprint_generator.generate(categories, strategy)
    print("Blueprint stored at", path)

asyncio.run(main())
```

## 📝 Deliverables

1. `blueprint_generator.py` with generation logic + Pydantic models
2. Optional schema validation helper or unit tests verifying blueprint structure
3. Update to `MASTER_TASKLIST.md`

## 🚨 Common Issues & Solutions

| Issue | Symptom | Fix |
|-------|---------|-----|
| Directory missing | OSError on write | Call `mkdir(parents=True, exist_ok=True)` before writing |
| Confidence missing | Pydantic validation fails | Provide default `0.5` when building metadata |
| Incorrect JSON types | Blueprint invalid | Ensure lists vs dicts align with schema (e.g., `interactions` is list) |
| Non-serializable objects | `TypeError: Object of type ... is not JSON serializable` | Convert datetimes to ISO strings via Pydantic `model_dump` |

## 📚 Next Steps

After Task 7:
1. Update task status/time in `MASTER_TASKLIST.md`.
2. Commit the tool and supporting tests.
3. Begin **Task 8: CLI Interface** modifications to expose new agent functionality to end users.

**Last Updated**: 2025-09-30
