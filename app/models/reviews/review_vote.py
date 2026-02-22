"""
ReviewVote Model
Helpfulness voting on reviews
"""

import uuid
from datetime import datetime

from app import db


class ReviewVote(db.Model):
    """
    ReviewVote model for tracking review helpfulness votes.

    Attributes:
        vote_id: UUID primary key
        review_id: Foreign key to Review
        user_id: Foreign key to User (voter)
        is_helpful: Whether vote was helpful/unhelpful
        voted_at: Timestamp when vote was cast
    """

    __tablename__ = "review_votes"

    # Primary Key
    vote_id = db.Column(
        db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False
    )

    # Foreign Keys
    review_id = db.Column(
        db.String(36),
        db.ForeignKey("reviews.review_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = db.Column(
        db.String(36), db.ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )

    # Vote Data
    is_helpful = db.Column(db.Boolean, nullable=True)

    # Timestamps
    voted_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Unique Constraint
    __table_args__ = (db.UniqueConstraint("user_id", "review_id", name="unique_user_review"),)

    def __repr__(self):
        return f"<ReviewVote {self.vote_id}>"

    def to_dict(self):
        """Convert vote to dictionary for JSON serialization."""
        return {
            "vote_id": self.vote_id,
            "review_id": self.review_id,
            "user_id": self.user_id,
            "is_helpful": self.is_helpful,
            "voted_at": self.voted_at.isoformat() if self.voted_at else None,
        }
