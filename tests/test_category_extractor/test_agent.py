"""Tests for CategoryExtractionAgent scaffolding."""
from __future__ import annotations

import importlib
from unittest import mock

import pytest


def test_agent_import_raises_without_strands(monkeypatch: pytest.MonkeyPatch) -> None:
    module = importlib.import_module("src.ai_agents.category_extractor.agent")
    monkeypatch.setattr(module, "StrandsAgent", None, raising=False)

    with pytest.raises(ImportError):
        module.CategoryExtractionAgent(retailer_id=1, site_url="https://example.com")
