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

# Import all quizzes models
from app.models.quizzes import (
    Quiz,
    Question,
    QuestionOption,
    QuizAttempt,
    AttemptAnswer,
    ManualGrade,
)

# Import all notifications models
from app.models.notifications import (
    Notification,
    NotificationPreferences,
    NotificationTypePreferences,
    NotificationDeliveryLog,
    NotificationTemplate,
    NotificationBatch,
)

# Import all reviews models
from app.models.reviews import (
    Review,
    ReviewResponse,
    ReviewVote,
    ReviewFlag,
)

# Import all rewards models
from app.models.rewards import (
    UserPoints,
    PointTransaction,
    Achievement,
    UserAchievement,
    LeaderboardSnapshot,
    Streak,
    Challenge,
)

# Import all certificates models
from app.models.certificates import (
    Certificate,
    CertificateTemplate,
    CertificateVerificationLog,
    CertificateSharingLog,
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
    # Quizzes Models (6)
    'Quiz',
    'Question',
    'QuestionOption',
    'QuizAttempt',
    'AttemptAnswer',
    'ManualGrade',
    # Notifications Models (6)
    'Notification',
    'NotificationPreferences',
    'NotificationTypePreferences',
    'NotificationDeliveryLog',
    'NotificationTemplate',
    'NotificationBatch',
    # Reviews Models (4)
    'Review',
    'ReviewResponse',
    'ReviewVote',
    'ReviewFlag',
    # Rewards Models (7)
    'UserPoints',
    'PointTransaction',
    'Achievement',
    'UserAchievement',
    'LeaderboardSnapshot',
    'Streak',
    'Challenge',
    # Certificates Models (4)
    'Certificate',
    'CertificateTemplate',
    'CertificateVerificationLog',
    'CertificateSharingLog',
]

# Import other models as they are created
# from app.models.quiz import Quiz
# from app.models.notifications import Notification
