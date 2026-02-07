"""Dependency injection container."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.config import Settings
    from app.services.database.connection import Database
    from app.services.database.chats import ChatsRepository
    from app.services.database.logs import LogsRepository
    from app.services.database.permissions import PermissionsRepository
    from app.services.permissions.checker import PermissionChecker
    from app.services.beget.manager import BegetClientManager


@dataclass(frozen=True)
class DependencyContainer:
    """Immutable container for all application dependencies.
    
    This container is created once at application startup and injected
    into handlers via middleware. Being frozen (immutable) ensures
    thread-safety and prevents accidental modifications.
    """
    
    settings: "Settings"
    db: "Database"
    chats_repo: "ChatsRepository"
    logs_repo: "LogsRepository"
    permissions_repo: "PermissionsRepository"
    permission_checker: "PermissionChecker"
    beget_manager: "BegetClientManager"
    admin_chat_id: int
    
    def is_admin(self, chat_id: int) -> bool:
        """Check if chat_id belongs to admin."""
        return chat_id == self.admin_chat_id
