"""Beget API type definitions."""

from pydantic import BaseModel


class BegetResponse(BaseModel):
    """Base Beget API response."""

    status: str
    answer: dict | list | None = None
    errors: list[str] | None = None


class Domain(BaseModel):
    """Domain information."""

    id: int
    fqdn: str


class Subdomain(BaseModel):
    """Subdomain information."""

    id: int
    fqdn: str


class DnsRecord(BaseModel):
    """DNS record."""

    value: str
    priority: int = 0


class DnsData(BaseModel):
    """DNS data for a domain."""

    fqdn: str
    dns_ip: list[str] = []
    dns: list[str] = []
    a: list[DnsRecord] = []
    aaaa: list[DnsRecord] = []
    mx: list[DnsRecord] = []
    txt: list[DnsRecord] = []
    cname: list[DnsRecord] = []
    ns: list[DnsRecord] = []


class DnsChangeRequest(BaseModel):
    """Request to change DNS records."""

    fqdn: str
    a: list[dict] | None = None
    aaaa: list[dict] | None = None
    mx: list[dict] | None = None
    txt: list[dict] | None = None
    cname: list[dict] | None = None
    ns: list[dict] | None = None
