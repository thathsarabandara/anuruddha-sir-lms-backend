"""
Course Service
Handles core course CRUD operations, search, and category management
"""

import logging
import re
import uuid
from datetime import datetime

from sqlalchemy import or_

from app import db
from app.exceptions import AuthorizationError, ConflictError, ResourceNotFoundError, ValidationError
from app.models.courses.course import Course
from app.models.courses.course_category import CourseCategory
from app.services.base_service import BaseService

logger = logging.getLogger(__name__)


def _slugify(title: str) -> str:
    """Generate a URL-friendly slug from a title."""
    slug = title.lower().strip()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"[\s_-]+", "-", slug)
    slug = re.sub(r"^-+|-+$", "", slug)
    return slug


class CourseService(BaseService):
    """Service for core course operations."""

    # ──────────────────────────────────────────────────────────────────────────
    # Create
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def create_course(
        instructor_id: str,
        title: str,
        description: str = None,
        category_id: str = None,
        difficulty: str = None,
        grade_level: str = None,
        language: str = "en",
        duration_hours: int = None,
        is_paid: bool = False,
        price: float = None,
        course_type: str = "monthly",
        visibility: str = "public",
        thumbnail_url: str = None,
    ) -> dict:
        """
        Create a new course.

        Args:
            instructor_id: Teacher user ID
            title: Course title
            description: Course description
            category_id: Category UUID
            difficulty: beginner / intermediate / advanced
            grade_level: Grade level for the course (e.g., "1", "2", "3-5")
            language: Language code (default 'en')
            duration_hours: Estimated duration
            is_paid: Whether course requires payment
            price: Course price (required if is_paid)
            course_type: monthly / paper / quiz / special
            visibility: public / private
            thumbnail_url: URL of uploaded thumbnail

        Returns:
            dict: Created course data

        Raises:
            ValidationError: On missing or invalid fields
            ConflictError: If title/slug already exists
        """
        try:
            if not title or not title.strip():
                raise ValidationError("Course title is required")

            if is_paid and not price:
                raise ValidationError("Price is required for paid courses")

            if category_id:
                cat = CourseCategory.query.get(category_id)
                if not cat:
                    raise ValidationError("Invalid category ID")

            # Generate unique slug
            base_slug = _slugify(title)
            slug = base_slug
            suffix = 1
            while Course.query.filter_by(slug=slug).first():
                slug = f"{base_slug}-{suffix}"
                suffix += 1

            course = Course(
                course_id=str(uuid.uuid4()),
                instructor_id=instructor_id,
                title=title.strip(),
                slug=slug,
                description=description,
                category_id=category_id,
                difficulty=difficulty,
                grade_level=grade_level,
                language=language or "en",
                duration_hours=duration_hours,
                is_paid=is_paid,
                price=price if is_paid else None,
                course_type=course_type or "monthly",
                visibility=visibility or "public",
                status="draft",
                thumbnail_url=thumbnail_url,
            )
            db.session.add(course)
            db.session.commit()

            logger.info("Course created: %s by instructor %s", course.course_id, instructor_id)
            return course.to_dict()

        except (ValidationError, ConflictError):
            db.session.rollback()
            raise
        except Exception as e:
            db.session.rollback()
            logger.error("Error creating course: %s", str(e))
            raise

    # ──────────────────────────────────────────────────────────────────────────
    # Read
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def get_course(course_id: str) -> dict:
        """
        Get a single course by ID.

        Args:
            course_id: Course UUID

        Returns:
            dict: Course data

        Raises:
            ResourceNotFoundError: If course not found
        """
        course = Course.query.get(course_id)
        if not course:
            raise ResourceNotFoundError("Course not found")
        return course.to_dict()

    @staticmethod
    def search_courses(
        query: str = None,
        category_id: str = None,
        course_type: str = None,
        difficulty: str = None,
        grade_level: str = None,
        language: str = None,
        is_paid: bool = None,
        status: str = "published",
        visibility: str = "public",
        page: int = 1,
        limit: int = 20,
    ) -> dict:
        """
        Search and filter published public courses.

        Returns:
            dict: Paginated course list
        """
        q = Course.query.filter(
            Course.status == status,
            Course.visibility == visibility,
        )

        if query:
            like = f"%{query}%"
            q = q.filter(or_(Course.title.ilike(like), Course.description.ilike(like)))

        if category_id:
            q = q.filter(Course.category_id == category_id)
        if course_type:
            q = q.filter(Course.course_type == course_type)
        if difficulty:
            q = q.filter(Course.difficulty == difficulty)
        if grade_level:
            q = q.filter(Course.grade_level == grade_level)
        if language:
            q = q.filter(Course.language == language)
        if is_paid is not None:
            q = q.filter(Course.is_paid == is_paid)

        total = q.count()
        offset = (page - 1) * limit
        courses = q.order_by(Course.created_at.desc()).offset(offset).limit(limit).all()

        return {
            "courses": [c.to_dict() for c in courses],
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit,
        }

    # ──────────────────────────────────────────────────────────────────────────
    # Update
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def update_course(course_id: str, instructor_id: str, user_role: str, **kwargs) -> dict:
        """
        Update course details. Only the course owner or admin can update.

        Args:
            course_id: Course UUID
            instructor_id: Requesting user ID
            user_role: Requesting user role
            **kwargs: Fields to update

        Returns:
            dict: Updated course data

        Raises:
            ResourceNotFoundError: Course not found
            AuthorizationError: Not the owner
        """
        course = Course.query.get(course_id)
        if not course:
            raise ResourceNotFoundError("Course not found")

        if user_role != "admin" and course.instructor_id != instructor_id:
            raise AuthorizationError("You do not have permission to update this course")

        allowed_fields = [
            "title", "description", "category_id", "difficulty", "grade_level", "language",
            "duration_hours", "is_paid", "price", "course_type", "visibility",
            "thumbnail_url",
        ]

        for field in allowed_fields:
            if field in kwargs and kwargs[field] is not None:
                setattr(course, field, kwargs[field])

        # Re-slug if title changed
        if "title" in kwargs and kwargs["title"]:
            new_title = kwargs["title"].strip()
            course.title = new_title
            base_slug = _slugify(new_title)
            slug = base_slug
            suffix = 1
            while True:
                existing = Course.query.filter(
                    Course.slug == slug, Course.course_id != course_id
                ).first()
                if not existing:
                    break
                slug = f"{base_slug}-{suffix}"
                suffix += 1
            course.slug = slug

        course.updated_at = datetime.utcnow()
        db.session.commit()

        logger.info("Course updated: %s", course_id)
        return course.to_dict()

    # ──────────────────────────────────────────────────────────────────────────
    # Delete
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def delete_course(course_id: str, instructor_id: str, user_role: str) -> None:
        """
        Delete a course. Blocked if students are enrolled.

        Args:
            course_id: Course UUID
            instructor_id: Requesting user ID
            user_role: Requesting user role

        Raises:
            ResourceNotFoundError: Course not found
            AuthorizationError: Not the owner
            ConflictError: Course has active enrollments
        """
        from app.models.courses.course_enrollment import CourseEnrollment

        course = Course.query.get(course_id)
        if not course:
            raise ResourceNotFoundError("Course not found")

        if user_role != "admin" and course.instructor_id != instructor_id:
            raise AuthorizationError("You do not have permission to delete this course")

        enrollment_count = CourseEnrollment.query.filter_by(course_id=course_id).count()
        if enrollment_count > 0:
            raise ConflictError(
                f"Cannot delete course with {enrollment_count} enrolled student(s). "
                "Archive the course instead."
            )

        db.session.delete(course)
        db.session.commit()
        logger.info("Course deleted: %s by %s", course_id, instructor_id)

    # ──────────────────────────────────────────────────────────────────────────
    # Categories
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def get_categories() -> list:
        """Return all course categories."""
        categories = CourseCategory.query.order_by(CourseCategory.name.asc()).all()
        return [c.to_dict() for c in categories]

    @staticmethod
    def verify_course_owner(course_id: str, user_id: str, user_role: str) -> "Course":
        """
        Verify user is the course owner (or admin).

        Returns:
            Course: The course instance

        Raises:
            ResourceNotFoundError: Course not found
            AuthorizationError: Not the owner
        """
        course = Course.query.get(course_id)
        if not course:
            raise ResourceNotFoundError("Course not found")
        if user_role != "admin" and course.instructor_id != user_id:
            raise AuthorizationError("Forbidden: You do not have permission to access this course")
        return course

    @staticmethod
    def verify_owner_or_enrolled(course_id: str, user_id: str, user_role: str) -> "Course":
        """
        Verify user is the course owner OR an enrolled student (or admin).

        Returns:
            Course: The course instance

        Raises:
            ResourceNotFoundError: Course not found
            AuthorizationError: Not enrolled or owner
        """
        from app.models.courses.course_enrollment import CourseEnrollment

        course = Course.query.get(course_id)
        if not course:
            raise ResourceNotFoundError("Course not found")

        if user_role == "admin":
            return course

        if course.instructor_id == user_id:
            return course

        enrollment = CourseEnrollment.query.filter_by(
            course_id=course_id, user_id=user_id
        ).first()
        if not enrollment:
            raise AuthorizationError("Forbidden: You must be enrolled or be the course owner")

        return course
