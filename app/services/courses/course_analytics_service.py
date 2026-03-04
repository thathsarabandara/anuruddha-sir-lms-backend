"""
Course Analytics Service
Provides analytics for courses: enrollment trends, content views, attendance, recordings
"""

import logging
from datetime import datetime, timedelta

from sqlalchemy import func

from app import db
from app.exceptions import ResourceNotFoundError
from app.models.courses.course import Course
from app.models.courses.course_activity_log import CourseActivityLog
from app.models.courses.course_enrollment import CourseEnrollment
from app.models.courses.lesson_content import LessonContent
from app.models.courses.lesson_content_progress import LessonContentProgress
from app.services.base_service import BaseService

logger = logging.getLogger(__name__)


class CourseAnalyticsService(BaseService):
    """Service for course-level analytics (instructor / admin)."""

    @staticmethod
    def get_course_analytics(course_id: str, user_id: str, user_role: str) -> dict:
        """
        Get comprehensive analytics for a course.

        Args:
            course_id: Course UUID
            user_id: Requesting user ID (must be owner or admin)
            user_role: Role of user

        Returns:
            dict: Analytics summary

        Raises:
            ResourceNotFoundError: Course not found
            AuthorizationError: Not the owner
        """
        from app.services.courses.course_service import CourseService

        CourseService.verify_course_owner(course_id, user_id, user_role)

        course = Course.query.get(course_id)

        # Enrollment counts by status
        enrollment_stats = (
            db.session.query(CourseEnrollment.status, func.count(CourseEnrollment.enrollment_id))
            .filter(CourseEnrollment.course_id == course_id)
            .group_by(CourseEnrollment.status)
            .all()
        )
        enrollment_breakdown = {status: count for status, count in enrollment_stats}

        # Enrollments over last 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_enrollments = CourseEnrollment.query.filter(
            CourseEnrollment.course_id == course_id,
            CourseEnrollment.enrolled_at >= thirty_days_ago,
        ).count()

        # Content completion rates
        total_contents = LessonContent.query.filter_by(course_id=course_id).count()
        content_completions = (
            db.session.query(
                LessonContentProgress.content_id,
                func.count(LessonContentProgress.progress_id).label("total"),
                func.sum(LessonContentProgress.is_completed.cast(db.Integer)).label("completed"),
            )
            .filter(LessonContentProgress.course_id == course_id)
            .group_by(LessonContentProgress.content_id)
            .all()
        )

        content_stats = []
        for row in content_completions:
            content = LessonContent.query.get(row.content_id)
            if content:
                content_stats.append({
                    "content_id": row.content_id,
                    "title": content.title,
                    "content_type": content.content_type,
                    "total_views": row.total,
                    "total_completed": int(row.completed or 0),
                    "completion_rate": round(
                        (int(row.completed or 0) / row.total) * 100, 1
                    ) if row.total > 0 else 0,
                })

        # Average progress
        avg_progress = (
            db.session.query(func.avg(CourseEnrollment.progress))
            .filter(CourseEnrollment.course_id == course_id)
            .scalar()
        )

        # Activity count by type (last 30 days)
        activity_stats = (
            db.session.query(
                CourseActivityLog.activity_type,
                func.count(CourseActivityLog.activity_id).label("count"),
            )
            .filter(
                CourseActivityLog.course_id == course_id,
                CourseActivityLog.timestamp >= thirty_days_ago,
            )
            .group_by(CourseActivityLog.activity_type)
            .all()
        )
        activity_breakdown = {atype: count for atype, count in activity_stats}

        return {
            "course_id": course_id,
            "course_title": course.title,
            "total_enrollments": course.total_enrollments,
            "recent_enrollments_30d": recent_enrollments,
            "enrollment_breakdown": enrollment_breakdown,
            "average_progress_percent": round(float(avg_progress), 1) if avg_progress else 0,
            "total_contents": total_contents,
            "content_completion_stats": content_stats,
            "activity_breakdown_30d": activity_breakdown,
            "rating": float(course.rating) if course.rating else None,
            "total_reviews": course.total_reviews,
        }

    @staticmethod
    def get_lesson_attendance(
        course_id: str, lesson_id: str, user_id: str, user_role: str
    ) -> dict:
        """
        Get Zoom attendance records for a lesson (owner/admin only).

        Returns:
            dict: Attendance records
        """
        from app.services.courses.course_service import CourseService
        from app.models.courses.course_lesson import CourseLesson

        CourseService.verify_course_owner(course_id, user_id, user_role)

        lesson = LessonContent.query.filter_by(
            lesson_id=lesson_id, content_type="zoom_live"
        ).first()

        attendance_records = (
            LessonContentProgress.query.filter(
                LessonContentProgress.lesson_id == lesson_id,
                LessonContentProgress.zoom_attended == True,  # noqa: E712
            )
            .all()
        )

        records = []
        for record in attendance_records:
            records.append({
                "user_id": record.user_id,
                "zoom_joined_at": record.zoom_joined_at.isoformat() if record.zoom_joined_at else None,
                "zoom_left_at": record.zoom_left_at.isoformat() if record.zoom_left_at else None,
                "zoom_attended_duration_minutes": record.zoom_attended_duration_minutes,
                "zoom_device_type": record.zoom_device_type,
            })

        return {
            "lesson_id": lesson_id,
            "course_id": course_id,
            "total_attendees": len(records),
            "attendance": records,
        }

    @staticmethod
    def export_attendance(course_id: str, lesson_id: str, user_id: str, user_role: str) -> list:
        """
        Export attendance as a list of dicts suitable for CSV generation.

        Returns:
            list: Flat list of attendance row dicts
        """
        data = CourseAnalyticsService.get_lesson_attendance(
            course_id, lesson_id, user_id, user_role
        )
        return data.get("attendance", [])

    @staticmethod
    def add_recording(
        course_id: str,
        lesson_id: str,
        content_id: str,
        instructor_id: str,
        user_role: str,
        recording_url: str,
    ) -> dict:
        """Add / update a recording URL to a zoom content item."""
        from app.services.courses.course_service import CourseService

        CourseService.verify_course_owner(course_id, instructor_id, user_role)

        content = LessonContent.query.filter_by(
            content_id=content_id, lesson_id=lesson_id, content_type="zoom_live"
        ).first()
        if not content:
            raise ResourceNotFoundError("Zoom content not found")

        content.is_recorded = True
        content.recording_url = recording_url
        db.session.commit()

        return content.to_dict()

    @staticmethod
    def distribute_recording(
        course_id: str, lesson_id: str, recording_id: str, instructor_id: str, user_role: str
    ) -> dict:
        """
        Distribute (mark available) a recording to enrolled students.
        (Stub – notification integration can hook in here.)
        """
        from app.services.courses.course_service import CourseService

        CourseService.verify_course_owner(course_id, instructor_id, user_role)

        content = LessonContent.query.filter_by(
            content_id=recording_id, content_type="zoom_live"
        ).first()
        if not content:
            raise ResourceNotFoundError("Recording not found")

        return {
            "recording_id": recording_id,
            "lesson_id": lesson_id,
            "course_id": course_id,
            "recording_url": content.recording_url,
            "distributed": True,
            "message": "Recording distributed to enrolled students",
        }

    @staticmethod
    def get_recording_views(
        course_id: str, lesson_id: str, recording_id: str, instructor_id: str, user_role: str
    ) -> dict:
        """Get view statistics for a recording."""
        from app.services.courses.course_service import CourseService

        CourseService.verify_course_owner(course_id, instructor_id, user_role)

        view_count = LessonContentProgress.query.filter_by(
            content_id=recording_id, is_completed=True
        ).count()

        total_enrolled = CourseEnrollment.query.filter_by(course_id=course_id).count()

        return {
            "recording_id": recording_id,
            "lesson_id": lesson_id,
            "total_views": view_count,
            "total_enrolled": total_enrolled,
            "view_rate": round((view_count / total_enrolled) * 100, 1) if total_enrolled else 0,
        }
