"""Domains module FSM states."""

from aiogram.fsm.state import State, StatesGroup


class SubdomainStates(StatesGroup):
    """FSM states for subdomain operations."""
    
    waiting_subdomain_name = State()
    confirm_create_subdomain = State()
    confirm_delete_subdomain = State()


class DnsStates(StatesGroup):
    """FSM states for DNS operations."""
    
    waiting_a_record_ip = State()
    waiting_new_a_ip = State()
    waiting_txt_value = State()
    confirm_delete_record = State()
