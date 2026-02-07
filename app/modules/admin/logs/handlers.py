"""Action logs handlers."""

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from app.core.container import DependencyContainer
from app.bot.callback_data import CB_ADMIN_LOGS, CB_MENU_ADMIN
from app.utils.helpers import format_datetime

router = Router(name="admin_logs")


@router.callback_query(F.data == CB_ADMIN_LOGS)
async def show_logs(
    callback: CallbackQuery,
    container: DependencyContainer,
) -> None:
    """Show recent action logs."""
    logs = await container.logs_repo.get_recent(limit=15)
    text = "Recent Actions:\n\n"

    if logs:
        for log in logs:
            time = format_datetime(log.created_at)
            user = f"@{log.username}" if log.username else str(log.user_id)
            text += f"{time}\n{user}: {log.action}\n\n"
    else:
        text += "No actions recorded yet."

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Back", callback_data=CB_MENU_ADMIN)]
            ]
        ),
    )
    await callback.answer()
