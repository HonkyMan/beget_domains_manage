"""Beget API client."""

import asyncio
import aiohttp
import json
import logging
from typing import Any
from urllib.parse import urlencode

logger = logging.getLogger(__name__)


class BegetApiError(Exception):
    """Beget API error."""

    def __init__(self, message: str, errors: list[str] | None = None):
        super().__init__(message)
        self.errors = errors or []


class BegetClient:
    """HTTP client for Beget API."""

    BASE_URL = "https://api.beget.com/api"
    DEFAULT_TIMEOUT = 15  # seconds

    def __init__(self, login: str, password: str, timeout: int = DEFAULT_TIMEOUT):
        self.login = login
        self.password = password
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self._session: aiohttp.ClientSession | None = None

    async def __aenter__(self) -> "BegetClient":
        """Enter async context."""
        self._session = aiohttp.ClientSession(timeout=self.timeout)
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Exit async context."""
        if self._session:
            await self._session.close()
            self._session = None

    @property
    def session(self) -> aiohttp.ClientSession:
        """Get active session."""
        if not self._session:
            raise RuntimeError("Client not initialized. Use 'async with' context.")
        return self._session

    def _build_url(self, endpoint: str, params: dict[str, Any] | None = None) -> str:
        """Build API URL with authentication."""
        base_params = {
            "login": self.login,
            "passwd": self.password,
            "output_format": "json",
        }
        if params:
            base_params["input_format"] = "json"
            # Use separators to remove spaces after : and ,
            base_params["input_data"] = json.dumps(params, ensure_ascii=False, separators=(',', ':'))
        
        url = f"{self.BASE_URL}/{endpoint}?{urlencode(base_params)}"
        # Log URL with masked password for debugging
        safe_url = url.replace(self.password, "***MASKED***")
        logger.info(f"API Request URL: {safe_url}")
        logger.debug(f"Login: {self.login}, Password length: {len(self.password)}")
        return url

    async def request(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """Make API request."""
        url = self._build_url(endpoint, params)
        try:
            async with self.session.get(url) as response:
                # Log response details
                content_type = response.headers.get('Content-Type', '')
                logger.info(f"API Response Status: {response.status}, Content-Type: {content_type}")
                
                # Try to parse as JSON regardless of Content-Type
                # (Beget API returns text/html but actually sends JSON)
                try:
                    data = await response.json(content_type=None)
                    logger.debug(f"API Response: {data}")
                except Exception as e:
                    text = await response.text()
                    logger.error(f"Failed to parse response as JSON. First 500 chars: {text[:500]}")
                    raise BegetApiError(
                        f"Invalid API response. Expected JSON but got parsing error: {e}. "
                        f"Please ensure you're using valid API credentials from: "
                        f"https://cp.beget.com/api"
                    )

                # Check top-level error
                if data.get("status") == "error":
                    errors = data.get("errors", [])
                    error_messages = self._extract_error_messages(errors)
                    raise BegetApiError(
                        f"API error: {error_messages or 'Unknown error'}",
                        errors,
                    )
                
                answer = data.get("answer")
                
                # Check nested error in answer
                if isinstance(answer, dict) and answer.get("status") == "error":
                    errors = answer.get("errors", [])
                    error_messages = self._extract_error_messages(errors)
                    raise BegetApiError(
                        f"API error: {error_messages or 'Unknown error'}",
                        errors,
                    )

                return answer
        except asyncio.TimeoutError:
            logger.error(f"API request timeout for endpoint: {endpoint}")
            raise BegetApiError(f"Request timeout. Beget API did not respond within {self.timeout.total}s")
    
    def _extract_error_messages(self, errors: list) -> str:
        """Extract readable error messages from Beget API errors."""
        if not errors:
            return ""
        messages = []
        for err in errors:
            if isinstance(err, dict):
                # Format: {"error_code": "...", "error_text": "..."}
                text = err.get("error_text", err.get("error_code", str(err)))
                messages.append(str(text))  # Ensure it's string
            else:
                messages.append(str(err))  # Convert to string
        return "; ".join(messages)
