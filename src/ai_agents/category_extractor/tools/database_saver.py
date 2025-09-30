"""Database saver tool for persisting categories to PostgreSQL."""
from __future__ import annotations

import asyncpg
from typing import List, Dict, Any, Optional
from datetime import datetime

from strands.tools import tool

from ..config import get_config
from ..errors import DatabaseError


class DatabaseSaverTool:
    """Tool for saving categories to PostgreSQL database."""
    
    def __init__(self, agent: 'CategoryExtractionAgent'):
        self.agent = agent
        self.config = get_config()
        self.db_pool: Optional[asyncpg.Pool] = None
    
    async def _get_db_pool(self) -> asyncpg.Pool:
        """Get or create database connection pool."""
        if self.db_pool is None:
            try:
                self.db_pool = await asyncpg.create_pool(
                    host=self.config.db_host,
                    port=self.config.db_port,
                    database=self.config.db_name,
                    user=self.config.db_user,
                    password=self.config.db_password,
                    min_size=1,
                    max_size=5
                )
            except Exception as e:
                raise DatabaseError(f"Failed to create database pool: {e}")
        
        return self.db_pool
    
    @tool
    async def save_to_database(
        self,
        categories: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Save extracted categories to PostgreSQL database.
        
        Args:
            categories: List of categories to save.
                       If None, uses categories from agent state.
        
        Returns:
            Statistics about saved categories
        """
        if categories is None:
            categories = self.agent.extraction_state.get("raw_categories", [])
        
        if not categories:
            return {
                "saved": 0,
                "skipped": 0,
                "errors": []
            }
        
        try:
            pool = await self._get_db_pool()
            
            saved_count = 0
            skipped_count = 0
            errors = []
            
            # Map local IDs to database IDs
            id_mapping = {}
            
            async with pool.acquire() as conn:
                # Sort by depth to insert parents before children
                sorted_categories = sorted(categories, key=lambda c: c.get("depth", 0))
                
                for category in sorted_categories:
                    try:
                        # Map parent_id
                        local_parent_id = category.get("parent_id")
                        db_parent_id = None
                        if local_parent_id is not None:
                            db_parent_id = id_mapping.get(local_parent_id)
                        
                        # Insert or update
                        result = await conn.fetchrow(
                            """
                            INSERT INTO categories (
                                name, url, parent_id, retailer_id, depth,
                                enabled, created_at
                            )
                            VALUES ($1, $2, $3, $4, $5, $6, $7)
                            ON CONFLICT (url)
                            DO UPDATE SET
                                name = EXCLUDED.name,
                                parent_id = EXCLUDED.parent_id,
                                depth = EXCLUDED.depth,
                                updated_at = CURRENT_TIMESTAMP
                            RETURNING id
                            """,
                            category["name"],
                            category["url"],
                            db_parent_id,
                            self.agent.retailer_id,
                            category.get("depth", 0),
                            True,  # enabled
                            datetime.now()
                        )
                        
                        # Store mapping
                        if category.get("id"):
                            id_mapping[category["id"]] = result["id"]
                        saved_count += 1
                        
                    except Exception as e:
                        error_msg = f"Error saving {category.get('name')}: {str(e)}"
                        errors.append(error_msg)
                        skipped_count += 1
            
            # Update agent state
            self.agent.extraction_state["stage"] = "saved"
            self.agent.extraction_state["saved_count"] = saved_count
            
            return {
                "saved": saved_count,
                "skipped": skipped_count,
                "errors": errors
            }
            
        except Exception as e:
            raise DatabaseError(f"Failed to save categories to database: {e}")
    
    async def close(self):
        """Close database connection pool."""
        if self.db_pool:
            await self.db_pool.close()
    
    def as_tool(self):
        """Return as Strands tool."""
        return self.save_to_database
