"""Domain list and menu keyboards with optimized callback_data."""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.services.beget.types import Domain
from app.bot.callback_data import CB_DOMAIN, CB_MENU_MAIN, CB_MENU_DOMAINS


def domains_list_keyboard(domains: list[Domain]) -> InlineKeyboardMarkup:
    """List of domains to select.
    
    Uses short callback: d:{id} instead of domain:{id}:{fqdn}
    FQDN is stored in FSM state by handler.
    """
    builder = InlineKeyboardBuilder()

    for domain in domains:
        builder.row(
            InlineKeyboardButton(
                text=domain.fqdn,
                callback_data=f"{CB_DOMAIN}:{domain.id}",
            )
        )

    builder.row(
        InlineKeyboardButton(text="Back", callback_data=CB_MENU_MAIN)
    )
    return builder.as_markup()


def domain_menu_keyboard(domain_id: int) -> InlineKeyboardMarkup:
    """Domain management menu.
    
    Uses short callbacks. FQDN from FSM state.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Subdomains",
                    callback_data=f"ss:{domain_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="DNS Records",
                    callback_data=f"dn:{domain_id}",
                )
            ],
            [InlineKeyboardButton(text="Back", callback_data=CB_MENU_DOMAINS)],
        ]
    )
