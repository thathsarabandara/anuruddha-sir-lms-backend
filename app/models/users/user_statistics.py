"""
UserStatistics Model
Tracks user engagement and learning statistics
"""

from app import db
from datetime import datetime
import uuid


class UserStatistics(db.Model):
    """
    UserStatistics model for user engagement and learning analytics.
    
    Attributes:
        stat_id: UUID primary key
        user_id: Foreign key to users table (unique)
        total_courses_enrolled: Total courses enrolled
        courses_completed: Number of courses completed
        average_quiz_score: Average quiz score
        total_certificates: Total certificates earned
        total_study_hours: Total study hours (decimal)
        learning_streak_days: Current learning streak
        last_activity: Last activity timestamp
        updated_at: Last update timestamp
    """
    
    __tablename__ = 'user_statistics'
    
    # Primary Key
    stat_id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False
    )
    
    # Foreign Key
    user_id = db.Column(
        db.String(36),
        db.ForeignKey('users.user_id', ondelete='CASCADE'),
        unique=True,
        nullable=False,
        index=True
    )
    
    # Enrollment Statistics
    total_courses_enrolled = db.Column(
        db.Integer,
        default=0,
        nullable=False
    )
    courses_completed = db.Column(
        db.Integer,
        default=0,
        nullable=False
    )
    
    # Performance Statistics
    average_quiz_score = db.Column(
        db.Numeric(5, 2),
        nullable=True
    )
    
    # Achievement Statistics
    total_certificates = db.Column(
        db.Integer,
        default=0,
        nullable=False
    )
    
    # Learning Statistics
    total_study_hours = db.Column(
        db.Numeric(8, 2),
        default=0,
        nullable=False
    )
    learning_streak_days = db.Column(
        db.Integer,
        default=0,
        nullable=False
    )
    
    # Activity Timestamp
    last_activity = db.Column(
        db.DateTime,
        nullable=True
    )
    
    # Timestamps
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    def __repr__(self):
        return f"<UserStatistics user_id={self.user_id}>"
    
    def to_dict(self):
        """Convert user statistics to dictionary representation."""
        return {
            'stat_id': self.stat_id,
            'user_id': self.user_id,
            'total_courses_enrolled': self.total_courses_enrolled,
            'courses_completed': self.courses_completed,
            'average_quiz_score': float(self.average_quiz_score) if self.average_quiz_score else None,
            'total_certificates': self.total_certificates,
            'total_study_hours': float(self.total_study_hours) if self.total_study_hours else 0,
            'learning_streak_days': self.learning_streak_days,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
