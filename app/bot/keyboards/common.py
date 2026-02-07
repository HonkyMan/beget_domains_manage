"""Common keyboards used across the bot."""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.bot.callback_data import CB_MENU_DOMAINS, CB_MENU_ADMIN, CB_MENU_MAIN


def main_menu_keyboard(is_admin: bool = False) -> InlineKeyboardMarkup:
    """Main menu keyboard."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Domains", callback_data=CB_MENU_DOMAINS)
    )
    if is_admin:
        builder.row(
            InlineKeyboardButton(text="Admin Panel", callback_data=CB_MENU_ADMIN)
        )
    return builder.as_markup()


def back_button(callback_data: str = CB_MENU_MAIN) -> InlineKeyboardMarkup:
    """Single back button."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Back", callback_data=callback_data)]
        ]
    )


def confirm_cancel_keyboard(
    confirm_data: str,
    cancel_data: str = "x",
) -> InlineKeyboardMarkup:
    """Confirm/Cancel keyboard."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Confirm", callback_data=confirm_data),
                InlineKeyboardButton(text="Cancel", callback_data=cancel_data),
            ]
        ]
    )
