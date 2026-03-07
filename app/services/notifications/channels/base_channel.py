"""
Base Notification Channel Interface
Abstract base class for all notification channels
"""

from abc import ABC, abstractmethod
import uuid
from datetime import datetime
from app import db
from app.models.notifications.notification_delivery_log import NotificationDeliveryLog


class BaseNotificationChannel(ABC):
    """
    Abstract base class for notification delivery channels.

    All channels (Email, WhatsApp, SMS, In-app) should extend this class
    and implement the send() and retry() methods.
    """

    def __init__(self, channel_name: str):
        """
        Initialize channel.

        Args:
            channel_name: Name of the channel (e.g., 'email', 'whatsapp')
        """
        self.channel_name = channel_name

    @abstractmethod
    def send(
        self,
        recipient: str,
        subject: str = None,
        content: str = None,
        notification_id: str = None,
        **kwargs,
    ) -> dict:
        """
        Send notification through this channel.

        Args:
            recipient: Recipient identifier (email, phone, user_id, etc.)
            subject: Message subject (optional)
            content: Message content
            notification_id: Associated notification ID for logging
            **kwargs: Additional channel-specific parameters

        Returns:
            dict: {
                'status': 'sent'|'failed'|'pending',
                'delivery_id': str,
                'message': str,
                'error': str (if failed)
            }
        """
        pass

    @abstractmethod
    def retry(self, delivery_log_id: str) -> dict:
        """
        Retry sending a failed notification.

        Args:
            delivery_log_id: ID of the failed delivery log entry

        Returns:
            dict: Retry result
        """
        pass

    def log_delivery(
        self,
        notification_id: str,
        recipient: str,
        status: str,
        error_message: str = None,
        retry_count: int = 0,
    ) -> str:
        """
        Log notification delivery attempt.

        Args:
            notification_id: Associated notification ID
            recipient: Recipient identifier
            status: Delivery status ('pending', 'sent', 'failed', 'bounced', 'complained')
            error_message: Error message if failed
            retry_count: Number of retries

        Returns:
            str: Delivery log ID
        """
        delivery_id = str(uuid.uuid4())

        delivery_log = NotificationDeliveryLog(
            delivery_id=delivery_id,
            notification_id=notification_id,
            channel=self.channel_name,
            recipient_email=recipient if self.channel_name == "email" else None,
            recipient_phone=recipient if self.channel_name == "whatsapp" else None,
            status=status,
            error_message=error_message,
            retry_count=retry_count,
            max_retries=3,
            sent_at=datetime.utcnow() if status == "sent" else None,
        )

        try:
            db.session.add(delivery_log)
            db.session.commit()
            return delivery_id
        except Exception as e:
            db.session.rollback()
            return None

    def get_delivery_log(self, delivery_id: str) -> dict:
        """
        Get delivery log entry.

        Args:
            delivery_id: Delivery log ID

        Returns:
            dict: Delivery log data
        """
        log = NotificationDeliveryLog.query.filter_by(delivery_id=delivery_id).first()
        if not log:
            return None

        return {
            "delivery_id": log.delivery_id,
            "notification_id": log.notification_id,
            "channel": log.channel,
            "recipient_email": log.recipient_email,
            "recipient_phone": log.recipient_phone,
            "status": log.status,
            "retry_count": log.retry_count,
            "max_retries": log.max_retries,
            "error_message": log.error_message,
            "sent_at": log.sent_at,
            "created_at": log.created_at,
            "updated_at": log.updated_at,
        }

    def update_delivery_log(
        self, delivery_id: str, status: str, error_message: str = None
    ) -> bool:
        """
        Update delivery log status.

        Args:
            delivery_id: Delivery log ID
            status: New status
            error_message: Error message if failed

        Returns:
            bool: Success status
        """
        try:
            log = NotificationDeliveryLog.query.filter_by(delivery_id=delivery_id).first()
            if not log:
                return False

            log.status = status
            if error_message:
                log.error_message = error_message
            if status == "sent":
                log.sent_at = datetime.utcnow()

            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            return False
