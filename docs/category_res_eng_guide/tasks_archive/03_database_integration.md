# Task 3: Database Integration

**Status**: 🔒 Blocked (depends on Task 2)  
**Estimated Time**: 6-8 hours  
**Dependencies**: Task 2 (Configuration Management)  
**Priority**: Critical

---

## 📋 Objective

Create a robust database layer using asyncpg for PostgreSQL operations, including connection pooling, category CRUD operations, and transaction support.

## 🎯 Success Criteria

- [ ] `CategoryDatabase` class created
- [ ] Connection pooling implemented
- [ ] `save_categories()` method working with hierarchy
- [ ] `get_retailer_info()` method implemented
- [ ] Transaction support for batch operations
- [ ] Error handling for all database operations
- [ ] Can connect to existing PostgreSQL database
- [ ] Can save and retrieve categories correctly

## 📊 Database Schema Reference

Your existing schema:

```sql
-- categories table (DO NOT CREATE - already exists)
CREATE TABLE categories (
    id serial4 PRIMARY KEY,
    name text NOT NULL,
    url text NULL,
    parent_id int4 NULL REFERENCES categories(id),
    retailer_id int4 NOT NULL REFERENCES retailers(id),
    depth int4 NULL,
    enabled bool DEFAULT false,
    created_at timestamptz DEFAULT CURRENT_TIMESTAMP
);

-- retailers table (already exists)
CREATE TABLE retailers (
    id serial4 PRIMARY KEY,
    name text NOT NULL,
    base_url text NULL,
    enabled bool DEFAULT true
);
```

## 📝 Specifications

### File: `src/ai_agents/category_extractor/database.py`

