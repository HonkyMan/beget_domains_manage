"""Authentication middleware."""

from typing import Any, Awaitable, Callable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject

from app.services.database import ChatsRepository, PermissionsRepository
from app.services.permissions import PermissionChecker


class AuthMiddleware(BaseMiddleware):
    """Middleware to check if chat is allowed to use the bot."""

    def __init__(
        self,
        chats_repo: ChatsRepository,
        permissions_repo: PermissionsRepository,
        admin_chat_id: int,
    ):
        self.chats_repo = chats_repo
        self.admin_chat_id = admin_chat_id
        self.permission_checker = PermissionChecker(permissions_repo, admin_chat_id)

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        # Extract chat_id from event
        chat_id: int | None = None

        if isinstance(event, Message) and event.chat:
            chat_id = event.chat.id
        elif isinstance(event, CallbackQuery) and event.message:
            chat_id = event.message.chat.id

        if chat_id is None:
            return None

        # Admin always has access
        if chat_id == self.admin_chat_id:
            data["is_admin"] = True
            data["user_chat_id"] = chat_id
            data["permission_checker"] = self.permission_checker
            return await handler(event, data)

        # Check if chat is in allowed list
        if await self.chats_repo.is_allowed(chat_id):
            data["is_admin"] = False
            data["user_chat_id"] = chat_id
            data["permission_checker"] = self.permission_checker
            return await handler(event, data)

        # Unauthorized - silently ignore
        return None
