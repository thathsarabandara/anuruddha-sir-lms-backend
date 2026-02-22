"""
Common Helper Functions
Utility functions used across the application
"""

from datetime import datetime


def get_page_and_limit(args, default_page_size=20, max_page_size=100):
    """
    Extract pagination parameters from request args

    Args:
        args: Request args (from request.args)
        default_page_size (int): Default items per page
        max_page_size (int): Maximum allowed items per page

    Returns:
        tuple: (page, limit)
    """
    try:
        page = max(1, int(args.get("page", 1)))
        limit = int(args.get("limit", default_page_size))
        limit = min(limit, max_page_size)
        limit = max(1, limit)
        return page, limit
    except (ValueError, TypeError):
        return 1, default_page_size


def get_offset_from_page(page, limit):
    """
    Calculate offset from page and limit

    Args:
        page (int): Page number (1-indexed)
        limit (int): Items per page

    Returns:
        int: Offset for database query
    """
    return (page - 1) * limit


def calculate_total_pages(total_items, limit):
    """
    Calculate total pages from items count

    Args:
        total_items (int): Total number of items
        limit (int): Items per page

    Returns:
        int: Total pages
    """
    return (total_items + limit - 1) // limit


def safe_int(value, default=None):
    """
    Safely convert value to integer

    Args:
        value: Value to convert
        default: Default value if conversion fails

    Returns:
        int or default: Converted value or default
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_str(value, default=""):
    """
    Safely convert value to string

    Args:
        value: Value to convert
        default: Default value if conversion fails

    Returns:
        str: Converted value or default
    """
    try:
        return str(value).strip()
    except Exception:
        return default


def safe_bool(value, default=False):
    """
    Safely convert value to boolean

    Args:
        value: Value to convert
        default: Default value if conversion fails

    Returns:
        bool: Converted value or default
    """
    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes", "on")

    return default


def generate_slug(text):
    """
    Generate URL-friendly slug from text

    Args:
        text (str): Text to slugify

    Returns:
        str: Slugified text
    """
    import re

    # Convert to lowercase
    slug = text.lower().strip()

    # Replace spaces and underscores with hyphens
    slug = re.sub(r"[\s_]+", "-", slug)

    # Remove non-alphanumeric characters (except hyphens)
    slug = re.sub(r"[^a-z0-9-]", "", slug)

    # Remove consecutive hyphens
    slug = re.sub(r"-+", "-", slug)

    # Remove leading/trailing hyphens
    slug = slug.strip("-")

    return slug


def format_datetime(dt, format_str="%Y-%m-%d %H:%M:%S"):
    """
    Format datetime object to string

    Args:
        dt (datetime): Datetime object
        format_str (str): Format string

    Returns:
        str: Formatted datetime string
    """
    if isinstance(dt, datetime):
        return dt.strftime(format_str)
    return str(dt)


def get_time_ago(dt):
    """
    Get human-readable time difference

    Args:
        dt (datetime): Datetime to compare

    Returns:
        str: Time difference in human-readable format
    """
    if not isinstance(dt, datetime):
        return "unknown"

    now = datetime.utcnow()
    diff = now - dt

    seconds = int(diff.total_seconds())

    if seconds < 60:
        return f"{seconds} seconds ago"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes} minutes ago"
    elif seconds < 86400:
        hours = seconds // 3600
        return f"{hours} hours ago"
    else:
        days = seconds // 86400
        return f"{days} days ago"
