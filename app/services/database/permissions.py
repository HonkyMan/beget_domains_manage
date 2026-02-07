"""Permissions repository for role-based access control."""

from dataclasses import dataclass
from datetime import datetime

from app.services.database.connection import Database


@dataclass
class DomainPermission:
    """Domain permission entity."""

    id: int
    chat_id: int
    domain_fqdn: str
    can_edit_dns: bool
    can_delete_dns: bool
    can_create_subdomain: bool
    can_delete_subdomain: bool
    granted_by: str
    granted_at: datetime


@dataclass
class SubdomainPermission:
    """Subdomain-only permission entity."""

    id: int
    chat_id: int
    subdomain_fqdn: str
    can_edit_dns: bool
    can_delete_dns: bool
    can_delete_subdomain: bool
    granted_by: str
    granted_at: datetime


class PermissionsRepository:
    """Repository for managing domain/subdomain permissions."""

    def __init__(self, db: Database):
        self.db = db

    # ============ Domain Permissions ============

    async def grant_domain_access(
        self,
        chat_id: int,
        domain_fqdn: str,
        can_edit_dns: bool,
        can_delete_dns: bool,
        can_create: bool,
        can_delete: bool,
        granted_by: str,
    ) -> bool:
        """Grant or update domain access for a user. Returns True if successful."""
        try:
            await self.db.connection.execute(
                """
                INSERT INTO domain_permissions 
                    (chat_id, domain_fqdn, can_edit_dns, can_delete_dns, 
                     can_create_subdomain, can_delete_subdomain, granted_by)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(chat_id, domain_fqdn) DO UPDATE SET
                    can_edit_dns = excluded.can_edit_dns,
                    can_delete_dns = excluded.can_delete_dns,
                    can_create_subdomain = excluded.can_create_subdomain,
                    can_delete_subdomain = excluded.can_delete_subdomain,
                    granted_by = excluded.granted_by,
                    granted_at = CURRENT_TIMESTAMP
                """,
                (chat_id, domain_fqdn, can_edit_dns, can_delete_dns, 
                 can_create, can_delete, granted_by),
            )
            await self.db.connection.commit()
            return True
        except Exception:
            return False

    async def revoke_domain_access(self, chat_id: int, domain_fqdn: str) -> bool:
        """Remove domain access from a user. Returns True if removed."""
        cursor = await self.db.connection.execute(
            "DELETE FROM domain_permissions WHERE chat_id = ? AND domain_fqdn = ?",
            (chat_id, domain_fqdn),
        )
        await self.db.connection.commit()
        return cursor.rowcount > 0

    async def get_user_domain_permissions(self, chat_id: int) -> list[DomainPermission]:
        """Get all domain permissions for a user."""
        cursor = await self.db.connection.execute(
            "SELECT * FROM domain_permissions WHERE chat_id = ? ORDER BY domain_fqdn",
            (chat_id,),
        )
        rows = await cursor.fetchall()
        return [self._row_to_domain_permission(row) for row in rows]

    async def has_domain_access(self, chat_id: int, domain_fqdn: str) -> bool:
        """Check if user has access to a domain."""
        cursor = await self.db.connection.execute(
            "SELECT 1 FROM domain_permissions WHERE chat_id = ? AND domain_fqdn = ?",
            (chat_id, domain_fqdn),
        )
        return await cursor.fetchone() is not None

    async def get_domain_permission(
        self, chat_id: int, domain_fqdn: str
    ) -> DomainPermission | None:
        """Get specific domain permission for a user."""
        cursor = await self.db.connection.execute(
            "SELECT * FROM domain_permissions WHERE chat_id = ? AND domain_fqdn = ?",
            (chat_id, domain_fqdn),
        )
        row = await cursor.fetchone()
        if not row:
            return None
        return self._row_to_domain_permission(row)

    async def get_domain_users(self, domain_fqdn: str) -> list[DomainPermission]:
        """Get all users with access to a domain."""
        cursor = await self.db.connection.execute(
            "SELECT * FROM domain_permissions WHERE domain_fqdn = ? ORDER BY chat_id",
            (domain_fqdn,),
        )
        rows = await cursor.fetchall()
        return [self._row_to_domain_permission(row) for row in rows]

    def _row_to_domain_permission(self, row) -> DomainPermission:
        """Convert database row to DomainPermission."""
        return DomainPermission(
            id=row["id"],
            chat_id=row["chat_id"],
            domain_fqdn=row["domain_fqdn"],
            can_edit_dns=bool(row["can_edit_dns"]) if "can_edit_dns" in row.keys() else False,
            can_delete_dns=bool(row["can_delete_dns"]) if "can_delete_dns" in row.keys() else False,
            can_create_subdomain=bool(row["can_create_subdomain"]),
            can_delete_subdomain=bool(row["can_delete_subdomain"]),
            granted_by=row["granted_by"],
            granted_at=datetime.fromisoformat(row["granted_at"]),
        )

    # ============ Subdomain Permissions ============

    async def grant_subdomain_access(
        self,
        chat_id: int,
        subdomain_fqdn: str,
        can_edit_dns: bool,
        can_delete_dns: bool,
        can_delete_subdomain: bool,
        granted_by: str,
    ) -> bool:
        """Grant subdomain-only access for a user. Returns True if successful."""
        try:
            await self.db.connection.execute(
                """
                INSERT INTO subdomain_permissions 
                    (chat_id, subdomain_fqdn, can_edit_dns, can_delete_dns, 
                     can_delete_subdomain, granted_by)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(chat_id, subdomain_fqdn) DO UPDATE SET
                    can_edit_dns = excluded.can_edit_dns,
                    can_delete_dns = excluded.can_delete_dns,
                    can_delete_subdomain = excluded.can_delete_subdomain,
                    granted_by = excluded.granted_by,
                    granted_at = CURRENT_TIMESTAMP
                """,
                (chat_id, subdomain_fqdn, can_edit_dns, can_delete_dns, 
                 can_delete_subdomain, granted_by),
            )
            await self.db.connection.commit()
            return True
        except Exception:
            return False

    async def revoke_subdomain_access(self, chat_id: int, subdomain_fqdn: str) -> bool:
        """Remove subdomain access from a user. Returns True if removed."""
        cursor = await self.db.connection.execute(
            "DELETE FROM subdomain_permissions WHERE chat_id = ? AND subdomain_fqdn = ?",
            (chat_id, subdomain_fqdn),
        )
        await self.db.connection.commit()
        return cursor.rowcount > 0

    async def get_user_subdomain_permissions(
        self, chat_id: int
    ) -> list[SubdomainPermission]:
        """Get all subdomain-only permissions for a user."""
        cursor = await self.db.connection.execute(
            "SELECT * FROM subdomain_permissions WHERE chat_id = ? ORDER BY subdomain_fqdn",
            (chat_id,),
        )
        rows = await cursor.fetchall()
        return [self._row_to_subdomain_permission(row) for row in rows]

    async def has_subdomain_access(self, chat_id: int, subdomain_fqdn: str) -> bool:
        """Check if user has explicit subdomain-only access."""
        cursor = await self.db.connection.execute(
            "SELECT 1 FROM subdomain_permissions WHERE chat_id = ? AND subdomain_fqdn = ?",
            (chat_id, subdomain_fqdn),
        )
        return await cursor.fetchone() is not None

    async def get_subdomain_permission(
        self, chat_id: int, subdomain_fqdn: str
    ) -> SubdomainPermission | None:
        """Get specific subdomain permission for a user."""
        cursor = await self.db.connection.execute(
            "SELECT * FROM subdomain_permissions WHERE chat_id = ? AND subdomain_fqdn = ?",
            (chat_id, subdomain_fqdn),
        )
        row = await cursor.fetchone()
        if not row:
            return None
        return self._row_to_subdomain_permission(row)

    async def get_subdomain_users(self, subdomain_fqdn: str) -> list[SubdomainPermission]:
        """Get all users with explicit access to a subdomain."""
        cursor = await self.db.connection.execute(
            "SELECT * FROM subdomain_permissions WHERE subdomain_fqdn = ? ORDER BY chat_id",
            (subdomain_fqdn,),
        )
        rows = await cursor.fetchall()
        return [self._row_to_subdomain_permission(row) for row in rows]

    def _row_to_subdomain_permission(self, row) -> SubdomainPermission:
        """Convert database row to SubdomainPermission."""
        return SubdomainPermission(
            id=row["id"],
            chat_id=row["chat_id"],
            subdomain_fqdn=row["subdomain_fqdn"],
            can_edit_dns=bool(row["can_edit_dns"]) if "can_edit_dns" in row.keys() else False,
            can_delete_dns=bool(row["can_delete_dns"]) if "can_delete_dns" in row.keys() else False,
            can_delete_subdomain=bool(row["can_delete_subdomain"]) if "can_delete_subdomain" in row.keys() else False,
            granted_by=row["granted_by"],
            granted_at=datetime.fromisoformat(row["granted_at"]),
        )

    # ============ Creator Tracking ============

    async def record_subdomain_creation(
        self, subdomain_fqdn: str, created_by_chat_id: int
    ) -> bool:
        """Record who created a subdomain. Returns True if successful."""
        try:
            await self.db.connection.execute(
                """
                INSERT INTO created_subdomains (subdomain_fqdn, created_by_chat_id)
                VALUES (?, ?)
                ON CONFLICT(subdomain_fqdn) DO NOTHING
                """,
                (subdomain_fqdn, created_by_chat_id),
            )
            await self.db.connection.commit()
            return True
        except Exception:
            return False

    async def get_subdomain_creator(self, subdomain_fqdn: str) -> int | None:
        """Get the chat_id of who created a subdomain."""
        cursor = await self.db.connection.execute(
            "SELECT created_by_chat_id FROM created_subdomains WHERE subdomain_fqdn = ?",
            (subdomain_fqdn,),
        )
        row = await cursor.fetchone()
        return row["created_by_chat_id"] if row else None

    async def delete_subdomain_record(self, subdomain_fqdn: str) -> bool:
        """Remove creator record when subdomain is deleted. Returns True if removed."""
        cursor = await self.db.connection.execute(
            "DELETE FROM created_subdomains WHERE subdomain_fqdn = ?",
            (subdomain_fqdn,),
        )
        await self.db.connection.commit()
        return cursor.rowcount > 0

    async def get_user_created_subdomains(self, chat_id: int) -> list[str]:
        """Get all subdomains created by a user."""
        cursor = await self.db.connection.execute(
            "SELECT subdomain_fqdn FROM created_subdomains WHERE created_by_chat_id = ?",
            (chat_id,),
        )
        rows = await cursor.fetchall()
        return [row["subdomain_fqdn"] for row in rows]

    # ============ Helpers ============

    @staticmethod
    def extract_parent_domain(subdomain_fqdn: str) -> str:
        """Extract parent domain from subdomain FQDN.
        
        Example: "api.example.com" -> "example.com"
        """
        parts = subdomain_fqdn.split(".", 1)
        if len(parts) > 1:
            return parts[1]
        return subdomain_fqdn
