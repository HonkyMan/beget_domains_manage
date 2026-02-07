"""Permission management handlers with optimized callback_data."""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from app.core.container import DependencyContainer
from app.core.state_helpers import StateContext
from app.services.beget import DomainsService
from app.bot.callback_data import (
    CB_PERM_DOMAINS, CB_PERM_DOMAIN, CB_PERM_ITEM,
    CB_PERM_GRANT, CB_PERM_CANCEL_GRANT, CB_PERM_USER,
    CB_PERM_REVOKE, CB_PERM_DO_REVOKE, CB_PERM_DNS,
    CB_PERM_SUB, CB_PERM_SUBDNS, CB_PERM_SUBDEL,
    CB_PERM_USERS, CB_PERM_VIEWUSER,
)
from app.modules.admin.states import PermissionStates
from app.modules.admin.permissions.keyboards import (
    permissions_menu_keyboard,
    domains_for_permissions_keyboard,
    domain_items_keyboard,
    item_users_keyboard,
    dns_permission_keyboard,
    subdomain_permission_keyboard,
    subdomain_item_dns_permission_keyboard,
    subdomain_item_delete_permission_keyboard,
    user_permission_action_keyboard,
    users_list_keyboard,
    user_permissions_detail_keyboard,
    grant_cancel_keyboard,
    confirm_revoke_keyboard,
)

router = Router(name="admin_permissions")


# ============ MENU ============


@router.callback_query(F.data == "ap")
async def show_permissions_menu(callback: CallbackQuery, state: FSMContext) -> None:
    """Show permissions management menu."""
    await state.clear()
    await callback.message.edit_text(
        "Permission Management\n\nSelect an option:",
        reply_markup=permissions_menu_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == CB_PERM_DOMAINS)
async def show_domains_for_permissions(
    callback: CallbackQuery,
    state: FSMContext,
    container: DependencyContainer,
) -> None:
    """Show list of domains for permission management."""
    try:
        async with container.beget_manager.client() as client:
            domains_service = DomainsService(client)
            domains = await domains_service.get_domains()
    except Exception as e:
        await callback.answer(f"Error: {e}", show_alert=True)
        return

    if not domains:
        await callback.answer("No domains found.", show_alert=True)
        return

    # Store domains in state for index-based access
    ctx = StateContext(state)
    await ctx.set_perm_domains([(d.id, d.fqdn) for d in domains])

    await callback.message.edit_text(
        "Select a domain to manage permissions:",
        reply_markup=domains_for_permissions_keyboard(domains),
    )
    await callback.answer()


@router.callback_query(F.data.startswith(f"{CB_PERM_DOMAIN}:"))
async def show_domain_items(
    callback: CallbackQuery, 
    state: FSMContext,
    container: DependencyContainer,
) -> None:
    """Show domain and its subdomains for permission assignment (pdo:index)."""
    domain_index = int(callback.data.split(":")[1])
    ctx = StateContext(state)
    
    domain_data = await ctx.get_perm_domain(domain_index)
    if not domain_data:
        await callback.answer("Domain not found", show_alert=True)
        return
    
    domain_id, domain_fqdn = domain_data
    
    # Store current domain for later use
    await ctx.set_current_perm_domain(domain_index, domain_fqdn)

    try:
        async with container.beget_manager.client() as client:
            domains_service = DomainsService(client)
            subdomains = await domains_service.get_subdomains(domain_id)
    except Exception as e:
        await callback.answer(f"Error: {e}", show_alert=True)
        return

    # Store subdomains in state
    await ctx.set_perm_subdomains([(s.id, s.fqdn) for s in subdomains])

    await callback.message.edit_text(
        f"Domain: {domain_fqdn}\n\n"
        "Select an item to manage access:",
        reply_markup=domain_items_keyboard(domain_index, subdomains),
    )
    await callback.answer()


# ============ ITEM USERS ============


