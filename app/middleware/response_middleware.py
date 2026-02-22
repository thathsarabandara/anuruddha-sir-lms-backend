"""
Response Formatter Middleware
Standardizes all API responses to consistent format
"""

from datetime import datetime
from functools import wraps

from flask import jsonify


class StandardResponse:
    """
    Standard response wrapper for all API endpoints

    Usage:
        return StandardResponse.success('User created', {'user_id': '123'}, 201)
    """

    @staticmethod
    def success(message=None, data=None, status_code=200, pagination=None):
        """Success response"""
        response = {
            "status": "success",
            "message": message,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        }

        if pagination:
            response["pagination"] = pagination

        return response, status_code

    @staticmethod
    def error(message, code="ERROR", status_code=400, details=None):
        """Error response"""
        response = {
            "status": "error",
            "message": message,
            "code": code,
            "timestamp": datetime.utcnow().isoformat(),
        }

        if details:
            response["details"] = details

        return response, status_code

    @staticmethod
    def validation_error(message, errors=None, status_code=422):
        """Validation error response"""
        response = {
            "status": "error",
            "message": message or "Validation failed",
            "code": "VALIDATION_ERROR",
            "errors": errors or {},
            "timestamp": datetime.utcnow().isoformat(),
        }

        return response, status_code


def format_response(f):
    """
    Decorator to ensure all responses are JSON with standard format

    Usage:
        @app.route('/api/v1/users')
        @format_response
        def create_user():
            return StandardResponse.success('User created', {'user_id': '123'}, 201)
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            result = f(*args, **kwargs)

            # If result is already a tuple (response, status_code), use it
            if isinstance(result, tuple):
                response, status_code = result
                return jsonify(response), status_code

            # If result is a dict, wrap it in success response
            if isinstance(result, dict):
                return (
                    jsonify(
                        {
                            "status": "success",
                            "data": result,
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                    ),
                    200,
                )

            # Otherwise return as is
            return result

        except Exception as e:
            # Catch unhandled exceptions and return error response
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": str(e),
                        "code": "INTERNAL_ERROR",
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                ),
                500,
            )

    return decorated_function


def paginated_response(limit=20, offset=0):
    """
    Create paginated response object

    Args:
        limit: Items per page
        offset: Starting item index
        total: Total number of items
    """
    return {
        "limit": limit,
        "offset": offset,
        "total": 0,  # Should be set by caller
        "has_more": False,
    }
