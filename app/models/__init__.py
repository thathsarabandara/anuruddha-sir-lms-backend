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

# Import all courses models
from app.models.courses import (
    CourseCategory,
    Course,
    CourseSection,
    CourseLesson,
    LessonContent,
    LessonContentProgress,
    CourseEnrollment,
    CourseEnrollmentKey,
    CourseReview,
    CourseActivityLog,
    CourseStatusAudit,
)

__all__ = [
    # Auth Models (12)
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
    # Users Models (5)
    'UserProfile',
    'UserPreferences',
    'UserActivityLog',
    'UserStatistics',
    'UserSuspensionLog',
    # Courses Models (11)
    'CourseCategory',
    'Course',
    'CourseSection',
    'CourseLesson',
    'LessonContent',
    'LessonContentProgress',
    'CourseEnrollment',
    'CourseEnrollmentKey',
    'CourseReview',
    'CourseActivityLog',
    'CourseStatusAudit',
]

# Import other models as they are created
# from app.models.quiz import Quiz
# from app.models.notifications import Notification
