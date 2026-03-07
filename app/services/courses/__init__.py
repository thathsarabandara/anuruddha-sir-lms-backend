"""
Courses Services Package
Services for handling all course-related workflows
"""

from app.services.courses.course_service import CourseService
from app.services.courses.course_status_service import CourseStatusService
from app.services.courses.course_enrollment_service import CourseEnrollmentService
from app.services.courses.course_enrollment_key_service import CourseEnrollmentKeyService
from app.services.courses.course_section_service import CourseSectionService
from app.services.courses.course_lesson_service import CourseLessonService
from app.services.courses.course_content_service import CourseContentService
from app.services.courses.course_progress_service import CourseProgressService
from app.services.courses.course_activity_service import CourseActivityService
from app.services.courses.course_review_service import CourseReviewService
from app.services.courses.course_analytics_service import CourseAnalyticsService

__all__ = [
    "CourseService",
    "CourseStatusService",
    "CourseEnrollmentService",
    "CourseEnrollmentKeyService",
    "CourseSectionService",
    "CourseLessonService",
    "CourseContentService",
    "CourseProgressService",
    "CourseActivityService",
    "CourseReviewService",
    "CourseAnalyticsService",
]
