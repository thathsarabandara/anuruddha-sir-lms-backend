"""
Authentication Middleware
Handles JWT authentication, authorization, and role-based access control via cookies
"""

from datetime import datetime, timedelta
from functools import wraps

import jwt
from flask import current_app, jsonify, request

from app.models import User
from app.models.auth.access_token import AccessToken
from app.models.auth.user_account_status import UserAccountStatus
from app.services.auth.token_verification_service import TokenVerificationService


class AuthenticationError(Exception):
    """Custom authentication error"""

    pass


class AuthorizationError(Exception):
    """Custom authorization error"""

    pass


def verify_token(token):
    """
    Verify JWT token from request cookies

    Args:
        token: JWT token string

    Returns:
        dict: Decoded token payload

    Raises:
        AuthenticationError: If token is invalid or expired
    """
    try:
        secret_key = current_app.config.get("SECRET_KEY", "your-secret-key")
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Token has expired")
    except jwt.InvalidTokenError:
        raise AuthenticationError("Invalid token")
    except Exception as e:
        raise AuthenticationError(f"Token verification failed: {str(e)}")


def require_auth(f):
    """
    Decorator to require authentication via JWT in cookies
    Checks for valid, non-expired JWT token

    Usage:
        @app.route('/api/v1/user/profile')
        @require_auth
        def get_profile():
            user_id = request.user_id
            ...
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # Get token from cookies
            token = request.cookies.get("access_token")
            refresh_token = request.cookies.get("refresh_token")
            new_access_token = None

            if not token:
                return (
                    jsonify(
                        {
                            "status": "error",
                            "message": "Authentication required",
                            "code": "MISSING_TOKEN",
                        }
                    ),
                    401,
                )

            # Verify token signature
            payload = verify_token(token)

            # Check token revocation status in database
            token_record = AccessToken.query.filter_by(token=token).first()
            if token_record and not token_record.is_valid():
                # Token is either revoked or expired
                if token_record.is_revoked:
                    raise AuthenticationError(
                        "Access token has been revoked. Please login again."
                    )
                elif token_record.is_expired():
                    # Token is expired, try to refresh if refresh token is available
                    if refresh_token:
                        try:
                            token_verification_service = TokenVerificationService()
                            verification_result = token_verification_service.verify_token(token, refresh_token)
                            if verification_result.get("new_access_token"):
                                # Got new access token - update payload and token for use
                                new_access_token = verification_result["new_access_token"]
                                payload = verify_token(new_access_token)
                            else:
                                raise AuthenticationError("Token refresh failed. Please login again.")
                        except AuthenticationError:
                            raise AuthenticationError("Token expired and refresh failed. Please login again.")
                    else:
                        raise AuthenticationError("Token has expired. Please login again.")

            user = User.query.filter_by(user_id=payload.get("user_id")).first()
            if not user:
                raise AuthenticationError("User not found")
            
            user_status = UserAccountStatus.query.filter_by(user_id=user.user_id).first() if user else None
            if not user_status or not user_status.is_active or user_status.is_banned:
                raise AuthenticationError("User account is not active")
            

            # Attach user info to request context
            request.user_id = payload.get("user_id")
            request.user_role = payload.get("role")
            request.user_email = payload.get("email")
            request.token_payload = payload
            # Store new token if it was refreshed
            request.new_access_token = new_access_token

            # Execute the original function
            response = f(*args, **kwargs)
            
            # If response is a tuple (response, status_code), extract response object
            if isinstance(response, tuple):
                response_body, status_code = response if len(response) >= 2 else (response[0], 200)
                if isinstance(response_body, dict):
                    response = jsonify(response_body)
                    response.status_code = status_code
            elif not hasattr(response, 'set_cookie'):
                # If it's a dict or plain response, convert to Flask response
                response = jsonify(response)
            
            # Set new access token cookie if token was refreshed
            if new_access_token:
                response.set_cookie("access_token", new_access_token, httponly=True, secure=True, samesite="Strict")
            
            return response

        except AuthenticationError as e:
            return jsonify({"status": "error", "message": str(e), "code": "AUTH_ERROR"}), 401
        except Exception:
            return (
                jsonify(
                    {"status": "error", "message": "Authentication failed", "code": "AUTH_FAILED"}
                ),
                401,
            )

    return decorated_function


def require_role(*allowed_roles):
    """
    Decorator to require specific user roles
    Must be used with @require_auth

    Usage:
        @app.route('/api/v1/admin/users')
        @require_auth
        @require_role('admin')
        def get_all_users():
            ...

    Args:
        *allowed_roles: One or more role names (e.g., 'admin', 'teacher', 'student')
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Check if user is authenticated (should have user_id from @require_auth)
                if not hasattr(request, "user_id"):
                    return (
                        jsonify(
                            {
                                "status": "error",
                                "message": "Authentication required",
                                "code": "UNAUTHENTICATED",
                            }
                        ),
                        401,
                    )

                user_role = getattr(request, "user_role", None)

                # Admin bypass - admins can access everything
                if user_role == "admin":
                    return f(*args, **kwargs)

                # Check if user has required role
                if user_role not in allowed_roles:
                    roles_msg = f'Access denied. Required role: {", ".join(allowed_roles)}'
                    return (
                        jsonify(
                            {
                                "status": "error",
                                "message": roles_msg,
                                "code": "INSUFFICIENT_PERMISSIONS",
                            }
                        ),
                        403,
                    )

                return f(*args, **kwargs)

            except Exception:
                return (
                    jsonify(
                        {
                            "status": "error",
                            "message": "Authorization check failed",
                            "code": "AUTH_CHECK_FAILED",
                        }
                    ),
                    403,
                )

        return decorated_function

    return decorator


