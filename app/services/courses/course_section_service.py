"""
Course Section Service
Handles creation and management of course sections
"""

import logging
import uuid
from datetime import datetime

from app import db
from app.exceptions import ResourceNotFoundError
from app.models.courses.course_section import CourseSection
from app.services.base_service import BaseService

logger = logging.getLogger(__name__)


class CourseSectionService(BaseService):
    """Service for managing course sections."""

    @staticmethod
    def create_section(
        course_id: str,
        instructor_id: str,
        user_role: str,
        title: str,
        description: str = None,
        section_order: int = None,
    ) -> dict:
        """
        Create a new section within a course.

        Args:
            course_id: Course UUID
            instructor_id: Requesting instructor ID
            user_role: Role of requestor
            title: Section title
            description: Optional description
            section_order: Position in course (auto-assigned if None)

        Returns:
            dict: Created section data

        Raises:
            ResourceNotFoundError: Course not found
            AuthorizationError: Not the owner
        """
        from app.services.courses.course_service import CourseService

        CourseService.verify_course_owner(course_id, instructor_id, user_role)

        if section_order is None:
            last = (
                CourseSection.query.filter_by(course_id=course_id)
                .order_by(CourseSection.section_order.desc())
                .first()
            )
            section_order = (last.section_order or 0) + 1 if last else 1

        section = CourseSection(
            section_id=str(uuid.uuid4()),
            course_id=course_id,
            title=title.strip(),
            description=description,
            section_order=section_order,
        )
        db.session.add(section)
        db.session.commit()

        logger.info("Section created for course %s: %s", course_id, section.section_id)
        return section.to_dict()

    @staticmethod
    def get_sections(course_id: str) -> list:
        """Return all sections of a course ordered by section_order."""
        sections = (
            CourseSection.query.filter_by(course_id=course_id)
            .order_by(CourseSection.section_order.asc())
            .all()
        )
        return [s.to_dict() for s in sections]

    @staticmethod
    def update_section(
        course_id: str,
        section_id: str,
        instructor_id: str,
        user_role: str,
        title: str = None,
        description: str = None,
        section_order: int = None,
    ) -> dict:
        """Update a section."""
        from app.services.courses.course_service import CourseService

        CourseService.verify_course_owner(course_id, instructor_id, user_role)

        section = CourseSection.query.filter_by(
            section_id=section_id, course_id=course_id
        ).first()
        if not section:
            raise ResourceNotFoundError("Section not found")

        if title:
            section.title = title.strip()
        if description is not None:
            section.description = description
        if section_order is not None:
            section.section_order = section_order

        section.updated_at = datetime.utcnow()
        db.session.commit()
        return section.to_dict()

    @staticmethod
    def delete_section(
        course_id: str, section_id: str, instructor_id: str, user_role: str
    ) -> None:
        """Delete a section and cascade-delete its lessons and contents."""
        from app.services.courses.course_service import CourseService

        CourseService.verify_course_owner(course_id, instructor_id, user_role)

        section = CourseSection.query.filter_by(
            section_id=section_id, course_id=course_id
        ).first()
        if not section:
            raise ResourceNotFoundError("Section not found")

        db.session.delete(section)
        db.session.commit()
        logger.info("Section %s deleted from course %s", section_id, course_id)
