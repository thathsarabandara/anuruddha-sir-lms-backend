"""
Course Status Service
Handles course lifecycle transitions: publish, unpublish, archive, unarchive, private, public
"""

import logging
import uuid
from datetime import datetime

from flask import request as flask_request

from app import db
from app.exceptions import AuthorizationError, ConflictError, ResourceNotFoundError, ValidationError
from app.models.courses.course import Course
from app.models.courses.course_status_audit import CourseStatusAudit
from app.services.health.base_service import BaseService

logger = logging.getLogger(__name__)


class CourseStatusService(BaseService):
    """Service for course status and visibility transitions."""

    VALID_STATUS_TRANSITIONS = {
        "draft": ["published"],
        "published": ["draft", "archived"],
        "archived": ["draft"],
    }

    # ──────────────────────────────────────────────────────────────────────────
    # Internal helpers
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _get_owned_course(course_id: str, user_id: str, user_role: str) -> "Course":
        """Fetch course and verify ownership or admin."""
        course = Course.query.get(course_id)
        if not course:
            raise ResourceNotFoundError("Course not found")
        if user_role != "admin" and course.instructor_id != user_id:
            raise AuthorizationError("You do not have permission to modify this course")
        return course

    @staticmethod
    def _log_status_change(
        course_id: str,
        changed_by: str,
        change_type: str,
        previous_status=None,
        new_status=None,
        previous_visibility=None,
        new_visibility=None,
        change_reason: str = None,
    ) -> None:
        """Persist a status-audit record."""
        try:
            audit = CourseStatusAudit(
                audit_id=str(uuid.uuid4()),
                course_id=course_id,
                changed_by=changed_by,
                change_type=change_type,
                previous_status=previous_status,
                new_status=new_status,
                previous_visibility=previous_visibility,
                new_visibility=new_visibility,
                change_reason=change_reason,
                ip_address=getattr(flask_request, "remote_addr", None),
                user_agent=str(flask_request.user_agent) if flask_request else None,
            )
            db.session.add(audit)
            # flushed together with the parent commit
        except Exception as e:
            logger.warning("Could not write status audit: %s", str(e))

    # ──────────────────────────────────────────────────────────────────────────
    # Status transitions
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def publish_course(
        course_id: str, user_id: str, user_role: str, reason: str = None
    ) -> dict:
        """Publish a draft course."""
        course = CourseStatusService._get_owned_course(course_id, user_id, user_role)

        if course.status == "published":
            raise ConflictError("Course is already published")
        if course.status == "archived":
            raise ValidationError("Archived courses must be unarchived before publishing")

        previous_status = course.status
        course.status = "published"
        course.updated_at = datetime.utcnow()

        CourseStatusService._log_status_change(
            course_id, user_id, "publish", previous_status, "published", change_reason=reason
        )
        db.session.commit()
        logger.info("Course %s published by %s", course_id, user_id)
        return course.to_dict()

    @staticmethod
    def unpublish_course(
        course_id: str, user_id: str, user_role: str, reason: str = None
    ) -> dict:
        """Unpublish (revert to draft) a published course."""
        course = CourseStatusService._get_owned_course(course_id, user_id, user_role)

        if course.status != "published":
            raise ConflictError("Only published courses can be unpublished")

        previous_status = course.status
        course.status = "draft"
        course.updated_at = datetime.utcnow()

        CourseStatusService._log_status_change(
            course_id, user_id, "unpublish", previous_status, "draft", change_reason=reason
        )
        db.session.commit()
        logger.info("Course %s unpublished by %s", course_id, user_id)
        return course.to_dict()

    @staticmethod
    def archive_course(
        course_id: str, user_id: str, user_role: str, reason: str = None
    ) -> dict:
        """Archive a course."""
        course = CourseStatusService._get_owned_course(course_id, user_id, user_role)

        if course.status == "archived":
            raise ConflictError("Course is already archived")

        previous_status = course.status
        course.status = "archived"
        course.updated_at = datetime.utcnow()

        CourseStatusService._log_status_change(
            course_id, user_id, "archive", previous_status, "archived", change_reason=reason
        )
        db.session.commit()
        logger.info("Course %s archived by %s", course_id, user_id)
        return course.to_dict()

    @staticmethod
    def unarchive_course(
        course_id: str, user_id: str, user_role: str, reason: str = None
    ) -> dict:
        """Unarchive a course (returns to draft)."""
        course = CourseStatusService._get_owned_course(course_id, user_id, user_role)

        if course.status != "archived":
            raise ConflictError("Only archived courses can be unarchived")

        previous_status = course.status
        course.status = "draft"
        course.updated_at = datetime.utcnow()

        CourseStatusService._log_status_change(
            course_id, user_id, "unarchive", previous_status, "draft", change_reason=reason
        )
        db.session.commit()
        logger.info("Course %s unarchived by %s", course_id, user_id)
        return course.to_dict()

    # ──────────────────────────────────────────────────────────────────────────
    # Visibility transitions
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def set_private(
        course_id: str, user_id: str, user_role: str, reason: str = None
    ) -> dict:
        """Set course visibility to private."""
        course = CourseStatusService._get_owned_course(course_id, user_id, user_role)

        if course.visibility == "private":
            raise ConflictError("Course is already private")

        previous_visibility = course.visibility
        course.visibility = "private"
        course.updated_at = datetime.utcnow()

        CourseStatusService._log_status_change(
            course_id, user_id, "private",
            previous_visibility=previous_visibility,
            new_visibility="private",
            change_reason=reason,
        )
        db.session.commit()
        logger.info("Course %s set to private by %s", course_id, user_id)
        return course.to_dict()

    @staticmethod
    def set_public(
        course_id: str, user_id: str, user_role: str, reason: str = None
    ) -> dict:
        """Set course visibility to public."""
        course = CourseStatusService._get_owned_course(course_id, user_id, user_role)

        if course.visibility == "public":
            raise ConflictError("Course is already public")

        previous_visibility = course.visibility
        course.visibility = "public"
        course.updated_at = datetime.utcnow()

        CourseStatusService._log_status_change(
            course_id, user_id, "public",
            previous_visibility=previous_visibility,
            new_visibility="public",
            change_reason=reason,
        )
        db.session.commit()
        logger.info("Course %s set to public by %s", course_id, user_id)
        return course.to_dict()
