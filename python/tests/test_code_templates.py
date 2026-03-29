# tests/test_code_templates.py
"""Tests for cached code template generation."""
import pytest
from app.platform.windows._code_templates import (
    _get_background_click_template,
    _get_background_right_click_template,
    _get_background_long_press_template,
    _get_background_swipe_template,
    _get_background_scroll_template,
    _get_background_hover_template,
    clear_template_cache,
)


class TestBackgroundClickTemplate:
    """Tests for _get_background_click_template."""

    def setup_method(self):
        clear_template_cache()

    def test_template_contains_correct_values(self):
        template = _get_background_click_template(12345, 100, 200)
        assert "hwnd = 12345" in template
        assert "x = 100" in template
        assert "y = 200" in template

    def test_template_is_cached(self):
        template1 = _get_background_click_template(12345, 100, 200)
        template2 = _get_background_click_template(12345, 100, 200)
        assert id(template1) == id(template2), "Template should be cached (same object identity)"

    def test_different_params_give_different_template(self):
        template1 = _get_background_click_template(12345, 100, 200)
        template3 = _get_background_click_template(99999, 50, 50)
        assert id(template1) != id(template3), "Different params should give different template"
        assert "hwnd = 99999" in template3
        assert "x = 50" in template3

    def test_template_contains_win32_imports(self):
        template = _get_background_click_template(12345, 100, 200)
        assert "win32gui" in template
        assert "win32api" in template
        assert "win32con" in template

    def test_template_contains_postmessage_calls(self):
        template = _get_background_click_template(12345, 100, 200)
        assert "WM_LBUTTONDOWN" in template
        assert "WM_LBUTTONUP" in template


class TestBackgroundRightClickTemplate:
    """Tests for _get_background_right_click_template."""

    def setup_method(self):
        clear_template_cache()

    def test_template_contains_correct_values(self):
        template = _get_background_right_click_template(12345, 100, 200)
        assert "hwnd, x, y = 12345, 100, 200" in template

    def test_template_is_cached(self):
        template1 = _get_background_right_click_template(12345, 100, 200)
        template2 = _get_background_right_click_template(12345, 100, 200)
        assert id(template1) == id(template2)

    def test_template_contains_rbutton(self):
        template = _get_background_right_click_template(12345, 100, 200)
        assert "WM_RBUTTONDOWN" in template
        assert "WM_RBUTTONUP" in template


class TestBackgroundLongPressTemplate:
    """Tests for _get_background_long_press_template."""

    def setup_method(self):
        clear_template_cache()

    def test_template_contains_correct_values(self):
        template = _get_background_long_press_template(12345, 100, 200, 500)
        assert "12345" in template
        assert "100" in template
        assert "200" in template
        assert "500" in template

    def test_template_is_cached(self):
        template1 = _get_background_long_press_template(12345, 100, 200, 500)
        template2 = _get_background_long_press_template(12345, 100, 200, 500)
        assert id(template1) == id(template2)

    def test_different_duration_gives_different_template(self):
        template1 = _get_background_long_press_template(12345, 100, 200, 500)
        template2 = _get_background_long_press_template(12345, 100, 200, 1000)
        assert id(template1) != id(template2)


class TestBackgroundSwipeTemplate:
    """Tests for _get_background_swipe_template."""

    def setup_method(self):
        clear_template_cache()

    def test_template_contains_correct_values(self):
        template = _get_background_swipe_template(12345, 10, 20, 30, 40)
        assert "hwnd = 12345" in template
        assert "sx = 10" in template
        assert "sy = 20" in template
        assert "ex = 30" in template
        assert "ey = 40" in template

    def test_template_is_cached(self):
        template1 = _get_background_swipe_template(12345, 10, 20, 30, 40)
        template2 = _get_background_swipe_template(12345, 10, 20, 30, 40)
        assert id(template1) == id(template2)

    def test_template_contains_interpolation_logic(self):
        template = _get_background_swipe_template(12345, 10, 20, 30, 40)
        assert "steps" in template
        assert "WM_MOUSEMOVE" in template


class TestBackgroundScrollTemplate:
    """Tests for _get_background_scroll_template."""

    def setup_method(self):
        clear_template_cache()

    def test_template_contains_correct_values(self):
        template = _get_background_scroll_template(12345, 100, 200, 120)
        assert "hwnd = 12345" in template
        assert "delta = 120" in template
        assert "100, 200" in template

    def test_template_is_cached(self):
        template1 = _get_background_scroll_template(12345, 100, 200, 120)
        template2 = _get_background_scroll_template(12345, 100, 200, 120)
        assert id(template1) == id(template2)

    def test_template_contains_mousewheel(self):
        template = _get_background_scroll_template(12345, 100, 200, 120)
        assert "WM_MOUSEWHEEL" in template


class TestBackgroundHoverTemplate:
    """Tests for _get_background_hover_template."""

    def setup_method(self):
        clear_template_cache()

    def test_template_contains_correct_values(self):
        template = _get_background_hover_template(12345, 100, 200, 500)
        assert "hwnd = 12345" in template
        assert "x = 100" in template
        assert "y = 200" in template
        assert "duration_ms = 500" in template

    def test_template_is_cached(self):
        template1 = _get_background_hover_template(12345, 100, 200, 500)
        template2 = _get_background_hover_template(12345, 100, 200, 500)
        assert id(template1) == id(template2)

    def test_template_contains_mousemove(self):
        template = _get_background_hover_template(12345, 100, 200, 500)
        assert "WM_MOUSEMOVE" in template


class TestCacheManagement:
    """Tests for cache statistics and clearing."""

    def setup_method(self):
        clear_template_cache()

    def test_clear_cache_works(self):
        """Test that clearing cache actually discards cached objects."""
        # Generate a template
        template1 = _get_background_click_template(12345, 100, 200)

        # Verify it is cached (same object identity)
        template2 = _get_background_click_template(12345, 100, 200)
        assert id(template1) == id(template2), "Template should be cached (same object identity)"

        # Clear the cache
        clear_template_cache()

        # Generate again - should be a new object since cache was cleared
        template3 = _get_background_click_template(12345, 100, 200)
        assert id(template1) != id(template3), "After clearing, should generate new template object"

        # Content should still be identical
        assert template1 == template3, "Content should be identical after cache clear"

    def test_cache_independence(self):
        """Verify different template types have independent caches."""
        click = _get_background_click_template(12345, 100, 200)
        right = _get_background_right_click_template(12345, 100, 200)
        assert click != right, "Different template types should produce different code"

    def test_template_output_is_string(self):
        """All templates must return strings."""
        assert isinstance(_get_background_click_template(1, 1, 1), str)
        assert isinstance(_get_background_right_click_template(1, 1, 1), str)
        assert isinstance(_get_background_long_press_template(1, 1, 1, 100), str)
        assert isinstance(_get_background_swipe_template(1, 1, 1, 2, 2), str)
        assert isinstance(_get_background_scroll_template(1, 1, 1, 120), str)
        assert isinstance(_get_background_hover_template(1, 1, 1, 100), str)
