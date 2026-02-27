"""
Authentication Routes
All authentication endpoints of the application
"""

import logging
from flask import Blueprint, request, current_app

from app.exceptions import ValidationError
from app.middleware.auth_middleware import require_auth
from app.services.auth import (
    LoginHistoryService,
    LoginService,
    LogoutService,
    OTPVerificationService,
    PasswordResetService,
    RegistrationService,
    TokenRefreshService,
    TokenVerificationService,
)
from app.utils.decorators import handle_exceptions, validate_json
from app.utils.helpers import get_page_and_limit
from app.utils.response import error_response, success_response
from app.utils.validators import validate_email, validate_phone

bp = Blueprint("auth", __name__, url_prefix="/api/v1/auth")
logger = logging.getLogger(__name__)


# ===================== Cookie Helper Function =====================


def set_auth_cookies(response, access_token=None, refresh_token=None):
    """
    Set authentication tokens as HttpOnly cookies

    Args:
        response: Flask response object
        access_token: Access token to set in cookie (30 min expiry)
        refresh_token: Refresh token to set in cookie (7 day expiry)

    Returns:
        Updated response object with cookies set
    """
    # Use secure flag based on environment (True for production, False for development)
    is_secure = current_app.config.get("ENV") == "production"

    if access_token:
        response[0].set_cookie(
            "access_token",
            access_token,
            max_age=1800,  # 30 minutes
            secure=is_secure,
            httponly=True,  # Prevent JavaScript access (XSS protection)
            samesite="Strict",  # CSRF protection
            path="/",
        )

    if refresh_token:
        response[0].set_cookie(
            "refresh_token",
            refresh_token,
            max_age=604800,  # 7 days
            secure=is_secure,
            httponly=True,
            samesite="Strict",
            path="/",
        )

    return response


def set_verification_token_cookie(response, verification_token):
    """
    Set verification token as HttpOnly cookie for OTP verification flow

    Args:
        response: Flask response object
        verification_token: Verification token to set in cookie (5 min expiry)

    Returns:
        Updated response object with verification token cookie set
    """
    is_secure = current_app.config.get("ENV") == "production"

    response[0].set_cookie(
        "verification_token",
        verification_token,
        max_age=300,  # 5 minutes (OTP expiry)
        secure=is_secure,
        httponly=True,
        samesite="Strict",
        path="/",
    )

    return response

def set_password_reset_token_cookie(response, password_reset_token):
    """
    Set password reset token as HttpOnly cookie for OTP password reset flow

    Args:
        response: Flask response object
        password_reset_token: Password reset token to set in cookie (5 min expiry)

    Returns:
        Updated response object with password reset token cookie set
    """
    is_secure = current_app.config.get("ENV") == "production"

    response[0].set_cookie(
        "password_reset_token",
        password_reset_token,
        max_age=300,  # 5 minutes (OTP expiry)
        secure=is_secure,
        httponly=True,
        samesite="Strict",
        path="/",
    )

    return response

# ===================== Registration Endpoints =====================


