"""Domains module router - assembles all domain submodules."""

from aiogram import Router

from app.modules.domains import domain, subdomain, dns

# Create main domains router
router = Router(name="domains")

# Include submodule routers
router.include_router(domain.router)
router.include_router(subdomain.router)
router.include_router(dns.router)
