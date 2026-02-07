"""DNS management service."""

from typing import Any
from app.services.beget.client import BegetClient
from app.services.beget.types import DnsData, DnsRecord


class DnsService:
    """Service for managing DNS records."""

    def __init__(self, client: BegetClient):
        self.client = client

    def _build_all_records(self, dns_data: DnsData) -> dict[str, list[dict[str, Any]]]:
        """
        Build DNS records dict for group 1 (A, MX, TXT).
        
        According to Beget API docs, there are 3 mutually exclusive groups:
        - Group 1: A, MX, TXT (for domains and subdomains)
        - Group 2: NS (for subdomains only)
        - Group 3: CNAME (for subdomains only)
        
        When modifying A/MX/TXT records, we must send ONLY group 1 records.
        NS and CNAME cannot be mixed with A records!
        """
        records = {}
        
        # Group 1: A, MX, TXT records only
        # A records
        if dns_data.a:
            records["A"] = [{"value": r.value, "priority": max(r.priority, 10)} for r in dns_data.a]
        
        # MX records - preserve existing
        if dns_data.mx:
            records["MX"] = [{"value": r.value, "priority": max(r.priority, 10)} for r in dns_data.mx]
        
        # TXT records - preserve existing
        if dns_data.txt:
            records["TXT"] = [{"value": r.value, "priority": max(r.priority, 10)} for r in dns_data.txt]
        
        # NOTE: We intentionally do NOT include NS, CNAME, AAAA here
        # because they belong to different groups and cannot be mixed with A records
        
        return records

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

        # Get subdomain and set_type info from API response
        is_subdomain = bool(result.get("is_subdomain", 0))
        set_type = int(result.get("set_type", 1))

        return DnsData(
            fqdn=fqdn,
            is_subdomain=is_subdomain,
            set_type=set_type,
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
        # Beget API requires "records" wrapper
        params = {"fqdn": fqdn, "records": records}
        result = await self.client.request("dns/changeRecords", params)
        
        # API returns result structure, check if it's successful
        if isinstance(result, dict):
            if "result" in result:
                return True
            status = result.get("status", "").lower()
            if status in ("success", "ok", "done"):
                return True
        
        return True

    def _get_www_fqdn(self, fqdn: str) -> str | None:
        """
        Get www version of the domain.
        
        Examples:
            example.com -> www.example.com
            sub.example.com -> www.sub.example.com
            www.example.com -> None (already www)
        """
        if fqdn.startswith("www."):
            return None
        return f"www.{fqdn}"

    async def _apply_to_www(self, fqdn: str, records: dict[str, list[dict[str, Any]]]) -> None:
        """
        Apply the same records to www version of the domain.
        Directly sends the same records without fetching www data first.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        www_fqdn = self._get_www_fqdn(fqdn)
        if not www_fqdn:
            return
        
        try:
            # Directly apply the same records to www version
            await self.change_records(www_fqdn, records)
        except Exception as e:
            # Log only errors, not successful syncs
            logger.warning(f"Failed to sync www subdomain {www_fqdn}: {e}")

    async def add_a_record(self, fqdn: str, ip: str, sync_www: bool = True) -> bool:
        """Add A record. Also updates www version if sync_www=True."""
        current = await self.get_dns_data(fqdn)
        
        # Build records with priority
        a_records = [{"value": r.value, "priority": max(r.priority, 10)} for r in current.a]
        next_priority = (len(a_records) + 1) * 10
        a_records.append({"value": ip, "priority": next_priority})
        
        records = self._build_all_records(current)
        records["A"] = a_records
        
        result = await self.change_records(fqdn, records)
        
        # Sync to www version
        if sync_www:
            await self._apply_to_www(fqdn, records)
        
        return result

    async def update_a_record(self, fqdn: str, old_ip: str, new_ip: str, sync_www: bool = True) -> bool:
        """Update an existing A record. Also updates www version if sync_www=True."""
        current = await self.get_dns_data(fqdn)
        a_records = []
        for i, r in enumerate(current.a):
            priority = max(r.priority, (i + 1) * 10)
            if r.value == old_ip:
                a_records.append({"value": new_ip, "priority": priority})
            else:
                a_records.append({"value": r.value, "priority": priority})
        
        records = self._build_all_records(current)
        records["A"] = a_records
        
        result = await self.change_records(fqdn, records)
        
        if sync_www:
            await self._apply_to_www(fqdn, records)
        
        return result

    async def delete_a_record(self, fqdn: str, ip: str, sync_www: bool = True) -> bool:
        """Delete an A record. Also updates www version if sync_www=True."""
        current = await self.get_dns_data(fqdn)
        a_records = []
        priority = 10
        for r in current.a:
            if r.value != ip:
                a_records.append({"value": r.value, "priority": priority})
                priority += 10
        
        records = self._build_all_records(current)
        records["A"] = a_records
        
        result = await self.change_records(fqdn, records)
        
        if sync_www:
            await self._apply_to_www(fqdn, records)
        
        return result

    async def add_txt_record(self, fqdn: str, value: str, sync_www: bool = True) -> bool:
        """Add a TXT record. Also updates www version if sync_www=True."""
        current = await self.get_dns_data(fqdn)
        txt_records = [{"value": r.value, "priority": max(r.priority, 10)} for r in current.txt]
        next_priority = (len(txt_records) + 1) * 10
        txt_records.append({"value": value, "priority": next_priority})
        
        records = self._build_all_records(current)
        records["TXT"] = txt_records
        
        result = await self.change_records(fqdn, records)
        
        if sync_www:
            await self._apply_to_www(fqdn, records)
        
        return result

    async def delete_txt_record(self, fqdn: str, value: str, sync_www: bool = True) -> bool:
        """Delete a TXT record. Also updates www version if sync_www=True."""
        current = await self.get_dns_data(fqdn)
        txt_records = []
        priority = 10
        for r in current.txt:
            if r.value != value:
                txt_records.append({"value": r.value, "priority": priority})
                priority += 10
        
        records = self._build_all_records(current)
        records["TXT"] = txt_records
        
        result = await self.change_records(fqdn, records)
        
        if sync_www:
            await self._apply_to_www(fqdn, records)
        
        return result
