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

# Import all user profile models
from app.models.users import (
    UserProfile,
    UserPreferences,
    UserActivityLog,
    UserStatistics,
    UserSuspensionLog,
)

__all__ = [
    # Auth Models
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
    # Users Models
    'UserProfile',
    'UserPreferences',
    'UserActivityLog',
    'UserStatistics',
    'UserSuspensionLog',
]

# Import other models as they are created
# from app.models.course import Course
# from app.models.quiz import Quiz
