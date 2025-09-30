"""Tests for blueprint loader and executor utilities."""
from __future__ import annotations

from pathlib import Path

import pytest

from src.ai_agents.category_extractor.blueprints.loader import load_blueprint
from src.ai_agents.category_extractor.blueprints.executor import execute_blueprint
from src.ai_agents.category_extractor.tools.blueprint_generator import BlueprintModel, BlueprintMetadata
from src.ai_agents.category_extractor.errors import BlueprintError


def test_load_blueprint_validates_schema(tmp_path: Path) -> None:
    blueprint = BlueprintModel(
        metadata=BlueprintMetadata(site_url="https://example.com", retailer_id=1, confidence_score=0.5),
        extraction_strategy={},
        selectors={"category_links": "nav a"},
        interactions=[],
        validation_rules={},
        extraction_stats={},
    )
    path = tmp_path / "blueprint.json"
    path.write_text(blueprint.model_dump_json())
    loaded = load_blueprint(path)
    assert loaded.metadata.site_url == "https://example.com"


def test_load_blueprint_missing_file() -> None:
    with pytest.raises(BlueprintError):
        load_blueprint("missing.json")


@pytest.mark.asyncio
async def test_execute_blueprint_requires_links(tmp_path: Path) -> None:
    blueprint = BlueprintModel(
        metadata=BlueprintMetadata(site_url="https://example.com", retailer_id=1, confidence_score=0.5),
        extraction_strategy={},
        selectors={},
        interactions=[],
        validation_rules={},
        extraction_stats={},
    )
    path = tmp_path / "blueprint.json"
    path.write_text(blueprint.model_dump_json())
    loaded = load_blueprint(path)

    class DummyPage:
        async def query_selector_all(self, selector):
            return []

    with pytest.raises(BlueprintError):
        await execute_blueprint(DummyPage(), loaded, "https://example.com")
