"""
Request Validation Middleware
Validates request data, query parameters, and JSON payloads
"""

import re
from functools import wraps

from flask import jsonify, request


class ValidationError(Exception):
    """Custom validation error"""

    pass


def validate_json(*required_fields):
    """
    Decorator to validate required JSON fields in request body

    Usage:
        @app.route('/api/v1/courses', methods=['POST'])
        @validate_json('title', 'description', 'price')
        def create_course():
            data = request.get_json()
            ...

    Args:
        *required_fields: Field names that must be present in JSON
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Check if content-type is JSON
                if not request.is_json:
                    return (
                        jsonify(
                            {
                                "status": "error",
                                "message": "Content-Type must be application/json",
                                "code": "INVALID_CONTENT_TYPE",
                            }
                        ),
                        400,
                    )

                data = request.get_json()

                if not data:
                    return (
                        jsonify(
                            {
                                "status": "error",
                                "message": "Request body cannot be empty",
                                "code": "EMPTY_BODY",
                            }
                        ),
                        400,
                    )

                # Check for required fields
                missing_fields = [field for field in required_fields if field not in data]

                if missing_fields:
                    return (
                        jsonify(
                            {
                                "status": "error",
                                "message": f'Missing required fields: {", ".join(missing_fields)}',
                                "code": "MISSING_FIELDS",
                                "missing_fields": missing_fields,
                            }
                        ),
                        400,
                    )

                return f(*args, **kwargs)

            except ValueError:
                return (
                    jsonify(
                        {
                            "status": "error",
                            "message": "Invalid JSON format",
                            "code": "INVALID_JSON",
                        }
                    ),
                    400,
                )
            except Exception:
                return (
                    jsonify(
                        {
                            "status": "error",
                            "message": "Validation failed",
                            "code": "VALIDATION_FAILED",
                        }
                    ),
                    400,
                )

        return decorated_function

    return decorator


def validate_query_params(**expected_params):
    """
    Decorator to validate query parameters

    Usage:
        @app.route('/api/v1/courses')
        @validate_query_params(
            limit={'type': int, 'default': 20, 'min': 1, 'max': 100},
            offset={'type': int, 'default': 0, 'min': 0},
            search={'type': str}
        )
        def get_courses():
            limit = request.args.get('limit', 20, type=int)
            ...

    Args:
        **expected_params: Parameter definitions with type and validation rules
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                validated_params = {}
                errors = []

                for param_name, param_config in expected_params.items():
                    param_type = param_config.get("type", str)
                    default = param_config.get("default")
                    required = param_config.get("required", False)
                    min_val = param_config.get("min")
                    max_val = param_config.get("max")

                    value = request.args.get(param_name, default)

                    if value is None and required:
                        errors.append(f"{param_name} is required")
                        continue

                    if value is not None:
                        try:
                            if param_type == int:
                                value = int(value)
                            validated_params[param_name] = value

                            # Validate min/max bounds
                            if min_val is not None and value < min_val:
                                errors.append(f"{param_name} must be >= {min_val}")
                            if max_val is not None and value > max_val:
                                errors.append(f"{param_name} must be <= {max_val}")
                        except (ValueError, TypeError):
                            errors.append(f"{param_name} must be of type {param_type.__name__}")
                    else:
                        validated_params[param_name] = default

                if errors:
                    return (
                        jsonify(
                            {
                                "status": "error",
                                "message": "Query parameter validation failed",
                                "code": "INVALID_QUERY_PARAMS",
                                "errors": errors,
                            }
                        ),
                        400,
                    )

                # Attach validated params to request
                request.validated_params = validated_params

                return f(*args, **kwargs)

            except Exception:
                return (
                    jsonify(
                        {
                            "status": "error",
                            "message": "Query parameter validation failed",
                            "code": "PARAM_VALIDATION_FAILED",
                        }
                    ),
                    400,
                )

        return decorated_function

    return decorator


def validate_uuid(param_name):
    """
    Decorator to validate UUID format in route parameters

    Usage:
        @app.route('/api/v1/courses/<course_id>')
        @validate_uuid('course_id')
        def get_course(course_id):
            ...

    Args:
        param_name: Route parameter name to validate
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                uuid_value = kwargs.get(param_name)
                uuid_pattern = (
                    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$|"
                    r"^[0-9a-f]{8}([0-9a-f]{4}){3}[0-9a-f]{12}$|^[a-f0-9]{36}$"
                )

                if uuid_value and not re.match(uuid_pattern, str(uuid_value), re.IGNORECASE):
                    return (
                        jsonify(
                            {
                                "status": "error",
                                "message": f"Invalid UUID format for {param_name}",
                                "code": "INVALID_UUID",
                            }
                        ),
                        400,
                    )

                return f(*args, **kwargs)

            except Exception:
                return (
                    jsonify(
                        {
                            "status": "error",
                            "message": "UUID validation failed",
                            "code": "UUID_VALIDATION_FAILED",
                        }
                    ),
                    400,
                )

        return decorated_function

    return decorator


def validate_email(email):
    """
    Validate email format

    Args:
        email: Email string to validate

    Returns:
        bool: True if valid, False otherwise
    """
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


def validate_phone(phone):
    """
    Validate phone number format

    Args:
        phone: Phone number string

    Returns:
        bool: True if valid, False otherwise
    """
    pattern = r"^\+?1?\d{9,15}$"
    return re.match(pattern, phone.replace(" ", "").replace("-", "")) is not None
