"""
Streak Model
User streaks for gamification
"""

from app import db
from datetime import date
import uuid


class Streak(db.Model):
    """
    Streak model for tracking user streaks (login, learning, etc.).
    
    Attributes:
        streak_id: UUID primary key
        user_id: Foreign key to User
        streak_type: Type of streak
        current_count: Current streak count
        best_count: Best streak count
        last_activity_date: Last activity date
        started_date: Streak start date
    """
    
    __tablename__ = 'streaks'
    
    # Primary Key
    streak_id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False
    )
    
    # Foreign Key
    user_id = db.Column(
        db.String(36),
        db.ForeignKey('users.user_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    # Streak Information
    streak_type = db.Column(
        db.String(50),
        nullable=True
    )
    
    # Streak Counts
    current_count = db.Column(
        db.Integer,
        default=0,
        nullable=False
    )
    best_count = db.Column(
        db.Integer,
        default=0,
        nullable=False
    )
    
    # Dates
    last_activity_date = db.Column(
        db.Date,
        nullable=True
    )
    started_date = db.Column(
        db.Date,
        nullable=True
    )
    
    def __repr__(self):
        return f"<Streak {self.streak_id} - {self.streak_type}>"
    
    def to_dict(self):
        """Convert streak to dictionary for JSON serialization."""
        return {
            'streak_id': self.streak_id,
            'user_id': self.user_id,
            'streak_type': self.streak_type,
            'current_count': self.current_count,
            'best_count': self.best_count,
            'last_activity_date': self.last_activity_date.isoformat() if self.last_activity_date else None,
            'started_date': self.started_date.isoformat() if self.started_date else None,
        }
