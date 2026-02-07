"""Admin module filters."""

import logging
from typing import Any
from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery

logger = logging.getLogger(__name__)


class IsAdminFilter(BaseFilter):
    """Filter to check if user is admin.
    
    This filter checks if the chat_id matches the configured admin_chat_id.
    It's applied to all handlers in the admin router.
    """

    def __init__(self, admin_chat_id: int | None = None):
        self.admin_chat_id = admin_chat_id

    async def __call__(self, event: Message | CallbackQuery, **kwargs: Any) -> bool:
        # Get admin_chat_id from kwargs if not set (injected by middleware)
        admin_chat_id = self.admin_chat_id
        if admin_chat_id is None:
            # Try to get from container
            container = kwargs.get("container")
            if container:
                admin_chat_id = container.admin_chat_id
            else:
                # Fallback to is_admin flag from auth middleware
                is_admin = kwargs.get("is_admin", False)
                logger.info(f"IsAdminFilter: no container, using is_admin={is_admin}")
                return is_admin

        chat_id = None
        if isinstance(event, Message) and event.chat:
            chat_id = event.chat.id
        elif isinstance(event, CallbackQuery) and event.message:
            chat_id = event.message.chat.id

        result = chat_id == admin_chat_id
        logger.info(f"IsAdminFilter: chat_id={chat_id}, admin_chat_id={admin_chat_id}, result={result}")
        return result
