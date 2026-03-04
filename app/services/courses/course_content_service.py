"""
Course Content Service
Handles CRUD for lesson content types: video, zoom_live, text, pdf, quiz
"""

import logging
import uuid
from datetime import datetime

from app import db
from app.exceptions import ResourceNotFoundError, ValidationError
from app.models.courses.course_lesson import CourseLesson
from app.models.courses.lesson_content import LessonContent
from app.services.base_service import BaseService

logger = logging.getLogger(__name__)

CONTENT_TYPES = ("video", "zoom_live", "text", "pdf", "quiz")


class CourseContentService(BaseService):
    """Service for managing lesson content items."""

    # ──────────────────────────────────────────────────────────────────────────
    # Internal helpers
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _verify_lesson_owner(course_id: str, lesson_id: str, user_id: str, user_role: str):
        """Verify lesson exists in course and user owns the course."""
        from app.services.courses.course_service import CourseService

        CourseService.verify_course_owner(course_id, user_id, user_role)

        lesson = CourseLesson.query.filter_by(
            lesson_id=lesson_id, course_id=course_id
        ).first()
        if not lesson:
            raise ResourceNotFoundError("Lesson not found in this course")
        return lesson

    @staticmethod
    def _next_content_order(lesson_id: str) -> int:
        last = (
            LessonContent.query.filter_by(lesson_id=lesson_id)
            .order_by(LessonContent.content_order.desc())
            .first()
        )
        return (last.content_order or 0) + 1 if last else 1

    # ──────────────────────────────────────────────────────────────────────────
    # Create
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def add_video_content(
        course_id: str,
        lesson_id: str,
        instructor_id: str,
        user_role: str,
        title: str,
        video_url: str,
        description: str = None,
        thumbnail_url: str = None,
        preview_url: str = None,
        video_duration_minutes: int = None,
        video_file_size_bytes: int = None,
        video_quality_available: str = None,
        content_order: int = None,
    ) -> dict:
        """Add a video content item to a lesson."""
        CourseContentService._verify_lesson_owner(course_id, lesson_id, instructor_id, user_role)

        if not video_url:
            raise ValidationError("video_url is required")

        content = LessonContent(
            content_id=str(uuid.uuid4()),
            lesson_id=lesson_id,
            course_id=course_id,
            content_type="video",
            title=title.strip(),
            description=description,
            content_order=content_order or CourseContentService._next_content_order(lesson_id),
            video_url=video_url,
            thumbnail_url=thumbnail_url,
            preview_url=preview_url,
            video_duration_minutes=video_duration_minutes,
            video_file_size_bytes=video_file_size_bytes,
            video_quality_available=video_quality_available,
        )
        db.session.add(content)
        db.session.commit()

        logger.info("Video content added to lesson %s", lesson_id)
        return content.to_dict()

    @staticmethod
    def update_video_content(
        course_id: str,
        lesson_id: str,
        content_id: str,
        instructor_id: str,
        user_role: str,
        **kwargs,
    ) -> dict:
        """Update a video content item."""
        CourseContentService._verify_lesson_owner(course_id, lesson_id, instructor_id, user_role)

        content = LessonContent.query.filter_by(
            content_id=content_id, lesson_id=lesson_id, content_type="video"
        ).first()
        if not content:
            raise ResourceNotFoundError("Video content not found")

        video_fields = [
            "title", "description", "content_order", "video_url", "thumbnail_url",
            "preview_url", "video_duration_minutes", "video_file_size_bytes",
            "video_quality_available",
        ]
        for field in video_fields:
            if field in kwargs and kwargs[field] is not None:
                setattr(content, field, kwargs[field])

        content.updated_at = datetime.utcnow()
        db.session.commit()
        return content.to_dict()

    @staticmethod
    def add_zoom_content(
        course_id: str,
        lesson_id: str,
        instructor_id: str,
        user_role: str,
        title: str,
        zoom_link: str,
        zoom_meeting_id: str = None,
        zoom_password: str = None,
        scheduled_date: datetime = None,
        scheduled_duration_minutes: int = None,
        description: str = None,
        content_order: int = None,
    ) -> dict:
        """Add a Zoom live class content item to a lesson."""
        CourseContentService._verify_lesson_owner(course_id, lesson_id, instructor_id, user_role)

        if not zoom_link:
            raise ValidationError("zoom_link is required")

        content = LessonContent(
            content_id=str(uuid.uuid4()),
            lesson_id=lesson_id,
            course_id=course_id,
            content_type="zoom_live",
            title=title.strip(),
            description=description,
            content_order=content_order or CourseContentService._next_content_order(lesson_id),
            zoom_link=zoom_link,
            zoom_meeting_id=zoom_meeting_id,
            zoom_password=zoom_password,
            scheduled_date=scheduled_date,
            scheduled_duration_minutes=scheduled_duration_minutes,
            is_recorded=False,
        )
        db.session.add(content)
        db.session.commit()

        logger.info("Zoom content added to lesson %s", lesson_id)
        return content.to_dict()

    @staticmethod
    def update_zoom_content(
        course_id: str,
        lesson_id: str,
        content_id: str,
        instructor_id: str,
        user_role: str,
        **kwargs,
    ) -> dict:
        """Update a Zoom content item."""
        CourseContentService._verify_lesson_owner(course_id, lesson_id, instructor_id, user_role)

        content = LessonContent.query.filter_by(
            content_id=content_id, lesson_id=lesson_id, content_type="zoom_live"
        ).first()
        if not content:
            raise ResourceNotFoundError("Zoom content not found")

        zoom_fields = [
            "title", "description", "content_order", "zoom_link", "zoom_meeting_id",
            "zoom_password", "scheduled_date", "scheduled_duration_minutes",
            "is_recorded", "recording_url",
        ]
        for field in zoom_fields:
            if field in kwargs and kwargs[field] is not None:
                setattr(content, field, kwargs[field])

        content.updated_at = datetime.utcnow()
        db.session.commit()
        return content.to_dict()

    @staticmethod
    def add_text_content(
        course_id: str,
        lesson_id: str,
        instructor_id: str,
        user_role: str,
        title: str,
        text_content: str,
        description: str = None,
        content_order: int = None,
    ) -> dict:
        """Add a text content item to a lesson."""
        CourseContentService._verify_lesson_owner(course_id, lesson_id, instructor_id, user_role)

        if not text_content:
            raise ValidationError("text_content is required")

        content = LessonContent(
            content_id=str(uuid.uuid4()),
            lesson_id=lesson_id,
            course_id=course_id,
            content_type="text",
            title=title.strip(),
            description=description,
            content_order=content_order or CourseContentService._next_content_order(lesson_id),
            text_content=text_content,
        )
        db.session.add(content)
        db.session.commit()

        logger.info("Text content added to lesson %s", lesson_id)
        return content.to_dict()

    @staticmethod
    def update_text_content(
        course_id: str,
        lesson_id: str,
        content_id: str,
        instructor_id: str,
        user_role: str,
        **kwargs,
    ) -> dict:
        """Update a text content item."""
        CourseContentService._verify_lesson_owner(course_id, lesson_id, instructor_id, user_role)

        content = LessonContent.query.filter_by(
            content_id=content_id, lesson_id=lesson_id, content_type="text"
        ).first()
        if not content:
            raise ResourceNotFoundError("Text content not found")

        for field in ["title", "description", "content_order", "text_content"]:
            if field in kwargs and kwargs[field] is not None:
                setattr(content, field, kwargs[field])

        content.updated_at = datetime.utcnow()
        db.session.commit()
        return content.to_dict()

    @staticmethod
    def add_pdf_content(
        course_id: str,
        lesson_id: str,
        instructor_id: str,
        user_role: str,
        title: str,
        pdf_file_url: str,
        description: str = None,
        pdf_file_size_bytes: int = None,
        content_order: int = None,
    ) -> dict:
        """Add a PDF content item to a lesson."""
        CourseContentService._verify_lesson_owner(course_id, lesson_id, instructor_id, user_role)

        if not pdf_file_url:
            raise ValidationError("pdf_file_url is required")

        content = LessonContent(
            content_id=str(uuid.uuid4()),
            lesson_id=lesson_id,
            course_id=course_id,
            content_type="pdf",
            title=title.strip(),
            description=description,
            content_order=content_order or CourseContentService._next_content_order(lesson_id),
            pdf_file_url=pdf_file_url,
            pdf_file_size_bytes=pdf_file_size_bytes,
        )
        db.session.add(content)
        db.session.commit()

        logger.info("PDF content added to lesson %s", lesson_id)
        return content.to_dict()

    @staticmethod
    def update_pdf_content(
        course_id: str,
        lesson_id: str,
        content_id: str,
        instructor_id: str,
        user_role: str,
        **kwargs,
    ) -> dict:
        """Update a PDF content item."""
        CourseContentService._verify_lesson_owner(course_id, lesson_id, instructor_id, user_role)

        content = LessonContent.query.filter_by(
            content_id=content_id, lesson_id=lesson_id, content_type="pdf"
        ).first()
        if not content:
            raise ResourceNotFoundError("PDF content not found")

        for field in ["title", "description", "content_order", "pdf_file_url", "pdf_file_size_bytes"]:
            if field in kwargs and kwargs[field] is not None:
                setattr(content, field, kwargs[field])

        content.updated_at = datetime.utcnow()
        db.session.commit()
        return content.to_dict()

    @staticmethod
    def add_quiz_content(
        course_id: str,
        lesson_id: str,
        instructor_id: str,
        user_role: str,
        title: str,
        quiz_id: str,
        passing_score: int = None,
        is_mandatory: bool = False,
        description: str = None,
        content_order: int = None,
    ) -> dict:
        """Add a quiz content item to a lesson."""
        CourseContentService._verify_lesson_owner(course_id, lesson_id, instructor_id, user_role)

        if not quiz_id:
            raise ValidationError("quiz_id is required")

        content = LessonContent(
            content_id=str(uuid.uuid4()),
            lesson_id=lesson_id,
            course_id=course_id,
            content_type="quiz",
            title=title.strip(),
            description=description,
            content_order=content_order or CourseContentService._next_content_order(lesson_id),
            quiz_id=quiz_id,
            passing_score=passing_score,
            is_mandatory=is_mandatory,
        )
        db.session.add(content)
        db.session.commit()

        logger.info("Quiz content added to lesson %s", lesson_id)
        return content.to_dict()

    @staticmethod
    def update_quiz_content(
        course_id: str,
        lesson_id: str,
        content_id: str,
        instructor_id: str,
        user_role: str,
        **kwargs,
    ) -> dict:
        """Update a quiz content item."""
        CourseContentService._verify_lesson_owner(course_id, lesson_id, instructor_id, user_role)

        content = LessonContent.query.filter_by(
            content_id=content_id, lesson_id=lesson_id, content_type="quiz"
        ).first()
        if not content:
            raise ResourceNotFoundError("Quiz content not found")

        for field in ["title", "description", "content_order", "quiz_id", "passing_score", "is_mandatory"]:
            if field in kwargs and kwargs[field] is not None:
                setattr(content, field, kwargs[field])

        content.updated_at = datetime.utcnow()
        db.session.commit()
        return content.to_dict()

    # ──────────────────────────────────────────────────────────────────────────
    # Delete
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def delete_content(
        course_id: str,
        lesson_id: str,
        content_id: str,
        instructor_id: str,
        user_role: str,
    ) -> None:
        """Delete any content item from a lesson."""
        CourseContentService._verify_lesson_owner(course_id, lesson_id, instructor_id, user_role)

        content = LessonContent.query.filter_by(
            content_id=content_id, lesson_id=lesson_id, course_id=course_id
        ).first()
        if not content:
            raise ResourceNotFoundError("Content not found")

        db.session.delete(content)
        db.session.commit()
        logger.info("Content %s deleted from lesson %s", content_id, lesson_id)

    # ──────────────────────────────────────────────────────────────────────────
    # Get course content (student / owner view)
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def get_course_content(course_id: str, user_id: str, user_role: str) -> dict:
        """
        Get full course content structure (sections → lessons → contents).
        Requires owner or enrollment.
        """
        from app.services.courses.course_service import CourseService
        from app.models.courses.course_section import CourseSection

        CourseService.verify_owner_or_enrolled(course_id, user_id, user_role)

        sections = (
            CourseSection.query.filter_by(course_id=course_id)
            .order_by(CourseSection.section_order.asc())
            .all()
        )

        result = []
        for section in sections:
            lessons = (
                CourseLesson.query.filter_by(section_id=section.section_id)
                .order_by(CourseLesson.lesson_order.asc())
                .all()
            )
            section_data = section.to_dict()
            section_data["lessons"] = []

            for lesson in lessons:
                contents = (
                    LessonContent.query.filter_by(lesson_id=lesson.lesson_id)
                    .order_by(LessonContent.content_order.asc())
                    .all()
                )
                lesson_data = lesson.to_dict()
                lesson_data["contents"] = [c.to_dict() for c in contents]
                section_data["lessons"].append(lesson_data)

            result.append(section_data)

        return {"course_id": course_id, "sections": result}

    @staticmethod
    def get_text_content(
        course_id: str, lesson_id: str, content_id: str, user_id: str, user_role: str
    ) -> dict:
        """Retrieve text content (owner or enrolled)."""
        from app.services.courses.course_service import CourseService

        CourseService.verify_owner_or_enrolled(course_id, user_id, user_role)

        content = LessonContent.query.filter_by(
            content_id=content_id, lesson_id=lesson_id, content_type="text"
        ).first()
        if not content:
            raise ResourceNotFoundError("Text content not found")

        return content.to_dict()
