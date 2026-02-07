"""Database connection manager."""

import logging
import aiosqlite
from pathlib import Path

from app.services.database.migrations import MigrationManager

logger = logging.getLogger(__name__)


class Database:
    """SQLite database connection manager.
    
    Uses MigrationManager for schema management instead of hardcoded schema.
    All schema changes should be done via migration files in versions/.
    """

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._connection: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        """Connect to database and run migrations."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = await aiosqlite.connect(self.db_path)
        self._connection.row_factory = aiosqlite.Row
        
        # Run migrations instead of hardcoded schema
        migration_manager = MigrationManager(self._connection)
        applied = await migration_manager.run_migrations()
        if applied > 0:
            logger.info(f"Applied {applied} database migration(s)")

    async def disconnect(self) -> None:
        """Close database connection."""
        if self._connection:
            await self._connection.close()
            self._connection = None

    @property
    def connection(self) -> aiosqlite.Connection:
        """Get active database connection."""
        if not self._connection:
            raise RuntimeError("Database not connected")
        return self._connection
