"""
Application constants and configuration values
"""

# User Roles
class UserRoles:
    """User role constants"""
    SUPER_ADMIN = 'super_admin'
    ADMIN = 'admin'
    TEACHER = 'teacher'
    STUDENT = 'student'
    
    ALL = [SUPER_ADMIN, ADMIN, TEACHER, STUDENT]

# Course Status
class CourseStatus:
    """Course status constants"""
    DRAFT = 'draft'
    PUBLISHED = 'published'
    ARCHIVED = 'archived'
    UNPUBLISHED = 'unpublished'
    
    ALL = [DRAFT, PUBLISHED, ARCHIVED, UNPUBLISHED]

# Course Visibility
class CourseVisibility:
    """Course visibility constants"""
    PUBLIC = 'public'
    PRIVATE = 'private'
    
    ALL = [PUBLIC, PRIVATE]

# Course Types
class CourseType:
    """Course type constants"""
    MONTHLY_THEORY = 'monthly_theory'
    PAPER = 'paper'
    QUIZ = 'quiz'
    SPECIAL = 'special'
    
    ALL = [MONTHLY_THEORY, PAPER, QUIZ, SPECIAL]

# Quiz Question Types
class QuestionType:
    """Quiz question type constants"""
    MULTIPLE_CHOICE = 'multiple_choice'
    MULTIPLE_CORRECT = 'multiple_correct'
    SHORT_ANSWER = 'short_answer'
    ESSAY = 'essay'
    FILL_BLANKS = 'fill_blanks'
    MATCHING = 'matching'
    
    ALL = [MULTIPLE_CHOICE, MULTIPLE_CORRECT, SHORT_ANSWER, ESSAY, FILL_BLANKS, MATCHING]

# Payment Status
class PaymentStatus:
    """Payment status constants"""
    PENDING = 'pending'
    COMPLETED = 'completed'
    FAILED = 'failed'
    REFUNDED = 'refunded'
    
    ALL = [PENDING, COMPLETED, FAILED, REFUNDED]

# Enrollment Status
class EnrollmentStatus:
    """Enrollment status constants"""
    ACTIVE = 'active'
    SUSPENDED = 'suspended'
    COMPLETED = 'completed'
    UNENROLLED = 'unenrolled'
    
    ALL = [ACTIVE, SUSPENDED, COMPLETED, UNENROLLED]

# Notification Types
class NotificationType:
    """Notification type constants"""
    EMAIL = 'email'
    SMS = 'sms'
    IN_APP = 'in_app'
    PUSH = 'push'
    
    ALL = [EMAIL, SMS, IN_APP, PUSH]

# API Response Codes
class ResponseCode:
    """API response code constants"""
    SUCCESS = 200
    CREATED = 201
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    CONFLICT = 409
    INTERNAL_ERROR = 500

# Error Messages
class ErrorMessage:
    """Common error messages"""
    INVALID_CREDENTIALS = 'Invalid email or password'
    UNAUTHORIZED = 'Unauthorized access'
    FORBIDDEN = 'Access forbidden'
    NOT_FOUND = 'Resource not found'
    BAD_REQUEST = 'Invalid request data'
    INTERNAL_ERROR = 'Internal server error'
    DATABASE_ERROR = 'Database error occurred'
    VALIDATION_ERROR = 'Validation failed'

# Success Messages
class SuccessMessage:
    """Common success messages"""
    CREATED = 'Resource created successfully'
    UPDATED = 'Resource updated successfully'
    DELETED = 'Resource deleted successfully'
    LOGIN_SUCCESS = 'Login successful'
    LOGOUT_SUCCESS = 'Logout successful'

# Pagination
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# Cache TTL (Time to Live) in seconds
CACHE_TTL = {
    'USER_PROFILE': 3600,        # 1 hour
    'COURSE_DATA': 1800,         # 30 minutes
    'QUIZ_QUESTIONS': 1800,      # 30 minutes
    'LEADERBOARD': 600,          # 10 minutes
    'SHORT': 300,                # 5 minutes
}

# Rate Limiting
RATE_LIMIT = {
    'LOGIN_ATTEMPTS': 5,         # Max 5 login attempts
    'LOGIN_TIMEOUT': 900,        # 15 minutes timeout
    'OTP_ATTEMPTS': 3,           # Max 3 OTP attempts
    'OTP_RESEND_LIMIT': 3,       # Max 3 OTP resends
}

# Token Expiration (in seconds)
TOKEN_EXPIRATION = {
    'ACCESS': 1800,              # 30 minutes
    'REFRESH': 604800,           # 7 days
}

# OTP Configuration
OTP_CONFIG = {
    'LENGTH': 6,                 # OTP length
    'EXPIRY': 300,               # 5 minutes
    'MAX_ATTEMPTS': 3,           # Max attempts
}

# File Upload Configuration
FILE_CONFIG = {
    'MAX_SIZE': 500 * 1024 * 1024,  # 500MB
    'ALLOWED_TYPES': {
        'document': ['pdf', 'docx', 'doc', 'txt', 'xlsx', 'xls'],
        'video': ['mp4', 'avi', 'mov', 'wmv', 'flv'],
        'image': ['jpg', 'jpeg', 'png', 'gif', 'bmp'],
        'audio': ['mp3', 'wav', 'flac', 'aac'],
    }
}

# Email Configuration
EMAIL_CONFIG = {
    'SENDER_NAME': 'LMS Platform',
    'SENDER_EMAIL': 'noreply@lms.com',
}

# Pagination
PAGINATION = {
    'DEFAULT_PAGE_SIZE': 20,
    'MAX_PAGE_SIZE': 100,
}
