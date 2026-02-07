"""Subdomain management keyboards with optimized callback_data."""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.services.beget.types import Subdomain
from app.bot.callback_data import CB_DOMAIN


def subdomains_list_keyboard(
    subdomains: list[Subdomain],
    domain_id: int,
    can_create: bool = True,
) -> InlineKeyboardMarkup:
    """List of subdomains with management options.
    
    Uses short callbacks: s:{id} for subdomain view
    """
    builder = InlineKeyboardBuilder()

    for sub in subdomains:
        builder.row(
            InlineKeyboardButton(
                text=sub.fqdn,
                callback_data=f"s:{sub.id}",
            )
        )

    if can_create:
        builder.row(
            InlineKeyboardButton(
                text="+ Add Subdomain",
                callback_data=f"as:{domain_id}",
            )
        )
    builder.row(
        InlineKeyboardButton(
            text="Back",
            callback_data=f"{CB_DOMAIN}:{domain_id}",
        )
    )
    return builder.as_markup()


def subdomain_actions_keyboard(
    subdomain_id: int,
    parent_domain_id: int,
    can_delete: bool = True,
    can_dns: bool = True,
) -> InlineKeyboardMarkup:
    """Actions for a subdomain using short callbacks."""
    buttons = []
    
    if can_dns:
        buttons.append([
            InlineKeyboardButton(
                text="DNS Records",
                callback_data=f"sdn:{subdomain_id}",
            )
        ])
    
    if can_delete:
        buttons.append([
            InlineKeyboardButton(
                text="Delete",
                callback_data=f"ds:{subdomain_id}",
            )
        ])
    
    buttons.append([
        InlineKeyboardButton(
            text="Back",
            callback_data=f"ss:{parent_domain_id}",
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


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
