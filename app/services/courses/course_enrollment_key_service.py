"""
Course Enrollment Key Service
Handles enrollment key creation, listing, deactivation, and analytics
"""

import logging
import uuid
from datetime import datetime

from app import db
from app.exceptions import AuthorizationError, ConflictError, ResourceNotFoundError, ValidationError
from app.models.courses.course_enrollment import CourseEnrollment
from app.models.courses.course_enrollment_key import CourseEnrollmentKey
from app.services.base_service import BaseService

logger = logging.getLogger(__name__)


class CourseEnrollmentKeyService(BaseService):
    """Service for managing enrollment keys."""

    # ──────────────────────────────────────────────────────────────────────────
    # Create
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def create_key(
        course_id: str,
        created_by: str,
        user_role: str,
        max_enrollments: int,
        description: str = None,
        expiry_date=None,
    ) -> dict:
        """
        Create a new enrollment key for a course.

        Args:
            course_id: Course UUID
            created_by: Instructor user ID
            user_role: Instructor role
            max_enrollments: Maximum students allowed via this key
            description: Optional description
            expiry_date: Optional expiry date (date object or ISO string)

        Returns:
            dict: Key data

        Raises:
            ValidationError: Invalid inputs
            AuthorizationError: Not the course owner
        """
        from app.services.courses.course_service import CourseService

        CourseService.verify_course_owner(course_id, created_by, user_role)

        if not max_enrollments or max_enrollments < 1:
            raise ValidationError("max_enrollments must be at least 1")

        # Generate a unique random key
        import secrets
        import string

        alphabet = string.ascii_uppercase + string.digits
        while True:
            key_str = "".join(secrets.choice(alphabet) for _ in range(12))
            if not CourseEnrollmentKey.query.filter_by(key=key_str).first():
                break

        # Parse expiry_date
        parsed_expiry = None
        if expiry_date:
            if isinstance(expiry_date, str):
                from datetime import date as date_type
                parsed_expiry = date_type.fromisoformat(expiry_date)
            else:
                parsed_expiry = expiry_date

        key_record = CourseEnrollmentKey(
            key_id=str(uuid.uuid4()),
            course_id=course_id,
            created_by=created_by,
            key=key_str,
            max_enrollments=max_enrollments,
            current_usage=0,
            description=description,
            expiry_date=parsed_expiry,
            is_active=True,
        )
        db.session.add(key_record)
        db.session.commit()

        logger.info("Enrollment key created for course %s by %s", course_id, created_by)
        return key_record.to_dict()

    # ──────────────────────────────────────────────────────────────────────────
    # Read
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def get_keys(
        course_id: str,
        user_id: str,
        user_role: str,
        is_active: bool = None,
        page: int = 1,
        limit: int = 20,
    ) -> dict:
        """
        List enrollment keys for a course.

        Returns:
            dict: Paginated key list
        """
        from app.services.courses.course_service import CourseService

        CourseService.verify_course_owner(course_id, user_id, user_role)

        q = CourseEnrollmentKey.query.filter_by(course_id=course_id)
        if is_active is not None:
            q = q.filter(CourseEnrollmentKey.is_active == is_active)

        total = q.count()
        offset = (page - 1) * limit
        keys = q.order_by(CourseEnrollmentKey.created_at.desc()).offset(offset).limit(limit).all()

        return {
            "keys": [k.to_dict() for k in keys],
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit,
        }

    # ──────────────────────────────────────────────────────────────────────────
    # Deactivate
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def deactivate_key(course_id: str, key_id: str, user_id: str, user_role: str) -> dict:
        """
        Deactivate an enrollment key.

        Returns:
            dict: Updated key data

        Raises:
            ResourceNotFoundError: Key not found
            ConflictError: Already inactive
        """
        from app.services.courses.course_service import CourseService

        CourseService.verify_course_owner(course_id, user_id, user_role)

        key_record = CourseEnrollmentKey.query.filter_by(
            key_id=key_id, course_id=course_id
        ).first()
        if not key_record:
            raise ResourceNotFoundError("Enrollment key not found")

        if not key_record.is_active:
            raise ConflictError("Enrollment key is already inactive")

        key_record.is_active = False
        key_record.deactivated_at = datetime.utcnow()
        db.session.commit()

        logger.info("Enrollment key %s deactivated for course %s", key_id, course_id)
        return key_record.to_dict()

    # ──────────────────────────────────────────────────────────────────────────
    # Analytics
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def get_key_analytics(course_id: str, key_id: str, user_id: str, user_role: str) -> dict:
        """
        Get detailed analytics for an enrollment key.

        Returns:
            dict: Key analytics including enrolled students
        """
        from app.services.courses.course_service import CourseService

        CourseService.verify_course_owner(course_id, user_id, user_role)

        key_record = CourseEnrollmentKey.query.filter_by(
            key_id=key_id, course_id=course_id
        ).first()
        if not key_record:
            raise ResourceNotFoundError("Enrollment key not found")

        enrollments = CourseEnrollment.query.filter_by(key_id=key_id).all()

        return {
            "key": key_record.to_dict(),
            "total_enrollments": len(enrollments),
            "remaining_slots": key_record.max_enrollments - key_record.current_usage,
            "is_full": key_record.current_usage >= key_record.max_enrollments,
            "enrolled_users": [e.user_id for e in enrollments],
        }
