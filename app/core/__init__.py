"""Core module - dependency injection and shared utilities."""

from app.core.container import DependencyContainer
from app.core.middleware import DependencyMiddleware

__all__ = ["DependencyContainer", "DependencyMiddleware"]
