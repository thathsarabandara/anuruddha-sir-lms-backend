"""
NotificationTypePreferences Model
Per-notification-type user preferences
"""

import uuid
from datetime import datetime

from app import db


class NotificationTypePreferences(db.Model):
    """
    NotificationTypePreferences model for per-type notification preferences per user.

    Attributes:
        type_pref_id: UUID primary key
        user_id: Foreign key to User
        notification_type: Notification type
        email: Enable email for this type
        sms: Enable SMS for this type
        in_app: Enable in-app for this type
        updated_at: Last update timestamp
    """

    __tablename__ = "notification_type_preferences"

    # Primary Key
    type_pref_id = db.Column(
        db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False
    )

    # Foreign Key
    user_id = db.Column(
        db.String(36),
        db.ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Notification Type
    notification_type = db.Column(db.String(100), nullable=False)

    # Channel Preferences
    email = db.Column(db.Boolean, default=True, nullable=False)
    sms = db.Column(db.Boolean, default=False, nullable=False)
    in_app = db.Column(db.Boolean, default=True, nullable=False)

    # Timestamps
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Unique Constraint
    __table_args__ = (db.UniqueConstraint("user_id", "notification_type", name="unique_user_type"),)

    def __repr__(self):
        return f"<NotificationTypePreferences {self.type_pref_id}>"

    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            "type_pref_id": self.type_pref_id,
            "user_id": self.user_id,
            "notification_type": self.notification_type,
            "email": self.email,
            "sms": self.sms,
            "in_app": self.in_app,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
