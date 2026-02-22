"""
ReviewResponse Model
Instructor responses to course reviews
"""

import uuid
from datetime import datetime

from app import db


class ReviewResponse(db.Model):
    """
    ReviewResponse model for instructor responses to student reviews.

    Attributes:
        response_id: UUID primary key
        review_id: Foreign key to Review
        course_id: Foreign key to Course
        instructor_id: Foreign key to User (instructor/responder)
        response_text: Response content
        created_at: Response creation timestamp
        updated_at: Last update timestamp
    """

    __tablename__ = "review_responses"

    # Primary Key
    response_id = db.Column(
        db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False
    )

    # Foreign Keys
    review_id = db.Column(
        db.String(36),
        db.ForeignKey("reviews.review_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    course_id = db.Column(
        db.String(36), db.ForeignKey("courses.course_id", ondelete="CASCADE"), nullable=False
    )
    instructor_id = db.Column(
        db.String(36), db.ForeignKey("users.user_id"), nullable=False, index=True
    )

    # Response Content
    response_text = db.Column(db.Text, nullable=False)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def __repr__(self):
        return f"<ReviewResponse {self.response_id}>"

    def to_dict(self):
        """Convert response to dictionary for JSON serialization."""
        return {
            "response_id": self.response_id,
            "review_id": self.review_id,
            "course_id": self.course_id,
            "instructor_id": self.instructor_id,
            "response_text": self.response_text,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
