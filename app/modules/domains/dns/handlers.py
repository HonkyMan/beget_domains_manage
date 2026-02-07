"""DNS management handlers with optimized callback_data."""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from app.core.container import DependencyContainer
from app.core.state_helpers import StateContext
from app.services.beget import DnsService
from app.modules.domains.states import DnsStates
from app.modules.domains.dns.keyboards import (
    dns_menu_keyboard,
    a_records_keyboard,
    txt_records_keyboard,
    edit_a_record_keyboard,
    confirm_keyboard,
    cancel_keyboard,
)

router = Router(name="domains_dns")


# ============ DNS MENU ENTRY ============


@router.callback_query(F.data.startswith("sdn:"))
async def show_subdomain_dns_menu(
    callback: CallbackQuery,
    state: FSMContext,
    container: DependencyContainer,
    user_chat_id: int,
) -> None:
    """Show DNS management menu for a subdomain (sdn:subdomain_id)."""
    ctx = StateContext(state)
    subdomain_id, subdomain_fqdn, parent_id, parent_fqdn = await ctx.get_subdomain()
    
    if not subdomain_fqdn:
        await callback.answer("Subdomain data not found", show_alert=True)
        return
    
    # Check DNS permission
    if not await container.permission_checker.can_manage_dns(user_chat_id, subdomain_fqdn):
        await callback.answer("No permission to manage DNS", show_alert=True)
        return
    
    # Store DNS context
    await ctx.set_dns(subdomain_fqdn, back_callback=f"s:{subdomain_id}")
    
    await callback.message.edit_text(
        f"DNS Management for {subdomain_fqdn}\n\nSelect an option:",
        reply_markup=dns_menu_keyboard(subdomain_id, back_callback=f"s:{subdomain_id}"),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("dn:"))
async def show_dns_menu(
    callback: CallbackQuery,
    state: FSMContext,
    container: DependencyContainer,
    user_chat_id: int,
) -> None:
    """Show DNS management menu (dn:domain_id)."""
    domain_id = int(callback.data.split(":")[1])
    ctx = StateContext(state)
    
    # Get FQDN from state
    stored_id, fqdn = await ctx.get_domain()
    if stored_id != domain_id or not fqdn:
        # Try to get from subdomain context
        sub_id, sub_fqdn, parent_id, parent_fqdn = await ctx.get_subdomain()
        if sub_id == domain_id:
            fqdn = sub_fqdn
        elif parent_id == domain_id:
            fqdn = parent_fqdn
    
    if not fqdn:
        await callback.answer("Domain data not found", show_alert=True)
        return
    
    # Check DNS permission
    if not await container.permission_checker.can_manage_dns(user_chat_id, fqdn):
        await callback.answer("No permission to manage DNS", show_alert=True)
        return
    
    # Store DNS context
    await ctx.set_dns(fqdn, back_callback=f"d:{domain_id}")

    await callback.message.edit_text(
        f"DNS Management for {fqdn}\n\nSelect an option:",
        reply_markup=dns_menu_keyboard(domain_id),
    )
    await callback.answer()


# ============ VIEW ALL RECORDS ============


@router.callback_query(F.data.startswith("dnv:"))
async def view_dns_records(
    callback: CallbackQuery,
    state: FSMContext,
    container: DependencyContainer,
) -> None:
    """View all DNS records (dnv:domain_id)."""
    domain_id = int(callback.data.split(":")[1])
    ctx = StateContext(state)
    fqdn, _ = await ctx.get_dns()
    
    if not fqdn:
        await callback.answer("Domain data not found", show_alert=True)
        return

    try:
        async with container.beget_manager.client() as client:
            dns_service = DnsService(client)
            dns_data = await dns_service.get_dns_data(fqdn)
    except Exception as e:
        await callback.answer(f"Error: {e}", show_alert=True)
        return

    text = f"DNS Records for {fqdn}:\n\n"

    if dns_data.a:
        text += "A Records:\n"
        for r in dns_data.a:
            text += f"  {r.value}\n"
        text += "\n"

    if dns_data.aaaa:
        text += "AAAA Records:\n"
        for r in dns_data.aaaa:
            text += f"  {r.value}\n"
        text += "\n"

    if dns_data.mx:
        text += "MX Records:\n"
        for r in dns_data.mx:
            text += f"  {r.value} (priority: {r.priority})\n"
        text += "\n"

    if dns_data.txt:
        text += "TXT Records:\n"
        for r in dns_data.txt:
            display = r.value[:50] + "..." if len(r.value) > 50 else r.value
            text += f"  {display}\n"
        text += "\n"

    if dns_data.cname:
        text += "CNAME Records:\n"
        for r in dns_data.cname:
            text += f"  {r.value}\n"
        text += "\n"

    if dns_data.ns:
        text += "NS Records:\n"
        for r in dns_data.ns:
            text += f"  {r.value}\n"

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Back", callback_data=f"dn:{domain_id}")]
            ]
        ),
    )
    await callback.answer()


