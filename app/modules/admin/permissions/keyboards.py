"""Permission management keyboards with optimized callback_data.

Uses short prefixes and indices instead of long FQDNs.
FQDNs are stored in FSM state and retrieved by handlers.
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.services.database.chats import AllowedChat
from app.services.database.permissions import DomainPermission, SubdomainPermission
from app.services.beget.types import Domain, Subdomain
from app.bot.callback_data import (
    CB_PERM_DOMAINS, CB_PERM_DOMAIN, CB_PERM_ITEM,
    CB_PERM_GRANT, CB_PERM_CANCEL_GRANT, CB_PERM_USER,
    CB_PERM_REVOKE, CB_PERM_DO_REVOKE, CB_PERM_DNS,
    CB_PERM_SUB, CB_PERM_SUBDNS, CB_PERM_SUBDEL,
    CB_PERM_USERS, CB_PERM_VIEWUSER, CB_MENU_ADMIN,
)


def permissions_menu_keyboard() -> InlineKeyboardMarkup:
    """Permission management menu."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Domain Permissions", callback_data=CB_PERM_DOMAINS)
    )
    builder.row(
        InlineKeyboardButton(text="View User Permissions", callback_data=CB_PERM_USERS)
    )
    builder.row(
        InlineKeyboardButton(text="Back", callback_data=CB_MENU_ADMIN)
    )
    return builder.as_markup()


def domains_for_permissions_keyboard(domains: list[Domain]) -> InlineKeyboardMarkup:
    """List of domains for permission management (uses index, fqdn stored in state)."""
    builder = InlineKeyboardBuilder()
    
    for i, domain in enumerate(domains):
        builder.row(
            InlineKeyboardButton(
                text=domain.fqdn,
                callback_data=f"{CB_PERM_DOMAIN}:{i}",  # pdo:0
            )
        )
    
    builder.row(
        InlineKeyboardButton(text="Back", callback_data="ap")  # admin permissions menu
    )
    return builder.as_markup()


def domain_items_keyboard(
    domain_index: int,
    subdomains: list[Subdomain],
) -> InlineKeyboardMarkup:
    """Show domain and its subdomains for permission assignment."""
    builder = InlineKeyboardBuilder()
    
    # Domain itself (pi:d:domain_index)
    builder.row(
        InlineKeyboardButton(
            text="[Domain] (this domain)",
            callback_data=f"{CB_PERM_ITEM}:d:{domain_index}",
        )
    )
    
    # Subdomains (pi:s:subdomain_index)
    for i, sub in enumerate(subdomains):
        # Truncate long names for display
        display = sub.fqdn[:40] + "..." if len(sub.fqdn) > 40 else sub.fqdn
        builder.row(
            InlineKeyboardButton(
                text=f"  {display}",
                callback_data=f"{CB_PERM_ITEM}:s:{i}",
            )
        )
    
    builder.row(
        InlineKeyboardButton(text="Back", callback_data=CB_PERM_DOMAINS)
    )
    return builder.as_markup()


def item_users_keyboard(
    item_index: int,
    is_domain: bool,
    users: list[DomainPermission] | list[SubdomainPermission],
    chat_notes: dict[int, str | None] | None = None,
) -> InlineKeyboardMarkup:
    """Show users with access to a domain/subdomain."""
    builder = InlineKeyboardBuilder()
    
    item_type = "d" if is_domain else "s"
    chat_notes = chat_notes or {}
    
    for i, user in enumerate(users):
        note = chat_notes.get(user.chat_id)
        note_str = f" ({note})" if note else ""
        
        if is_domain and isinstance(user, DomainPermission):
            perms = []
            if user.can_edit_dns:
                perms.append("E")
            if user.can_delete_dns:
                perms.append("D")
            if user.can_create_subdomain:
                perms.append("C")
            if user.can_delete_subdomain:
                perms.append("X")
            perm_str = f" [{','.join(perms)}]" if perms else ""
            builder.row(
                InlineKeyboardButton(
                    text=f"Chat {user.chat_id}{note_str}{perm_str}",
                    callback_data=f"{CB_PERM_USER}:{item_type}:{i}",  # pu:d:0
                )
            )
        elif isinstance(user, SubdomainPermission):
            perms = []
            if user.can_edit_dns:
                perms.append("E")
            if user.can_delete_dns:
                perms.append("D")
            if user.can_delete_subdomain:
                perms.append("X")
            perm_str = f" [{','.join(perms)}]" if perms else ""
            builder.row(
                InlineKeyboardButton(
                    text=f"Chat {user.chat_id}{note_str}{perm_str}",
                    callback_data=f"{CB_PERM_USER}:{item_type}:{i}",
                )
            )
        else:
            builder.row(
                InlineKeyboardButton(
                    text=f"Chat {user.chat_id}{note_str}",
                    callback_data=f"{CB_PERM_USER}:{item_type}:{i}",
                )
            )
    
    builder.row(
        InlineKeyboardButton(
            text="+ Grant Access",
            callback_data=f"{CB_PERM_GRANT}:{item_type}",  # pg:d
        )
    )
    
    # Back navigation
    builder.row(
        InlineKeyboardButton(
            text="Back",
            callback_data=f"{CB_PERM_DOMAIN}:{item_index}" if is_domain else f"{CB_PERM_DOMAIN}:0",
        )
    )
    
    return builder.as_markup()


