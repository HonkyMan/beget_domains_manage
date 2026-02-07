"""Permission checker for role-based access control."""

from app.services.database.permissions import PermissionsRepository
from app.services.beget.types import Domain, Subdomain


class PermissionChecker:
    """Central permission checking logic."""

    def __init__(self, permissions_repo: PermissionsRepository, admin_chat_id: int):
        self.repo = permissions_repo
        self.admin_chat_id = admin_chat_id

    def is_admin(self, chat_id: int) -> bool:
        """Check if user is admin."""
        return chat_id == self.admin_chat_id

    async def can_view_domain(self, chat_id: int, domain_fqdn: str) -> bool:
        """Check if user can view a domain."""
        if self.is_admin(chat_id):
            return True
        return await self.repo.has_domain_access(chat_id, domain_fqdn)

    async def can_view_subdomain(self, chat_id: int, subdomain_fqdn: str) -> bool:
        """Check if user can view a subdomain.
        
        Access is granted if:
        1. User is admin
        2. User has access to parent domain (inherits all subdomain access)
        3. User has explicit subdomain-only access
        4. User created the subdomain (and has create permission on parent domain)
        """
        if self.is_admin(chat_id):
            return True

        # Check parent domain access (inherits subdomain access)
        parent_domain = self.repo.extract_parent_domain(subdomain_fqdn)
        if await self.repo.has_domain_access(chat_id, parent_domain):
            return True

        # Check explicit subdomain-only access
        if await self.repo.has_subdomain_access(chat_id, subdomain_fqdn):
            return True

        # Check creator privilege
        perm = await self.repo.get_domain_permission(chat_id, parent_domain)
        if perm and perm.can_create_subdomain:
            creator = await self.repo.get_subdomain_creator(subdomain_fqdn)
            if creator == chat_id:
                return True

        return False

    async def can_create_subdomain(self, chat_id: int, domain_fqdn: str) -> bool:
        """Check if user can create subdomains under a domain."""
        if self.is_admin(chat_id):
            return True

        perm = await self.repo.get_domain_permission(chat_id, domain_fqdn)
        return perm is not None and perm.can_create_subdomain

    async def can_delete_subdomain(self, chat_id: int, subdomain_fqdn: str) -> bool:
        """Check if user can delete a subdomain.
        
        Access is granted if:
        1. User is admin
        2. User has delete permission on parent domain
        3. User has explicit subdomain permission with can_delete_subdomain
        4. User created the subdomain AND has create permission on parent domain
        """
        if self.is_admin(chat_id):
            return True

        parent_domain = self.repo.extract_parent_domain(subdomain_fqdn)
        
        # Check parent domain permission
        perm = await self.repo.get_domain_permission(chat_id, parent_domain)
        if perm and perm.can_delete_subdomain:
            return True

        # Check explicit subdomain permission
        sub_perm = await self.repo.get_subdomain_permission(chat_id, subdomain_fqdn)
        if sub_perm and sub_perm.can_delete_subdomain:
            return True

        # Creator privilege: can delete own subdomains if has create permission
        if perm and perm.can_create_subdomain:
            creator = await self.repo.get_subdomain_creator(subdomain_fqdn)
            if creator == chat_id:
                return True

        return False

    async def can_view_dns(self, chat_id: int, fqdn: str) -> bool:
        """Check if user can view DNS records for a domain or subdomain.
        
        Viewing is allowed if user has any access to the domain/subdomain.
        """
        if self.is_admin(chat_id):
            return True

        # Try as domain first
        if await self.repo.has_domain_access(chat_id, fqdn):
            return True

        # Try as subdomain
        return await self.can_view_subdomain(chat_id, fqdn)

    async def can_edit_dns(self, chat_id: int, fqdn: str) -> bool:
        """Check if user can edit (add/change) DNS records.
        
        Access is granted if:
        1. User is admin
        2. User has edit DNS permission on the domain
        3. For subdomains: user has edit DNS on subdomain OR inherits from parent domain
        """
        if self.is_admin(chat_id):
            return True

        # Check as domain
        domain_perm = await self.repo.get_domain_permission(chat_id, fqdn)
        if domain_perm and domain_perm.can_edit_dns:
            return True

        # Check as subdomain
        sub_perm = await self.repo.get_subdomain_permission(chat_id, fqdn)
        if sub_perm and sub_perm.can_edit_dns:
            return True

        # Check parent domain permission for subdomains
        parent_domain = self.repo.extract_parent_domain(fqdn)
        if parent_domain != fqdn:
            parent_perm = await self.repo.get_domain_permission(chat_id, parent_domain)
            if parent_perm and parent_perm.can_edit_dns:
                return True

        # Creator privilege: can edit DNS of own subdomains
        if parent_domain != fqdn:
            parent_perm = await self.repo.get_domain_permission(chat_id, parent_domain)
            if parent_perm and parent_perm.can_create_subdomain:
                creator = await self.repo.get_subdomain_creator(fqdn)
                if creator == chat_id:
                    return True

        return False

    async def can_delete_dns(self, chat_id: int, fqdn: str) -> bool:
        """Check if user can delete DNS records.
        
        Access is granted if:
        1. User is admin
        2. User has delete DNS permission on the domain
        3. For subdomains: user has delete DNS on subdomain OR inherits from parent domain
        """
        if self.is_admin(chat_id):
            return True

        # Check as domain
        domain_perm = await self.repo.get_domain_permission(chat_id, fqdn)
        if domain_perm and domain_perm.can_delete_dns:
            return True

        # Check as subdomain
        sub_perm = await self.repo.get_subdomain_permission(chat_id, fqdn)
        if sub_perm and sub_perm.can_delete_dns:
            return True

        # Check parent domain permission for subdomains
        parent_domain = self.repo.extract_parent_domain(fqdn)
        if parent_domain != fqdn:
            parent_perm = await self.repo.get_domain_permission(chat_id, parent_domain)
            if parent_perm and parent_perm.can_delete_dns:
                return True

        # Creator privilege: can delete DNS of own subdomains
        if parent_domain != fqdn:
            parent_perm = await self.repo.get_domain_permission(chat_id, parent_domain)
            if parent_perm and parent_perm.can_create_subdomain:
                creator = await self.repo.get_subdomain_creator(fqdn)
                if creator == chat_id:
                    return True

        return False

    async def can_manage_dns(self, chat_id: int, fqdn: str) -> bool:
        """Check if user can manage (view) DNS records for a domain or subdomain.
        
        This is the basic access check - viewing DNS is allowed if user has any access.
        For editing/deleting, use can_edit_dns/can_delete_dns.
        """
        return await self.can_view_dns(chat_id, fqdn)

    async def filter_domains(
        self, chat_id: int, all_domains: list[Domain]
    ) -> list[Domain]:
        """Filter domain list to only those user can access.
        
        User can see a domain if they have:
        1. Direct domain permission, OR
        2. Subdomain-only permission for any subdomain of that domain
        """
        if self.is_admin(chat_id):
            return all_domains

        # Get domains with direct access
        user_permissions = await self.repo.get_user_domain_permissions(chat_id)
        allowed_fqdns = {p.domain_fqdn for p in user_permissions}

        # Also include parent domains of subdomain-only permissions
        subdomain_perms = await self.repo.get_user_subdomain_permissions(chat_id)
        for sp in subdomain_perms:
            parent = self.repo.extract_parent_domain(sp.subdomain_fqdn)
            allowed_fqdns.add(parent)

        # Also include parent domains of created subdomains
        created_subs = await self.repo.get_user_created_subdomains(chat_id)
        for sub_fqdn in created_subs:
            parent = self.repo.extract_parent_domain(sub_fqdn)
            allowed_fqdns.add(parent)

        return [d for d in all_domains if d.fqdn in allowed_fqdns]

    async def filter_subdomains(
        self,
        chat_id: int,
        domain_fqdn: str,
        all_subdomains: list[Subdomain],
    ) -> list[Subdomain]:
        """Filter subdomain list to only those user can access.
        
        If user has domain access, they can see all subdomains.
        Otherwise, filter to only explicitly permitted + created subdomains.
        """
        if self.is_admin(chat_id):
            return all_subdomains

        # User with domain access can see all subdomains
        if await self.repo.has_domain_access(chat_id, domain_fqdn):
            return all_subdomains

        # Otherwise, filter to permitted subdomains
        user_subdomain_perms = await self.repo.get_user_subdomain_permissions(chat_id)
        allowed_fqdns = {p.subdomain_fqdn for p in user_subdomain_perms}

        # Also include created subdomains if user has create permission
        perm = await self.repo.get_domain_permission(chat_id, domain_fqdn)
        if perm and perm.can_create_subdomain:
            created = await self.repo.get_user_created_subdomains(chat_id)
            allowed_fqdns.update(created)

        return [s for s in all_subdomains if s.fqdn in allowed_fqdns]

    async def get_user_accessible_domain_fqdns(self, chat_id: int) -> set[str]:
        """Get set of domain FQDNs user can access."""
        if self.is_admin(chat_id):
            return set()  # Empty means all for admin

        perms = await self.repo.get_user_domain_permissions(chat_id)
        return {p.domain_fqdn for p in perms}

    async def get_permission_details(
        self, chat_id: int, domain_fqdn: str
    ) -> dict:
        """Get detailed permission info for a user on a domain."""
        if self.is_admin(chat_id):
            return {
                "has_access": True,
                "can_edit_dns": True,
                "can_delete_dns": True,
                "can_create_subdomain": True,
                "can_delete_subdomain": True,
                "is_admin": True,
            }

        perm = await self.repo.get_domain_permission(chat_id, domain_fqdn)
        if perm:
            return {
                "has_access": True,
                "can_edit_dns": perm.can_edit_dns,
                "can_delete_dns": perm.can_delete_dns,
                "can_create_subdomain": perm.can_create_subdomain,
                "can_delete_subdomain": perm.can_delete_subdomain,
                "is_admin": False,
            }

        return {
            "has_access": False,
            "can_edit_dns": False,
            "can_delete_dns": False,
            "can_create_subdomain": False,
            "can_delete_subdomain": False,
            "is_admin": False,
        }

    async def get_subdomain_permission_details(
        self, chat_id: int, subdomain_fqdn: str
    ) -> dict:
        """Get detailed permission info for a user on a subdomain."""
        if self.is_admin(chat_id):
            return {
                "has_access": True,
                "can_edit_dns": True,
                "can_delete_dns": True,
                "can_delete_subdomain": True,
                "is_admin": True,
            }

        perm = await self.repo.get_subdomain_permission(chat_id, subdomain_fqdn)
        if perm:
            return {
                "has_access": True,
                "can_edit_dns": perm.can_edit_dns,
                "can_delete_dns": perm.can_delete_dns,
                "can_delete_subdomain": perm.can_delete_subdomain,
                "is_admin": False,
            }

        return {
            "has_access": False,
            "can_edit_dns": False,
            "can_delete_dns": False,
            "can_delete_subdomain": False,
            "is_admin": False,
        }
