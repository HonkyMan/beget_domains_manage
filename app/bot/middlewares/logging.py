"""Logging middleware."""

from typing import Any, Awaitable, Callable
from aiogram import BaseMiddleware, Bot
from aiogram.types import Message, CallbackQuery, TelegramObject

from app.services.database import LogsRepository
from app.utils.helpers import format_datetime
from datetime import datetime

# Actions that should be logged (significant user actions only)
LOGGABLE_CALLBACK_PREFIXES = (
    "confirm_subdomain:",  # Subdomain created
    "do_del_sub:",         # Subdomain deleted
    "do_delete_a:",        # A record deleted
    "delete_txt:",         # TXT record deleted
)

LOGGABLE_COMMANDS = (
    "/start",
    "/help",
)


class LoggingMiddleware(BaseMiddleware):
    """Middleware to log significant user actions and notify admin."""

    def __init__(self, logs_repo: LogsRepository, bot: Bot, admin_chat_id: int):
        self.logs_repo = logs_repo
        self.bot = bot
        self.admin_chat_id = admin_chat_id

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        # Inject action logger into data for handlers to use
        data["action_logger"] = ActionLogger(
            self.logs_repo, self.bot, self.admin_chat_id
        )
        
        # Extract info from event
        chat_id: int | None = None
        user_id: int | None = None
        username: str | None = None
        action: str | None = None
        should_log = False

        if isinstance(event, Message):
            if event.chat:
                chat_id = event.chat.id
            if event.from_user:
                user_id = event.from_user.id
                username = event.from_user.username or event.from_user.full_name
            
            # Log commands
            text = event.text or ""
            if text.startswith("/"):
                if any(text.startswith(cmd) for cmd in LOGGABLE_COMMANDS):
                    action = text
                    should_log = True
            
        elif isinstance(event, CallbackQuery):
            if event.message:
                chat_id = event.message.chat.id
            if event.from_user:
                user_id = event.from_user.id
                username = event.from_user.username or event.from_user.full_name
            
            callback_data = event.data or ""
            # Check if this is a loggable action
            if any(callback_data.startswith(prefix) for prefix in LOGGABLE_CALLBACK_PREFIXES):
                action = f"callback: {callback_data}"
                should_log = True

        # Execute handler first
        result = await handler(event, data)

        # Log action if significant and from non-admin chat
        if should_log and action and chat_id and chat_id != self.admin_chat_id:
            await self._log_action(chat_id, user_id, username, action)

        return result

    async def _log_action(
        self,
        chat_id: int,
        user_id: int | None,
        username: str | None,
        action: str,
    ) -> None:
        """Log action to database and notify admin."""
        await self.logs_repo.add(
            chat_id=chat_id,
            user_id=user_id,
            username=username,
            action=action,
        )

        now = format_datetime(datetime.now())
        notification = (
            f"Action from user:\n"
            f"Time: {now}\n"
            f"Chat ID: {chat_id}\n"
            f"User ID: {user_id}\n"
            f"Username: @{username}\n"
            f"Action: {action}"
        )
        try:
            await self.bot.send_message(self.admin_chat_id, notification)
        except Exception:
            pass


class ActionLogger:
    """Helper class for handlers to log significant actions."""
    
    def __init__(self, logs_repo: LogsRepository, bot: Bot, admin_chat_id: int):
        self.logs_repo = logs_repo
        self.bot = bot
        self.admin_chat_id = admin_chat_id
    
    async def log(
        self,
        chat_id: int,
        user_id: int | None,
        username: str | None,
        action: str,
    ) -> None:
        """Log a significant action."""
        if chat_id == self.admin_chat_id:
            return
            
        await self.logs_repo.add(
            chat_id=chat_id,
            user_id=user_id,
            username=username,
            action=action,
        )
        
        now = format_datetime(datetime.now())
        notification = (
            f"Action from user:\n"
            f"Time: {now}\n"
            f"Chat ID: {chat_id}\n"
            f"User ID: {user_id}\n"
            f"Username: @{username}\n"
            f"Action: {action}"
        )
        try:
            await self.bot.send_message(self.admin_chat_id, notification)
        except Exception:
            pass
