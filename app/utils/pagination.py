"""Pagination utility for inline keyboards."""

from typing import TypeVar, Generic, Sequence
from dataclasses import dataclass
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

T = TypeVar("T")


@dataclass
class Page(Generic[T]):
    """Represents a page of items."""
    
    items: list[T]
    page: int
    total_pages: int
    total_items: int
    has_prev: bool
    has_next: bool


class Paginator(Generic[T]):
    """Paginator for lists of items.
    
    Usage:
        paginator = Paginator(items, page_size=5)
        page = paginator.get_page(1)
        
        for item in page.items:
            # render item
        
        if page.has_prev or page.has_next:
            # add navigation buttons
    """
    
    def __init__(self, items: Sequence[T], page_size: int = 10):
        self.items = list(items)
        self.page_size = page_size
        self.total_items = len(self.items)
        self.total_pages = max(1, (self.total_items + page_size - 1) // page_size)
    
    def get_page(self, page: int) -> Page[T]:
        """Get a specific page of items.
        
        Args:
            page: 1-based page number
            
        Returns:
            Page object with items and metadata
        """
        # Clamp page to valid range
        page = max(1, min(page, self.total_pages))
        
        start = (page - 1) * self.page_size
        end = start + self.page_size
        items = self.items[start:end]
        
        return Page(
            items=items,
            page=page,
            total_pages=self.total_pages,
            total_items=self.total_items,
            has_prev=page > 1,
            has_next=page < self.total_pages,
        )


def add_pagination_buttons(
    builder: InlineKeyboardBuilder,
    page: int,
    total_pages: int,
    callback_prefix: str,
) -> None:
    """Add pagination buttons to a keyboard builder.
    
    Adds a row with prev/next buttons like:
    [<< Prev] [1/5] [Next >>]
    
    Args:
        builder: The keyboard builder to add buttons to
        page: Current page number (1-based)
        total_pages: Total number of pages
        callback_prefix: Prefix for callback data (e.g., "domains:page")
    """
    if total_pages <= 1:
        return
    
    buttons = []
    
    # Previous button
    if page > 1:
        buttons.append(
            InlineKeyboardButton(
                text="<< Prev",
                callback_data=f"{callback_prefix}:{page - 1}",
            )
        )
    else:
        buttons.append(
            InlineKeyboardButton(
                text=" ",  # Placeholder for alignment
                callback_data="noop",
            )
        )
    
    # Page indicator
    buttons.append(
        InlineKeyboardButton(
            text=f"{page}/{total_pages}",
            callback_data="noop",
        )
    )
    
    # Next button
    if page < total_pages:
        buttons.append(
            InlineKeyboardButton(
                text="Next >>",
                callback_data=f"{callback_prefix}:{page + 1}",
            )
        )
    else:
        buttons.append(
            InlineKeyboardButton(
                text=" ",  # Placeholder for alignment
                callback_data="noop",
            )
        )
    
    builder.row(*buttons)
