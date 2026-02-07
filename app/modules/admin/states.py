"""Admin FSM states."""

from aiogram.fsm.state import State, StatesGroup


class AdminStates(StatesGroup):
    """FSM states for admin operations."""

    waiting_chat_id = State()
    waiting_chat_note = State()
    confirm_remove_chat = State()


class PermissionStates(StatesGroup):
    """FSM states for permission management."""

    # Grant domain access flow (2-step)
    waiting_domain_chat_id = State()
    waiting_domain_dns_permissions = State()
    waiting_domain_subdomain_permissions = State()
    waiting_domain_permissions = State()  # Legacy, kept for compatibility
    confirm_domain_grant = State()
    
    # Grant subdomain access flow (2-step)
    waiting_subdomain_chat_id = State()
    waiting_subdomain_dns_permissions = State()
    waiting_subdomain_delete_permission = State()
    confirm_subdomain_grant = State()
    
    # Revoke access
    confirm_revoke = State()
