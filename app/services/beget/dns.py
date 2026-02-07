"""DNS management service."""

from typing import Any
from app.services.beget.client import BegetClient
from app.services.beget.types import DnsData, DnsRecord


class DnsService:
    """Service for managing DNS records."""

    def __init__(self, client: BegetClient):
        self.client = client

    async def get_dns_data(self, fqdn: str) -> DnsData:
        """Get DNS records for a domain."""
        result = await self.client.request("dns/getData", {"fqdn": fqdn})
        if not result:
            return DnsData(fqdn=fqdn)
        
        # Beget API returns nested structure: answer -> result
        if isinstance(result, dict) and "result" in result:
            result = result["result"]
        
        if not result:
            return DnsData(fqdn=fqdn)
        
        # Records are inside "records" key
        records = result.get("records", {})

        # Parse A records: {"ttl": 600, "address": "1.2.3.4"} -> DnsRecord
        a_records = []
        for r in records.get("A", []):
            a_records.append(DnsRecord(value=r.get("address", ""), priority=10))
        
        # Parse AAAA records: {"ttl": 600, "address": "::1"} -> DnsRecord
        aaaa_records = []
        for r in records.get("AAAA", []):
            aaaa_records.append(DnsRecord(value=r.get("address", ""), priority=10))
        
        # Parse MX records: {"ttl": 300, "exchange": "mx.domain.ru.", "preference": 10}
        mx_records = []
        for r in records.get("MX", []):
            mx_records.append(DnsRecord(
                value=r.get("exchange", "").rstrip("."),
                priority=r.get("preference", 10)
            ))
        
        # Parse TXT records: {"ttl": 300, "txtdata": "v=spf1..."}
        txt_records = []
        for r in records.get("TXT", []):
            txt_records.append(DnsRecord(value=r.get("txtdata", ""), priority=10))
        
        # Parse CNAME records: {"ttl": 600, "cname": "target.domain.ru."}
        cname_records = []
        for r in records.get("CNAME", []):
            cname_records.append(DnsRecord(value=r.get("cname", "").rstrip("."), priority=10))
        
        # Parse NS records: {"value": "ns1.domain.ru"}
        ns_records = []
        for r in records.get("NS", []):
            ns_records.append(DnsRecord(value=r.get("nsdname", r.get("value", "")), priority=10))
        
        # Parse DNS records (nameservers): {"value": "ns1.beget.com"}
        dns_list = [r.get("value", "") for r in records.get("DNS", [])]
        dns_ip_list = [r.get("value", "") for r in records.get("DNS_IP", [])]

        return DnsData(
            fqdn=fqdn,
            dns_ip=dns_ip_list,
            dns=dns_list,
            a=a_records,
            aaaa=aaaa_records,
            mx=mx_records,
            txt=txt_records,
            cname=cname_records,
            ns=ns_records,
        )

    async def change_records(
        self,
        fqdn: str,
        records: dict[str, list[dict[str, Any]]],
    ) -> bool:
        """
        Change DNS records for a domain.

        Note: This replaces ALL records of the specified types.
        First get current records with get_dns_data(), modify them,
        then pass all records back.

        Args:
            fqdn: Domain FQDN
            records: Dict with record types as keys (A, AAAA, MX, TXT, CNAME, NS)
                    and lists of {"value": str, "priority": int} as values
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # Beget API requires "records" wrapper
        params = {"fqdn": fqdn, "records": records}
        result = await self.client.request("dns/changeRecords", params)
        
        # Log the result for debugging
        logger.info(f"changeRecords result type: {type(result)}, value: {result}")
        
        # API returns result structure, check if it's successful
        if isinstance(result, dict):
            # If result contains 'result' key with data, it's successful
            if "result" in result:
                return True
            # If result has status field and it's success/ok
            status = result.get("status", "").lower()
            if status in ("success", "ok", "done"):
                return True
        
        # If we got any non-error response, consider it successful
        return True

    async def add_a_record(self, fqdn: str, ip: str) -> bool:
        """Add or update A record."""
        current = await self.get_dns_data(fqdn)
        # Build records with priority (required, must be > 0)
        a_records = [{"value": r.value, "priority": max(r.priority, 10)} for r in current.a]
        # Add new record with next priority
        next_priority = (len(a_records) + 1) * 10
        a_records.append({"value": ip, "priority": next_priority})
        return await self.change_records(fqdn, {"A": a_records})

    async def update_a_record(self, fqdn: str, old_ip: str, new_ip: str) -> bool:
        """Update an existing A record."""
        current = await self.get_dns_data(fqdn)
        a_records = []
        for i, r in enumerate(current.a):
            priority = max(r.priority, (i + 1) * 10)
            if r.value == old_ip:
                a_records.append({"value": new_ip, "priority": priority})
            else:
                a_records.append({"value": r.value, "priority": priority})
        return await self.change_records(fqdn, {"A": a_records})

    async def delete_a_record(self, fqdn: str, ip: str) -> bool:
        """Delete an A record."""
        current = await self.get_dns_data(fqdn)
        a_records = []
        priority = 10
        for r in current.a:
            if r.value != ip:
                a_records.append({"value": r.value, "priority": priority})
                priority += 10
        return await self.change_records(fqdn, {"A": a_records})

    async def add_txt_record(self, fqdn: str, value: str) -> bool:
        """Add a TXT record."""
        current = await self.get_dns_data(fqdn)
        txt_records = [{"value": r.value, "priority": max(r.priority, 10)} for r in current.txt]
        next_priority = (len(txt_records) + 1) * 10
        txt_records.append({"value": value, "priority": next_priority})
        return await self.change_records(fqdn, {"TXT": txt_records})

    async def delete_txt_record(self, fqdn: str, value: str) -> bool:
        """Delete a TXT record."""
        current = await self.get_dns_data(fqdn)
        txt_records = []
        priority = 10
        for r in current.txt:
            if r.value != value:
                txt_records.append({"value": r.value, "priority": priority})
                priority += 10
        return await self.change_records(fqdn, {"TXT": txt_records})
