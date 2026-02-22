"""
Database models module
All SQLAlchemy models should be imported here for migration purposes
"""

from app import db

# Import all authentication models
from app.models.auth import (
    User,
    Role,
    Permission,
    UserRole,
    RolePermission,
    OTPRequest,
    LoginFailure,
    UserAccountStatus,
    LoginHistory,
    PasswordResetToken,
    EmailVerificationToken,
)

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

# Import other models as they are created
# from app.models.course import Course
# from app.models.quiz import Quiz
