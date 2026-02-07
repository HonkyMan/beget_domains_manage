"""Pytest configuration and fixtures."""

import pytest
import asyncio
from pathlib import Path
from typing import AsyncGenerator

import aiosqlite


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_db(tmp_path: Path) -> AsyncGenerator[aiosqlite.Connection, None]:
    """Create a temporary test database."""
    db_path = tmp_path / "test.db"
    connection = await aiosqlite.connect(db_path)
    connection.row_factory = aiosqlite.Row
    yield connection
    await connection.close()


@pytest.fixture
def mock_settings():
    """Create mock settings for testing."""
    from app.config import Settings
    
    return Settings(
        telegram_bot_token="test_token",
        admin_chat_id=123456789,
        beget_login="test_login",
        beget_password="test_password",
        log_level="DEBUG",
        data_dir=Path("/tmp/test_data"),
    )
