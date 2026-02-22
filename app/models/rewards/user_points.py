"""
UserPoints Model
User points and level tracking
"""

from app import db
from datetime import datetime
import uuid


class UserPoints(db.Model):
    """
    UserPoints model for tracking user points and experience levels.
    
    Attributes:
        points_id: UUID primary key
        user_id: Foreign key to User (unique - one per user)
        total_points: Total accumulated points
        current_xp: Current experience points
        current_level: Level name (Bronze, Silver, etc.)
        level_number: Numeric level
        created_at: Account creation timestamp
        updated_at: Last update timestamp
    """
    
    __tablename__ = 'user_points'
    
    # Primary Key
    points_id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False
    )
    
    # Foreign Key - One to One with User
    user_id = db.Column(
        db.String(36),
        db.ForeignKey('users.user_id', ondelete='CASCADE'),
        nullable=False,
        unique=True,
        index=True
    )
    
    # Points & Experience
    total_points = db.Column(
        db.Integer,
        default=0,
        nullable=False,
        index=True
    )
    current_xp = db.Column(
        db.Integer,
        default=0,
        nullable=False
    )
    
    # Level Information
    current_level = db.Column(
        db.String(50),
        default='Bronze',
        nullable=False
    )
    level_number = db.Column(
        db.Integer,
        default=1,
        nullable=False
    )
    
    # Timestamps
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    def __repr__(self):
        return f"<UserPoints {self.user_id} - Level {self.current_level}>"
    
    def to_dict(self):
        """Convert user points to dictionary for JSON serialization."""
        return {
            'points_id': self.points_id,
            'user_id': self.user_id,
            'total_points': self.total_points,
            'current_xp': self.current_xp,
            'current_level': self.current_level,
            'level_number': self.level_number,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