```python
"""Database operations for category extraction."""
import asyncpg
from typing import List, Dict, Any, Optional
from datetime import datetime
from loguru import logger

from .config import get_config
from .errors import DatabaseError


class CategoryDatabase:
    """Manages database operations for categories.
    
    Uses asyncpg with connection pooling for efficient PostgreSQL access.
    """
    
    def __init__(self):
        """Initialize database manager."""
        self.pool: Optional[asyncpg.Pool] = None
        self.config = get_config()
    
    async def connect(self) -> None:
        """Create database connection pool.
        
        Raises:
            DatabaseError: If connection fails
        """
        if self.pool is not None:
            logger.debug("Database pool already exists")
            return
        
        try:
            logger.info(f"Connecting to database: {self.config.db_host}:{self.config.db_port}/{self.config.db_name}")
            
            self.pool = await asyncpg.create_pool(
                host=self.config.db_host,
                port=self.config.db_port,
                database=self.config.db_name,
                user=self.config.db_user,
                password=self.config.db_password,
                min_size=2,
                max_size=10,
                command_timeout=60,
                server_settings={
                    'application_name': 'ai_category_extractor'
                }
            )
            
            # Test connection
            async with self.pool.acquire() as conn:
                version = await conn.fetchval("SELECT version()")
                logger.info(f"Connected to PostgreSQL: {version.split(',')[0]}")
        
        except asyncpg.PostgresError as e:
            raise DatabaseError(f"Failed to connect to database: {e}")
        except Exception as e:
            raise DatabaseError(f"Unexpected error connecting to database: {e}")
    
    async def disconnect(self) -> None:
        """Close database connection pool."""
        if self.pool:
            await self.pool.close()
            self.pool = None
            logger.info("Database connection pool closed")
    
    async def save_categories(
        self,
        categories: List[Dict[str, Any]],
        retailer_id: int
    ) -> Dict[str, int]:
        """Save categories to database with hierarchy.
        
        Handles parent-child relationships by processing categories by depth.
        Updates existing categories and inserts new ones.
        
        Args:
            categories: List of category dicts with: name, url, depth, parent_id, id (local)
            retailer_id: Retailer ID to associate categories with
        
        Returns:
            Statistics dict: {"saved": N, "updated": N, "errors": N}
        
        Raises:
            DatabaseError: If save operation fails
        """
        await self.connect()
        
        stats = {"saved": 0, "updated": 0, "skipped": 0, "errors": 0}
        id_map = {}  # Map local IDs to database IDs
        
        logger.info(f"Saving {len(categories)} categories for retailer {retailer_id}")
        
        # Sort by depth to ensure parents are inserted before children
        sorted_categories = sorted(categories, key=lambda c: c.get("depth", 0))
        
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                for category in sorted_categories:
                    try:
                        # Resolve parent_id from local to database ID
                        local_parent_id = category.get("parent_id")
                        db_parent_id = None
                        
                        if local_parent_id is not None:
                            db_parent_id = id_map.get(local_parent_id)
                            if db_parent_id is None:
                                logger.warning(
                                    f"Parent ID {local_parent_id} not found in id_map "
                                    f"for category '{category.get('name')}'"
                                )
                        
                        # Check if category already exists (by URL and retailer)
                        existing = await conn.fetchrow(
                            """
                            SELECT id FROM categories 
                            WHERE url = $1 AND retailer_id = $2
                            """,
                            category["url"],
                            retailer_id
                        )
                        
                        if existing:
                            # Update existing category
                            await conn.execute(
                                """
                                UPDATE categories
                                SET name = $1, parent_id = $2, depth = $3, 
                                    enabled = $4, created_at = COALESCE(created_at, $5)
                                WHERE id = $6
                                """,
                                category["name"],
                                db_parent_id,
                                category.get("depth", 0),
                                True,
                                datetime.now(),
                                existing["id"]
                            )
                            
                            # Map local ID to database ID
                            id_map[category.get("id")] = existing["id"]
                            stats["updated"] += 1
                            
                            logger.debug(f"Updated category: {category['name']} (ID: {existing['id']})")
                        
                        else:
                            # Insert new category
                            result = await conn.fetchrow(
                                """
                                INSERT INTO categories (
                                    name, url, parent_id, retailer_id, depth,
                                    enabled, created_at
                                )
                                VALUES ($1, $2, $3, $4, $5, $6, $7)
                                RETURNING id
                                """,
                                category["name"],
                                category["url"],
                                db_parent_id,
                                retailer_id,
                                category.get("depth", 0),
                                True,
                                datetime.now()
                            )
                            
                            # Map local ID to database ID
                            id_map[category.get("id")] = result["id"]
                            stats["saved"] += 1
                            
                            logger.debug(f"Inserted category: {category['name']} (ID: {result['id']})")
                    
                    except asyncpg.PostgresError as e:
                        logger.error(f"Database error saving category '{category.get('name')}': {e}")
                        stats["errors"] += 1
                    
                    except Exception as e:
                        logger.error(f"Unexpected error saving category '{category.get('name')}': {e}")
                        stats["errors"] += 1
        
        logger.info(
            f"Save complete: {stats['saved']} inserted, {stats['updated']} updated, "
            f"{stats['errors']} errors"
        )
        
        return stats
    
    async def get_retailer_info(self, retailer_id: int) -> Optional[Dict[str, Any]]:
        """Get retailer information from database.
        
        Args:
            retailer_id: Retailer ID to fetch
        
        Returns:
            Dict with retailer info or None if not found
        """
        await self.connect()
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id, name, base_url, enabled FROM retailers WHERE id = $1",
                retailer_id
            )
            
            if row:
                return dict(row)
            else:
                logger.warning(f"Retailer {retailer_id} not found")
                return None
    
    async def get_categories_by_retailer(
        self,
        retailer_id: int,
        enabled_only: bool = True
    ) -> List[Dict[str, Any]]:
        """Get all categories for a retailer.
        
        Args:
            retailer_id: Retailer ID
            enabled_only: If True, only return enabled categories
        
        Returns:
            List of category dicts
        """
        await self.connect()
        
        query = """
            SELECT id, name, url, parent_id, depth, enabled, created_at
            FROM categories
            WHERE retailer_id = $1
        """
        
        if enabled_only:
            query += " AND enabled = true"
        
        query += " ORDER BY depth, name"
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, retailer_id)
            return [dict(row) for row in rows]
    
    async def delete_categories_by_retailer(
        self,
        retailer_id: int
    ) -> int:
        """Delete all categories for a retailer.
        
        Args:
            retailer_id: Retailer ID
        
        Returns:
            Number of categories deleted
        """
        await self.connect()
        
        logger.warning(f"Deleting all categories for retailer {retailer_id}")
        
        async with self.pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM categories WHERE retailer_id = $1",
                retailer_id
            )
            
            # Parse result: "DELETE N"
            count = int(result.split()[-1])
            logger.info(f"Deleted {count} categories for retailer {retailer_id}")
            
            return count
    
    async def health_check(self) -> bool:
        """Check if database connection is healthy.
        
        Returns:
            True if database is accessible, False otherwise
        """
        try:
            await self.connect()
            
            async with self.pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            
            return True
        
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False


# Export
__all__ = ["CategoryDatabase"]
```