@router.callback_query(F.data.startswith(f"{CB_PERM_ITEM}:"))
async def show_item_users(
    callback: CallbackQuery, 
    state: FSMContext,
    container: DependencyContainer,
) -> None:
    """Show users with access to a domain or subdomain (pi:d:index or pi:s:index)."""
    parts = callback.data.split(":")
    item_type = parts[1]  # 'd' for domain, 's' for subdomain
    item_index = int(parts[2])
    is_domain = item_type == "d"
    
    ctx = StateContext(state)
    
    if is_domain:
        domain_idx, item_fqdn = await ctx.get_current_perm_domain()
    else:
        sub_data = await ctx.get_perm_subdomain(item_index)
        if not sub_data:
            await callback.answer("Subdomain not found", show_alert=True)
            return
        _, item_fqdn = sub_data
        # Store subdomain context
        await ctx.set_perm_item(item_fqdn, False)

    if is_domain:
        users = await container.permissions_repo.get_domain_users(item_fqdn)
    else:
        users = await container.permissions_repo.get_subdomain_users(item_fqdn)

    # Store users in state for index-based access
    await ctx.set_perm_users([(u.chat_id, item_fqdn) for u in users])
    await ctx.set_perm_item(item_fqdn, is_domain)

    # Fetch chat notes for display
    chats = await container.chats_repo.get_all()
    chat_notes = {chat.chat_id: chat.note for chat in chats}

    item_label = "Domain" if is_domain else "Subdomain"
    text = f"{item_label}: {item_fqdn}\n\n"
    
    if users:
        text += "Users with access:\n"
        if is_domain:
            text += "(E=Edit DNS, D=Delete DNS, C=Create Sub, X=Delete Sub)\n\n"
        else:
            text += "(E=Edit DNS, D=Delete DNS, X=Delete Subdomain)\n\n"
    else:
        text += "No users have access yet.\n"

    domain_idx, _ = await ctx.get_current_perm_domain()
    await callback.message.edit_text(
        text,
        reply_markup=item_users_keyboard(domain_idx, is_domain, users, chat_notes),
    )
    await callback.answer()


# ============ GRANT ACCESS - DOMAIN ============


@router.callback_query(F.data.startswith(f"{CB_PERM_GRANT}:"))
async def start_grant_access(
    callback: CallbackQuery, 
    state: FSMContext,
) -> None:
    """Start granting access to a user (pg:d or pg:s)."""
    parts = callback.data.split(":")
    item_type = parts[1]
    is_domain = item_type == "d"
    
    ctx = StateContext(state)
    item_fqdn, _ = await ctx.get_perm_item()
    
    await state.update_data(
        grant_item_fqdn=item_fqdn,
        grant_is_domain=is_domain,
    )

    if is_domain:
        await state.set_state(PermissionStates.waiting_domain_chat_id)
    else:
        await state.set_state(PermissionStates.waiting_subdomain_chat_id)

    await callback.message.edit_text(
        f"Grant access to {'domain' if is_domain else 'subdomain'}: {item_fqdn}\n\n"
        "Enter the Chat ID of the user to grant access to:\n\n"
        "(User must be in the Allowed Chats list)",
        reply_markup=grant_cancel_keyboard(is_domain),
    )
    await callback.answer()


@router.callback_query(F.data.startswith(f"{CB_PERM_CANCEL_GRANT}:"))
async def cancel_grant_access(
    callback: CallbackQuery, 
    state: FSMContext,
    container: DependencyContainer,
) -> None:
    """Cancel grant access and return to item users view (pcg:d or pcg:s)."""
    parts = callback.data.split(":")
    item_type = parts[1]
    is_domain = item_type == "d"
    
    ctx = StateContext(state)
    item_fqdn, _ = await ctx.get_perm_item()

    await state.set_state(None)

    # Fetch users and render item users view directly
    if is_domain:
        users = await container.permissions_repo.get_domain_users(item_fqdn)
    else:
        users = await container.permissions_repo.get_subdomain_users(item_fqdn)

    await ctx.set_perm_users([(u.chat_id, item_fqdn) for u in users])

    chats = await container.chats_repo.get_all()
    chat_notes = {chat.chat_id: chat.note for chat in chats}

    item_label = "Domain" if is_domain else "Subdomain"
    text = f"{item_label}: {item_fqdn}\n\n"
    
    if users:
        text += "Users with access:\n"
        if is_domain:
            text += "(E=Edit DNS, D=Delete DNS, C=Create Sub, X=Delete Sub)\n\n"
        else:
            text += "(E=Edit DNS, D=Delete DNS, X=Delete Subdomain)\n\n"
    else:
        text += "No users have access yet.\n"

    domain_idx, _ = await ctx.get_current_perm_domain()
    await callback.message.edit_text(
        text,
        reply_markup=item_users_keyboard(domain_idx, is_domain, users, chat_notes),
    )
    await callback.answer()


