"""
NotificationPreferences Model
User notification preference settings
"""

from app import db
from datetime import datetime, time
import uuid
import json


class NotificationPreferences(db.Model):
    """
    NotificationPreferences model for user notification channel preferences.
    
    Attributes:
        preference_id: UUID primary key
        user_id: Foreign key to User (unique - one per user)
        email_enabled: Whether email notifications enabled
        sms_enabled: Whether SMS notifications enabled
        in_app_enabled: Whether in-app notifications enabled
        email_digest: Email frequency (instant, daily, weekly, never)
        quiet_hours_start: Quiet period start time
        quiet_hours_end: Quiet period end time
        preferences_json: Additional JSON preferences
        updated_at: Last update timestamp
    """
    
    __tablename__ = 'notification_preferences'
    
    # Primary Key
    preference_id = db.Column(
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
    
    # Channel Settings
    email_enabled = db.Column(
        db.Boolean,
        default=True,
        nullable=False
    )
    sms_enabled = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )
    in_app_enabled = db.Column(
        db.Boolean,
        default=True,
        nullable=False
    )
    
    # Email Configuration
    email_digest = db.Column(
        db.Enum('instant', 'daily', 'weekly', 'never'),
        default='daily',
        nullable=False
    )
    
    # Quiet Hours
    quiet_hours_start = db.Column(
        db.Time,
        nullable=True
    )
    quiet_hours_end = db.Column(
        db.Time,
        nullable=True
    )
    
    # Additional Preferences (JSON)
    preferences_json = db.Column(
        db.JSON,
        nullable=True
    )
    
    # Timestamps
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    def get_preferences(self):
        """Get preferences JSON safely."""
        if not self.preferences_json:
            return {}
        try:
            if isinstance(self.preferences_json, str):
                return json.loads(self.preferences_json)
            return self.preferences_json if isinstance(self.preferences_json, dict) else {}
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def set_preferences(self, data):
        """Set preferences JSON."""
        self.preferences_json = json.dumps(data) if data else None
    
    def __repr__(self):
        return f"<NotificationPreferences {self.preference_id} - {self.user_id}>"
    
    def to_dict(self):
        """Convert preferences to dictionary for JSON serialization."""
        return {
            'preference_id': self.preference_id,
            'user_id': self.user_id,
            'email_enabled': self.email_enabled,
            'sms_enabled': self.sms_enabled,
            'in_app_enabled': self.in_app_enabled,
            'email_digest': self.email_digest,
            'quiet_hours_start': self.quiet_hours_start.isoformat() if self.quiet_hours_start else None,
            'quiet_hours_end': self.quiet_hours_end.isoformat() if self.quiet_hours_end else None,
            'preferences_json': self.get_preferences(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