def require_owner(*resource_id_param):
    """
    Decorator to verify user owns the resource

    Usage:
        @app.route('/api/v1/users/<user_id>')
        @require_auth
        @require_owner('user_id')
        def get_user(user_id):
            ...

    Args:
        *resource_id_param: Route parameter names that should match user_id
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                if not hasattr(request, "user_id"):
                    return (
                        jsonify(
                            {
                                "status": "error",
                                "message": "Authentication required",
                                "code": "UNAUTHENTICATED",
                            }
                        ),
                        401,
                    )

                user_id = request.user_id
                user_role = getattr(request, "user_role", None)

                # Admin bypass
                if user_role == "admin":
                    return f(*args, **kwargs)

                # Check ownership
                resource_id = kwargs.get(resource_id_param[0]) if resource_id_param else None

                if resource_id and resource_id != user_id:
                    return (
                        jsonify(
                            {
                                "status": "error",
                                "message": "Access denied. You do not own this resource",
                                "code": "FORBIDDEN",
                            }
                        ),
                        403,
                    )

                return f(*args, **kwargs)

            except Exception:
                return (
                    jsonify(
                        {
                            "status": "error",
                            "message": "Ownership verification failed",
                            "code": "OWNERSHIP_CHECK_FAILED",
                        }
                    ),
                    403,
                )

        return decorated_function

    return decorator


def create_access_token(user_id, role, email, expires_in_hours=24):
    """
    Create JWT access token for user

    Args:
        user_id: User UUID
        role: User role (admin, teacher, student)
        email: User email
        expires_in_hours: Token expiration time in hours

    Returns:
        str: Encoded JWT token
    """
    try:
        secret_key = current_app.config.get("SECRET_KEY", "your-secret-key")

        payload = {
            "user_id": user_id,
            "role": role,
            "email": email,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=expires_in_hours),
        }

        token = jwt.encode(payload, secret_key, algorithm="HS256")
        return token
    except Exception as e:
        raise Exception(f"Token creation failed: {str(e)}")
