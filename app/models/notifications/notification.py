"""
Notification Model
Represents a notification message sent to a user
"""

import json
import uuid
from datetime import datetime

from app import db


class Notification(db.Model):
    """
    Notification model for user notifications across multiple channels.

    Attributes:
        notification_id: UUID primary key
        user_id: Foreign key to User
        type: Notification type/category
        title: Notification title
        message: Short notification message
        detailed_content: Detailed content
        channels: JSON list of channels used
        related_resource_type: Type of resource (course, quiz, etc.)
        related_resource_id: ID of related resource
        action_url: URL for action button
        is_read: Read status
        is_deleted: Soft delete flag
        read_at: Timestamp when marked read
        created_at: Creation timestamp
    """

    __tablename__ = "notifications"

    # Primary Key
    notification_id = db.Column(
        db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False
    )

    # Foreign Key
    user_id = db.Column(
        db.String(36),
        db.ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Notification Content
    type = db.Column(db.String(100), nullable=False, index=True)
    title = db.Column(db.String(255), nullable=True)
    message = db.Column(db.Text, nullable=True)
    detailed_content = db.Column(db.Text, nullable=True)

    # Channels (JSON array)
    channels = db.Column(db.JSON, nullable=True)

    # Related Resource
    related_resource_type = db.Column(db.String(50), nullable=True)
    related_resource_id = db.Column(db.String(36), nullable=True)
    action_url = db.Column(db.String(500), nullable=True)

    # Status Flags
    is_read = db.Column(db.Boolean, default=False, nullable=False, index=True)
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)
    read_at = db.Column(db.DateTime, nullable=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    def get_channels(self):
        """Get channels list safely."""
        if not self.channels:
            return []
        try:
            if isinstance(self.channels, str):
                return json.loads(self.channels)
            return self.channels if isinstance(self.channels, list) else []
        except (json.JSONDecodeError, TypeError):
            return []

    def set_channels(self, data):
        """Set channels list."""
        self.channels = json.dumps(data) if data else None

    def __repr__(self):
        return f"<Notification {self.notification_id} - {self.type}>"

    def to_dict(self):
        """Convert notification to dictionary for JSON serialization."""
        return {
            "notification_id": self.notification_id,
            "user_id": self.user_id,
            "type": self.type,
            "title": self.title,
            "message": self.message,
            "detailed_content": self.detailed_content,
            "channels": self.get_channels(),
            "related_resource_type": self.related_resource_type,
            "related_resource_id": self.related_resource_id,
            "action_url": self.action_url,
            "is_read": self.is_read,
            "is_deleted": self.is_deleted,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
