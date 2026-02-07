"""Beget API client manager - singleton pattern for connection pooling."""

import aiohttp
from contextlib import asynccontextmanager
from typing import AsyncIterator

from app.services.beget.client import BegetClient


class BegetClientManager:
    """Manager for BegetClient with connection pooling.
    
    Instead of creating a new aiohttp session for each request,
    this manager maintains a single session that is reused across
    all requests during the application lifecycle.
    """
    
    def __init__(self, login: str, password: str, timeout: int = 15):
        self.login = login
        self.password = password
        self.timeout = timeout
        self._session: aiohttp.ClientSession | None = None
    
    async def start(self) -> None:
        """Initialize the shared aiohttp session."""
        if self._session is None:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )
    
    async def stop(self) -> None:
        """Close the shared aiohttp session."""
        if self._session:
            await self._session.close()
            self._session = None
    
    @asynccontextmanager
    async def client(self) -> AsyncIterator[BegetClient]:
        """Get a BegetClient instance using the shared session.
        
        Usage:
            async with manager.client() as client:
                domains = await client.request("domain/getList")
        """
        if self._session is None:
            await self.start()
        
        # Create client that uses our managed session
        beget_client = BegetClient(
            login=self.login,
            password=self.password,
            timeout=self.timeout,
        )
        # Inject our managed session
        beget_client._session = self._session
        
        try:
            yield beget_client
        finally:
            # Don't close the session - it's managed by us
            beget_client._session = None
    
    async def __aenter__(self) -> "BegetClientManager":
        """Async context manager entry."""
        await self.start()
        return self
    
    async def __aexit__(self, *args) -> None:
        """Async context manager exit."""
        await self.stop()
