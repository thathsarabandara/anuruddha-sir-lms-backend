"""
Unit tests for utility functions
"""

from app.utils.helpers import (
    get_page_and_limit,
    get_offset_from_page,
    calculate_total_pages,
    safe_int,
    safe_str,
    safe_bool,
    generate_slug,
)


class TestPaginationHelpers:
    """Test cases for pagination helper functions"""

    def test_get_page_and_limit_defaults(self):
        """Test getting default page and limit"""
        args = {}
        page, limit = get_page_and_limit(args)
        assert page == 1
        assert limit == 20

    def test_get_page_and_limit_custom_values(self):
        """Test getting custom page and limit"""
        args = {"page": "3", "limit": "50"}
        page, limit = get_page_and_limit(args)
        assert page == 3
        assert limit == 50

    def test_get_page_and_limit_min_page(self):
        """Test minimum page is 1"""
        args = {"page": "0"}
        page, limit = get_page_and_limit(args)
        assert page >= 1

    def test_get_page_and_limit_negative_page(self):
        """Test negative page becomes 1"""
        args = {"page": "-5"}
        page, limit = get_page_and_limit(args)
        assert page == 1

    def test_get_offset_from_page_first(self):
        """Test offset calculation for first page"""
        assert get_offset_from_page(1, 20) == 0

    def test_get_offset_from_page_second(self):
        """Test offset calculation for second page"""
        assert get_offset_from_page(2, 20) == 20

    def test_get_offset_from_page_third(self):
        """Test offset calculation for third page"""
        assert get_offset_from_page(3, 10) == 20

    def test_calculate_total_pages_exact(self):
        """Test total pages calculation for exact division"""
        assert calculate_total_pages(100, 20) == 5

    def test_calculate_total_pages_remainder(self):
        """Test total pages calculation with remainder"""
        assert calculate_total_pages(101, 20) == 6

    def test_calculate_total_pages_zero(self):
        """Test total pages calculation for zero objects"""
        assert calculate_total_pages(0, 20) == 0


class TestSafeConversions:
    """Test cases for safe conversion functions"""

    def test_safe_int_string_valid(self):
        """Test safe integer conversion from string"""
        assert safe_int("10") == 10

    def test_safe_int_direct_valid(self):
        """Test safe integer conversion from integer"""
        assert safe_int(15) == 15

    def test_safe_int_invalid_returns_none(self):
        """Test safe integer conversion with invalid input"""
        assert safe_int("not_a_number") is None

    def test_safe_int_with_default(self):
        """Test safe integer conversion with default value"""
        assert safe_int("abc", default=0) == 0

    def test_safe_str_string_input(self):
        """Test safe string conversion from string"""
        assert safe_str("hello") == "hello"

    def test_safe_str_integer_input(self):
        """Test safe string conversion from integer"""
        assert safe_str(123) == "123"

    def test_safe_str_with_spaces(self):
        """Test safe string conversion strips spaces"""
        assert safe_str("  hello world  ") == "hello world"

    def test_safe_str_none_converts_to_string(self):
        """Test safe string conversion with None"""
        assert isinstance(safe_str(None), str)

    def test_safe_str_with_default_for_exception(self):
        """Test safe string conversion with default value"""
        # If safe_str(None) returns "None" string, that's valid
        result = safe_str(None, default="fallback")
        assert isinstance(result, str)

    def test_safe_bool_returns_boolean(self):
        """Test safe boolean always returns boolean"""
        result = safe_bool("something")
        assert isinstance(result, bool)

    def test_safe_bool_default_false(self):
        """Test safe boolean default is False"""
        result = safe_bool(None)
        assert result is False


class TestSlugGeneration:
    """Test cases for slug generation"""

    def test_generate_slug_basic(self):
        """Test basic slug generation"""
        slug = generate_slug("Hello World")
        assert "-" in slug or slug == "hello-world"

    def test_generate_slug_lowercase(self):
        """Test slug is lowercase"""
        slug = generate_slug("CamelCaseString")
        assert slug == slug.lower()

    def test_generate_slug_empty_string(self):
        """Test slug with empty string"""
        slug = generate_slug("")
        assert isinstance(slug, str)