@router.message(PermissionStates.waiting_domain_chat_id)
async def receive_domain_grant_chat_id(
    message: Message, 
    state: FSMContext,
    container: DependencyContainer,
) -> None:
    """Receive chat ID for domain grant."""
    try:
        chat_id = int(message.text.strip())
    except ValueError:
        await message.answer("Invalid Chat ID. Please enter a number:")
        return

    # Verify user is in allowed chats
    if not await container.chats_repo.is_allowed(chat_id):
        await message.answer(
            f"Chat ID {chat_id} is not in the Allowed Chats list.\n"
            "Please add them first, then try again."
        )
        return

    data = await state.get_data()
    item_fqdn = data["grant_item_fqdn"]

    await state.update_data(grant_chat_id=chat_id)
    await state.set_state(PermissionStates.waiting_domain_dns_permissions)

    await message.answer(
        f"Granting access to {item_fqdn} for Chat {chat_id}\n\n"
        "Step 1/2: Select DNS permissions:",
        reply_markup=dns_permission_keyboard(),
    )


@router.callback_query(F.data.startswith(f"{CB_PERM_DNS}:"))
async def receive_domain_dns_permissions(
    callback: CallbackQuery, 
    state: FSMContext,
) -> None:
    """Step 1: Receive DNS permissions for domain grant (pdn:edit:delete)."""
    parts = callback.data.split(":")
    can_edit_dns = parts[1] == "1"
    can_delete_dns = parts[2] == "1"

    await state.update_data(
        grant_can_edit_dns=can_edit_dns,
        grant_can_delete_dns=can_delete_dns,
    )
    await state.set_state(PermissionStates.waiting_domain_subdomain_permissions)

    data = await state.get_data()
    item_fqdn = data["grant_item_fqdn"]

    await callback.message.edit_text(
        f"Step 2/2: Select subdomain management permissions for {item_fqdn}:",
        reply_markup=subdomain_permission_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith(f"{CB_PERM_SUB}:"))
async def receive_domain_subdomain_permissions(
    callback: CallbackQuery, 
    state: FSMContext,
    container: DependencyContainer,
) -> None:
    """Step 2: Receive subdomain permissions and complete domain grant (ps:create:delete)."""
    parts = callback.data.split(":")
    can_create = parts[1] == "1"
    can_delete = parts[2] == "1"

    data = await state.get_data()
    item_fqdn = data["grant_item_fqdn"]
    chat_id = data["grant_chat_id"]
    can_edit_dns = data.get("grant_can_edit_dns", False)
    can_delete_dns = data.get("grant_can_delete_dns", False)

    # Get admin username for granted_by
    granted_by = f"@{callback.from_user.username or callback.from_user.id}"

    success = await container.permissions_repo.grant_domain_access(
        chat_id=chat_id,
        domain_fqdn=item_fqdn,
        can_edit_dns=can_edit_dns,
        can_delete_dns=can_delete_dns,
        can_create=can_create,
        can_delete=can_delete,
        granted_by=granted_by,
    )

    if success:
        perms = []
        if can_edit_dns:
            perms.append("Edit DNS")
        if can_delete_dns:
            perms.append("Delete DNS")
        if can_create:
            perms.append("Create Sub")
        if can_delete:
            perms.append("Delete Sub")
        perm_label = ", ".join(perms) if perms else "View Only"
        await callback.answer(
            f"Access granted! Chat {chat_id} now has [{perm_label}] access",
            show_alert=True,
        )
    else:
        await callback.answer("Error granting access.", show_alert=True)

    await state.set_state(None)

    # Get users for the updated view
    users = await container.permissions_repo.get_domain_users(item_fqdn)
    ctx = StateContext(state)
    await ctx.set_perm_users([(u.chat_id, item_fqdn) for u in users])

    # Fetch chat notes for display
    chats = await container.chats_repo.get_all()
    chat_notes = {chat.chat_id: chat.note for chat in chats}

    # Update the current message to show item users view
    text = f"Domain: {item_fqdn}\n\n"
    if users:
        text += "Users with access:\n"
        text += "(E=Edit DNS, D=Delete DNS, C=Create Sub, X=Delete Sub)\n\n"
    else:
        text += "No users have access yet.\n"

    domain_idx, _ = await ctx.get_current_perm_domain()
    await callback.message.edit_text(
        text,
        reply_markup=item_users_keyboard(domain_idx, True, users, chat_notes),
    )


