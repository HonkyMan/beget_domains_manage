"""Tests for DependencyContainer."""

import pytest
from app.core.container import DependencyContainer


class TestDependencyContainer:
    """Tests for DependencyContainer class."""
    
    def test_is_admin_returns_true_for_admin(self, mock_settings):
        """Test is_admin returns True for admin chat_id."""
        container = DependencyContainer(
            settings=mock_settings,
            db=None,
            chats_repo=None,
            logs_repo=None,
            permissions_repo=None,
            permission_checker=None,
            beget_manager=None,
            admin_chat_id=123456789,
        )
        
        assert container.is_admin(123456789) is True
    
    def test_is_admin_returns_false_for_non_admin(self, mock_settings):
        """Test is_admin returns False for non-admin chat_id."""
        container = DependencyContainer(
            settings=mock_settings,
            db=None,
            chats_repo=None,
            logs_repo=None,
            permissions_repo=None,
            permission_checker=None,
            beget_manager=None,
            admin_chat_id=123456789,
        )
        
        assert container.is_admin(987654321) is False
    
    def test_container_is_frozen(self, mock_settings):
        """Test that container is immutable (frozen dataclass)."""
        container = DependencyContainer(
            settings=mock_settings,
            db=None,
            chats_repo=None,
            logs_repo=None,
            permissions_repo=None,
            permission_checker=None,
            beget_manager=None,
            admin_chat_id=123456789,
        )
        
        with pytest.raises(AttributeError):
            container.admin_chat_id = 111111111
