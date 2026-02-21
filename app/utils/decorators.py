"""
Decorators
Custom decorators for routes and services
"""

from functools import wraps
from flask import request
from app.utils.response import error_response


def validate_json(*required_fields):
    """
    Decorator to validate JSON request has required fields
    
    Args:
        *required_fields: Field names that must be present in JSON body
    
    Usage:
        @bp.route('/users', methods=['POST'])
        @validate_json('email', 'password')
        def create_user():
            data = request.get_json()
            # email and password are guaranteed to exist
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            data = request.get_json()
            
            if not data:
                return error_response('Request body must be JSON', 400)
            
            missing_fields = [
                field for field in required_fields 
                if field not in data
            ]
            
            if missing_fields:
                return error_response(
                    f'Missing required fields: {", ".join(missing_fields)}',
                    400
                )
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def handle_exceptions(func):
    """
    Decorator to handle exceptions and return proper error responses
    
    Usage:
        @bp.route('/users/<id>')
        @handle_exceptions
        def get_user(id):
            raise ValidationError('Invalid user ID')
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            from app.exceptions import LMSException
            
            if isinstance(e, LMSException):
                return error_response(e.message, e.status_code)
            
            # Log unexpected exceptions
            import logging
            logging.error(f'Unexpected error: {str(e)}', exc_info=True)
            
            return error_response('Internal server error', 500)
    
    return wrapper


def require_json():
    """
    Decorator to ensure request is JSON
    
    Usage:
        @bp.route('/endpoint', methods=['POST'])
        @require_json()
        def create_something():
            data = request.get_json()
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not request.is_json:
                return error_response('Request must be JSON', 400)
            return func(*args, **kwargs)
        return wrapper
    return decorator
