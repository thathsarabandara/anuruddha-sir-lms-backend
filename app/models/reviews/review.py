"""
Review Model
Course and content reviews with ratings
"""

from app import db
from datetime import datetime
import uuid


class Review(db.Model):
    """
    Review model for course reviews with ratings and helpfulness tracking.
    
    Attributes:
        review_id: UUID primary key
        course_id: Foreign key to Course
        user_id: Foreign key to User (reviewer)
        rating: Rating 1-5 stars
        title: Review title
        review_text: Review content
        is_anonymous: Whether review is anonymous
        verified_purchase: Whether user completed course
        would_recommend: Would recommend flag
        status: ENUM(pending, approved, rejected, deleted)
        helpful_count: Count of helpful votes
        unhelpful_count: Count of unhelpful votes
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """
    
    __tablename__ = 'reviews'
    
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
    
    # Rating
    rating = db.Column(
        db.Integer,
        nullable=False,
        index=True
    )
    
    # Review Content
    title = db.Column(
        db.String(255),
        nullable=True
    )
    review_text = db.Column(
        db.Text,
        nullable=True
    )
    
    # Review Metadata
    is_anonymous = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )
    verified_purchase = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )
    would_recommend = db.Column(
        db.Boolean,
        nullable=True
    )
    
    # Status & Moderation
    status = db.Column(
        db.Enum(
            'pending',
            'approved',
            'rejected',
            'deleted'
        ),
        default='pending',
        nullable=False,
        index=True
    )
    
    # Helpfulness Tracking
    helpful_count = db.Column(
        db.Integer,
        default=0,
        nullable=False
    )
    unhelpful_count = db.Column(
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
    
    # Relationships
    responses = db.relationship(
        'ReviewResponse',
        backref='review',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    votes = db.relationship(
        'ReviewVote',
        backref='review',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    flags = db.relationship(
        'ReviewFlag',
        backref='review',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    
    def __repr__(self):
        return f"<Review {self.review_id} - {self.rating} stars>"
    
    def to_dict(self):
        """Convert review to dictionary for JSON serialization."""
        return {
            'review_id': self.review_id,
            'course_id': self.course_id,
            'user_id': self.user_id,
            'rating': self.rating,
            'title': self.title,
            'review_text': self.review_text,
            'is_anonymous': self.is_anonymous,
            'verified_purchase': self.verified_purchase,
            'would_recommend': self.would_recommend,
            'status': self.status,
            'helpful_count': self.helpful_count,
            'unhelpful_count': self.unhelpful_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
