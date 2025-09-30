"""E2E smoke test placeholder."""
from __future__ import annotations

import os

import pytest


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_e2e_placeholder() -> None:
    pytest.skip("E2E requires Playwright/Bedrock setup; run with RUN_E2E=1 in real environment")
