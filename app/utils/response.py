"""
Response helper utilities for consistent API responses
"""

from datetime import datetime
import logging

from flask import jsonify

logger = logging.getLogger(__name__)


def sanitize_error_message(error_str, error_type=None):
    """
    Sanitize error messages to prevent backend details from leaking to frontend.
    
    Maps backend exceptions to user-friendly messages while logging actual errors.
    
    Args:
        error_str: Original error message from backend
        error_type: Type of exception for more specific sanitization
        
    Returns:
        str: User-friendly error message
    """
    error_str = str(error_str).lower()
    
    if any(keyword in error_str for keyword in ["sqlalchemy", "operational error", "database", "mysql", "postgres"]):
        return "A database error occurred. Please try again later."
    
    if any(keyword in error_str for keyword in ["connection", "timeout", "network"]):
        return "Connection error. Please check your internet and try again."
    
    if any(keyword in error_str for keyword in ["invalid", "incorrect", "wrong", "unauthorized"]):
        if "password" in error_str:
            return "Invalid email or password."
        if "token" in error_str:
            return "Your session has expired. Please log in again."
    
    if any(keyword in error_str for keyword in ["required", "format", "invalid", "must", "validation"]):
        return error_str  
    
    if "rate limit" in error_str or "too many" in error_str:
        return "Too many attempts. Please try again later."
    
    if any(keyword in error_str for keyword in ["already exists", "already registered", "duplicate"]):
        if "email" in error_str:
            return "This email is already registered. Please log in or use a different email."
        if "phone" in error_str:
            return "This phone number is already registered. Please use a different phone number."
    
    if any(keyword in error_str for keyword in ["banned", "suspended", "disabled", "inactive"]):
        return error_str
    
    return error_str


def success_response(data=None, message="Success", status_code=200):
    """
    Format a successful API response

    Args:
        data: Response data/payload
        message: Success message
        status_code: HTTP status code

    Returns:
        Flask JSON response
    """
    response = {
        "status": "success",
        "message": message,
        "timestamp": datetime.utcnow().isoformat(),
        "data": data,
    }
    return jsonify(response), status_code


def error_response(message="Error", status_code=400, errors=None):
    """
    Format an error API response
    
    Automatically sanitizes error messages to prevent backend details leaking.

    Args:
        message: Error message (will be sanitized)
        status_code: HTTP status code
        errors: Additional error details (will be sanitized)

    Returns:
        Flask JSON response
    """
    # Sanitize the main error message
    user_friendly_message = sanitize_error_message(message)
    
    # Sanitize individual error details if provided
    if errors:
        if isinstance(errors, dict):
            errors = {key: sanitize_error_message(str(val)) for key, val in errors.items()}
        elif isinstance(errors, list):
            errors = [sanitize_error_message(str(err)) for err in errors]
    
    response = {
        "status": "error",
        "message": user_friendly_message,
        "timestamp": datetime.utcnow().isoformat(),
    }
    if errors:
        response["errors"] = errors

    return jsonify(response), status_code


def paginated_response(data, total, page, page_size, status_code=200):
    """
    Format a paginated API response

    Args:
        data: List of items
        total: Total number of items
        page: Current page number
        page_size: Items per page
        status_code: HTTP status code

    Returns:
        Flask JSON response
    """
    response = {
        "status": "success",
        "timestamp": datetime.utcnow().isoformat(),
        "data": data,
        "pagination": {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        },
    }
    return jsonify(response), status_code
