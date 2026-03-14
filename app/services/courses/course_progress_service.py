"""
Course Progress Service
Handles lesson completion, watch progress, zoom attendance, and overall course progress
"""

import logging
import uuid
from datetime import datetime

from app import db
from app.exceptions import ResourceNotFoundError, ValidationError
from app.models.courses.course_enrollment import CourseEnrollment
from app.models.courses.course_lesson import CourseLesson
from app.models.courses.lesson_content import LessonContent
from app.models.courses.lesson_content_progress import LessonContentProgress
from app.services.health.base_service import BaseService

logger = logging.getLogger(__name__)


class CourseProgressService(BaseService):
    """Service for tracking student progress through course content."""

    # ──────────────────────────────────────────────────────────────────────────
    # Watch Progress (video)
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def update_watch_progress(
        course_id: str,
        lesson_id: str,
        content_id: str,
        user_id: str,
        user_role: str,
        watched_percentage: int,
        current_position_seconds: int = 0,
        quality_watched: str = None,
        watch_time_seconds: int = 0,
    ) -> dict:
        """
        Update video watch progress for a student.

        Args:
            course_id: Course UUID
            lesson_id: Lesson UUID
            content_id: Content UUID
            user_id: Student user ID
            user_role: Role of user
            watched_percentage: 0-100
            current_position_seconds: Playback position
            quality_watched: Video quality string
            watch_time_seconds: Additional watch time in this session

        Returns:
            dict: Updated progress record
        """
        from app.services.courses.course_service import CourseService

        CourseService.verify_owner_or_enrolled(course_id, user_id, user_role)

        content = LessonContent.query.filter_by(
            content_id=content_id, lesson_id=lesson_id, content_type="video"
        ).first()
        if not content:
            raise ResourceNotFoundError("Video content not found")

        progress = LessonContentProgress.query.filter_by(
            content_id=content_id, user_id=user_id
        ).first()

        now = datetime.utcnow()

        if not progress:
            progress = LessonContentProgress(
                progress_id=str(uuid.uuid4()),
                content_id=content_id,
                lesson_id=lesson_id,
                user_id=user_id,
                course_id=course_id,
                first_accessed=now,
            )
            db.session.add(progress)

        progress.last_accessed = now
        progress.video_watched_percentage = max(
            progress.video_watched_percentage or 0, watched_percentage
        )
        progress.video_current_position_seconds = current_position_seconds
        progress.video_total_watch_time_seconds = (
            (progress.video_total_watch_time_seconds or 0) + watch_time_seconds
        )
        if quality_watched:
            progress.video_quality_watched = quality_watched
        progress.video_watch_count = (progress.video_watch_count or 0) + 1

        # Mark complete when fully watched
        if watched_percentage >= 100 and not progress.is_completed:
            progress.is_completed = True
            progress.completed_at = now

        db.session.commit()

        # Recalculate overall enrollment progress
        CourseProgressService._recalculate_enrollment_progress(course_id, user_id)

        return CourseProgressService._to_dict(progress)

    # ──────────────────────────────────────────────────────────────────────────
    # Zoom Attendance
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def record_zoom_attendance(
        course_id: str,
        lesson_id: str,
        content_id: str,
        user_id: str,
        user_role: str,
        joined_at: datetime = None,
        left_at: datetime = None,
        device_type: str = None,
    ) -> dict:
        """Record zoom class attendance for a student."""
        from app.services.courses.course_service import CourseService

        CourseService.verify_owner_or_enrolled(course_id, user_id, user_role)

        content = LessonContent.query.filter_by(
            content_id=content_id, lesson_id=lesson_id, content_type="zoom_live"
        ).first()
        if not content:
            raise ResourceNotFoundError("Zoom content not found")

        progress = LessonContentProgress.query.filter_by(
            content_id=content_id, user_id=user_id
        ).first()

        now = datetime.utcnow()

        if not progress:
            progress = LessonContentProgress(
                progress_id=str(uuid.uuid4()),
                content_id=content_id,
                lesson_id=lesson_id,
                user_id=user_id,
                course_id=course_id,
                first_accessed=now,
            )
            db.session.add(progress)

        progress.zoom_attended = True
        progress.zoom_joined_at = joined_at or now
        if left_at:
            progress.zoom_left_at = left_at
            if joined_at:
                duration = (left_at - joined_at).seconds // 60
                progress.zoom_attended_duration_minutes = duration
        if device_type:
            progress.zoom_device_type = device_type
        progress.last_accessed = now
        progress.is_completed = True
        progress.completed_at = now

        db.session.commit()
        CourseProgressService._recalculate_enrollment_progress(course_id, user_id)

        return CourseProgressService._to_dict(progress)

    # ──────────────────────────────────────────────────────────────────────────
    # Lesson Completion
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def complete_lesson(
        course_id: str, lesson_id: str, user_id: str, user_role: str
    ) -> dict:
        """
        Mark all content items in a lesson as complete for a student.

        Returns:
            dict: Updated enrollment progress
        """
        from app.services.courses.course_service import CourseService

        CourseService.verify_owner_or_enrolled(course_id, user_id, user_role)

        lesson = CourseLesson.query.filter_by(
            lesson_id=lesson_id, course_id=course_id
        ).first()
        if not lesson:
            raise ResourceNotFoundError("Lesson not found")

        contents = LessonContent.query.filter_by(lesson_id=lesson_id).all()
        now = datetime.utcnow()

        for content in contents:
            progress = LessonContentProgress.query.filter_by(
                content_id=content.content_id, user_id=user_id
            ).first()
            if not progress:
                progress = LessonContentProgress(
                    progress_id=str(uuid.uuid4()),
                    content_id=content.content_id,
                    lesson_id=lesson_id,
                    user_id=user_id,
                    course_id=course_id,
                    first_accessed=now,
                )
                db.session.add(progress)

            if not progress.is_completed:
                progress.is_completed = True
                progress.completed_at = now
            progress.last_accessed = now

        db.session.commit()
        return CourseProgressService._recalculate_enrollment_progress(course_id, user_id)

    # ──────────────────────────────────────────────────────────────────────────
    # Overall Progress
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def get_course_progress(course_id: str, user_id: str, user_role: str) -> dict:
        """
        Get overall course progress for a student.

        Returns:
            dict: Progress summary including per-lesson status
        """
        from app.services.courses.course_service import CourseService

        CourseService.verify_owner_or_enrolled(course_id, user_id, user_role)

        enrollment = CourseEnrollment.query.filter_by(
            course_id=course_id, user_id=user_id
        ).first()

        all_contents = LessonContent.query.filter_by(course_id=course_id).all()
        total_contents = len(all_contents)

        completed_progress = LessonContentProgress.query.filter_by(
            course_id=course_id, user_id=user_id, is_completed=True
        ).count()

        overall_percentage = 0
        if total_contents > 0:
            overall_percentage = int((completed_progress / total_contents) * 100)

        return {
            "course_id": course_id,
            "user_id": user_id,
            "overall_progress": overall_percentage,
            "completed_contents": completed_progress,
            "total_contents": total_contents,
            "enrollment_status": enrollment.status if enrollment else None,
            "enrollment_progress": enrollment.progress if enrollment else 0,
            "total_time_spent_minutes": enrollment.total_time_spent_minutes if enrollment else 0,
            "last_accessed": enrollment.last_accessed.isoformat() if enrollment and enrollment.last_accessed else None,
        }

    # ──────────────────────────────────────────────────────────────────────────
    # Internal
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _recalculate_enrollment_progress(course_id: str, user_id: str) -> dict:
        """Recalculate and persist enrollment.progress percentage."""
        all_contents = LessonContent.query.filter_by(course_id=course_id).count()
        completed = LessonContentProgress.query.filter_by(
            course_id=course_id, user_id=user_id, is_completed=True
        ).count()

        percentage = int((completed / all_contents) * 100) if all_contents > 0 else 0

        enrollment = CourseEnrollment.query.filter_by(
            course_id=course_id, user_id=user_id
        ).first()
        if enrollment:
            enrollment.progress = percentage
            enrollment.last_accessed = datetime.utcnow()
            if percentage >= 100:
                enrollment.status = "completed"
                enrollment.completed_at = datetime.utcnow()
            elif percentage > 0:
                enrollment.status = "in_progress"
            db.session.commit()
            return enrollment.to_dict()

        return {"progress": percentage}

    @staticmethod
    def _to_dict(progress: "LessonContentProgress") -> dict:
        """Serialize a progress record."""
        return {
            "progress_id": progress.progress_id,
            "content_id": progress.content_id,
            "lesson_id": progress.lesson_id,
            "user_id": progress.user_id,
            "course_id": progress.course_id,
            "is_completed": progress.is_completed,
            "completed_at": progress.completed_at.isoformat() if progress.completed_at else None,
            "first_accessed": progress.first_accessed.isoformat() if progress.first_accessed else None,
            "last_accessed": progress.last_accessed.isoformat() if progress.last_accessed else None,
            "video_watched_percentage": progress.video_watched_percentage,
            "video_current_position_seconds": progress.video_current_position_seconds,
            "video_watch_count": progress.video_watch_count,
            "video_quality_watched": progress.video_quality_watched,
            "video_total_watch_time_seconds": progress.video_total_watch_time_seconds,
            "zoom_attended": progress.zoom_attended,
            "zoom_joined_at": progress.zoom_joined_at.isoformat() if progress.zoom_joined_at else None,
            "zoom_left_at": progress.zoom_left_at.isoformat() if progress.zoom_left_at else None,
            "zoom_attended_duration_minutes": progress.zoom_attended_duration_minutes,
            "pdf_downloaded": progress.pdf_downloaded,
            "pdf_download_count": progress.pdf_download_count,
            "quiz_attempted": progress.quiz_attempted,
            "quiz_score": progress.quiz_score,
            "quiz_attempt_count": progress.quiz_attempt_count,
        }
