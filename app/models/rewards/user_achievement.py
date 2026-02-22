"""
UserAchievement Model
User earned achievements
"""

from app import db
from datetime import datetime
import uuid


class UserAchievement(db.Model):
    """
    UserAchievement model for tracking achievements earned by users.
    
    Attributes:
        user_achievement_id: UUID primary key
        user_id: Foreign key to User
        achievement_id: Foreign key to Achievement
        earned_at: Timestamp when earned
        progress: Progress towards achievement (0-100)
    """
    
    __tablename__ = 'user_achievements'
    
    # Primary Key
    user_achievement_id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False
    )
    
    # Foreign Keys
    user_id = db.Column(
        db.String(36),
        db.ForeignKey('users.user_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    achievement_id = db.Column(
        db.String(36),
        db.ForeignKey('achievements.achievement_id', ondelete='CASCADE'),
        nullable=False
    )
    
    # Achievement Data
    progress = db.Column(
        db.Integer,
        default=0,
        nullable=False
    )
    
    # Timestamps
    earned_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )
    
    # Unique Constraint
    __table_args__ = (
        db.UniqueConstraint(
            'user_id',
            'achievement_id',
            name='unique_user_achievement'
        ),
    )
    
    def __repr__(self):
        return f"<UserAchievement {self.user_achievement_id}>"
    
    def to_dict(self):
        """Convert user achievement to dictionary for JSON serialization."""
        return {
            'user_achievement_id': self.user_achievement_id,
            'user_id': self.user_id,
            'achievement_id': self.achievement_id,
            'progress': self.progress,
            'earned_at': self.earned_at.isoformat() if self.earned_at else None,
        }
