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
    - auth_middleware.py: JWT authentication (@require_auth, @require_role, @require_owner)
    - validators_middleware.py: Request validation (@validate_json, @validate_query_params, @validate_uuid)
    - rate_limiting_middleware.py: Rate limiting (@limit_rate, @limit_payment_attempts, @limit_login_attempts)
    - response_middleware.py: Response formatting (StandardResponse, @format_response)
    - audit_middleware.py: Audit logging (@audit_action, @log_authentication)
    - error_handlers.py: Exception handling
"""

# Authentication exports
from .auth_middleware import (
    require_auth,
    require_role,
    require_owner,
    create_access_token,
    AuthenticationError,
    AuthorizationError
)

# Validation exports
from .validators_middleware import (
    validate_json,
    validate_query_params,
    validate_uuid,
    validate_email,
    validate_phone,
    ValidationError
)

# Rate limiting exports
from .rate_limiting_middleware import (
    limit_rate,
    limit_payment_attempts,
    limit_login_attempts,
    RateLimiter,
    rate_limiter
)

# Response formatting exports
from .response_middleware import (
    StandardResponse,
    format_response,
    paginated_response
)

# Audit logging exports
from .audit_middleware import (
    audit_action,
    log_authentication,
    log_to_database,
    AuditLog
)

__all__ = [
    # Authentication
    'require_auth',
    'require_role',
    'require_owner',
    'create_access_token',
    'AuthenticationError',
    'AuthorizationError',
    
    # Validation
    'validate_json',
    'validate_query_params',
    'validate_uuid',
    'validate_email',
    'validate_phone',
    'ValidationError',
    
    # Rate Limiting
    'limit_rate',
    'limit_payment_attempts',
    'limit_login_attempts',
    'RateLimiter',
    'rate_limiter',
    
    # Response Formatting
    'StandardResponse',
    'format_response',
    'paginated_response',
    
    # Audit Logging
    'audit_action',
    'log_authentication',
    'log_to_database',
    'AuditLog'
]
