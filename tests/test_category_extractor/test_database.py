"""Integration-oriented tests for CategoryDatabase."""
from __future__ import annotations

import os

import pytest

from src.ai_agents.category_extractor.database import CategoryDatabase
from src.ai_agents.category_extractor.errors import DatabaseError

TEST_RETAILER_ID = 999


@pytest.fixture
async def db() -> CategoryDatabase:
    database = CategoryDatabase()
    try:
        await database.connect()
    except DatabaseError as exc:
        pytest.skip(f"Database unavailable: {exc}")
    yield database
    try:
        await database.delete_categories_by_retailer(TEST_RETAILER_ID)
    finally:
        await database.disconnect()


@pytest.mark.asyncio
async def test_health_check(db: CategoryDatabase) -> None:
    assert await db.health_check() is True


@pytest.mark.asyncio
async def test_save_and_fetch_categories(db: CategoryDatabase) -> None:
    categories = [
        {"id": 1, "name": "Root", "url": "https://example.com/root", "depth": 0, "parent_id": None},
        {"id": 2, "name": "Child", "url": "https://example.com/root/child", "depth": 1, "parent_id": 1},
    ]
    stats = await db.save_categories(categories, TEST_RETAILER_ID)
    assert stats["saved"] >= 1
    fetched = await db.get_categories_by_retailer(TEST_RETAILER_ID, enabled_only=False)
    assert len(fetched) >= 2


@pytest.mark.asyncio
async def test_duplicate_category_updates_existing(db: CategoryDatabase) -> None:
    category = {
        "id": 1,
        "name": "Duplicate",
        "url": "https://example.com/dup",
        "depth": 0,
        "parent_id": None,
    }
    await db.save_categories([category], TEST_RETAILER_ID)
    updated = {**category, "name": "Duplicate Updated"}
    stats = await db.save_categories([updated], TEST_RETAILER_ID)
    assert stats["updated"] >= 1
