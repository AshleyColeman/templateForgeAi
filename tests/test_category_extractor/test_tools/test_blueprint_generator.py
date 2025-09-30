"""Tests for BlueprintGeneratorTool."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ai_agents.category_extractor.tools.blueprint_generator import BlueprintGeneratorTool
from src.ai_agents.category_extractor.config import reload_config


class DummyDB:
    async def get_retailer_info(self, retailer_id: int):  # noqa: D401 - simple stub
        return {"name": "Retailer"}


class DummyAgent:
    def __init__(self, tmp_path: Path) -> None:
        self.retailer_id = 42
        self.site_url = "https://example.com"
        self.state = {}
        self.db = DummyDB()
        self.config = reload_config()
        self.config.blueprint_dir = str(tmp_path)


@pytest.mark.asyncio
async def test_generate_blueprint_writes_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BLUEPRINT_DIR", str(tmp_path))
    monkeypatch.setenv("DB_PASSWORD", "pwd")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "key")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "secret")
    reload_config()

    agent = DummyAgent(tmp_path)
    tool = BlueprintGeneratorTool(agent)

    categories = [
        {"id": 1, "name": "Root", "url": "https://example.com/root", "depth": 0, "parent_id": None},
        {"id": 2, "name": "Child", "url": "https://example.com/root/child", "depth": 1, "parent_id": 1},
    ]
    strategy = {
        "navigation_type": "hover_menu",
        "selectors": {"nav_container": "nav"},
        "interactions": [],
        "confidence": 0.9,
    }

    path = await tool.generate(categories, strategy)
    assert Path(path).exists()
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    assert data["metadata"]["retailer_id"] == agent.retailer_id
    assert agent.state["blueprint_path"] == path
