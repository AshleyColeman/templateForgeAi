"""Tests for CLI extract command."""
from __future__ import annotations

from unittest import mock

import pytest
from click.testing import CliRunner

from src.ai_agents.category_extractor import cli


@pytest.mark.asyncio
async def test_cli_extract_runs_with_mocks(monkeypatch: pytest.MonkeyPatch) -> None:
    runner = CliRunner()

    class DummyAgent:
        def __init__(self, *args, **kwargs):
            self.retailer_id = kwargs.get("retailer_id", 1)
            self.site_url = kwargs.get("site_url", "https://example.com")
            self.config = type("Cfg", (), {"browser_timeout": 1000})
            self.state = {}
            self.page_analyzer = mock.AsyncMock()
            self.category_extractor = mock.AsyncMock()
            self.blueprint_generator = mock.AsyncMock()
            self.db = mock.AsyncMock()

            self.page_analyzer.analyze.return_value = {
                "navigation_type": "generic",
                "selectors": {},
                "interactions": [],
            }
            self.category_extractor.extract.return_value = {
                "categories": [
                    {"id": 1, "name": "Root", "url": "https://example.com", "depth": 0, "parent_id": None}
                ],
                "total": 1,
                "navigation_type": "generic",
            }
            self.db.save_categories.return_value = {"saved": 1, "updated": 0}
            self.blueprint_generator.generate.return_value = "/tmp/blueprint.json"

        async def initialize_browser(self):
            return None

        async def cleanup(self):
            return None

    monkeypatch.setattr(cli, "CategoryExtractionAgent", DummyAgent)
    result = runner.invoke(
        cli.cli,
        ["extract", "--url", "https://example.com", "--retailer-id", "1", "--blueprint-only"]
    )
    assert result.exit_code == 0
