"""Database operations for AI category extractor."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import asyncpg

from .config import get_config
from .errors import DatabaseError
from .utils.logger import get_logger


class CategoryDatabase:
    """Manage PostgreSQL interactions for category data."""

    def __init__(self) -> None:
        self.config = get_config()
        self.pool: Optional[asyncpg.Pool] = None
        self.logger = get_logger()

    async def connect(self) -> None:
        """Create asyncpg connection pool."""
        if self.pool is not None:
            self.logger.debug("Database pool already initialised")
            return
        try:
            self.logger.info(
                "Connecting to database {}:{}/{}",
                self.config.db_host,
                self.config.db_port,
                self.config.db_name,
            )
            self.pool = await asyncpg.create_pool(
                host=self.config.db_host,
                port=self.config.db_port,
                database=self.config.db_name,
                user=self.config.db_user,
                password=self.config.db_password,
                min_size=2,
                max_size=10,
                command_timeout=60,
                server_settings={"application_name": "ai_category_extractor"},
            )
            async with self.pool.acquire() as conn:
                version = await conn.fetchval("SELECT version()")
                self.logger.info("Connected to PostgreSQL: {}", version.split()[0])
        except asyncpg.PostgresError as exc:  # pragma: no cover - connection failure
            raise DatabaseError(f"Failed to connect to database: {exc}") from exc
        except Exception as exc:  # noqa: BLE001  # pragma: no cover
            raise DatabaseError(f"Unexpected error connecting to database: {exc}") from exc

    async def disconnect(self) -> None:
        """Close existing connection pool."""
        if self.pool is None:
            return
        await self.pool.close()
        self.pool = None
        self.logger.info("Database connection pool closed")

    async def save_categories(self, categories: List[Dict[str, Any]], retailer_id: int) -> Dict[str, int]:
        """Persist category hierarchy for a retailer.

        Args:
            categories: List of category dicts containing name, url, depth, parent_id, id (local).
            retailer_id: Retailer identifier.

        Returns:
            Dict with counts for saved, updated, skipped, errors.
        """
        await self.connect()
        assert self.pool is not None  # for type checkers

        stats = {"saved": 0, "updated": 0, "skipped": 0, "errors": 0}
        id_map: Dict[Any, int] = {}
        sorted_categories = sorted(categories, key=lambda cat: cat.get("depth", 0))
        logger = self.logger.bind(retailer_id=retailer_id)
        logger.info("Saving {} categories for retailer {}", len(sorted_categories), retailer_id)

        async with self.pool.acquire() as conn:
            async with conn.transaction():
                for category in sorted_categories:
                    try:
                        name = category["name"]
                        url = category.get("url")
                        if not url:
                            stats["skipped"] += 1
                            logger.warning("Skipping category without URL: {}", name)
                            continue

                        local_parent_id = category.get("parent_id")
                        db_parent_id = id_map.get(local_parent_id) if local_parent_id is not None else None

                        existing = await conn.fetchrow(
                            "SELECT id FROM categories WHERE url = $1 AND retailer_id = $2",
                            url,
                            retailer_id,
                        )
                        if existing:
                            await conn.execute(
                                """
                                UPDATE categories
                                SET name = $1,
                                    parent_id = $2,
                                    depth = $3,
                                    enabled = $4
                                WHERE id = $5
                                """,
                                name,
                                db_parent_id,
                                category.get("depth", 0),
                                True,
                                existing["id"],
                            )
                            id_map[category.get("id")] = existing["id"]
                            stats["updated"] += 1
                            logger.debug("Updated category {} ({})", name, existing["id"])
                        else:
                            inserted = await conn.fetchrow(
                                """
                                INSERT INTO categories (
                                    name, url, parent_id, retailer_id, depth, enabled, created_at
                                )
                                VALUES ($1, $2, $3, $4, $5, $6, $7)
                                RETURNING id
                                """,
                                name,
                                url,
                                db_parent_id,
                                retailer_id,
                                category.get("depth", 0),
                                True,
                                datetime.now(timezone.utc),
                            )
                            id_map[category.get("id")] = inserted["id"]
                            stats["saved"] += 1
                            logger.debug("Inserted category {} ({})", name, inserted["id"])
                    except asyncpg.PostgresError as exc:
                        stats["errors"] += 1
                        logger.error("Database error saving category '{}': {}", category.get("name"), exc)
                    except Exception as exc:  # noqa: BLE001
                        stats["errors"] += 1
                        logger.error("Unexpected error saving category '{}': {}", category.get("name"), exc)
        logger.info(
            "Save complete: saved={} updated={} skipped={} errors={}",
            stats["saved"],
            stats["updated"],
            stats["skipped"],
            stats["errors"],
        )
        return stats

    async def get_retailer_info(self, retailer_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve retailer information."""
        await self.connect()
        assert self.pool is not None

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id, name, base_url, enabled FROM retailers WHERE id = $1",
                retailer_id,
            )
            result = dict(row) if row else None
            if not result:
                self.logger.warning("Retailer {} not found in database", retailer_id)
            return result

    async def get_categories_by_retailer(self, retailer_id: int, enabled_only: bool = True) -> List[Dict[str, Any]]:
        """Return categories for a retailer."""
        await self.connect()
        assert self.pool is not None

        query = [
            "SELECT id, name, url, parent_id, depth, enabled, created_at",
            "FROM categories",
            "WHERE retailer_id = $1",
        ]
        if enabled_only:
            query.append("AND enabled = true")
        query.append("ORDER BY depth, name")
        sql = " ".join(query)

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(sql, retailer_id)
            return [dict(row) for row in rows]

    async def delete_categories_by_retailer(self, retailer_id: int) -> int:
        """Delete categories for a retailer (used in tests)."""
        await self.connect()
        assert self.pool is not None

        async with self.pool.acquire() as conn:
            result = await conn.execute("DELETE FROM categories WHERE retailer_id = $1", retailer_id)
        count = int(result.split()[-1])
        self.logger.bind(retailer_id=retailer_id).info("Deleted {} categories for retailer {}", count, retailer_id)
        return count

    async def health_check(self) -> bool:
        """Simple health check to verify connectivity."""
        try:
            await self.connect()
            assert self.pool is not None
            async with self.pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            return True
        except Exception as exc:  # noqa: BLE001
            self.logger.error("Database health check failed: {}", exc)
            return False


__all__ = ["CategoryDatabase"]
