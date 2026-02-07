"""Dependency injection middleware."""

from typing import Any, Awaitable, Callable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery

from app.core.container import DependencyContainer


class DependencyMiddleware(BaseMiddleware):
    """Middleware that injects the dependency container into handlers.
    
    This middleware makes the container available to all handlers
    via the `container` parameter, enabling clean dependency injection
    without global state.
    """
    
    def __init__(self, container: DependencyContainer):
        self.container = container
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        # Inject container into handler data
        data["container"] = self.container
        
        # Extract chat_id for convenience
        chat_id: int | None = None
        if isinstance(event, Message) and event.chat:
            chat_id = event.chat.id
        elif isinstance(event, CallbackQuery) and event.message:
            chat_id = event.message.chat.id
        
        if chat_id is not None:
            data["user_chat_id"] = chat_id
            data["is_admin"] = self.container.is_admin(chat_id)
        
        return await handler(event, data)
