"""Allowed chats management handlers with optimized callback_data."""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from app.core.container import DependencyContainer
from app.bot.callback_data import (
    CB_ADMIN_CHATS, CB_ADMIN_CHAT, CB_ADMIN_ADD_CHAT,
    CB_ADMIN_REMOVE, CB_ADMIN_CONFIRM_RM,
)
from app.modules.admin.states import AdminStates
from app.modules.admin.chats.keyboards import (
    chats_list_keyboard,
    chat_actions_keyboard,
    confirm_remove_keyboard,
)
from app.utils.helpers import format_datetime

router = Router(name="admin_chats")


@router.callback_query(F.data == CB_ADMIN_CHATS)
async def list_chats(
    callback: CallbackQuery, 
    state: FSMContext,
    container: DependencyContainer,
) -> None:
    """Show list of allowed chats."""
    await state.clear()

    chats = await container.chats_repo.get_all()
    text = "Allowed Chats:\n\n"

    if chats:
        for chat in chats:
            note = f" - {chat.note}" if chat.note else ""
            added = format_datetime(chat.added_at)
            text += f"ID: {chat.chat_id}{note}\nAdded: {added}\n\n"
    else:
        text += "No allowed chats yet."

    await callback.message.edit_text(text, reply_markup=chats_list_keyboard(chats))
    await callback.answer()


@router.callback_query(F.data == CB_ADMIN_ADD_CHAT)
async def start_add_chat(callback: CallbackQuery, state: FSMContext) -> None:
    """Start adding a new chat."""
    await state.set_state(AdminStates.waiting_chat_id)
    await callback.message.edit_text(
        "Enter the Chat ID to add:\n\n"
        "(You can get it by forwarding a message from the chat to @userinfobot)",
    )
    await callback.answer()


@router.message(AdminStates.waiting_chat_id)
async def receive_chat_id(message: Message, state: FSMContext) -> None:
    """Receive chat ID from admin."""
    try:
        chat_id = int(message.text.strip())
    except ValueError:
        await message.answer("Invalid Chat ID. Please enter a number:")
        return

    await state.update_data(chat_id=chat_id)
    await state.set_state(AdminStates.waiting_chat_note)
    await message.answer(
        f"Adding Chat ID: {chat_id}\n\n"
        "Enter a note for this chat (or send '-' to skip):"
    )


@router.message(AdminStates.waiting_chat_note)
async def receive_chat_note(
    message: Message, 
    state: FSMContext,
    container: DependencyContainer,
) -> None:
    """Receive note and add chat."""
    data = await state.get_data()
    chat_id = data["chat_id"]
    note = message.text.strip() if message.text.strip() != "-" else None

    success = await container.chats_repo.add(
        chat_id=chat_id,
        added_by=f"@{message.from_user.username or message.from_user.id}",
        note=note,
    )

    if success:
        await message.answer(f"Chat {chat_id} added successfully!")
    else:
        await message.answer(f"Chat {chat_id} already exists or error occurred.")

    await state.clear()


@router.callback_query(F.data.startswith(f"{CB_ADMIN_CHAT}:"))
async def show_chat_actions(callback: CallbackQuery) -> None:
    """Show actions for a specific chat (ach:chat_id)."""
    chat_id = int(callback.data.split(":")[1])
    await callback.message.edit_text(
        f"Chat ID: {chat_id}\n\nSelect action:",
        reply_markup=chat_actions_keyboard(chat_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith(f"{CB_ADMIN_REMOVE}:"))
async def confirm_remove_chat(callback: CallbackQuery) -> None:
    """Confirm chat removal (arc:chat_id)."""
    chat_id = int(callback.data.split(":")[1])
    await callback.message.edit_text(
        f"Are you sure you want to remove Chat ID: {chat_id}?",
        reply_markup=confirm_remove_keyboard(chat_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith(f"{CB_ADMIN_CONFIRM_RM}:"))
async def do_remove_chat(
    callback: CallbackQuery,
    state: FSMContext,
    container: DependencyContainer,
) -> None:
    """Remove chat from allowed list (acr:chat_id)."""
    chat_id = int(callback.data.split(":")[1])
    success = await container.chats_repo.remove(chat_id)

    if success:
        await callback.answer(f"Chat {chat_id} removed!", show_alert=True)
    else:
        await callback.answer("Chat not found or error occurred.", show_alert=True)

    # Refresh chat list
    chats = await container.chats_repo.get_all()
    text = "Allowed Chats:\n\n"

    if chats:
        for chat in chats:
            note = f" - {chat.note}" if chat.note else ""
            added = format_datetime(chat.added_at)
            text += f"ID: {chat.chat_id}{note}\nAdded: {added}\n\n"
    else:
        text += "No allowed chats yet."

    await callback.message.edit_text(text, reply_markup=chats_list_keyboard(chats))
