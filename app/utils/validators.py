"""
Validators
Input validation utility functions
"""

import re

from app.exceptions import ValidationError


def validate_email(email):
    """
    Validate email format

    Args:
        email (str): Email address to validate

    Returns:
        str: Valid email

    Raises:
        ValidationError: If email is invalid
    """
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

    if not email or not re.match(pattern, email):
        raise ValidationError("Invalid email format")

    return email


def validate_password(password, min_length=8):
    """
    Validate password strength

    Args:
        password (str): Password to validate
        min_length (int): Minimum password length

    Returns:
        str: Valid password

    Raises:
        ValidationError: If password is weak
    """
    if not password or len(password) < min_length:
        raise ValidationError(f"Password must be at least {min_length} characters")

    if not re.search(r"[A-Z]", password):
        raise ValidationError("Password must contain uppercase letter")

    if not re.search(r"[a-z]", password):
        raise ValidationError("Password must contain lowercase letter")

    if not re.search(r"[0-9]", password):
        raise ValidationError("Password must contain digit")

    return password


def validate_username(username):
    """
    Validate username format

    Args:
        username (str): Username to validate

    Returns:
        str: Valid username

    Raises:
        ValidationError: If username is invalid
    """
    if not username or len(username) < 3 or len(username) > 50:
        raise ValidationError("Username must be 3-50 characters long")

    if not re.match(r"^[a-zA-Z0-9_-]+$", username):
        raise ValidationError("Username can only contain letters, numbers, underscores, hyphens")

    return username


def validate_phone(phone):
    """
    Validate phone number format (supports Sri Lankan phone numbers)

    Accepts Sri Lankan phone formats:
    - 10 digits: 9471928289 (with optional country code prefix)
    - With +94: +94 71928289 or +94771928289
    - With leading 0: 0771928289
    - With separators: 071-792-8289 or 071 792 8289

    Args:
        phone (str): Phone number to validate

    Returns:
        str: Normalized phone number (without separators, 10 digits)

    Raises:
        ValidationError: If phone is invalid
    """
    if not phone or not isinstance(phone, str):
        raise ValidationError("Phone number must be a non-empty string")

    # Remove common separators and spaces
    phone_clean = re.sub(r"[\s\-\(\)\.+]", "", phone)

    # Remove country code +94 or 0094 prefix if present
    if phone_clean.startswith("0094"):
        phone_clean = phone_clean[4:]  # Remove "0094"
    elif phone_clean.startswith("94"):
        phone_clean = phone_clean[2:]  # Remove "94"
    elif phone_clean.startswith("+94"):
        phone_clean = phone_clean[3:]  # Remove "+94"

    # Remove leading 0 if present (for numbers like 0771928289)
    if phone_clean.startswith("0"):
        phone_clean = phone_clean[1:]

    # Validate: must be 9 digits after normalization (SL format without country code)
    if not phone_clean.isdigit() or len(phone_clean) != 9:
        raise ValidationError(
            "Invalid Sri Lankan phone format. Expected 10 digits (e.g., 0771928289) "
            "or with country code (e.g., +94771928289)"
        )

    # Validate that it starts with valid Sri Lankan mobile prefixes (7x for mobile)
    # Sri Lanka mobile prefixes: 70, 71, 72, 73, 74, 75, 76, 77, 78, 79 (Dialog, Airtel, Hutch, Mobitel, SLT)
    if not phone_clean.startswith(("7", "1")):  # Allow 7x or 1x (for legacy/special numbers)
        raise ValidationError(
            "Invalid Sri Lankan mobile prefix. Number must start with 7x (e.g., 0771928289)"
        )

    # Return normalized 10-digit format with leading 0
    return f"0{phone_clean}"


def validate_string(value, min_length=1, max_length=255, field_name="Field"):
    """
    Validate string field

    Args:
        value (str): String to validate
        min_length (int): Minimum length
        max_length (int): Maximum length
        field_name (str): Field name for error message

    Returns:
        str: Valid string

    Raises:
        ValidationError: If string is invalid
    """
    if not value or not isinstance(value, str):
        raise ValidationError(f"{field_name} must be a non-empty string")

    if len(value) < min_length or len(value) > max_length:
        raise ValidationError(f"{field_name} must be {min_length}-{max_length} characters")

    return value.strip()


def validate_integer(value, min_value=None, max_value=None, field_name="Value"):
    """
    Validate integer field

    Args:
        value: Value to validate
        min_value (int): Minimum value
        max_value (int): Maximum value
        field_name (str): Field name for error message

    Returns:
        int: Valid integer

    Raises:
        ValidationError: If value is invalid
    """
    try:
        int_value = int(value)
    except (TypeError, ValueError):
        raise ValidationError(f"{field_name} must be an integer")

    if min_value is not None and int_value < min_value:
        raise ValidationError(f"{field_name} must be at least {min_value}")

    if max_value is not None and int_value > max_value:
        raise ValidationError(f"{field_name} must be at most {max_value}")

    return int_value


def validate_enum(value, allowed_values, field_name="Field"):
    """
    Validate enum/choice field

    Args:
        value: Value to validate
        allowed_values (list): List of allowed values
        field_name (str): Field name for error message

    Returns:
        str: Valid value

    Raises:
        ValidationError: If value not in allowed values
    """
    if value not in allowed_values:
        raise ValidationError(f'{field_name} must be one of: {", ".join(map(str, allowed_values))}')

    return value
