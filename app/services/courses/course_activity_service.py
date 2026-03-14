"""
Course Activity Service
Handles activity tracking for course interactions and activity log retrieval
"""

import logging
import uuid
from datetime import datetime

from flask import request as flask_request

from app import db
from app.exceptions import ResourceNotFoundError
from app.models.courses.course_activity_log import CourseActivityLog
from app.services.health.base_service import BaseService

logger = logging.getLogger(__name__)


class CourseActivityService(BaseService):
    """Service for tracking and retrieving course activity logs."""

    # ──────────────────────────────────────────────────────────────────────────
    # Track
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def track_activity(
        course_id: str,
        user_id: str,
        activity_type: str,
        lesson_id: str = None,
        content_id: str = None,
        activity_description: str = None,
        metadata: dict = None,
        session_id: str = None,
    ) -> dict:
        """
        Record a course activity event.

        Common activity_type values:
            - course_view, lesson_start, lesson_complete, content_view,
              video_play, video_pause, video_seek, pdf_download,
              zoom_join, zoom_leave, quiz_start, quiz_submit

        Args:
            course_id: Course UUID
            user_id: Student user ID
            activity_type: Event type string
            lesson_id: Optional lesson UUID
            content_id: Optional content UUID
            activity_description: Human-readable description
            metadata: JSON-serializable dict with extra data
            session_id: Optional session UUID

        Returns:
            dict: Created activity log entry
        """
        device_type = None
        browser = None
        ip_address = None

        try:
            ua = flask_request.headers.get("User-Agent", "")
            ip_address = flask_request.remote_addr

            # Simple UA parsing
            if "Mobile" in ua:
                device_type = "mobile"
            elif "Tablet" in ua:
                device_type = "tablet"
            else:
                device_type = "desktop"

            for b in ["Chrome", "Firefox", "Safari", "Edge", "Opera"]:
                if b in ua:
                    browser = b
                    break
        except Exception:
            pass

        log = CourseActivityLog(
            activity_id=str(uuid.uuid4()),
            course_id=course_id,
            lesson_id=lesson_id,
            content_id=content_id,
            user_id=user_id,
            activity_type=activity_type,
            activity_description=activity_description,
            device_type=device_type,
            browser=browser,
            ip_address=ip_address,
            session_id=session_id,
            timestamp=datetime.utcnow(),
        )
        if metadata:
            log.set_metadata(metadata)
        db.session.add(log)
        db.session.commit()

        logger.debug("Activity tracked for user %s in course %s: %s", user_id, course_id, activity_type)
        return log.to_dict()

    # ──────────────────────────────────────────────────────────────────────────
    # Read
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def get_activity_log(
        course_id: str,
        user_id: str,
        user_role: str,
        activity_type: str = None,
        page: int = 1,
        limit: int = 50,
    ) -> dict:
        """
        Get activity log for a student in a course (owner or enrolled).

        Returns:
            dict: Paginated activity log
        """
        from app.services.courses.course_service import CourseService

        CourseService.verify_owner_or_enrolled(course_id, user_id, user_role)

        q = CourseActivityLog.query.filter_by(course_id=course_id, user_id=user_id)
        if activity_type:
            q = q.filter(CourseActivityLog.activity_type == activity_type)

        total = q.count()
        offset = (page - 1) * limit
        logs = q.order_by(CourseActivityLog.timestamp.desc()).offset(offset).limit(limit).all()

        return {
            "activities": [l.to_dict() for l in logs],
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit,
        }