### File: `src/ai_agents/category_extractor/errors.py`

```python
"""Custom exception classes for category extractor."""


class ExtractorError(Exception):
    """Base exception for all extractor errors."""
    pass


class DatabaseError(ExtractorError):
    """Error during database operations."""
    pass


class NavigationError(ExtractorError):
    """Error during page navigation."""
    pass


class AnalysisError(ExtractorError):
    """Error during page analysis."""
    pass


class ExtractionError(ExtractorError):
    """Error during category extraction."""
    pass


class BotDetectionError(ExtractorError):
    """Bot detection or Cloudflare challenge encountered."""
    pass


class ValidationError(ExtractorError):
    """Data validation error."""
    pass


class BlueprintError(ExtractorError):
    """Error with blueprint operations."""
    pass


# Export
__all__ = [
    "ExtractorError",
    "DatabaseError",
    "NavigationError",
    "AnalysisError",
    "ExtractionError",
    "BotDetectionError",
    "ValidationError",
    "BlueprintError",
]
```

## 🔧 Implementation Steps

### Step 1: Create errors.py

Create `/home/ashleycoleman/Projects/product_scraper/src/ai_agents/category_extractor/errors.py` with the code above.

### Step 2: Create database.py

Create `/home/ashleycoleman/Projects/product_scraper/src/ai_agents/category_extractor/database.py` with the code above.

### Step 3: Verify Database Connection

Test connection with simple script:

```python
"""Test database connection."""
import asyncio
from src.ai_agents.category_extractor.database import CategoryDatabase


async def test_connection():
    db = CategoryDatabase()
    
    try:
        await db.connect()
        print("✅ Connected to database")
        
        # Test health check
        healthy = await db.health_check()
        print(f"✅ Health check: {'OK' if healthy else 'FAILED'}")
        
        # Test get retailer (assuming retailer ID 1 exists)
        retailer = await db.get_retailer_info(1)
        if retailer:
            print(f"✅ Got retailer: {retailer['name']}")
        else:
            print("⚠️  Retailer 1 not found (this is OK if you haven't created it yet)")
        
    finally:
        await db.disconnect()
        print("✅ Disconnected from database")


if __name__ == "__main__":
    asyncio.run(test_connection())
```

Save as `test_database_connection.py` and run:
```bash
poetry run python test_database_connection.py
```

### Step 4: Create Full Test Script

Create `/home/ashleycoleman/Projects/product_scraper/test_database.py`:

