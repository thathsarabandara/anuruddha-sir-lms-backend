"""
Response helper utilities for consistent API responses
"""

from flask import jsonify
from datetime import datetime

def success_response(data=None, message='Success', status_code=200):
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
        'status': 'success',
        'message': message,
        'timestamp': datetime.utcnow().isoformat(),
        'data': data
    }
    return jsonify(response), status_code

def error_response(message='Error', status_code=400, errors=None):
    """
    Format an error API response
    
    Args:
        message: Error message
        status_code: HTTP status code
        errors: Additional error details
    
    Returns:
        Flask JSON response
    """
    response = {
        'status': 'error',
        'message': message,
        'timestamp': datetime.utcnow().isoformat(),
    }
    if errors:
        response['errors'] = errors
    
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
        'status': 'success',
        'timestamp': datetime.utcnow().isoformat(),
        'data': data,
        'pagination': {
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': (total + page_size - 1) // page_size
        }
    }
    return jsonify(response), status_code
