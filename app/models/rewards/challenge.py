"""
Challenge Model
Time-limited challenges and competitions
"""

import uuid
from datetime import datetime

from app import db


class Challenge(db.Model):
    """
    Challenge model for time-limited challenges and competitions.

    Attributes:
        challenge_id: UUID primary key
        title: Challenge title
        description: Challenge description
        criteria_type: Challenge criteria type
        criteria_threshold: Threshold to complete
        point_reward: Points awarded
        badge_reward_id: Foreign key to Achievement (badge reward)
        start_date: Challenge start timestamp
        end_date: Challenge end timestamp
        status: ENUM(active, completed, cancelled)
        created_at: Creation timestamp
    """

    __tablename__ = "challenges"

    # Primary Key
    challenge_id = db.Column(
        db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False
    )

    # Challenge Information
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)

    # Criteria
    criteria_type = db.Column(db.String(100), nullable=True)
    criteria_threshold = db.Column(db.Integer, nullable=True)

    # Rewards
    point_reward = db.Column(db.Integer, nullable=True)
    badge_reward_id = db.Column(
        db.String(36), db.ForeignKey("achievements.achievement_id"), nullable=True
    )

    # Timing
    start_date = db.Column(db.DateTime, nullable=True)
    end_date = db.Column(db.DateTime, nullable=True)

    # Status
    status = db.Column(
        db.Enum("active", "completed", "cancelled"), default="active", nullable=False, index=True
    )

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Challenge {self.challenge_id} - {self.title}>"

    def to_dict(self):
        """Convert challenge to dictionary for JSON serialization."""
        return {
            "challenge_id": self.challenge_id,
            "title": self.title,
            "description": self.description,
            "criteria_type": self.criteria_type,
            "criteria_threshold": self.criteria_threshold,
            "point_reward": self.point_reward,
            "badge_reward_id": self.badge_reward_id,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
