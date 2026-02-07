"""Tests for pagination utility."""

import pytest
from app.utils.pagination import Paginator, Page


class TestPaginator:
    """Tests for Paginator class."""
    
    def test_empty_list(self):
        """Test pagination with empty list."""
        paginator = Paginator([], page_size=5)
        page = paginator.get_page(1)
        
        assert page.items == []
        assert page.page == 1
        assert page.total_pages == 1
        assert page.total_items == 0
        assert not page.has_prev
        assert not page.has_next
    
    def test_single_page(self):
        """Test list that fits in one page."""
        items = [1, 2, 3]
        paginator = Paginator(items, page_size=5)
        page = paginator.get_page(1)
        
        assert page.items == [1, 2, 3]
        assert page.page == 1
        assert page.total_pages == 1
        assert page.total_items == 3
        assert not page.has_prev
        assert not page.has_next
    
    def test_multiple_pages(self):
        """Test list that spans multiple pages."""
        items = list(range(1, 12))  # 11 items
        paginator = Paginator(items, page_size=5)
        
        # First page
        page1 = paginator.get_page(1)
        assert page1.items == [1, 2, 3, 4, 5]
        assert page1.page == 1
        assert page1.total_pages == 3
        assert not page1.has_prev
        assert page1.has_next
        
        # Second page
        page2 = paginator.get_page(2)
        assert page2.items == [6, 7, 8, 9, 10]
        assert page2.page == 2
        assert page2.has_prev
        assert page2.has_next
        
        # Third page (partial)
        page3 = paginator.get_page(3)
        assert page3.items == [11]
        assert page3.page == 3
        assert page3.has_prev
        assert not page3.has_next
    
    def test_page_clamping(self):
        """Test that invalid page numbers are clamped."""
        items = [1, 2, 3]
        paginator = Paginator(items, page_size=5)
        
        # Page 0 -> 1
        page = paginator.get_page(0)
        assert page.page == 1
        
        # Page 100 -> 1 (max)
        page = paginator.get_page(100)
        assert page.page == 1
    
    def test_exact_page_boundary(self):
        """Test list that exactly fills pages."""
        items = list(range(1, 11))  # 10 items
        paginator = Paginator(items, page_size=5)
        
        assert paginator.total_pages == 2
        
        page1 = paginator.get_page(1)
        assert page1.items == [1, 2, 3, 4, 5]
        
        page2 = paginator.get_page(2)
        assert page2.items == [6, 7, 8, 9, 10]