# ============ GRANT ACCESS - SUBDOMAIN ============


@router.message(PermissionStates.waiting_subdomain_chat_id)
async def receive_subdomain_grant_chat_id(
    message: Message, 
    state: FSMContext,
    container: DependencyContainer,
) -> None:
    """Receive chat ID for subdomain grant."""
    try:
        chat_id = int(message.text.strip())
    except ValueError:
        await message.answer("Invalid Chat ID. Please enter a number:")
        return

    # Verify user is in allowed chats
    if not await container.chats_repo.is_allowed(chat_id):
        await message.answer(
            f"Chat ID {chat_id} is not in the Allowed Chats list.\n"
            "Please add them first, then try again."
        )
        return

    data = await state.get_data()
    item_fqdn = data["grant_item_fqdn"]

    await state.update_data(grant_chat_id=chat_id)
    await state.set_state(PermissionStates.waiting_subdomain_dns_permissions)

    await message.answer(
        f"Granting access to subdomain {item_fqdn} for Chat {chat_id}\n\n"
        "Step 1/2: Select DNS permissions:",
        reply_markup=subdomain_item_dns_permission_keyboard(),
    )


@router.callback_query(F.data.startswith(f"{CB_PERM_SUBDNS}:"))
async def receive_subdomain_dns_permissions(
    callback: CallbackQuery, 
    state: FSMContext,
) -> None:
    """Step 1: Receive DNS permissions for subdomain grant (psd:edit:delete)."""
    parts = callback.data.split(":")
    can_edit_dns = parts[1] == "1"
    can_delete_dns = parts[2] == "1"

    await state.update_data(
        grant_can_edit_dns=can_edit_dns,
        grant_can_delete_dns=can_delete_dns,
    )
    await state.set_state(PermissionStates.waiting_subdomain_delete_permission)

    data = await state.get_data()
    item_fqdn = data["grant_item_fqdn"]

    await callback.message.edit_text(
        f"Step 2/2: Can user delete the subdomain {item_fqdn}?",
        reply_markup=subdomain_item_delete_permission_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith(f"{CB_PERM_SUBDEL}:"))
