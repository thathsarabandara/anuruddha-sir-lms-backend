"""
NotificationDeliveryLog Model
Tracks notification delivery attempts and status
"""

from app import db
from datetime import datetime
import uuid


class NotificationDeliveryLog(db.Model):
    """
    NotificationDeliveryLog model for tracking notification delivery across channels.
    
    Attributes:
        delivery_id: UUID primary key
        notification_id: Foreign key to Notification
        channel: Channel used (email, sms, whatsapp, in_app)
        recipient_email: Email address if applicable
        recipient_phone: Phone number if applicable
        status: Delivery status (pending, sent, failed, bounced, complained)
        retry_count: Number of retry attempts
        max_retries: Maximum allowed retries
        error_message: Error details if failed
        sent_at: Timestamp when successfully sent
        created_at: Log creation timestamp
        updated_at: Last update timestamp
    """
    
    __tablename__ = 'notification_delivery_log'
    
    # Primary Key
    delivery_id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False
    )
    
    # Foreign Key
    notification_id = db.Column(
        db.String(36),
        db.ForeignKey('notifications.notification_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    # Channel Information
    channel = db.Column(
        db.String(50),
        nullable=True
    )
    recipient_email = db.Column(
        db.String(255),
        nullable=True
    )
    recipient_phone = db.Column(
        db.String(20),
        nullable=True
    )
    
    # Delivery Status
    status = db.Column(
        db.Enum(
            'pending',
            'sent',
            'failed',
            'bounced',
            'complained'
        ),
        default='pending',
        nullable=False,
        index=True
    )
    
    # Retry Information
    retry_count = db.Column(
        db.Integer,
        default=0,
        nullable=False
    )
    max_retries = db.Column(
        db.Integer,
        default=3,
        nullable=False
    )
    error_message = db.Column(
        db.Text,
        nullable=True
    )
    
    # Timestamps
    sent_at = db.Column(
        db.DateTime,
        nullable=True,
        index=True
    )
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
        return f"<NotificationDeliveryLog {self.delivery_id} - {self.status}>"
    
    def to_dict(self):
        """Convert delivery log to dictionary for JSON serialization."""
        return {
            'delivery_id': self.delivery_id,
            'notification_id': self.notification_id,
            'channel': self.channel,
            'recipient_email': self.recipient_email,
            'recipient_phone': self.recipient_phone,
            'status': self.status,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'error_message': self.error_message,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
