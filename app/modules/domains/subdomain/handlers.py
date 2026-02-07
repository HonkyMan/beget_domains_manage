"""Subdomain management handlers with optimized callback_data."""

import re
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from app.core.container import DependencyContainer
from app.core.state_helpers import StateContext
from app.services.beget import DomainsService
from app.modules.domains.states import SubdomainStates
from app.modules.domains.subdomain.keyboards import (
    subdomains_list_keyboard,
    subdomain_actions_keyboard,
    confirm_keyboard,
    cancel_keyboard,
)

router = Router(name="domains_subdomain")


@router.callback_query(F.data.startswith("ss:"))
async def show_subdomains(
    callback: CallbackQuery,
    state: FSMContext,
    container: DependencyContainer,
    user_chat_id: int,
) -> None:
    """Show subdomains for a domain. Callback: ss:{domain_id}"""
    domain_id = int(callback.data.split(":")[1])
    
    # Get FQDN from state
    ctx = StateContext(state)
    stored_id, fqdn = await ctx.get_domain()
    
    if stored_id != domain_id or not fqdn:
        # Fetch from API
        try:
            async with container.beget_manager.client() as client:
                domains_service = DomainsService(client)
                domains = await domains_service.get_domains()
                for d in domains:
                    if d.id == domain_id:
                        fqdn = d.fqdn
                        await ctx.set_domain(domain_id, fqdn)
                        break
        except Exception as e:
            await callback.answer(f"Error: {e}", show_alert=True)
            return

    try:
        async with container.beget_manager.client() as client:
            domains_service = DomainsService(client)
            all_subdomains = await domains_service.get_subdomains(domain_id)
    except Exception as e:
        await callback.answer(f"Error: {e}", show_alert=True)
        return

    # Filter and check permissions
    subdomains = await container.permission_checker.filter_subdomains(
        user_chat_id, fqdn, all_subdomains
    )
    can_create = await container.permission_checker.can_create_subdomain(user_chat_id, fqdn)

    # Store subdomain map for ID lookup
    subdomain_map = {s.id: s.fqdn for s in subdomains}
    await state.update_data(subdomain_map=subdomain_map)

    text = f"Subdomains of {fqdn}:\n\n"
    if subdomains:
        for sub in subdomains:
            text += f"- {sub.fqdn}\n"
    else:
        text += "No subdomains yet."

    await callback.message.edit_text(
        text,
        reply_markup=subdomains_list_keyboard(subdomains, domain_id, can_create),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("s:") & ~F.data.startswith("ss:") & ~F.data.startswith("sdn:"))
async def show_subdomain_actions(
    callback: CallbackQuery,
    state: FSMContext,
    container: DependencyContainer,
    user_chat_id: int,
) -> None:
    """Show actions for a subdomain. Callback: s:{subdomain_id}"""
    subdomain_id = int(callback.data.split(":")[1])
    
    # Get FQDN from state map
    data = await state.get_data()
    subdomain_map = data.get("subdomain_map", {})
    fqdn = subdomain_map.get(subdomain_id, "")
    
    if not fqdn:
        await callback.answer("Subdomain not found", show_alert=True)
        return

    # Check access
    if not await container.permission_checker.can_view_subdomain(user_chat_id, fqdn):
        await callback.answer("You don't have access to this subdomain.", show_alert=True)
        return

    # Get parent domain info
    ctx = StateContext(state)
    parent_domain_id, parent_fqdn = await ctx.get_domain()
    
    if not parent_fqdn and "." in fqdn:
        parent_fqdn = fqdn.split(".", 1)[1]

    # Store subdomain context
    await ctx.set_subdomain(subdomain_id, fqdn, parent_domain_id, parent_fqdn)

    # Check permissions
    can_delete = await container.permission_checker.can_delete_subdomain(user_chat_id, fqdn)
    can_dns = await container.permission_checker.can_manage_dns(user_chat_id, fqdn)

    await callback.message.edit_text(
        f"Subdomain: {fqdn}\n\nSelect action:",
        reply_markup=subdomain_actions_keyboard(
            subdomain_id, parent_domain_id,
            can_delete=can_delete, can_dns=can_dns,
        ),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("as:"))
async def start_add_subdomain(
    callback: CallbackQuery,
    state: FSMContext,
    container: DependencyContainer,
    user_chat_id: int,
) -> None:
    """Start adding a subdomain. Callback: as:{domain_id}"""
    domain_id = int(callback.data.split(":")[1])
    
    ctx = StateContext(state)
    _, fqdn = await ctx.get_domain()

    if not await container.permission_checker.can_create_subdomain(user_chat_id, fqdn):
        await callback.answer("You don't have permission to create subdomains.", show_alert=True)
        return

    await state.update_data(
        domain_id=domain_id,
        parent_fqdn=fqdn,
        creator_chat_id=user_chat_id,
    )
    await state.set_state(SubdomainStates.waiting_subdomain_name)

    await callback.message.edit_text(
        f"Creating subdomain for {fqdn}\n\n"
        "Enter subdomain name (without the domain part):\n"
        "Example: 'api' for api.example.com",
        reply_markup=cancel_keyboard(f"ss:{domain_id}"),
    )
    await callback.answer()