async def receive_subdomain_delete_permission(
    callback: CallbackQuery, 
    state: FSMContext,
    container: DependencyContainer,
) -> None:
    """Step 2: Receive delete permission and complete subdomain grant (psl:can_delete)."""
    parts = callback.data.split(":")
    can_delete_subdomain = parts[1] == "1"

    data = await state.get_data()
    item_fqdn = data["grant_item_fqdn"]
    chat_id = data["grant_chat_id"]
    can_edit_dns = data.get("grant_can_edit_dns", False)
    can_delete_dns = data.get("grant_can_delete_dns", False)

    # Get admin username for granted_by
    granted_by = f"@{callback.from_user.username or callback.from_user.id}"

    success = await container.permissions_repo.grant_subdomain_access(
        chat_id=chat_id,
        subdomain_fqdn=item_fqdn,
        can_edit_dns=can_edit_dns,
        can_delete_dns=can_delete_dns,
        can_delete_subdomain=can_delete_subdomain,
        granted_by=granted_by,
    )

    if success:
        perms = []
        if can_edit_dns:
            perms.append("Edit DNS")
        if can_delete_dns:
            perms.append("Delete DNS")
        if can_delete_subdomain:
            perms.append("Delete Subdomain")
        perm_label = ", ".join(perms) if perms else "View Only"
        await callback.answer(
            f"Access granted! Chat {chat_id} now has [{perm_label}] access",
            show_alert=True,
        )
    else:
        await callback.answer("Error granting access.", show_alert=True)

    await state.set_state(None)

    # Get users for the updated view
    users = await container.permissions_repo.get_subdomain_users(item_fqdn)
    ctx = StateContext(state)
    await ctx.set_perm_users([(u.chat_id, item_fqdn) for u in users])

    # Fetch chat notes for display
    chats = await container.chats_repo.get_all()
    chat_notes = {chat.chat_id: chat.note for chat in chats}

    # Update the current message to show item users view
    text = f"Subdomain: {item_fqdn}\n\n"
    if users:
        text += "Users with access:\n"
        text += "(E=Edit DNS, D=Delete DNS, X=Delete Subdomain)\n\n"
    else:
        text += "No users have access yet.\n"

    domain_idx, _ = await ctx.get_current_perm_domain()
    await callback.message.edit_text(
        text,
        reply_markup=item_users_keyboard(domain_idx, False, users, chat_notes),
    )


# ============ USER ACTIONS ============


@router.callback_query(F.data.startswith(f"{CB_PERM_USER}:"))
async def show_user_permission_actions(
    callback: CallbackQuery, 
    state: FSMContext,
) -> None:
    """Show actions for a user's permission on an item (pu:d:index or pu:s:index)."""
    parts = callback.data.split(":")
    item_type = parts[1]
    user_index = int(parts[2])
    is_domain = item_type == "d"
    
    ctx = StateContext(state)
    user_data = await ctx.get_perm_user(user_index)
    if not user_data:
        await callback.answer("User not found", show_alert=True)
        return
    
    chat_id, item_fqdn = user_data

    await callback.message.edit_text(
        f"User Chat ID: {chat_id}\n"
        f"{'Domain' if is_domain else 'Subdomain'}: {item_fqdn}\n\n"
        "Select action:",
        reply_markup=user_permission_action_keyboard(user_index, is_domain),
    )
    await callback.answer()