def dns_permission_keyboard() -> InlineKeyboardMarkup:
    """Step 1: Select DNS permissions for domain."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="View Only",
                    callback_data=f"{CB_PERM_DNS}:0:0",  # pdn:0:0
                )
            ],
            [
                InlineKeyboardButton(
                    text="View + Edit",
                    callback_data=f"{CB_PERM_DNS}:1:0",
                )
            ],
            [
                InlineKeyboardButton(
                    text="View + Edit + Delete",
                    callback_data=f"{CB_PERM_DNS}:1:1",
                )
            ],
            [
                InlineKeyboardButton(text="Cancel", callback_data=f"{CB_PERM_CANCEL_GRANT}:d")
            ],
        ]
    )


def subdomain_permission_keyboard() -> InlineKeyboardMarkup:
    """Step 2: Select subdomain management permissions for domain."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="View Only",
                    callback_data=f"{CB_PERM_SUB}:0:0",  # ps:0:0
                )
            ],
            [
                InlineKeyboardButton(
                    text="View + Create",
                    callback_data=f"{CB_PERM_SUB}:1:0",
                )
            ],
            [
                InlineKeyboardButton(
                    text="View + Create + Delete",
                    callback_data=f"{CB_PERM_SUB}:1:1",
                )
            ],
            [
                InlineKeyboardButton(text="Cancel", callback_data=f"{CB_PERM_CANCEL_GRANT}:d")
            ],
        ]
    )


def subdomain_item_dns_permission_keyboard() -> InlineKeyboardMarkup:
    """Select DNS permissions for a subdomain."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="View Only",
                    callback_data=f"{CB_PERM_SUBDNS}:0:0",  # psd:0:0
                )
            ],
            [
                InlineKeyboardButton(
                    text="View + Edit",
                    callback_data=f"{CB_PERM_SUBDNS}:1:0",
                )
            ],
            [
                InlineKeyboardButton(
                    text="View + Edit + Delete",
                    callback_data=f"{CB_PERM_SUBDNS}:1:1",
                )
            ],
            [
                InlineKeyboardButton(
                    text="Cancel", 
                    callback_data=f"{CB_PERM_CANCEL_GRANT}:s"
                )
            ],
        ]
    )


def subdomain_item_delete_permission_keyboard() -> InlineKeyboardMarkup:
    """Select delete permission for a subdomain."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="View Only (cannot delete)",
                    callback_data=f"{CB_PERM_SUBDEL}:0",  # psl:0
                )
            ],
            [
                InlineKeyboardButton(
                    text="Can Delete Subdomain",
                    callback_data=f"{CB_PERM_SUBDEL}:1",
                )
            ],
            [
                InlineKeyboardButton(
                    text="Cancel", 
                    callback_data=f"{CB_PERM_CANCEL_GRANT}:s"
                )
            ],
        ]
    )


def user_permission_action_keyboard(
    user_index: int,
    is_domain: bool,
) -> InlineKeyboardMarkup:
    """Actions for a user's permission on an item."""
    item_type = "d" if is_domain else "s"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Revoke Access",
                    callback_data=f"{CB_PERM_REVOKE}:{item_type}:{user_index}",  # pr:d:0
                )
            ],
            [
                InlineKeyboardButton(
                    text="Back",
                    callback_data=f"{CB_PERM_ITEM}:{item_type}:0",  # Back to item users
                )
            ],
        ]
    )


def users_list_keyboard(chats: list[AllowedChat]) -> InlineKeyboardMarkup:
    """List of users for viewing permissions."""
    builder = InlineKeyboardBuilder()
    
    for chat in chats:
        note = f" ({chat.note})" if chat.note else ""
        builder.row(
            InlineKeyboardButton(
                text=f"{chat.chat_id}{note}",
                callback_data=f"{CB_PERM_VIEWUSER}:{chat.chat_id}",  # pvu:123
            )
        )
    
    builder.row(
        InlineKeyboardButton(text="Back", callback_data="ap")  # admin permissions
    )
    return builder.as_markup()


def user_permissions_detail_keyboard() -> InlineKeyboardMarkup:
    """Back button for user permissions detail view."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Back", callback_data=CB_PERM_USERS)
            ]
        ]
    )


def grant_cancel_keyboard(is_domain: bool) -> InlineKeyboardMarkup:
    """Cancel button for grant access flow."""
    item_type = "d" if is_domain else "s"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Cancel",
                    callback_data=f"{CB_PERM_CANCEL_GRANT}:{item_type}",  # pcg:d
                )
            ]
        ]
    )


def confirm_revoke_keyboard(
    user_index: int,
    is_domain: bool,
) -> InlineKeyboardMarkup:
    """Confirm revoke access."""
    item_type = "d" if is_domain else "s"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Yes, Revoke",
                    callback_data=f"{CB_PERM_DO_REVOKE}:{item_type}:{user_index}",  # pdr:d:0
                ),
                InlineKeyboardButton(
                    text="Cancel",
                    callback_data=f"{CB_PERM_ITEM}:{item_type}:0",
                ),
            ]
        ]
    )
