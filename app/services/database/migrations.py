"""Database migration system.

A lightweight migration system for SQLite that:
- Tracks applied migrations in a schema_version table
- Discovers migration files from the versions/ directory
- Applies pending migrations on startup
"""

import importlib
import logging
from pathlib import Path
from typing import Protocol, runtime_checkable

import aiosqlite

logger = logging.getLogger(__name__)


@runtime_checkable
class Migration(Protocol):
    """Protocol for migration modules."""
    
    VERSION: int
    DESCRIPTION: str
    
    async def upgrade(self, connection: aiosqlite.Connection) -> None: ...
    async def downgrade(self, connection: aiosqlite.Connection) -> None: ...


class MigrationManager:
    """Manages database migrations.
    
    Usage:
        manager = MigrationManager(connection)
        await manager.run_migrations()
    """
    
    VERSIONS_PACKAGE = "app.services.database.versions"
    
    def __init__(self, connection: aiosqlite.Connection):
        self.connection = connection
    
    async def init_schema_version_table(self) -> None:
        """Create the schema_version table if it doesn't exist."""
        await self.connection.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY,
                description TEXT NOT NULL,
                applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await self.connection.commit()
    
    async def get_current_version(self) -> int:
        """Get the current schema version."""
        try:
            cursor = await self.connection.execute(
                "SELECT MAX(version) FROM schema_version"
            )
            row = await cursor.fetchone()
            return row[0] if row and row[0] else 0
        except Exception:
            return 0
    
    def discover_migrations(self) -> list[Migration]:
        """Discover all migration modules in the versions directory."""
        migrations = []
        versions_dir = Path(__file__).parent / "versions"
        
        for file_path in sorted(versions_dir.glob("v*.py")):
            if file_path.name.startswith("__"):
                continue
            
            module_name = f"{self.VERSIONS_PACKAGE}.{file_path.stem}"
            try:
                module = importlib.import_module(module_name)
                if hasattr(module, "VERSION") and hasattr(module, "upgrade"):
                    migrations.append(module)
            except Exception as e:
                logger.error(f"Failed to load migration {module_name}: {e}")
        
        # Sort by version number
        migrations.sort(key=lambda m: m.VERSION)
        return migrations
    
    async def get_pending_migrations(self) -> list[Migration]:
        """Get migrations that haven't been applied yet."""
        current_version = await self.get_current_version()
        all_migrations = self.discover_migrations()
        return [m for m in all_migrations if m.VERSION > current_version]
    
    async def apply_migration(self, migration: Migration) -> None:
        """Apply a single migration."""
        logger.info(f"Applying migration v{migration.VERSION}: {migration.DESCRIPTION}")
        
        try:
            await migration.upgrade(self.connection)
            
            # Record the migration
            await self.connection.execute(
                "INSERT INTO schema_version (version, description) VALUES (?, ?)",
                (migration.VERSION, migration.DESCRIPTION),
            )
            await self.connection.commit()
            
            logger.info(f"Migration v{migration.VERSION} applied successfully")
        except Exception as e:
            logger.error(f"Migration v{migration.VERSION} failed: {e}")
            raise
    
    async def run_migrations(self) -> int:
        """Run all pending migrations.
        
        Returns:
            Number of migrations applied.
        """
        await self.init_schema_version_table()
        
        pending = await self.get_pending_migrations()
        if not pending:
            logger.info("Database is up to date")
            return 0
        
        logger.info(f"Found {len(pending)} pending migration(s)")
        
        for migration in pending:
            await self.apply_migration(migration)
        
        logger.info(f"Applied {len(pending)} migration(s)")
        return len(pending)
    
    async def get_migration_history(self) -> list[dict]:
        """Get the migration history."""
        try:
            cursor = await self.connection.execute(
                "SELECT version, description, applied_at FROM schema_version ORDER BY version"
            )
            rows = await cursor.fetchall()
            return [
                {"version": row[0], "description": row[1], "applied_at": row[2]}
                for row in rows
            ]
        except Exception:
            return []
