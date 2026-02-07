"""Admin module router - assembles all admin submodules."""

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.bot.callback_data import (
    CB_ADMIN_CHATS, CB_ADMIN_LOGS, CB_MENU_MAIN, CB_MENU_ADMIN,
)
from app.modules.admin.filters import IsAdminFilter
from app.modules.admin import chats, permissions, logs

# Create main admin router
router = Router(name="admin")

# Include submodule routers (filters applied in setup_admin_deps)
router.include_router(chats.router)
router.include_router(permissions.router)
router.include_router(logs.router)


def admin_menu_keyboard() -> InlineKeyboardMarkup:
    """Admin panel main menu."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Allowed Chats", callback_data=CB_ADMIN_CHATS)
    )
    builder.row(
        InlineKeyboardButton(text="Manage Permissions", callback_data="ap")  # admin permissions
    )
    builder.row(
        InlineKeyboardButton(text="Action Logs", callback_data=CB_ADMIN_LOGS)
    )
    builder.row(
        InlineKeyboardButton(text="Back", callback_data=CB_MENU_MAIN)
    )
    return builder.as_markup()


@router.callback_query(F.data == CB_MENU_ADMIN)
async def admin_menu(callback: CallbackQuery) -> None:
    """Show admin panel menu."""
    await callback.message.edit_text(
        "Admin Panel\n\nSelect an option:",
        reply_markup=admin_menu_keyboard(),
    )
    await callback.answer()


def setup_admin_deps(chats_repo, logs_repo, permissions_repo, admin_chat_id: int) -> None:
    """Setup admin filter with actual admin_chat_id.
    
    This must be called during bot initialization to configure
    the admin filter with the correct admin_chat_id value.
    """
    admin_filter = IsAdminFilter(admin_chat_id=admin_chat_id)
    router.message.filter(admin_filter)
    router.callback_query.filter(admin_filter)
