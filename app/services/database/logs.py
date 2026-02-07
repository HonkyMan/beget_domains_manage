"""Action logs repository."""

from dataclasses import dataclass
from datetime import datetime

from app.services.database.connection import Database


@dataclass
class ActionLog:
    """Action log entity."""

    id: int
    chat_id: int
    user_id: int | None
    username: str | None
    action: str
    details: str | None
    created_at: datetime


class LogsRepository:
    """Repository for managing action logs."""

    def __init__(self, db: Database):
        self.db = db

    async def add(
        self,
        chat_id: int,
        action: str,
        user_id: int | None = None,
        username: str | None = None,
        details: str | None = None,
    ) -> None:
        """Add an action log entry."""
        await self.db.connection.execute(
            """
            INSERT INTO action_logs (chat_id, user_id, username, action, details)
            VALUES (?, ?, ?, ?, ?)
            """,
            (chat_id, user_id, username, action, details),
        )
        await self.db.connection.commit()

    async def get_recent(self, limit: int = 20) -> list[ActionLog]:
        """Get recent action logs."""
        cursor = await self.db.connection.execute(
            "SELECT * FROM action_logs ORDER BY created_at DESC LIMIT ?",
            (limit,),
        )
        rows = await cursor.fetchall()
        return [
            ActionLog(
                id=row["id"],
                chat_id=row["chat_id"],
                user_id=row["user_id"],
                username=row["username"],
                action=row["action"],
                details=row["details"],
                created_at=datetime.fromisoformat(row["created_at"]),
            )
            for row in rows
        ]

    async def get_by_chat(self, chat_id: int, limit: int = 20) -> list[ActionLog]:
        """Get action logs for a specific chat."""
        cursor = await self.db.connection.execute(
            """
            SELECT * FROM action_logs 
            WHERE chat_id = ? 
            ORDER BY created_at DESC 
            LIMIT ?
            """,
            (chat_id, limit),
        )
        rows = await cursor.fetchall()
        return [
            ActionLog(
                id=row["id"],
                chat_id=row["chat_id"],
                user_id=row["user_id"],
                username=row["username"],
                action=row["action"],
                details=row["details"],
                created_at=datetime.fromisoformat(row["created_at"]),
            )
            for row in rows
        ]