```python
"""Comprehensive database tests."""
import asyncio
import sys
from datetime import datetime
from src.ai_agents.category_extractor.database import CategoryDatabase


async def test_connection():
    """Test database connection."""
    print("🔍 Test 1: Database Connection")
    
    db = CategoryDatabase()
    
    try:
        await db.connect()
        print("✅ Connected successfully")
        return True, db
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False, None


async def test_health_check(db: CategoryDatabase):
    """Test health check."""
    print("\n🔍 Test 2: Health Check")
    
    try:
        healthy = await db.health_check()
        if healthy:
            print("✅ Database is healthy")
            return True
        else:
            print("❌ Database health check failed")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False


async def test_save_categories(db: CategoryDatabase):
    """Test saving categories."""
    print("\n🔍 Test 3: Save Categories")
    
    # Create test categories
    test_categories = [
        {
            "id": 1,
            "name": "Test Category 1",
            "url": "https://test.com/cat1",
            "depth": 0,
            "parent_id": None
        },
        {
            "id": 2,
            "name": "Test Category 1.1",
            "url": "https://test.com/cat1/sub1",
            "depth": 1,
            "parent_id": 1
        },
        {
            "id": 3,
            "name": "Test Category 1.2",
            "url": "https://test.com/cat1/sub2",
            "depth": 1,
            "parent_id": 1
        }
    ]
    
    try:
        # Use retailer ID 999 for testing
        stats = await db.save_categories(test_categories, retailer_id=999)
        
        print(f"✅ Saved: {stats['saved']}, Updated: {stats['updated']}, Errors: {stats['errors']}")
        
        if stats['errors'] == 0:
            return True
        else:
            print(f"⚠️  Some errors occurred")
            return False
    
    except Exception as e:
        print(f"❌ Save failed: {e}")
        return False


async def test_get_categories(db: CategoryDatabase):
    """Test retrieving categories."""
    print("\n🔍 Test 4: Get Categories")
    
    try:
        categories = await db.get_categories_by_retailer(999)
        
        print(f"✅ Retrieved {len(categories)} categories")
        
        for cat in categories[:3]:  # Show first 3
            print(f"  - {cat['name']} (depth: {cat['depth']})")
        
        return len(categories) > 0
    
    except Exception as e:
        print(f"❌ Retrieval failed: {e}")
        return False


async def test_cleanup(db: CategoryDatabase):
    """Clean up test data."""
    print("\n🔍 Test 5: Cleanup")
    
    try:
        count = await db.delete_categories_by_retailer(999)
        print(f"✅ Deleted {count} test categories")
        return True
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")
        return False


async def run_all_tests():
    """Run all database tests."""
    print("\n" + "="*60)
    print("Database Integration Test Suite")
    print("="*60 + "\n")
    
    # Test 1: Connection
    success, db = await test_connection()
    if not success:
        print("\n❌ Cannot continue without database connection")
        return False
    
    try:
        # Run all tests
        results = [
            success,  # Connection test
            await test_health_check(db),
            await test_save_categories(db),
            await test_get_categories(db),
            await test_cleanup(db),
        ]
        
        print("\n" + "="*60)
        if all(results):
            print("✅ All database tests passed!")
            return True
        else:
            print("❌ Some database tests failed")
            return False
    
    finally:
        await db.disconnect()
        print("\n✅ Database disconnected")


if __name__ == "__main__":
    result = asyncio.run(run_all_tests())
    sys.exit(0 if result else 1)
```

Run the tests:
```bash
poetry run python test_database.py
```

## ✅ Validation Checklist

- [ ] `errors.py` created with all exception classes
- [ ] `database.py` created with CategoryDatabase class
- [ ] Can connect to PostgreSQL database
- [ ] Connection pooling working
- [ ] `save_categories()` inserts new categories
- [ ] `save_categories()` updates existing categories
- [ ] Parent-child relationships preserved
- [ ] `get_retailer_info()` retrieves retailer data
- [ ] `get_categories_by_retailer()` works
- [ ] `delete_categories_by_retailer()` works
- [ ] Health check passes
- [ ] Test script passes all tests
- [ ] No SQL injection vulnerabilities (using parameterized queries)
- [ ] Transactions used for batch operations
- [ ] Error handling catches database exceptions

## 🚨 Common Issues & Solutions

### Issue: asyncpg not installed
**Solution**:
```bash
poetry add asyncpg@^0.29.0
```

### Issue: Connection refused
**Solution**: Check PostgreSQL is running:
```bash
sudo systemctl status postgresql
# or
pg_isready -h localhost -p 5432
```

### Issue: Authentication failed
**Solution**: Verify .env credentials:
```bash
grep DB_ .env
# Try connecting with psql:
psql -h localhost -U postgres -d products
```

### Issue: Database doesn't exist
**Solution**: Create it:
```bash
createdb -U postgres products
```

### Issue: Retailer not found
**Solution**: Insert test retailer:
```sql
INSERT INTO retailers (id, name, base_url, enabled)
VALUES (999, 'Test Retailer', 'https://test.com', true);
```

## 📚 Next Steps

Once complete:
1. Mark task as ✅ Complete in MASTER_TASKLIST.md
2. Commit: `git add . && git commit -m "Add database integration"`
3. Proceed to **Task 4: Core Agent Implementation**

## 🎯 Time Tracking

**Estimated**: 6-8 hours  
**Actual**: ___ hours  
**Notes**: ___

---

**Last Updated**: 2025-09-30