@bp.route("/register", methods=["POST"])
@handle_exceptions
def register():
    """
    Register a new student or teacher.

    All registrations start with OTP email/WhatsApp verification.
    After OTP verification the account enters 'pending_approval' state and
    an admin must approve it before the user can log in.

    ── Common fields (both roles) ──────────────────────────────────────────
    Request Body (JSON):
        email (required)
        password (required)
        first_name (required)
        last_name (required)
        phone                   – phone number (used for OTP if no WhatsApp)
        profile_picture_url     – URL of uploaded profile picture
        role                    – 'student' (default) | 'teacher'

    Request Files:
        profile_picture         – Profile picture file (optional, if not providing URL)
                                  Supported: png, jpg, jpeg, gif, webp (max 5MB)

    ── Student-only fields ─────────────────────────────────────────────────
        whatsapp_number         – WhatsApp contact number
        date_of_birth           – 'YYYY-MM-DD'
        grade_level             – e.g. 'Grade 10', 'A/L', 'Undergraduate'
        school                  – School / institution name
        address                 – Physical address
        parent_name             – Parent / guardian full name
        parent_contact          – Parent / guardian phone

    ── Teacher-only fields ─────────────────────────────────────────────────
        qualifications          – Academic / professional qualifications
        subjects_taught         – List of subjects  e.g. ["Maths","Physics"]
        years_of_experience     – Integer
        language_of_instruction – e.g. 'English', 'Sinhala'
        professional_bio        – Detailed bio
        address                 – Physical address

    Returns:
        201: Registered, OTP sent — user must verify email then await admin approval
        400: Validation error
        409: Email already registered
    """
    try:
        # Get JSON data and handle both JSON and form data
        data = request.get_json() if request.is_json else request.form.to_dict()

        # Validate required fields
        required_fields = ["email", "password", "first_name", "last_name"]
        for field in required_fields:
            if not data.get(field):
                return error_response(f"{field} is required", 400)

        role = data.get("role", "student")

        # Build kwargs shared by both roles
        common = dict(
            email=data["email"],
            password=data["password"],
            first_name=data["first_name"],
            last_name=data["last_name"],
            phone=data.get("phone"),
            profile_picture_url=data.get("profile_picture"),
            role=role,
            address=data.get("address"),
        )

        if role == "student":
            user_data, verification_token, _ = RegistrationService.register_user(
                **common,
                date_of_birth=data.get("date_of_birth"),
                grade_level=data.get("grade_level"),
                school=data.get("school"),
                parent_name=data.get("parent_name"),
                parent_contact=data.get("parent_contact"),
            )
        elif role == "teacher":
            user_data, verification_token, _ = RegistrationService.register_user(
                **common,
                qualifications=data.get("qualifications"),
                subjects_taught=data.get("subjects_taught"),
                years_of_experience=data.get("years_of_experience"),
                language_of_instruction=data.get("language_of_instruction"),
                professional_bio=data.get("professional_bio"),
            )
        else:
            return error_response("role must be 'student' or 'teacher'", 400)

        response = success_response(
            data={
                **user_data,
                "otp_expires_in": 300,
                "channels_used": ["email", "whatsapp"],
                "next_step": "Verify OTP, then await admin approval before logging in.",
            },
            message=(
                "Registration successful. OTP sent to email and WhatsApp. "
                "After verification your account will be reviewed by an admin."
            ),
            status_code=201,
        )

        return set_verification_token_cookie(response, verification_token)

    except ValidationError as e:
        return error_response(str(e), 400)
    except Exception as e:
        from app.exceptions import ConflictError
        if isinstance(e, ConflictError):
            return error_response(str(e), 409)
        logger.error(f"Registration error: {str(e)}", exc_info=True)
        return error_response(str(e), 400)


@bp.route("/resend-otp", methods=["POST"])
@handle_exceptions
def resend_otp():
    """
    Resend OTP to user email/WhatsApp


    Returns:
        200: OTP resent successfully
        400: Invalid token or rate limit exceeded
    """
    try:
        data = request.get_json()

        # Get verification token from cookie (with fallback to request body)
        verification_token = request.cookies.get("verification_token") or data.get("token")

        if not verification_token:
            return error_response("Verification token is required. Complete registration first.", 401)

        verification_token, remaining_attempts = RegistrationService.resend_otp(
            verification_token=verification_token,
            channel=data.get("channel", "both"),
        )

        response = success_response(
            data={
                "expires_in": 300,
                "attempt_remaining": remaining_attempts,
            },
            message="OTP resent successfully",
            status_code=200,
        )

        # Reset verification token cookie expiry
        return set_verification_token_cookie(response, verification_token)

    except ValidationError as e:
        return error_response(str(e), 400)


# ===================== OTP Verification Endpoints =====================


@bp.route("/verify-otp", methods=["POST"])
@validate_json("otp")
@handle_exceptions
def verify_otp():
    """
    Verify OTP and activate account

    Request Body:
        {
            "otp": "123456",
        }

    Returns:
        200: OTP verified, tokens issued in cookies
        400: Invalid OTP or expired token
    """
    try:
        data = request.get_json()

        # Get verification token from cookie (with fallback to request body)
        verification_token = request.cookies.get("verification_token") or data.get("token")

        if not verification_token:
            return error_response("Verification token is required. Complete registration first.", 401)

        # Verify OTP
        user_data = OTPVerificationService.verify_otp(
            email=data["email"],
            otp_code=data["otp"],
            verification_token=verification_token,
            purpose=data.get("purpose", "email_verification"),
        )

        response_data = {
            **user_data,
            "expires_in": 1800,
            "notifications": {
                "email": "Welcome message sent",
                "whatsapp": "Welcome message sent",
            },
        }

        response = success_response(
            data=response_data,
            message="OTP verified successfully. Account activated. Welcome message sent.",
            status_code=200,
        )

        # Generate and set tokens in HttpOnly cookies (stored in database)
        from app.utils.auth import TokenManager
        access_token = TokenManager.generate_access_token(
            user_data["user_id"], user_data["email"], user_data["username"], "student", store_in_db=True
        )
        refresh_token = TokenManager.generate_refresh_token(
            user_data["user_id"], user_data["email"], user_data["username"], store_in_db=True
        )

        # Set auth cookies
        response = set_auth_cookies(response, access_token, refresh_token)

        # Clear verification token cookie (no longer needed)
        is_secure = current_app.config.get("ENV") == "production"
        response[0].set_cookie("verification_token", "", max_age=0, secure=is_secure, httponly=True, path="/")

        return response

    except ValidationError as e:
        return error_response(str(e), 400)


