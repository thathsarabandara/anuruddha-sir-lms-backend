"""
NotificationBatch Model
Bulk notification batch tracking
"""

import uuid
from datetime import datetime

from app import db


class NotificationBatch(db.Model):
    """
    NotificationBatch model for tracking bulk notification batches.

    Attributes:
        batch_id: UUID primary key
        title: Batch title
        content: Batch content
        created_by: Foreign key to User (creator)
        total_recipients: Expected recipient count
        sent_count: Number successfully sent
        failed_count: Number of failures
        scheduled_for: Scheduled send timestamp
        sent_at: Actual send timestamp
        status: Batch status (scheduled, sending, sent, failed)
        created_at: Creation timestamp
    """

    __tablename__ = "notification_batch"

    # Primary Key
    batch_id = db.Column(
        db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False
    )

    # Batch Information
    title = db.Column(db.String(255), nullable=True)
    content = db.Column(db.Text, nullable=True)

    # Creator (Foreign Key)
    created_by = db.Column(db.String(36), db.ForeignKey("users.user_id"), nullable=True, index=True)

    # Recipient Statistics
    total_recipients = db.Column(db.Integer, nullable=False)
    sent_count = db.Column(db.Integer, default=0, nullable=False)
    failed_count = db.Column(db.Integer, default=0, nullable=False)

    # Scheduling
    scheduled_for = db.Column(db.DateTime, nullable=True, index=True)
    sent_at = db.Column(db.DateTime, nullable=True)

    # Status
    status = db.Column(
        db.Enum("scheduled", "sending", "sent", "failed"),
        default="scheduled",
        nullable=False,
        index=True,
    )

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<NotificationBatch {self.batch_id} - {self.status}>"

    def to_dict(self):
        """Convert batch to dictionary for JSON serialization."""
        return {
            "batch_id": self.batch_id,
            "title": self.title,
            "content": self.content,
            "created_by": self.created_by,
            "total_recipients": self.total_recipients,
            "sent_count": self.sent_count,
            "failed_count": self.failed_count,
            "scheduled_for": self.scheduled_for.isoformat() if self.scheduled_for else None,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
