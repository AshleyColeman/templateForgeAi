"""Tests for CLI extract command."""
from __future__ import annotations

from unittest import mock

import pytest
from click.testing import CliRunner

from src.ai_agents.category_extractor import cli


def test_cli_extract_runs_with_mocks(monkeypatch: pytest.MonkeyPatch) -> None:
    runner = CliRunner()

    class DummyAgent:
        def __init__(self, *args, **kwargs):
            self.retailer_id = kwargs.get("retailer_id", 1)
            self.site_url = kwargs.get("site_url", "https://example.com")
            self.config = type("Cfg", (), {"browser_timeout": 1000})
            self.state = {}
            self.page = mock.MagicMock()  # Mock Playwright page
            
            # Create async mocks for tools
            self.page_analyzer = mock.MagicMock()
            self.page_analyzer.analyze = mock.AsyncMock(return_value={
                "navigation_type": "generic",
                "selectors": {},
                "interactions": [],
            })
            
            self.category_extractor = mock.MagicMock()
            self.category_extractor.extract = mock.AsyncMock(return_value={
                "categories": [
                    {"id": 1, "name": "Root", "url": "https://example.com", "depth": 0, "parent_id": None}
                ],
                "total": 1,
                "navigation_type": "generic",
            })
            
            self.blueprint_generator = mock.MagicMock()
            self.blueprint_generator.generate = mock.AsyncMock(return_value="/tmp/blueprint.json")
            
            self.db = mock.MagicMock()
            self.db.save_categories = mock.AsyncMock(return_value={"saved": 1, "updated": 0})

        async def initialize_browser(self):
            return None

        async def cleanup(self):
            return None

    monkeypatch.setattr(cli, "CategoryExtractionAgent", DummyAgent)
    result = runner.invoke(
        cli.cli,
        ["extract", "--url", "https://example.com", "--retailer-id", "1", "--blueprint-only"]
    )
    
    # Print output for debugging if test fails
    if result.exit_code != 0:
        print(f"\n CLI Output:\n{result.output}")
        if result.exception:
            print(f"\nException: {result.exception}")
    
    assert result.exit_code == 0, f"CLI failed with output: {result.output}"
