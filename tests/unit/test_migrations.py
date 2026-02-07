"""Tests for database migrations."""

import pytest
from app.services.database.migrations import MigrationManager


@pytest.mark.asyncio
class TestMigrationManager:
    """Tests for MigrationManager class."""
    
    async def test_init_schema_version_table(self, test_db):
        """Test schema_version table creation."""
        manager = MigrationManager(test_db)
        await manager.init_schema_version_table()
        
        # Verify table exists
        cursor = await test_db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'"
        )
        row = await cursor.fetchone()
        assert row is not None
        assert row[0] == "schema_version"
    
    async def test_get_current_version_empty_db(self, test_db):
        """Test getting version from empty database."""
        manager = MigrationManager(test_db)
        await manager.init_schema_version_table()
        
        version = await manager.get_current_version()
        assert version == 0
    
    async def test_discover_migrations(self, test_db):
        """Test migration discovery."""
        manager = MigrationManager(test_db)
        migrations = manager.discover_migrations()
        
        # Should find at least v001 and v002
        assert len(migrations) >= 2
        
        # Migrations should be sorted by version
        versions = [m.VERSION for m in migrations]
        assert versions == sorted(versions)
    
    async def test_run_migrations(self, test_db):
        """Test running all migrations."""
        manager = MigrationManager(test_db)
        applied = await manager.run_migrations()
        
        # Should have applied migrations
        assert applied >= 2
        
        # Check version is updated
        version = await manager.get_current_version()
        assert version >= 2
        
        # Check tables were created
        cursor = await test_db.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        tables = {row[0] for row in await cursor.fetchall()}
        
        assert "allowed_chats" in tables
        assert "action_logs" in tables
        assert "domain_permissions" in tables
        assert "subdomain_permissions" in tables
    
    async def test_migrations_are_idempotent(self, test_db):
        """Test that running migrations twice doesn't fail."""
        manager = MigrationManager(test_db)
        
        # Run once
        applied1 = await manager.run_migrations()
        assert applied1 >= 2
        
        # Run again - should apply 0
        applied2 = await manager.run_migrations()
        assert applied2 == 0