# ============ A RECORDS ============


@router.callback_query(F.data.startswith("dna:"))
async def show_a_records(
    callback: CallbackQuery,
    state: FSMContext,
    container: DependencyContainer,
) -> None:
    """Show A records management (dna:domain_id)."""
    domain_id = int(callback.data.split(":")[1])
    ctx = StateContext(state)
    fqdn, _ = await ctx.get_dns()
    
    if not fqdn:
        await callback.answer("Domain data not found", show_alert=True)
        return

    try:
        async with container.beget_manager.client() as client:
            dns_service = DnsService(client)
            dns_data = await dns_service.get_dns_data(fqdn)
    except Exception as e:
        await callback.answer(f"Error: {e}", show_alert=True)
        return

    # Store A records in state for index-based access
    await ctx.set_dns_records(
        a_records=[r.value for r in dns_data.a],
        txt_records=[],
    )

    text = f"A Records for {fqdn}:\n\n"
    if dns_data.a:
        for r in dns_data.a:
            text += f"- {r.value}\n"
    else:
        text += "No A records."

    await callback.message.edit_text(
        text,
        reply_markup=a_records_keyboard(domain_id, dns_data.a),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("ea:"))
async def edit_a_record(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Show edit options for A record (ea:domain_id:index)."""
    parts = callback.data.split(":")
    domain_id = int(parts[1])
    index = int(parts[2])
    
    ctx = StateContext(state)
    ip = await ctx.get_a_record(index)
    
    if ip is None:
        await callback.answer("Record not found", show_alert=True)
        return

    await callback.message.edit_text(
        f"A Record: {ip}\n\nSelect action:",
        reply_markup=edit_a_record_keyboard(domain_id, index),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("aa:"))
async def start_add_a_record(
    callback: CallbackQuery,
    state: FSMContext,
    container: DependencyContainer,
    user_chat_id: int,
) -> None:
    """Start adding A record (aa:domain_id)."""
    domain_id = int(callback.data.split(":")[1])
    ctx = StateContext(state)
    fqdn, _ = await ctx.get_dns()
    
    if not fqdn:
        await callback.answer("Domain data not found", show_alert=True)
        return

    # Check edit DNS permission
    if not await container.permission_checker.can_edit_dns(user_chat_id, fqdn):
        await callback.answer("No permission to add DNS records", show_alert=True)
        return

    await state.update_data(dns_domain_id=domain_id)
    await state.set_state(DnsStates.waiting_a_record_ip)

    await callback.message.edit_text(
        f"Enter IP address for new A record on {fqdn}:",
        reply_markup=cancel_keyboard(f"dna:{domain_id}"),
    )
    await callback.answer()


@router.message(DnsStates.waiting_a_record_ip)
async def receive_new_a_ip(
    message: Message, 
    state: FSMContext,
    container: DependencyContainer,
) -> None:
    """Receive IP for new A record."""
    import logging
    logger = logging.getLogger(__name__)
    
    ip = message.text.strip()
    ctx = StateContext(state)
    fqdn, _ = await ctx.get_dns()

    # Basic IP validation
    parts = ip.split(".")
    if len(parts) != 4 or not all(p.isdigit() and 0 <= int(p) <= 255 for p in parts):
        await message.answer("Invalid IP address. Please enter a valid IPv4:")
        return

    try:
        async with container.beget_manager.client() as client:
            dns_service = DnsService(client)
            await dns_service.add_a_record(fqdn, ip)
        await message.answer(f"A record {ip} added to {fqdn}!")
    except Exception as e:
        logger.error(f"Error adding A record: {type(e).__name__}: {e}", exc_info=True)
        error_msg = str(e) if str(e) else f"{type(e).__name__}: Unknown error"
        await message.answer(f"Error: {error_msg}")

    await state.clear()


@router.callback_query(F.data.startswith("ca:"))
async def start_change_a_record(
    callback: CallbackQuery,
    state: FSMContext,
    container: DependencyContainer,
    user_chat_id: int,
) -> None:
    """Start changing A record IP (ca:domain_id:index)."""
    parts = callback.data.split(":")
    domain_id = int(parts[1])
    index = int(parts[2])
    
    ctx = StateContext(state)
    fqdn, _ = await ctx.get_dns()
    old_ip = await ctx.get_a_record(index)
    
    if not fqdn or old_ip is None:
        await callback.answer("Record not found", show_alert=True)
        return

    # Check edit DNS permission
    if not await container.permission_checker.can_edit_dns(user_chat_id, fqdn):
        await callback.answer("No permission to edit DNS records", show_alert=True)
        return

    await state.update_data(
        dns_domain_id=domain_id,
        dns_old_ip=old_ip,
        dns_record_index=index,
    )
    await state.set_state(DnsStates.waiting_new_a_ip)

    await callback.message.edit_text(
        f"Current IP: {old_ip}\n\nEnter new IP address:",
        reply_markup=cancel_keyboard(f"ea:{domain_id}:{index}"),
    )
    await callback.answer()


@router.message(DnsStates.waiting_new_a_ip)
async def receive_changed_a_ip(
    message: Message, 
    state: FSMContext,
    container: DependencyContainer,
) -> None:
    """Receive new IP for A record."""
    new_ip = message.text.strip()
    ctx = StateContext(state)
    fqdn, _ = await ctx.get_dns()
    data = await state.get_data()
    old_ip = data.get("dns_old_ip", "")

    # Basic IP validation
    parts = new_ip.split(".")
    if len(parts) != 4 or not all(p.isdigit() and 0 <= int(p) <= 255 for p in parts):
        await message.answer("Invalid IP address. Please enter a valid IPv4:")
        return

    try:
        async with container.beget_manager.client() as client:
            dns_service = DnsService(client)
            await dns_service.update_a_record(fqdn, old_ip, new_ip)
        await message.answer(f"A record updated: {old_ip} -> {new_ip}")
    except Exception as e:
        await message.answer(f"Error: {e}")

    await state.clear()


@router.callback_query(F.data.startswith("da:"))
async def confirm_delete_a(
    callback: CallbackQuery,
    state: FSMContext,
    container: DependencyContainer,
    user_chat_id: int,
) -> None:
    """Confirm A record deletion (da:domain_id:index)."""
    parts = callback.data.split(":")
    domain_id = int(parts[1])
    index = int(parts[2])
    
    ctx = StateContext(state)
    fqdn, _ = await ctx.get_dns()
    ip = await ctx.get_a_record(index)
    
    if not fqdn or ip is None:
        await callback.answer("Record not found", show_alert=True)
        return

    # Check delete DNS permission
    if not await container.permission_checker.can_delete_dns(user_chat_id, fqdn):
        await callback.answer("No permission to delete DNS records", show_alert=True)
        return

    await callback.message.edit_text(
        f"Delete A record: {ip}?",
        reply_markup=confirm_keyboard(
            f"dda:{domain_id}:{index}",
            f"dna:{domain_id}",
        ),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("dda:"))
async def do_delete_a(
    callback: CallbackQuery, 
    state: FSMContext,
    container: DependencyContainer,
) -> None:
    """Delete A record (dda:domain_id:index)."""
    parts = callback.data.split(":")
    domain_id = int(parts[1])
    index = int(parts[2])
    
    ctx = StateContext(state)
    fqdn, _ = await ctx.get_dns()
    ip = await ctx.get_a_record(index)
    
    if not fqdn or ip is None:
        await callback.answer("Record not found", show_alert=True)
        return

    try:
        async with container.beget_manager.client() as client:
            dns_service = DnsService(client)
            await dns_service.delete_a_record(fqdn, ip)
            # Fetch updated records
            dns_data = await dns_service.get_dns_data(fqdn)
        
        await callback.answer("A record deleted!", show_alert=True)
        
        # Update state with new records
        await ctx.set_dns_records(
            a_records=[r.value for r in dns_data.a],
            txt_records=[],
        )
        
        # Show updated A records list
        text = f"A Records for {fqdn}:\n\n"
        if dns_data.a:
            for r in dns_data.a:
                text += f"- {r.value}\n"
        else:
            text += "No A records."

        await callback.message.edit_text(
            text,
            reply_markup=a_records_keyboard(domain_id, dns_data.a),
        )
    except Exception as e:
        await callback.answer(f"Error: {e}", show_alert=True)


# ============ TXT RECORDS ============


@router.callback_query(F.data.startswith("dnt:"))
async def show_txt_records(
    callback: CallbackQuery, 
    state: FSMContext,
    container: DependencyContainer,
) -> None:
    """Show TXT records management (dnt:domain_id)."""
    domain_id = int(callback.data.split(":")[1])
    ctx = StateContext(state)
    fqdn, _ = await ctx.get_dns()
    
    if not fqdn:
        await callback.answer("Domain data not found", show_alert=True)
        return

    try:
        async with container.beget_manager.client() as client:
            dns_service = DnsService(client)
            dns_data = await dns_service.get_dns_data(fqdn)
    except Exception as e:
        await callback.answer(f"Error: {e}", show_alert=True)
        return

    # Store TXT records in state for index-based access
    await ctx.set_dns_records(
        a_records=[],
        txt_records=[r.value for r in dns_data.txt],
    )

    text = f"TXT Records for {fqdn}:\n\n"
    if dns_data.txt:
        for i, r in enumerate(dns_data.txt):
            display = r.value[:50] + "..." if len(r.value) > 50 else r.value
            text += f"{i + 1}. {display}\n"
    else:
        text += "No TXT records."

    await callback.message.edit_text(
        text,
        reply_markup=txt_records_keyboard(domain_id, dns_data.txt),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("tr:"))
async def show_txt_record_detail(
    callback: CallbackQuery,
    state: FSMContext,
    container: DependencyContainer,
    user_chat_id: int,
) -> None:
    """Show TXT record detail and options (tr:domain_id:index)."""
    parts = callback.data.split(":")
    domain_id = int(parts[1])
    index = int(parts[2])
    
    ctx = StateContext(state)
    fqdn, _ = await ctx.get_dns()
    value = await ctx.get_txt_record(index)

    if value is None:
        await callback.answer("Record not found", show_alert=True)
        return

    # Check if user can delete
    can_delete = await container.permission_checker.can_delete_dns(user_chat_id, fqdn)

    if can_delete:
        await callback.message.edit_text(
            f"TXT Record:\n\n{value}",
            reply_markup=confirm_keyboard(
                f"dt:{domain_id}:{index}",
                f"dnt:{domain_id}",
            ),
        )
    else:
        # View-only mode
        await callback.message.edit_text(
            f"TXT Record:\n\n{value}",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="Back", callback_data=f"dnt:{domain_id}")]
                ]
            ),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("at:"))
async def start_add_txt_record(
    callback: CallbackQuery,
    state: FSMContext,
    container: DependencyContainer,
    user_chat_id: int,
) -> None:
    """Start adding TXT record (at:domain_id)."""
    domain_id = int(callback.data.split(":")[1])
    ctx = StateContext(state)
    fqdn, _ = await ctx.get_dns()
    
    if not fqdn:
        await callback.answer("Domain data not found", show_alert=True)
        return

    # Check edit DNS permission
    if not await container.permission_checker.can_edit_dns(user_chat_id, fqdn):
        await callback.answer("No permission to add DNS records", show_alert=True)
        return

    await state.update_data(dns_domain_id=domain_id)
    await state.set_state(DnsStates.waiting_txt_value)

    await callback.message.edit_text(
        f"Enter TXT record value for {fqdn}:\n\n"
        "Example: v=spf1 include:_spf.google.com ~all",
        reply_markup=cancel_keyboard(f"dnt:{domain_id}"),
    )
    await callback.answer()


@router.message(DnsStates.waiting_txt_value)
async def receive_txt_value(
    message: Message, 
    state: FSMContext,
    container: DependencyContainer,
) -> None:
    """Receive TXT record value."""
    value = message.text.strip()
    ctx = StateContext(state)
    fqdn, _ = await ctx.get_dns()

    if not value:
        await message.answer("Please enter a valid TXT value:")
        return

    try:
        async with container.beget_manager.client() as client:
            dns_service = DnsService(client)
            await dns_service.add_txt_record(fqdn, value)
        await message.answer(f"TXT record added to {fqdn}!")
    except Exception as e:
        await message.answer(f"Error: {e}")

    await state.clear()


@router.callback_query(F.data.startswith("dt:"))
async def do_delete_txt(
    callback: CallbackQuery, 
    state: FSMContext,
    container: DependencyContainer,
) -> None:
    """Delete TXT record (dt:domain_id:index)."""
    parts = callback.data.split(":")
    domain_id = int(parts[1])
    index = int(parts[2])
    
    ctx = StateContext(state)
    fqdn, _ = await ctx.get_dns()
    value = await ctx.get_txt_record(index)

    if value is None:
        await callback.answer("Record not found", show_alert=True)
        return

    try:
        async with container.beget_manager.client() as client:
            dns_service = DnsService(client)
            await dns_service.delete_txt_record(fqdn, value)
            # Fetch updated records
            dns_data = await dns_service.get_dns_data(fqdn)
        
        await callback.answer("TXT record deleted!", show_alert=True)
        
        # Update state with new records
        await ctx.set_dns_records(
            a_records=[],
            txt_records=[r.value for r in dns_data.txt],
        )
        
        # Show updated TXT records list
        text = f"TXT Records for {fqdn}:\n\n"
        if dns_data.txt:
            for i, r in enumerate(dns_data.txt):
                display = r.value[:50] + "..." if len(r.value) > 50 else r.value
                text += f"{i + 1}. {display}\n"
        else:
            text += "No TXT records."

        await callback.message.edit_text(
            text,
            reply_markup=txt_records_keyboard(domain_id, dns_data.txt),
        )
    except Exception as e:
        await callback.answer(f"Error: {e}", show_alert=True)