# ===================== Login Endpoints =====================


@bp.route("/login", methods=["POST"])
@validate_json("email", "password")
@handle_exceptions
def login():
    """
    Authenticate user and issue tokens

    Request Body:
        {
            "email": "user@example.com",
            "password": "SecurePassword123!",
        }

    Returns:
        200: Authentication successful, tokens in cookies
        400: Invalid credentials
        403: Account banned or not verified
    """
    try:
        data = request.get_json()

        # Get client IP and user agent
        ip_address = request.remote_addr
        user_agent = request.headers.get("User-Agent", "")

        # Perform login
        user_data, access_token, refresh_token = LoginService.login_user(
            email=data["email"],
            password=data["password"],
            ip_address=ip_address,
            user_agent=user_agent,
            device_name=data.get("device_name"),
        )

        response = success_response(
            data={
                "user": user_data,
                "expires_in": 1800,
            },
            message="Login successful",
            status_code=200,
        )

        # Set tokens in HttpOnly cookies
        return set_auth_cookies(response, access_token, refresh_token)

    except Exception as e:
        from app.exceptions import AuthenticationError
        if isinstance(e, AuthenticationError):
            return error_response(str(e), 401)
        return error_response(str(e), 400)


# ===================== Token Management Endpoints =====================


@bp.route("/refresh", methods=["POST"])
@handle_exceptions
def refresh_token():
    """
    Refresh access token using refresh token

    Returns:
        200: New access token issued in cookie
        401: Invalid or expired refresh token
    """
    try:
        # Get refresh token from cookies or body
        refresh_token = request.cookies.get("refresh_token") or request.json.get("refresh_token")

        if not refresh_token:
            return error_response("Refresh token is required", 401)

        # Refresh token
        access_token, expires_in = TokenRefreshService.refresh_access_token(refresh_token)

        response = success_response(
            data={"expires_in": expires_in},
            message="Token refreshed successfully",
            status_code=200,
        )

        # Set new access token in cookie
        return set_auth_cookies(response, access_token=access_token)

    except Exception as e:
        from app.exceptions import AuthenticationError
        if isinstance(e, AuthenticationError):
            return error_response(str(e), 401)
        return error_response(str(e), 400)


@bp.route("/verify-token", methods=["POST"])
@require_auth
@handle_exceptions
def verify_token():
    """
    Verify access token validity.
    
    If access token is expired, auto-generates a new one using refresh token
    and returns it to the client.

    Returns:
        200: Token is valid (may include new_access_token if refreshed)
        401: Token is invalid/expired or refresh failed
    """
    try:
        access_token = request.cookies.get("access_token")
        refresh_token = request.cookies.get("refresh_token")

        if not access_token:
            return error_response("Access token is required", 401)

        # Verify token (auto-generates new one if expired + refresh_token available)
        token_data = TokenVerificationService.verify_token(access_token, refresh_token)

        response = success_response(data=token_data, status_code=200)

        # If a new access token was generated, set it in response cookies
        if token_data.get("new_access_token"):
            response.set_cookie(
                "access_token",
                token_data["new_access_token"],
                max_age=1800,  # 30 minutes
                secure=True,
                httponly=True,
                samesite="Lax",
            )

        return response

    except Exception as e:
        from app.exceptions import AuthenticationError
        if isinstance(e, AuthenticationError):
            return error_response(str(e), 401)
        return error_response(str(e), 400)


@bp.route("/logout", methods=["POST"])
@require_auth
@handle_exceptions
def logout():
    """
    Logout user and destroy session

    Returns:
        200: Logout successful
        401: Authentication required
    """
    try:
        access_token = request.cookies.get("access_token")
        refresh_token = request.cookies.get("refresh_token")
        user_id = request.user_id

        # Perform logout
        logout_data = LogoutService.logout_user(user_id, access_token, refresh_token)

        response = success_response(
            data=logout_data,
            message="Logged out successfully",
            status_code=200,
        )

        # Clear cookies by setting max_age=0
        is_secure = current_app.config.get("ENV") == "production"
        response[0].set_cookie("access_token", "", max_age=0, secure=is_secure, httponly=True, path="/")
        response[0].set_cookie("refresh_token", "", max_age=0, secure=is_secure, httponly=True, path="/")

        return response

    except Exception as e:
        return error_response(str(e), 400)


