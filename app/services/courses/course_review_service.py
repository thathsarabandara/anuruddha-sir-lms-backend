"""
Course Review Service
Handles student course reviews and ratings
"""

import logging
import uuid
from datetime import datetime

from sqlalchemy import func

from app import db
from app.exceptions import AuthorizationError, ConflictError, ResourceNotFoundError, ValidationError
from app.models.courses.course import Course
from app.models.courses.course_enrollment import CourseEnrollment
from app.models.courses.course_review import CourseReview
from app.services.health.base_service import BaseService

logger = logging.getLogger(__name__)


class CourseReviewService(BaseService):
    """Service for managing course reviews."""

    # ──────────────────────────────────────────────────────────────────────────
    # Create
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def create_review(
        course_id: str,
        user_id: str,
        user_role: str,
        rating: int,
        review_text: str = None,
        title: str = None,
        is_anonymous: bool = False,
    ) -> dict:
        """
        Create a review for a course.

        Only enrolled students (or course owner / admin) can review.
        One review per student per course.

        Args:
            course_id: Course UUID
            user_id: Reviewer user ID
            user_role: User role
            rating: Integer 1-5
            review_text: Optional review body
            title: Optional review title
            is_anonymous: Whether to display anonymously

        Returns:
            dict: Created review data

        Raises:
            ValidationError: Invalid rating
            ConflictError: Review already submitted
            AuthorizationError: Not enrolled
        """
        from app.services.courses.course_service import CourseService

        # Must be enrolled or owner/admin
        CourseService.verify_owner_or_enrolled(course_id, user_id, user_role)

        if not isinstance(rating, int) or rating < 1 or rating > 5:
            raise ValidationError("Rating must be an integer between 1 and 5")

        existing = CourseReview.query.filter_by(
            course_id=course_id, user_id=user_id
        ).first()
        if existing:
            raise ConflictError("You have already reviewed this course")

        review = CourseReview(
            review_id=str(uuid.uuid4()),
            course_id=course_id,
            user_id=user_id,
            rating=rating,
            review_text=review_text,
            title=title,
            is_anonymous=is_anonymous,
            helpful_count=0,
        )
        db.session.add(review)

        # Update course aggregate rating
        CourseReviewService._update_course_rating(course_id, db.session)

        db.session.commit()

        logger.info("Review created for course %s by user %s", course_id, user_id)
        return review.to_dict()

    # ──────────────────────────────────────────────────────────────────────────
    # Read
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def get_reviews(
        course_id: str,
        page: int = 1,
        limit: int = 20,
        sort: str = "newest",
    ) -> dict:
        """
        Get public reviews for a course (no auth required).

        Returns:
            dict: Paginated review list
        """
        q = CourseReview.query.filter_by(course_id=course_id)

        if sort == "highest":
            q = q.order_by(CourseReview.rating.desc())
        elif sort == "lowest":
            q = q.order_by(CourseReview.rating.asc())
        elif sort == "helpful":
            q = q.order_by(CourseReview.helpful_count.desc())
        else:
            q = q.order_by(CourseReview.created_at.desc())

        total = q.count()
        offset = (page - 1) * limit
        reviews = q.offset(offset).limit(limit).all()

        return {
            "reviews": [r.to_dict() for r in reviews],
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit,
        }

    # ──────────────────────────────────────────────────────────────────────────
    # Internal
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _update_course_rating(course_id: str, session) -> None:
        """Recalculate and persist average rating on course."""
        result = session.query(
            func.avg(CourseReview.rating).label("avg"),
            func.count(CourseReview.review_id).label("cnt"),
        ).filter(CourseReview.course_id == course_id).first()

        course = Course.query.get(course_id)
        if course:
            course.rating = round(float(result.avg), 2) if result.avg else None
            course.total_reviews = result.cnt or 0
