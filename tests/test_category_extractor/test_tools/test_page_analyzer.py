"""Smoke tests for PageAnalyzerTool structure (no Bedrock invocation)."""
from __future__ import annotations

import pytest

from src.ai_agents.category_extractor.errors import AnalysisError
from src.ai_agents.category_extractor.tools.page_analyzer import PageAnalyzerTool


class DummyAgent:
    def __init__(self) -> None:
        self.page = None
        self.state = {}


@pytest.mark.asyncio
async def test_analyzer_requires_page() -> None:
    analyzer = PageAnalyzerTool(DummyAgent())
    with pytest.raises(AnalysisError):
        await analyzer.analyze("https://example.com")
