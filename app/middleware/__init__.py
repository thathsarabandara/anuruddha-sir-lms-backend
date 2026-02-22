"""
Middleware Module
Request/response interceptors and middleware components

Pattern:
    - Middleware for authentication verification
    - Error handling and transformations
    - Request logging and auditing
    - CORS handling
    - Rate limiting
    - Request validation
    - Response formatting

Files:
    - auth_middleware.py: JWT authentication
      (@require_auth, @require_role, @require_owner)
    - validators_middleware.py: Request validation
      (@validate_json, @validate_query_params, @validate_uuid)
    - rate_limiting_middleware.py: Rate limiting
      (@limit_rate, @limit_payment_attempts, @limit_login_attempts)
    - response_middleware.py: Response formatting
      (StandardResponse, @format_response)
    - audit_middleware.py: Audit logging
      (@audit_action, @log_authentication)
    - error_handlers.py: Exception handling
"""

# Audit logging exports
from .audit_middleware import (
    AuditLog,
    audit_action,
    log_authentication,
    log_to_database,
)

# Authentication exports
from .auth_middleware import (
    AuthenticationError,
    AuthorizationError,
    create_access_token,
    require_auth,
    require_owner,
    require_role,
)

# CORS exports
from .cors_middleware import (
    add_security_headers,
    configure_cors,
    require_origin,
    setup_cors_error_handler,
)

# Rate limiting exports
from .rate_limiting_middleware import (
    RateLimiter,
    limit_login_attempts,
    limit_payment_attempts,
    limit_rate,
    rate_limiter,
)

# Response formatting exports
from .response_middleware import StandardResponse, format_response, paginated_response

# Validation exports
from .validators_middleware import (
    ValidationError,
    validate_email,
    validate_json,
    validate_phone,
    validate_query_params,
    validate_uuid,
)

__all__ = [
    # Authentication
    "require_auth",
    "require_role",
    "require_owner",
    "create_access_token",
    "AuthenticationError",
    "AuthorizationError",
    # Validation
    "validate_json",
    "validate_query_params",
    "validate_uuid",
    "validate_email",
    "validate_phone",
    "ValidationError",
    # Rate Limiting
    "limit_rate",
    "limit_payment_attempts",
    "limit_login_attempts",
    "RateLimiter",
    "rate_limiter",
    # Response Formatting
    "StandardResponse",
    "format_response",
    "paginated_response",
    # Audit Logging
    "audit_action",
    "log_authentication",
    "log_to_database",
    "AuditLog",
    # CORS
    "configure_cors",
    "setup_cors_error_handler",
    "require_origin",
    "add_security_headers",
]
