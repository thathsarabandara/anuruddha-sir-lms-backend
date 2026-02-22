"""
UserAccountStatus Model
Tracks account security status including bans and failed login attempts
"""

import json
import uuid
from datetime import datetime

from app import db


class UserAccountStatus(db.Model):
    """
    UserAccountStatus model for account security and ban tracking.

    Attributes:
        status_id: UUID primary key
        user_id: Foreign key to users (unique)
        is_active: Whether account is active
        is_banned: Whether account is banned
        ban_reason: Reason for ban
        banned_at: When ban was applied
        ban_expires_at: When ban expires
        failed_login_attempts: Count of failed attempts
        last_failed_attempt_at: Last failed attempt timestamp
        last_notification_sent_at: When last notification was sent
        notification_channels: JSON array of channels
        updated_at: Last update timestamp
    """

    __tablename__ = "user_account_status"

    # Primary Key
    status_id = db.Column(
        db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False
    )

    # Foreign Key
    user_id = db.Column(
        db.String(36),
        db.ForeignKey("users.user_id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    # Account Status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_banned = db.Column(db.Boolean, default=False, nullable=False, index=True)

    # Ban Information
    ban_reason = db.Column(db.String(255), nullable=True)
    banned_at = db.Column(db.DateTime, nullable=True)
    ban_expires_at = db.Column(db.DateTime, nullable=True, index=True)

    # Failed Login Tracking
    failed_login_attempts = db.Column(db.Integer, default=0, nullable=False)
    last_failed_attempt_at = db.Column(db.DateTime, nullable=True)

    # Notifications
    last_notification_sent_at = db.Column(db.DateTime, nullable=True)
    notification_channels = db.Column(db.Text, nullable=True)

    # Timestamps
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def __repr__(self):
        return f"<UserAccountStatus user_id={self.user_id} banned={self.is_banned}>"

    def get_notification_channels(self):
        """Parse notification channels from JSON."""
        if not self.notification_channels:
            return []
        try:
            return json.loads(self.notification_channels)
        except (json.JSONDecodeError, TypeError):
            return []

    def set_notification_channels(self, channels):
        """Set notification channels from list."""
        self.notification_channels = json.dumps(channels) if channels else None

    def to_dict(self):
        """Convert account status to dictionary representation."""
        return {
            "status_id": self.status_id,
            "user_id": self.user_id,
            "is_active": self.is_active,
            "is_banned": self.is_banned,
            "ban_reason": self.ban_reason,
            "banned_at": self.banned_at.isoformat() if self.banned_at else None,
            "ban_expires_at": self.ban_expires_at.isoformat() if self.ban_expires_at else None,
            "failed_login_attempts": self.failed_login_attempts,
            "last_failed_attempt_at": (
                self.last_failed_attempt_at.isoformat() if self.last_failed_attempt_at else None
            ),
            "last_notification_sent_at": (
                self.last_notification_sent_at.isoformat()
                if self.last_notification_sent_at
                else None
            ),
            "notification_channels": self.get_notification_channels(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
