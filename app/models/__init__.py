"""
Database models module
All SQLAlchemy models should be imported here for migration purposes
"""

# Import all authentication models
from app.models.auth import (
    User,
    EmailVerificationToken,
    LoginFailure,
    LoginHistory,
    OTPRequest,
    PasswordResetToken,
    Permission,
    Role,
    RolePermission,
    UserAccountStatus,
    UserRole,
    AccessToken,
    RefreshToken,   
)

# Import all user-role profile models
from app.models.users import (
    StudentProfile,
    TeacherProfile,
    UserActivityLog,
    UserPreferences,
    UserProfile,
    UserStatistics,
    UserSuspensionLog,
)

# Import all certificates models
from app.models.certificates import (
    Certificate,
    CertificateSharingLog,
    CertificateTemplate,
    CertificateVerificationLog,
)

# Import all courses models
from app.models.courses import (
    Course,
    CourseActivityLog,
    CourseCategory,
    CourseEnrollment,
    CourseEnrollmentKey,
    CourseLesson,
    CourseReview,
    CourseSection,
    CourseStatusAudit,
    LessonContent,
    LessonContentProgress,
)

# Import all notifications models
from app.models.notifications import (
    Notification,
    NotificationBatch,
    NotificationDeliveryLog,
    NotificationPreferences,
    NotificationTypePreferences,
)

# Import all payment models
from app.models.payment import Coupon, Invoice, Refund, Transaction

# Import all quizzes models
from app.models.quizzes import (
    AttemptAnswer,
    ManualGrade,
    Question,
    QuestionOption,
    Quiz,
    QuizAttempt,
)

# Import all reviews models
from app.models.reviews import Review, ReviewFlag, ReviewResponse, ReviewVote

# Import all rewards models
from app.models.rewards import (
    Achievement,
    Challenge,
    LeaderboardSnapshot,
    PointTransaction,
    Streak,
    UserAchievement,
    UserPoints,
)

__all__ = [
    # Auth Models (12)
    "User",
    "Role",
    "Permission",
    "UserRole",
    "RolePermission",
    "OTPRequest",
    "LoginFailure",
    "UserAccountStatus",
    "LoginHistory",
    "PasswordResetToken",
    "EmailVerificationToken",
    "AccessToken",
    "RefreshToken",
    # Users Models (7)
    "StudentProfile",
    "TeacherProfile",
    "UserProfile",
    "UserPreferences",
    "UserActivityLog",
    "UserStatistics",
    "UserSuspensionLog",
    # Courses Models (11)
    "CourseCategory",
    "Course",
    "CourseSection",
    "CourseLesson",
    "LessonContent",
    "LessonContentProgress",
    "CourseEnrollment",
    "CourseEnrollmentKey",
    "CourseReview",
    "CourseActivityLog",
    "CourseStatusAudit",
    # Quizzes Models (6)
    "Quiz",
    "Question",
    "QuestionOption",
    "QuizAttempt",
    "AttemptAnswer",
    "ManualGrade",
    # Notifications Models (6)
    "Notification",
    "NotificationPreferences",
    "NotificationTypePreferences",
    "NotificationDeliveryLog",
    "NotificationBatch",
    # Reviews Models (4)
    "Review",
    "ReviewResponse",
    "ReviewVote",
    "ReviewFlag",
    # Rewards Models (7)
    "UserPoints",
    "PointTransaction",
    "Achievement",
    "UserAchievement",
    "LeaderboardSnapshot",
    "Streak",
    "Challenge",
    # Certificates Models (4)
    "Certificate",
    "CertificateTemplate",
    "CertificateVerificationLog",
    "CertificateSharingLog",
    # Payment Models (4)
    "Transaction",
    "Invoice",
    "Refund",
    "Coupon",
]