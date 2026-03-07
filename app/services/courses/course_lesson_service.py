"""
Course Lesson Service
Handles creation and management of lessons within sections
"""

import logging
import uuid
from datetime import datetime

from app import db
from app.exceptions import ResourceNotFoundError
from app.models.courses.course_lesson import CourseLesson
from app.models.courses.course_section import CourseSection
from app.services.base_service import BaseService

logger = logging.getLogger(__name__)


class CourseLessonService(BaseService):
    """Service for managing course lessons."""

    @staticmethod
    def create_lesson(
        course_id: str,
        section_id: str,
        instructor_id: str,
        user_role: str,
        title: str,
        description: str = None,
        duration_minutes: int = None,
        lesson_order: int = None,
    ) -> dict:
        """
        Create a lesson within a section.

        Args:
            course_id: Course UUID
            section_id: Section UUID
            instructor_id: Requesting instructor ID
            user_role: Role of requestor
            title: Lesson title
            description: Optional description
            duration_minutes: Estimated duration
            lesson_order: Position in section (auto-assigned if None)

        Returns:
            dict: Created lesson data

        Raises:
            ResourceNotFoundError: Course or section not found
            AuthorizationError: Not the owner
        """
        from app.services.courses.course_service import CourseService

        CourseService.verify_course_owner(course_id, instructor_id, user_role)

        section = CourseSection.query.filter_by(
            section_id=section_id, course_id=course_id
        ).first()
        if not section:
            raise ResourceNotFoundError("Section not found in this course")

        if lesson_order is None:
            last = (
                CourseLesson.query.filter_by(section_id=section_id)
                .order_by(CourseLesson.lesson_order.desc())
                .first()
            )
            lesson_order = (last.lesson_order or 0) + 1 if last else 1

        lesson = CourseLesson(
            lesson_id=str(uuid.uuid4()),
            section_id=section_id,
            course_id=course_id,
            title=title.strip(),
            description=description,
            duration_minutes=duration_minutes,
            lesson_order=lesson_order,
        )
        db.session.add(lesson)
        db.session.commit()

        logger.info("Lesson created in section %s: %s", section_id, lesson.lesson_id)
        return lesson.to_dict()

    @staticmethod
    def get_lessons(course_id: str, section_id: str) -> list:
        """Return all lessons in a section ordered by lesson_order."""
        lessons = (
            CourseLesson.query.filter_by(section_id=section_id, course_id=course_id)
            .order_by(CourseLesson.lesson_order.asc())
            .all()
        )
        return [l.to_dict() for l in lessons]

    @staticmethod
    def update_lesson(
        course_id: str,
        lesson_id: str,
        instructor_id: str,
        user_role: str,
        **kwargs,
    ) -> dict:
        """Update lesson fields."""
        from app.services.courses.course_service import CourseService

        CourseService.verify_course_owner(course_id, instructor_id, user_role)

        lesson = CourseLesson.query.filter_by(
            lesson_id=lesson_id, course_id=course_id
        ).first()
        if not lesson:
            raise ResourceNotFoundError("Lesson not found")

        for field in ["title", "description", "duration_minutes", "lesson_order"]:
            if field in kwargs and kwargs[field] is not None:
                setattr(lesson, field, kwargs[field])

        lesson.updated_at = datetime.utcnow()
        db.session.commit()
        return lesson.to_dict()

    @staticmethod
    def delete_lesson(
        course_id: str, lesson_id: str, instructor_id: str, user_role: str
    ) -> None:
        """Delete a lesson and cascade-delete its contents."""
        from app.services.courses.course_service import CourseService

        CourseService.verify_course_owner(course_id, instructor_id, user_role)

        lesson = CourseLesson.query.filter_by(
            lesson_id=lesson_id, course_id=course_id
        ).first()
        if not lesson:
            raise ResourceNotFoundError("Lesson not found")

        db.session.delete(lesson)
        db.session.commit()
        logger.info("Lesson %s deleted from course %s", lesson_id, course_id)
