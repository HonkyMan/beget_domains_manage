"""DNS management keyboards with optimized callback_data."""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.services.beget.types import DnsRecord
from app.bot.callback_data import CB_DOMAIN


def dns_menu_keyboard(domain_id: int, back_callback: str = "") -> InlineKeyboardMarkup:
    """DNS management menu with short callbacks."""
    if not back_callback:
        back_callback = f"{CB_DOMAIN}:{domain_id}"
    
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="View Records", callback_data=f"dnv:{domain_id}")
            ],
            [
                InlineKeyboardButton(text="A Records", callback_data=f"dna:{domain_id}"),
                InlineKeyboardButton(text="TXT Records", callback_data=f"dnt:{domain_id}"),
            ],
            [InlineKeyboardButton(text="Back", callback_data=back_callback)],
        ]
    )


def a_records_keyboard(domain_id: int, records: list[DnsRecord]) -> InlineKeyboardMarkup:
    """A records management with index-based callbacks."""
    builder = InlineKeyboardBuilder()

    for i, record in enumerate(records):
        builder.row(
            InlineKeyboardButton(
                text=f"{record.value}",
                callback_data=f"ea:{domain_id}:{i}",
            )
        )

    builder.row(
        InlineKeyboardButton(text="+ Add A Record", callback_data=f"aa:{domain_id}")
    )
    builder.row(
        InlineKeyboardButton(text="Back", callback_data=f"dn:{domain_id}")
    )
    return builder.as_markup()


def txt_records_keyboard(domain_id: int, records: list[DnsRecord]) -> InlineKeyboardMarkup:
    """TXT records management with index-based callbacks."""
    builder = InlineKeyboardBuilder()

    for i, record in enumerate(records):
        display = record.value[:30] + "..." if len(record.value) > 30 else record.value
        builder.row(
            InlineKeyboardButton(
                text=display,
                callback_data=f"tr:{domain_id}:{i}",
            )
        )

    builder.row(
        InlineKeyboardButton(text="+ Add TXT Record", callback_data=f"at:{domain_id}")
    )
    builder.row(
        InlineKeyboardButton(text="Back", callback_data=f"dn:{domain_id}")
    )
    return builder.as_markup()


def edit_a_record_keyboard(domain_id: int, record_index: int) -> InlineKeyboardMarkup:
    """Edit A record options."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Change IP",
                    callback_data=f"ca:{domain_id}:{record_index}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="Delete",
                    callback_data=f"da:{domain_id}:{record_index}",
                )
            ],
            [InlineKeyboardButton(text="Back", callback_data=f"dna:{domain_id}")],
        ]
    )


def confirm_keyboard(confirm_data: str, cancel_data: str) -> InlineKeyboardMarkup:
    """Generic confirm/cancel keyboard."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Confirm", callback_data=confirm_data),
                InlineKeyboardButton(text="Cancel", callback_data=cancel_data),
            ]
        ]
    )


def cancel_keyboard(cancel_data: str) -> InlineKeyboardMarkup:
    """Generic cancel-only keyboard for text input prompts."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Cancel", callback_data=cancel_data)]
        ]
    )
