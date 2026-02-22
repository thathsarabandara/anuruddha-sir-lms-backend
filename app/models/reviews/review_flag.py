"""
ReviewFlag Model
Flagging inappropriate reviews for moderation
"""

from app import db
from datetime import datetime
import uuid


class ReviewFlag(db.Model):
    """
    ReviewFlag model for flagging reviews for content moderation.
    
    Attributes:
        flag_id: UUID primary key
        review_id: Foreign key to Review
        flagged_by: Foreign key to User (flagger)
        reason: ENUM(spam, harassment, misinformation, other)
        description: Detailed flag reason
        status: ENUM(pending, reviewed, resolved)
        flagged_at: Flag creation timestamp
    """
    
    __tablename__ = 'review_flags'
    
    # Primary Key
    flag_id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False
    )
    
    # Foreign Keys
    review_id = db.Column(
        db.String(36),
        db.ForeignKey('reviews.review_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    flagged_by = db.Column(
        db.String(36),
        db.ForeignKey('users.user_id'),
        nullable=False
    )
    
    # Flag Information
    reason = db.Column(
        db.Enum(
            'spam',
            'harassment',
            'misinformation',
            'other'
        ),
        nullable=True
    )
    description = db.Column(
        db.Text,
        nullable=True
    )
    
    # Status
    status = db.Column(
        db.Enum(
            'pending',
            'reviewed',
            'resolved'
        ),
        default='pending',
        nullable=False,
        index=True
    )
    
    # Timestamps
    flagged_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    
    def __repr__(self):
        return f"<ReviewFlag {self.flag_id} - {self.reason}>"
    
    def to_dict(self):
        """Convert flag to dictionary for JSON serialization."""
        return {
            'flag_id': self.flag_id,
            'review_id': self.review_id,
            'flagged_by': self.flagged_by,
            'reason': self.reason,
            'description': self.description,
            'status': self.status,
            'flagged_at': self.flagged_at.isoformat() if self.flagged_at else None,
        }
