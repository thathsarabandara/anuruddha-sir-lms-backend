"""
Course Enrollment Service
Handles student enrollment, unenrollment, and enrollment listing
"""

import logging
import uuid
from datetime import datetime, date

from app import db
from app.exceptions import AuthorizationError, ConflictError, ResourceNotFoundError, ValidationError
from app.models.courses.course import Course
from app.models.courses.course_enrollment import CourseEnrollment
from app.models.courses.course_enrollment_key import CourseEnrollmentKey
from app.services.health.base_service import BaseService

logger = logging.getLogger(__name__)


class CourseEnrollmentService(BaseService):
    """Service for managing course enrollments."""

    # ──────────────────────────────────────────────────────────────────────────
    # Enroll
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def enroll_student(
        course_id: str,
        user_id: str,
        enrollment_method: str = "payment",
        enrollment_key: str = None,
    ) -> dict:
        """
        Enroll a student in a course.

        Supports payment-based enrollment and key-based enrollment.

        Args:
            course_id: Course UUID
            user_id: Student user ID
            enrollment_method: 'payment' or 'enrollment_key'
            enrollment_key: Key string (required if enrollment_method == 'enrollment_key')

        Returns:
            dict: Enrollment record data

        Raises:
            ResourceNotFoundError: Course or key not found
            ConflictError: Already enrolled
            ValidationError: Invalid key or expired
        """
        course = Course.query.get(course_id)
        if not course:
            raise ResourceNotFoundError("Course not found")

        if course.status != "published":
            raise ValidationError("Cannot enroll in a course that is not published")

        # Prevent double enrollment
        existing = CourseEnrollment.query.filter_by(
            course_id=course_id, user_id=user_id
        ).first()
        if existing:
            raise ConflictError("You are already enrolled in this course")

        key_id = None

        if enrollment_method == "enrollment_key":
            if not enrollment_key:
                raise ValidationError("Enrollment key is required")

            key_record = CourseEnrollmentKey.query.filter_by(
                key=enrollment_key, course_id=course_id
            ).first()

            if not key_record:
                raise ResourceNotFoundError("Enrollment key not found")
            if not key_record.is_active:
                raise ValidationError("Enrollment key is inactive")
            if key_record.expiry_date and key_record.expiry_date < date.today():
                raise ValidationError("Enrollment key has expired")
            if key_record.current_usage >= key_record.max_enrollments:
                raise ValidationError("Enrollment key has reached its usage limit")

            key_record.current_usage += 1
            key_id = key_record.key_id

        enrollment = CourseEnrollment(
            enrollment_id=str(uuid.uuid4()),
            course_id=course_id,
            user_id=user_id,
            enrollment_method=enrollment_method,
            key_id=key_id,
            status="enrolled",
            progress=0,
        )
        db.session.add(enrollment)

        # Increment total_enrollments counter
        course.total_enrollments = (course.total_enrollments or 0) + 1
        db.session.commit()

        logger.info("Student %s enrolled in course %s", user_id, course_id)
        return enrollment.to_dict()

    # ──────────────────────────────────────────────────────────────────────────
    # Unenroll
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def unenroll_student(course_id: str, user_id: str, requesting_user_id: str, user_role: str) -> None:
        """
        Remove a student's enrollment from a course.

        Only the enrolled student or admin can unenroll.

        Args:
            course_id: Course UUID
            user_id: Student to unenroll
            requesting_user_id: User making the request
            user_role: Role of requesting user

        Raises:
            AuthorizationError: If requester is not the student or admin
            ResourceNotFoundError: Enrollment not found
        """
        if user_role != "admin" and requesting_user_id != user_id:
            raise AuthorizationError("You can only unenroll yourself")

        enrollment = CourseEnrollment.query.filter_by(
            course_id=course_id, user_id=user_id
        ).first()
        if not enrollment:
            raise ResourceNotFoundError("Enrollment not found")

        course = Course.query.get(course_id)

        db.session.delete(enrollment)

        if course and course.total_enrollments and course.total_enrollments > 0:
            course.total_enrollments -= 1

        db.session.commit()
        logger.info("Student %s unenrolled from course %s", user_id, course_id)

    # ──────────────────────────────────────────────────────────────────────────
    # Read
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def get_my_courses(user_id: str, status: str = None, page: int = 1, limit: int = 20) -> dict:
        """
        Get all courses a student is enrolled in.

        Returns:
            dict: Paginated list of enrolled courses with progress
        """
        q = CourseEnrollment.query.filter_by(user_id=user_id)
        if status:
            q = q.filter(CourseEnrollment.status == status)

        total = q.count()
        offset = (page - 1) * limit
        enrollments = q.order_by(CourseEnrollment.enrolled_at.desc()).offset(offset).limit(limit).all()

        result = []
        for enrollment in enrollments:
            course = Course.query.get(enrollment.course_id)
            if course:
                data = {**course.to_dict(), **enrollment.to_dict()}
                result.append(data)

        return {
            "courses": result,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit,
        }

    @staticmethod
    def get_course_enrollments(
        course_id: str,
        instructor_id: str,
        user_role: str,
        page: int = 1,
        limit: int = 20,
        status: str = None,
    ) -> dict:
        """
        Get all enrollments for a course (instructor / admin only).

        Returns:
            dict: Paginated list of enrollments
        """
        from app.services.courses.course_service import CourseService

        CourseService.verify_course_owner(course_id, instructor_id, user_role)

        q = CourseEnrollment.query.filter_by(course_id=course_id)
        if status:
            q = q.filter(CourseEnrollment.status == status)

        total = q.count()
        offset = (page - 1) * limit
        enrollments = q.order_by(CourseEnrollment.enrolled_at.desc()).offset(offset).limit(limit).all()

        return {
            "enrollments": [e.to_dict() for e in enrollments],
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit,
        }