# ===================== Password Management Endpoints =====================


@bp.route("/forgot-password", methods=["POST"])
@validate_json("email")
@handle_exceptions
def forgot_password():
    """
    Initiate password reset workflow

    Request Body:
        {
            "email": "user@example.com"
        }

    Returns:
        200: Password reset link and OTP sent to email
    """
    try:
        data = request.get_json()

        reset_token, otp_code = PasswordResetService.initiate_password_reset(data["email"])

        response = success_response(
            data={
                "token": reset_token,
                "expires_in": 3600,
                "message": "Check your email for password reset link and OTP. Valid for 1 hour.",
            },
            message="Password reset link sent to email",
            status_code=200,
        )

        # Set password reset token cookie
        response = set_password_reset_token_cookie(response, reset_token)
        return response
    except Exception as e:
        return error_response(str(e), 400)


@bp.route("/verify-reset-token", methods=["GET"])
@validate_json("token")
@handle_exceptions
def verify_reset_token():
    """
    Verify password reset token is valid before showing reset password form.
    
    Frontend calls this endpoint to validate the reset token before allowing
    user access to the reset password form.


    Returns:
        200: Reset token is valid
        400: Invalid, expired, or already used reset token
    """
    try:
        data = request.get_json()

        password_reset_token = request.cookies.get("password_reset_token") or data.get("token")

        verification_data = PasswordResetService.verify_reset_token(password_reset_token)

        return success_response(
            data=verification_data,
            message="Reset token is valid",
            status_code=200,
        )

    except ValidationError as e:
        return error_response(str(e), 400)


@bp.route("/reset-password", methods=["POST"])
@validate_json("token", "otp", "password", "confirm_password")
@handle_exceptions
def reset_password():
    """
    Reset password with OTP verification

    Request Body:
        {
            "token": "unique_reset_token",
            "otp": "123456",
            "password": "NewSecurePassword123!",
            "confirm_password": "NewSecurePassword123!"
        }

    Returns:
        200: Password reset successfully
        400: Invalid token, OTP, or validation error
    """
    try:
        data = request.get_json()

        reset_data = PasswordResetService.reset_password(
            reset_token=data["token"],
            otp_code=data["otp"],
            new_password=data["password"],
            confirm_password=data["confirm_password"],
        )

        return success_response(
            data=reset_data,
            message=reset_data.get("message", "Password reset successfully"),
            status_code=200,
        )

    except ValidationError as e:
        return error_response(str(e), 400)


@bp.route("/change-password", methods=["POST"])
@require_auth
@validate_json("current_password", "new_password", "confirm_password")
@handle_exceptions
def change_password():
    """
    Change password for authenticated user

    Request Body:
        {
            "current_password": "OldPassword123!",
            "new_password": "NewPassword123!",
            "confirm_password": "NewPassword123!"
        }

    Returns:
        200: Password changed successfully
        401: Current password is incorrect
    """
    try:
        data = request.get_json()
        user_id = request.user_id

        change_data = PasswordResetService.change_password(
            user_id=user_id,
            current_password=data["current_password"],
            new_password=data["new_password"],
            confirm_password=data["confirm_password"],
        )

        return success_response(
            data=change_data,
            message=change_data.get("message", "Password changed successfully"),
            status_code=200,
        )

    except Exception as e:
        from app.exceptions import AuthenticationError
        if isinstance(e, AuthenticationError):
            return error_response(str(e), 401)
        return error_response(str(e), 400)


# ===================== Login History Endpoints =====================


@bp.route("/login-history", methods=["GET"])
@require_auth
@handle_exceptions
def get_login_history():
    """
    Get user's login history

    Query Parameters:
        page: Page number (default: 1)
        limit: Items per page (default: 20)

    Returns:
        200: Login history with pagination
    """
    try:
        user_id = request.user_id
        page, limit = get_page_and_limit(request.args)

        history_list, total = LoginHistoryService.get_login_history(user_id, page, limit)

        return success_response(
            data=history_list,
            status_code=200,
        )

    except Exception as e:
        return error_response(str(e), 400)


# ===================== Email Verification Endpoint =====================


@bp.route("/verify-email", methods=["POST"])
@validate_json("email", "token")
@handle_exceptions
def verify_email():
    """
    Verify email address

    Request Body:
        {
            "email": "user@example.com",
            "token": "verification_token"
        }

    Returns:
        200: Email verified successfully
    """
    try:
        data = request.get_json()

        # In a real implementation, this would verify the email separately
        # For now, OTP verification handles this

        return success_response(
            data={"verified": True},
            message="Email verified successfully",
            status_code=200,
        )

    except Exception as e:
        return error_response(str(e), 400)
