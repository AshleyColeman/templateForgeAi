"""Tests for CategoryExtractorTool post-processing and validation helpers."""
from __future__ import annotations

import pytest

from src.ai_agents.category_extractor.errors import ValidationError
from src.ai_agents.category_extractor.tools.category_extractor import CategoryExtractorTool
from src.ai_agents.category_extractor.tools.validators import validate_category, validate_hierarchy


class DummyAgent:
    def __init__(self) -> None:
        self.page = None
        self.site_url = "https://example.com"
        self.config = type("Cfg", (), {"browser_timeout": 1000})
        self.state = {
            "analysis": {
                "navigation_type": "generic",
                "selectors": {"category_links": "a"},
            }
        }


def test_validate_category_requires_fields() -> None:
    with pytest.raises(ValidationError):
        validate_category({"name": "", "url": None})


def test_validate_hierarchy_detects_missing_parent() -> None:
    categories = [
        {"id": 1, "name": "Root", "url": "https://example.com", "parent_id": None},
        {"id": 2, "name": "Child", "url": "https://example.com/child", "parent_id": 99},
    ]
    with pytest.raises(ValidationError):
        validate_hierarchy(categories)


def test_post_process_deduplicates(monkeypatch: pytest.MonkeyPatch) -> None:
    agent = DummyAgent()
    tool = CategoryExtractorTool(agent)
    categories = [
        {"id": 1, "name": "A", "url": "https://example.com/a", "depth": 0, "parent_id": None},
        {"id": 2, "name": "A Dup", "url": "https://example.com/a", "depth": 0, "parent_id": None},
    ]
    result = tool._post_process(categories, agent.site_url)
    assert len(result) == 1
