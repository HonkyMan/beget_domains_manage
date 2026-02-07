"""Allowed chats repository."""

from dataclasses import dataclass
from datetime import datetime

from app.services.database.connection import Database


@dataclass
class AllowedChat:
    """Allowed chat entity."""

    id: int
    chat_id: int
    added_by: str
    added_at: datetime
    note: str | None


class ChatsRepository:
    """Repository for managing allowed chats."""

    def __init__(self, db: Database):
        self.db = db

    async def get_all(self) -> list[AllowedChat]:
        """Get all allowed chats."""
        cursor = await self.db.connection.execute(
            "SELECT * FROM allowed_chats ORDER BY added_at DESC"
        )
        rows = await cursor.fetchall()
        return [
            AllowedChat(
                id=row["id"],
                chat_id=row["chat_id"],
                added_by=row["added_by"],
                added_at=datetime.fromisoformat(row["added_at"]),
                note=row["note"],
            )
            for row in rows
        ]

    async def get_chat_ids(self) -> set[int]:
        """Get set of allowed chat IDs."""
        cursor = await self.db.connection.execute(
            "SELECT chat_id FROM allowed_chats"
        )
        rows = await cursor.fetchall()
        return {row["chat_id"] for row in rows}

    async def is_allowed(self, chat_id: int) -> bool:
        """Check if chat is allowed."""
        cursor = await self.db.connection.execute(
            "SELECT 1 FROM allowed_chats WHERE chat_id = ?",
            (chat_id,),
        )
        return await cursor.fetchone() is not None

    async def add(self, chat_id: int, added_by: str, note: str | None = None) -> bool:
        """Add a chat to allowed list. Returns True if added, False if exists."""
        try:
            await self.db.connection.execute(
                "INSERT INTO allowed_chats (chat_id, added_by, note) VALUES (?, ?, ?)",
                (chat_id, added_by, note),
            )
            await self.db.connection.commit()
            return True
        except Exception:
            return False

    async def remove(self, chat_id: int) -> bool:
        """Remove a chat from allowed list. Returns True if removed."""
        cursor = await self.db.connection.execute(
            "DELETE FROM allowed_chats WHERE chat_id = ?",
            (chat_id,),
        )
        await self.db.connection.commit()
        return cursor.rowcount > 0
