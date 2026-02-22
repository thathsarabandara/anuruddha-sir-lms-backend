"""
UserPreferences Model
Represents user preferences and settings
"""

from app import db
from datetime import datetime
import uuid
import json


class UserPreferences(db.Model):
    """
    UserPreferences model for user customization and settings.
    
    Attributes:
        preference_id: UUID primary key
        user_id: Foreign key to users table (unique)
        language: Preferred language code (default: 'en')
        theme: UI theme preference (default: 'light')
        timezone: User's timezone (default: UTC)
        notifications_email: Email notifications enabled
        notifications_sms: SMS notifications enabled
        notifications_in_app: In-app notifications enabled
        notification_settings: JSON object with detailed notification settings
        privacy_settings: JSON object with privacy preferences
        created_at: Preferences creation timestamp
        updated_at: Last update timestamp
    """
    
    __tablename__ = 'user_preferences'
    
    # Primary Key
    preference_id = db.Column(
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
    
    # Basic Preferences
    language = db.Column(
        db.String(10),
        default='en',
        nullable=False
    )
    theme = db.Column(
        db.String(20),
        default='light',
        nullable=False
    )
    timezone = db.Column(
        db.String(50),
        nullable=True
    )
    
    # Notification Preferences
    notifications_email = db.Column(
        db.Boolean,
        default=True,
        nullable=False
    )
    notifications_sms = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )
    notifications_in_app = db.Column(
        db.Boolean,
        default=True,
        nullable=False
    )
    
    # Advanced Settings (JSON)
    notification_settings = db.Column(
        db.Text,
        nullable=True
    )
    privacy_settings = db.Column(
        db.Text,
        nullable=True
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
        return f"<UserPreferences user_id={self.user_id}>"
    
    def get_notification_settings(self):
        """Parse notification settings from JSON."""
        if not self.notification_settings:
            return {}
        try:
            return json.loads(self.notification_settings)
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def set_notification_settings(self, settings):
        """Set notification settings from dict."""
        self.notification_settings = json.dumps(settings) if settings else None
    
    def get_privacy_settings(self):
        """Parse privacy settings from JSON."""
        if not self.privacy_settings:
            return {}
        try:
            return json.loads(self.privacy_settings)
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def set_privacy_settings(self, settings):
        """Set privacy settings from dict."""
        self.privacy_settings = json.dumps(settings) if settings else None
    
    def to_dict(self):
        """Convert user preferences to dictionary representation."""
        return {
            'preference_id': self.preference_id,
            'user_id': self.user_id,
            'language': self.language,
            'theme': self.theme,
            'timezone': self.timezone,
            'notifications_email': self.notifications_email,
            'notifications_sms': self.notifications_sms,
            'notifications_in_app': self.notifications_in_app,
            'notification_settings': self.get_notification_settings(),
            'privacy_settings': self.get_privacy_settings(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