@router.callback_query(F.data.startswith(f"{CB_PERM_REVOKE}:"))
async def confirm_revoke_access(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Confirm revoking access (pr:d:index or pr:s:index)."""
    parts = callback.data.split(":")
    item_type = parts[1]
    user_index = int(parts[2])
    is_domain = item_type == "d"
    
    ctx = StateContext(state)
    user_data = await ctx.get_perm_user(user_index)
    if not user_data:
        await callback.answer("User not found", show_alert=True)
        return
    
    chat_id, item_fqdn = user_data

    await callback.message.edit_text(
        f"Revoke access for Chat {chat_id} to {item_fqdn}?",
        reply_markup=confirm_revoke_keyboard(user_index, is_domain),
    )
    await callback.answer()


@router.callback_query(F.data.startswith(f"{CB_PERM_DO_REVOKE}:"))
async def do_revoke_access(
    callback: CallbackQuery, 
    state: FSMContext,
    container: DependencyContainer,
) -> None:
    """Execute revoking access (pdr:d:index or pdr:s:index)."""
    parts = callback.data.split(":")
    item_type = parts[1]
    user_index = int(parts[2])
    is_domain = item_type == "d"
    
    ctx = StateContext(state)
    user_data = await ctx.get_perm_user(user_index)
    if not user_data:
        await callback.answer("User not found", show_alert=True)
        return
    
    chat_id, item_fqdn = user_data

    if is_domain:
        success = await container.permissions_repo.revoke_domain_access(chat_id, item_fqdn)
    else:
        success = await container.permissions_repo.revoke_subdomain_access(chat_id, item_fqdn)

    if success:
        await callback.answer(f"Access revoked for Chat {chat_id}", show_alert=True)
    else:
        await callback.answer("Error revoking access.", show_alert=True)

    # Fetch updated users and render item users view directly
    if is_domain:
        users = await container.permissions_repo.get_domain_users(item_fqdn)
    else:
        users = await container.permissions_repo.get_subdomain_users(item_fqdn)

    await ctx.set_perm_users([(u.chat_id, item_fqdn) for u in users])

    chats = await container.chats_repo.get_all()
    chat_notes = {chat.chat_id: chat.note for chat in chats}

    item_label = "Domain" if is_domain else "Subdomain"
    text = f"{item_label}: {item_fqdn}\n\n"
    
    if users:
        text += "Users with access:\n"
        if is_domain:
            text += "(E=Edit DNS, D=Delete DNS, C=Create Sub, X=Delete Sub)\n\n"
        else:
            text += "(E=Edit DNS, D=Delete DNS, X=Delete Subdomain)\n\n"
    else:
        text += "No users have access yet.\n"

    domain_idx, _ = await ctx.get_current_perm_domain()
    await callback.message.edit_text(
        text,
        reply_markup=item_users_keyboard(domain_idx, is_domain, users, chat_notes),
    )


# ============ VIEW USER PERMISSIONS ============


@router.callback_query(F.data == CB_PERM_USERS)
async def show_users_list(
    callback: CallbackQuery,
    container: DependencyContainer,
) -> None:
    """Show list of users for viewing their permissions."""
    chats = await container.chats_repo.get_all()

    if not chats:
        await callback.answer("No users in the system.", show_alert=True)
        return

    await callback.message.edit_text(
        "Select a user to view their permissions:",
        reply_markup=users_list_keyboard(chats),
    )
    await callback.answer()


@router.callback_query(F.data.startswith(f"{CB_PERM_VIEWUSER}:"))
async def show_user_permissions_detail(
    callback: CallbackQuery,
    container: DependencyContainer,
) -> None:
    """Show detailed permissions for a user (pvu:chat_id)."""
    chat_id = int(callback.data.split(":")[1])

    domain_perms = await container.permissions_repo.get_user_domain_permissions(chat_id)
    subdomain_perms = await container.permissions_repo.get_user_subdomain_permissions(chat_id)
    created_subs = await container.permissions_repo.get_user_created_subdomains(chat_id)

    text = f"Permissions for Chat {chat_id}:\n\n"

    if domain_perms:
        text += "Domain Access:\n"
        for p in domain_perms:
            perms = []
            if p.can_edit_dns:
                perms.append("Edit DNS")
            if p.can_delete_dns:
                perms.append("Del DNS")
            if p.can_create_subdomain:
                perms.append("Create Sub")
            if p.can_delete_subdomain:
                perms.append("Del Sub")
            perm_str = f" [{', '.join(perms)}]" if perms else " [View Only]"
            text += f"  - {p.domain_fqdn}{perm_str}\n"
        text += "\n"

    if subdomain_perms:
        text += "Subdomain-Only Access:\n"
        for p in subdomain_perms:
            perms = []
            if p.can_edit_dns:
                perms.append("Edit DNS")
            if p.can_delete_dns:
                perms.append("Del DNS")
            if p.can_delete_subdomain:
                perms.append("Del Sub")
            perm_str = f" [{', '.join(perms)}]" if perms else " [View Only]"
            text += f"  - {p.subdomain_fqdn}{perm_str}\n"
        text += "\n"

    if created_subs:
        text += "Created Subdomains:\n"
        for s in created_subs:
            text += f"  - {s}\n"
        text += "\n"

    if not domain_perms and not subdomain_perms and not created_subs:
        text += "No permissions assigned."

    await callback.message.edit_text(
        text,
        reply_markup=user_permissions_detail_keyboard(),
    )
    await callback.answer()