@router.message(SubdomainStates.waiting_subdomain_name)
async def receive_subdomain_name(message: Message, state: FSMContext) -> None:
    """Receive subdomain name."""
    subdomain_name = message.text.strip().lower()

    if not subdomain_name:
        await message.answer("Subdomain name cannot be empty. Please enter a valid name:")
        return
    
    if " " in subdomain_name:
        await message.answer("Subdomain name cannot contain spaces. Please enter a valid name:")
        return
    
    if not re.match(r'^[a-z0-9]([a-z0-9-]*[a-z0-9])?$', subdomain_name):
        await message.answer(
            "Invalid subdomain name.\n\n"
            "Allowed: lowercase letters (a-z), numbers (0-9), hyphens (-)\n"
            "Not allowed: Cyrillic, special characters, spaces\n\n"
            "Please enter a valid subdomain name:"
        )
        return

    data = await state.get_data()
    fqdn = data["parent_fqdn"]
    domain_id = data["domain_id"]
    full_subdomain = f"{subdomain_name}.{fqdn}"

    await state.update_data(subdomain_name=subdomain_name, full_subdomain=full_subdomain)
    await state.set_state(SubdomainStates.confirm_create_subdomain)

    await message.answer(
        f"Create subdomain: {full_subdomain}?",
        reply_markup=confirm_keyboard(f"cs:{subdomain_name}", f"ss:{domain_id}"),
    )


@router.callback_query(F.data.startswith("cs:"))
async def confirm_create_subdomain(
    callback: CallbackQuery,
    state: FSMContext,
    container: DependencyContainer,
) -> None:
    """Confirm and create subdomain. Callback: cs:{name}"""
    data = await state.get_data()
    domain_id = data["domain_id"]
    subdomain_name = data["subdomain_name"]
    fqdn = data["parent_fqdn"]
    creator_chat_id = data.get("creator_chat_id")
    full_subdomain = f"{subdomain_name}.{fqdn}"

    try:
        async with container.beget_manager.client() as client:
            domains_service = DomainsService(client)
            await domains_service.add_subdomain(domain_id, subdomain_name)
            subdomains = await domains_service.get_subdomains(domain_id)
        
        if creator_chat_id:
            await container.permissions_repo.record_subdomain_creation(
                full_subdomain, creator_chat_id
            )
        
        await callback.message.delete()
        await callback.answer(f"Subdomain {full_subdomain} created!", show_alert=True)
        
        # Update subdomain map
        subdomain_map = {s.id: s.fqdn for s in subdomains}
        await state.update_data(subdomain_map=subdomain_map)
        
        text = f"Subdomains of {fqdn}:\n\n"
        for sub in subdomains:
            text += f"- {sub.fqdn}\n"
        
        await callback.message.answer(
            text,
            reply_markup=subdomains_list_keyboard(subdomains, domain_id, can_create=True),
        )
    except Exception as e:
        await callback.answer(f"Error: {e}", show_alert=True)

    await state.set_state(None)


@router.callback_query(F.data.startswith("ds:"))
async def confirm_delete_subdomain(
    callback: CallbackQuery,
    state: FSMContext,
    container: DependencyContainer,
    user_chat_id: int,
) -> None:
    """Confirm subdomain deletion. Callback: ds:{subdomain_id}"""
    subdomain_id = int(callback.data.split(":")[1])
    
    ctx = StateContext(state)
    _, fqdn, parent_domain_id, _ = await ctx.get_subdomain()

    if not await container.permission_checker.can_delete_subdomain(user_chat_id, fqdn):
        await callback.answer("You don't have permission to delete this subdomain.", show_alert=True)
        return

    await callback.message.edit_text(
        f"Delete subdomain: {fqdn}?\n\nThis action cannot be undone!",
        reply_markup=confirm_keyboard(f"dds:{subdomain_id}", f"ss:{parent_domain_id}"),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("dds:"))
async def do_delete_subdomain(
    callback: CallbackQuery,
    state: FSMContext,
    container: DependencyContainer,
    user_chat_id: int,
) -> None:
    """Delete subdomain. Callback: dds:{subdomain_id}"""
    subdomain_id = int(callback.data.split(":")[1])
    
    ctx = StateContext(state)
    _, subdomain_fqdn, parent_domain_id, parent_fqdn = await ctx.get_subdomain()

    if not await container.permission_checker.can_delete_subdomain(user_chat_id, subdomain_fqdn):
        await callback.answer("You don't have permission.", show_alert=True)
        return

    try:
        async with container.beget_manager.client() as client:
            domains_service = DomainsService(client)
            await domains_service.delete_subdomain(subdomain_id)
            subdomains = await domains_service.get_subdomains(parent_domain_id)
        
        await container.permissions_repo.delete_subdomain_record(subdomain_fqdn)
        
        await callback.message.delete()
        await callback.answer("Subdomain deleted!", show_alert=True)
        
        can_create = await container.permission_checker.can_create_subdomain(user_chat_id, parent_fqdn)
        
        text = f"Subdomains of {parent_fqdn}:\n\n"
        if subdomains:
            for sub in subdomains:
                text += f"- {sub.fqdn}\n"
        else:
            text += "No subdomains yet."
        
        await callback.message.answer(
            text,
            reply_markup=subdomains_list_keyboard(subdomains, parent_domain_id, can_create),
        )
    except Exception as e:
        await callback.answer(f"Error: {e}", show_alert=True)

    await ctx.clear_context()
