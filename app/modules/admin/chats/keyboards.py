"""Allowed chats keyboards with optimized callback_data."""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.services.database.chats import AllowedChat
from app.bot.callback_data import (
    CB_ADMIN_CHATS, CB_ADMIN_CHAT, CB_ADMIN_ADD_CHAT,
    CB_ADMIN_REMOVE, CB_ADMIN_CONFIRM_RM, CB_MENU_ADMIN,
)


def chats_list_keyboard(chats: list[AllowedChat]) -> InlineKeyboardMarkup:
    """List of allowed chats with management options."""
    builder = InlineKeyboardBuilder()

    for chat in chats:
        note = f" ({chat.note})" if chat.note else ""
        builder.row(
            InlineKeyboardButton(
                text=f"{chat.chat_id}{note}",
                callback_data=f"{CB_ADMIN_CHAT}:{chat.chat_id}",
            )
        )

    builder.row(
        InlineKeyboardButton(text="+ Add Chat", callback_data=CB_ADMIN_ADD_CHAT)
    )
    builder.row(
        InlineKeyboardButton(text="Back", callback_data=CB_MENU_ADMIN)
    )
    return builder.as_markup()


def chat_actions_keyboard(chat_id: int) -> InlineKeyboardMarkup:
    """Actions for a specific chat."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Remove",
                    callback_data=f"{CB_ADMIN_REMOVE}:{chat_id}",
                )
            ],
            [
                InlineKeyboardButton(text="Back", callback_data=CB_ADMIN_CHATS)
            ],
        ]
    )


def confirm_remove_keyboard(chat_id: int) -> InlineKeyboardMarkup:
    """Confirm chat removal."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Yes, Remove",
                    callback_data=f"{CB_ADMIN_CONFIRM_RM}:{chat_id}",
                ),
                InlineKeyboardButton(text="Cancel", callback_data=CB_ADMIN_CHATS),
            ]
        ]
    )
