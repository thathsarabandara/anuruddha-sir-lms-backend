"""
CourseReview Model
Represents student reviews and ratings for courses
"""

from app import db
from datetime import datetime
import uuid


class CourseReview(db.Model):
    """
    CourseReview model for student reviews and ratings of courses.
    
    Attributes:
        review_id: UUID primary key
        course_id: Foreign key to Course
        user_id: Foreign key to User (reviewer)
        rating: Rating value (1-5 scale)
        title: Review title (max 255 chars)
        review_text: Full review text content
        is_anonymous: Whether user identity is anonymous
        helpful_count: Number of helpful votes received
        created_at: Review creation timestamp
        updated_at: Last modification timestamp
    """
    
    __tablename__ = 'course_reviews'
    
    # Primary Key
    review_id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False
    )
    
    # Foreign Keys
    course_id = db.Column(
        db.String(36),
        db.ForeignKey('courses.course_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    user_id = db.Column(
        db.String(36),
        db.ForeignKey('users.user_id', ondelete='CASCADE'),
        nullable=False
    )
    
    # Review Content
    rating = db.Column(
        db.Integer,
        nullable=False
    )
    title = db.Column(
        db.String(255),
        nullable=True
    )
    review_text = db.Column(
        db.Text,
        nullable=True
    )
    
    # Review Settings
    is_anonymous = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )
    helpful_count = db.Column(
        db.Integer,
        default=0,
        nullable=False
    )
    
    # Timestamps
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    def __repr__(self):
        return f"<CourseReview {self.review_id} - {self.rating}/5>"
    
    def to_dict(self):
        """Convert review to dictionary for JSON serialization."""
        return {
            'review_id': self.review_id,
            'course_id': self.course_id,
            'user_id': self.user_id if not self.is_anonymous else None,
            'rating': self.rating,
            'title': self.title,
            'review_text': self.review_text,
            'is_anonymous': self.is_anonymous,
            'helpful_count': self.helpful_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
