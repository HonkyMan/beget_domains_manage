"""Domain browsing handlers with optimized callback_data."""

from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from app.core.container import DependencyContainer
from app.core.state_helpers import StateContext
from app.services.beget import DomainsService
from app.bot.callback_data import CB_DOMAIN, CB_MENU_DOMAINS
from app.modules.domains.domain.keyboards import (
    domains_list_keyboard,
    domain_menu_keyboard,
)

router = Router(name="domains_domain")


@router.callback_query(F.data == CB_MENU_DOMAINS)
async def show_domains(
    callback: CallbackQuery,
    state: FSMContext,
    container: DependencyContainer,
    user_chat_id: int,
) -> None:
    """Show list of domains."""
    await state.clear()

    try:
        async with container.beget_manager.client() as client:
            domains_service = DomainsService(client)
            all_domains = await domains_service.get_domains()
    except Exception as e:
        await callback.message.edit_text(f"Error loading domains: {e}")
        await callback.answer()
        return

    # Filter domains by user permissions
    domains = await container.permission_checker.filter_domains(user_chat_id, all_domains)

    if not domains:
        await callback.message.edit_text(
            "No domains available.\n\n"
            "Contact administrator to get access to domains."
        )
        await callback.answer()
        return

    # Store domain list in state for ID->FQDN lookup
    ctx = StateContext(state)
    domain_map = {d.id: d.fqdn for d in domains}
    await state.update_data(domain_map=domain_map)

    await callback.message.edit_text(
        "Select a domain:",
        reply_markup=domains_list_keyboard(domains),
    )
    await callback.answer()


@router.callback_query(F.data.startswith(f"{CB_DOMAIN}:"))
async def show_domain_menu(
    callback: CallbackQuery,
    state: FSMContext,
    container: DependencyContainer,
    user_chat_id: int,
) -> None:
    """Show domain management menu."""
    # Parse short callback: d:123
    domain_id = int(callback.data.split(":")[1])
    
    # Get FQDN from state or fetch from API
    data = await state.get_data()
    domain_map = data.get("domain_map", {})
    fqdn = domain_map.get(domain_id, "")
    
    if not fqdn:
        # Fallback: fetch from API
        try:
            async with container.beget_manager.client() as client:
                domains_service = DomainsService(client)
                domains = await domains_service.get_domains()
                for d in domains:
                    if d.id == domain_id:
                        fqdn = d.fqdn
                        break
        except Exception:
            pass
    
    if not fqdn:
        await callback.answer("Domain not found", show_alert=True)
        return

    # Check permission
    if not await container.permission_checker.can_view_domain(user_chat_id, fqdn):
        await callback.answer("You don't have access to this domain.", show_alert=True)
        return

    # Store domain context for child handlers
    ctx = StateContext(state)
    await ctx.set_domain(domain_id, fqdn)

    await callback.message.edit_text(
        f"Domain: {fqdn}\n\nSelect an option:",
        reply_markup=domain_menu_keyboard(domain_id),
    )
    await callback.answer()
