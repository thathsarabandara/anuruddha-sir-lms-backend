"""
Achievement Model
Achievement and badge definitions
"""

import uuid
from datetime import datetime

from app import db


class Achievement(db.Model):
    """
    Achievement model for defining badges and achievements.

    Attributes:
        achievement_id: UUID primary key
        name: Achievement name
        description: Achievement description
        icon_url: Icon URL
        rarity: ENUM(common, rare, epic, legendary)
        points_reward: Points awarded for achievement
        badge_icon: Binary badge icon data
        auto_award: Auto-award on criteria match
        criteria_type: Achievement criteria type
        criteria_threshold: Threshold for criteria
        created_at: Creation timestamp
    """

    __tablename__ = "achievements"

    # Primary Key
    achievement_id = db.Column(
        db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False
    )

    # Achievement Information
    name = db.Column(db.String(255), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    icon_url = db.Column(db.Text, nullable=True)

    # Rarity & Rewards
    rarity = db.Column(
        db.Enum("common", "rare", "epic", "legendary"), default="common", nullable=False
    )
    points_reward = db.Column(db.Integer, default=0, nullable=False)
    badge_icon = db.Column(db.LargeBinary, nullable=True)

    # Criteria
    auto_award = db.Column(db.Boolean, default=True, nullable=False)
    criteria_type = db.Column(db.String(100), nullable=True)
    criteria_threshold = db.Column(db.Integer, nullable=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Achievement {self.achievement_id} - {self.name}>"

    def to_dict(self):
        """Convert achievement to dictionary for JSON serialization."""
        return {
            "achievement_id": self.achievement_id,
            "name": self.name,
            "description": self.description,
            "icon_url": self.icon_url,
            "rarity": self.rarity,
            "points_reward": self.points_reward,
            "auto_award": self.auto_award,
            "criteria_type": self.criteria_type,
            "criteria_threshold": self.criteria_threshold,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
