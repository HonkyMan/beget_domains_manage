"""Domain management service."""

from app.services.beget.client import BegetClient
from app.services.beget.types import Domain, Subdomain


class DomainsService:
    """Service for managing domains and subdomains."""

    def __init__(self, client: BegetClient):
        self.client = client

    async def get_domains(self) -> list[Domain]:
        """Get all domains."""
        result = await self.client.request("domain/getList")
        if not result:
            return []
        # Beget API returns nested structure: answer -> result -> list
        if isinstance(result, dict):
            result = result.get("result", [])
        if not result:
            return []
        return [Domain(id=d["id"], fqdn=d["fqdn"]) for d in result]

    async def get_subdomains(self, domain_id: int) -> list[Subdomain]:
        """Get subdomains for a domain."""
        # Beget API getSubdomainList doesn't accept parameters
        # It returns all subdomains, we need to filter by domain_id
        result = await self.client.request("domain/getSubdomainList")
        
        if not result:
            return []
        # Beget API returns nested structure: answer -> result -> list
        if isinstance(result, dict):
            result = result.get("result", [])
        if not result:
            return []
        
        # Filter subdomains by domain_id
        filtered = [s for s in result if s.get("domain_id") == domain_id]
        return [Subdomain(id=s["id"], fqdn=s["fqdn"]) for s in filtered]

    async def add_subdomain(self, domain_id: int, subdomain: str) -> bool:
        """Add a virtual subdomain."""
        await self.client.request(
            "domain/addSubdomainVirtual",
            {"domain_id": domain_id, "subdomain": subdomain},
        )
        return True

    async def delete_subdomain(self, subdomain_id: int) -> bool:
        """Delete a subdomain."""
        await self.client.request(
            "domain/deleteSubdomain",
            {"id": subdomain_id},
        )
        return True
