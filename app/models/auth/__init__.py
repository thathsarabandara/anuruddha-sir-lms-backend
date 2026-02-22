"""
Authentication Module Models
Contains all database models for authentication, authorization, and account management
"""

from app.models.auth.user import User
from app.models.auth.role import Role
from app.models.auth.permission import Permission
from app.models.auth.user_role import UserRole
from app.models.auth.role_permission import RolePermission
from app.models.auth.otp_request import OTPRequest
from app.models.auth.login_failure import LoginFailure
from app.models.auth.user_account_status import UserAccountStatus
from app.models.auth.login_history import LoginHistory
from app.models.auth.password_reset_token import PasswordResetToken
from app.models.auth.email_verification_token import EmailVerificationToken

__all__ = [
    'User',
    'Role',
    'Permission',
    'UserRole',
    'RolePermission',
    'OTPRequest',
    'LoginFailure',
    'UserAccountStatus',
    'LoginHistory',
    'PasswordResetToken',
    'EmailVerificationToken',
]
