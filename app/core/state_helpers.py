"""FSM state helpers for managing navigation context.

When callback_data is too short to hold all needed info (like long FQDNs),
we store the context in FSM state and use short IDs in callbacks.
"""

from typing import Any
from aiogram.fsm.context import FSMContext


class StateContext:
    """Helper for managing navigation context in FSM state.
    
    Usage:
        # Store context when showing a list
        ctx = StateContext(state)
        await ctx.set_domain(domain_id=123, fqdn="example.com")
        
        # Retrieve in handler
        domain_id, fqdn = await ctx.get_domain()
    """
    
    def __init__(self, state: FSMContext):
        self.state = state
    
    # ============ DOMAIN CONTEXT ============
    
    async def set_domain(self, domain_id: int, fqdn: str) -> None:
        """Store current domain context."""
        await self.state.update_data(
            ctx_domain_id=domain_id,
            ctx_domain_fqdn=fqdn,
        )
    
    async def get_domain(self) -> tuple[int, str]:
        """Get current domain context."""
        data = await self.state.get_data()
        return data.get("ctx_domain_id", 0), data.get("ctx_domain_fqdn", "")
    
    # ============ SUBDOMAIN CONTEXT ============
    
    async def set_subdomain(
        self,
        subdomain_id: int,
        fqdn: str,
        parent_domain_id: int,
        parent_fqdn: str,
    ) -> None:
        """Store current subdomain context."""
        await self.state.update_data(
            ctx_subdomain_id=subdomain_id,
            ctx_subdomain_fqdn=fqdn,
            ctx_parent_domain_id=parent_domain_id,
            ctx_parent_fqdn=parent_fqdn,
        )
    
    async def get_subdomain(self) -> tuple[int, str, int, str]:
        """Get current subdomain context.
        
        Returns: (subdomain_id, subdomain_fqdn, parent_domain_id, parent_fqdn)
        """
        data = await self.state.get_data()
        return (
            data.get("ctx_subdomain_id", 0),
            data.get("ctx_subdomain_fqdn", ""),
            data.get("ctx_parent_domain_id", 0),
            data.get("ctx_parent_fqdn", ""),
        )
    
    # ============ DNS CONTEXT ============
    
    async def set_dns(self, fqdn: str, back_callback: str = "") -> None:
        """Store DNS context."""
        await self.state.update_data(
            ctx_dns_fqdn=fqdn,
            ctx_dns_back=back_callback,
        )
    
    async def get_dns(self) -> tuple[str, str]:
        """Get DNS context.
        
        Returns: (fqdn, back_callback)
        """
        data = await self.state.get_data()
        return data.get("ctx_dns_fqdn", ""), data.get("ctx_dns_back", "")
    
    async def set_dns_records(self, a_records: list[str], txt_records: list[str]) -> None:
        """Store DNS records for reference by index."""
        await self.state.update_data(
            ctx_a_records=a_records,
            ctx_txt_records=txt_records,
        )
    
    async def get_a_record(self, index: int) -> str | None:
        """Get A record by index."""
        data = await self.state.get_data()
        records = data.get("ctx_a_records", [])
        return records[index] if index < len(records) else None
    
    async def get_txt_record(self, index: int) -> str | None:
        """Get TXT record by index."""
        data = await self.state.get_data()
        records = data.get("ctx_txt_records", [])
        return records[index] if index < len(records) else None
    
    # ============ PERMISSION CONTEXT ============
    
    async def set_perm_item(self, fqdn: str, is_domain: bool) -> None:
        """Store permission item context."""
        await self.state.update_data(
            ctx_perm_fqdn=fqdn,
            ctx_perm_is_domain=is_domain,
        )
    
    async def get_perm_item(self) -> tuple[str, bool]:
        """Get permission item context.
        
        Returns: (fqdn, is_domain)
        """
        data = await self.state.get_data()
        return data.get("ctx_perm_fqdn", ""), data.get("ctx_perm_is_domain", True)
    
    async def set_grant_context(
        self,
        fqdn: str,
        is_domain: bool,
        chat_id: int | None = None,
    ) -> None:
        """Store grant access context."""
        await self.state.update_data(
            ctx_grant_fqdn=fqdn,
            ctx_grant_is_domain=is_domain,
            ctx_grant_chat_id=chat_id,
        )
    
    async def get_grant_context(self) -> tuple[str, bool, int | None]:
        """Get grant access context.
        
        Returns: (fqdn, is_domain, chat_id)
        """
        data = await self.state.get_data()
        return (
            data.get("ctx_grant_fqdn", ""),
            data.get("ctx_grant_is_domain", True),
            data.get("ctx_grant_chat_id"),
        )
    
    # ============ PERMISSION LISTS ============
    
    async def set_perm_domains(self, domains: list[tuple[int, str]]) -> None:
        """Store domains list for permissions (list of (id, fqdn))."""
        await self.state.update_data(ctx_perm_domains=domains)
    
    async def get_perm_domain(self, index: int) -> tuple[int, str] | None:
        """Get domain by index from stored list."""
        data = await self.state.get_data()
        domains = data.get("ctx_perm_domains", [])
        return domains[index] if index < len(domains) else None
    
    async def set_perm_subdomains(self, subdomains: list[tuple[int, str]]) -> None:
        """Store subdomains list for permissions (list of (id, fqdn))."""
        await self.state.update_data(ctx_perm_subdomains=subdomains)
    
    async def get_perm_subdomain(self, index: int) -> tuple[int, str] | None:
        """Get subdomain by index from stored list."""
        data = await self.state.get_data()
        subs = data.get("ctx_perm_subdomains", [])
        return subs[index] if index < len(subs) else None
    
    async def set_perm_users(self, users: list[tuple[int, str]]) -> None:
        """Store users with permissions (list of (chat_id, fqdn))."""
        await self.state.update_data(ctx_perm_users=users)
    
    async def get_perm_user(self, index: int) -> tuple[int, str] | None:
        """Get user by index from stored list."""
        data = await self.state.get_data()
        users = data.get("ctx_perm_users", [])
        return users[index] if index < len(users) else None
    
    async def set_current_perm_domain(self, index: int, fqdn: str) -> None:
        """Store current domain being edited for permissions."""
        await self.state.update_data(
            ctx_current_perm_domain_idx=index,
            ctx_current_perm_domain_fqdn=fqdn,
        )
    
    async def get_current_perm_domain(self) -> tuple[int, str]:
        """Get current domain for permissions."""
        data = await self.state.get_data()
        return (
            data.get("ctx_current_perm_domain_idx", 0),
            data.get("ctx_current_perm_domain_fqdn", ""),
        )
    
    # ============ UTILITY ============
    
    async def clear_context(self) -> None:
        """Clear all context data (keeps state itself)."""
        data = await self.state.get_data()
        # Remove only ctx_ prefixed keys
        clean_data = {k: v for k, v in data.items() if not k.startswith("ctx_")}
        await self.state.set_data(clean_data)
    
    async def get_all(self) -> dict[str, Any]:
        """Get all state data."""
        return await self.state.get_data()
