"""
In-App Notification Channel
Handles in-app notification storage and retrieval
"""

import logging

from app import db
from app.models.notifications.notification import Notification
from app.services.notifications.channels.base_channel import BaseNotificationChannel

logger = logging.getLogger(__name__)


class InAppChannel(BaseNotificationChannel):
    """
    In-app notification channel.

    Stores notifications in the database for display in the notification center.
    Instant delivery - notifications available immediately in the app.
    """

    def __init__(self):
        """Initialize in-app channel."""
        super().__init__("in_app")

    def send(
        self,
        recipient: str,
        content: str = None,
        subject: str = None,
        notification_id: str = None,
        notification_type: str = None,
        title: str = None,
        detailed_content: str = None,
        related_resource_type: str = None,
        related_resource_id: str = None,
        action_url: str = None,
        **kwargs,
    ) -> dict:
        """
        Store in-app notification for user.

        Args:
            recipient: Recipient user ID
            content: Short notification message
            subject: Subject (used as title if title not provided)
            notification_id: Associated notification IDs (can reuse or create new)
            notification_type: Type of notification
            title: Notification title
            detailed_content: Detailed message content
            related_resource_type: Type of related resource (course, quiz, etc.)
            related_resource_id: ID of related resource
            action_url: URL for action button
            **kwargs: Additional parameters

        Returns:
            dict: Send result
        """
        if not self._is_valid_user_id(recipient):
            return {
                "status": "failed",
                "message": "Invalid user ID",
                "error": f"Invalid recipient: {recipient}",
            }

        try:
            # Check if notification already exists (avoid duplicates)
            if notification_id:
                existing = Notification.query.filter_by(
                    notification_id=notification_id
                ).first()
                if existing:
                    # Update if already exists
                    self._update_notification(
                        existing,
                        title=title,
                        message=content,
                        detailed_content=detailed_content,
                        action_url=action_url,
                    )
                    notification_id = existing.notification_id
            else:
                # Create new notification
                from uuid import uuid4

                notification_id = str(uuid4())

                notification = Notification(
                    notification_id=notification_id,
                    user_id=recipient,
                    type=notification_type or "in_app",
                    title=title or subject or "Notification",
                    message=content,
                    detailed_content=detailed_content,
                    channels=["in_app"],
                    related_resource_type=related_resource_type,
                    related_resource_id=related_resource_id,
                    action_url=action_url,
                    is_read=False,
                )

                db.session.add(notification)
                db.session.commit()

            # Log delivery (in-app is always instant/successful)
            delivery_id = self.log_delivery(
                notification_id=notification_id,
                recipient=recipient,
                status="sent",
                error_message=None,
            )

            logger.info(f"In-app notification created for user {recipient} (id: {notification_id})")

            return {
                "status": "sent",
                "delivery_id": delivery_id,
                "notification_id": notification_id,
                "message": "In-app notification created",
            }

        except Exception as e:
            error_msg = f"Failed to create in-app notification: {str(e)}"
            logger.error(error_msg)

            # Log failed attempt
            delivery_id = self.log_delivery(
                notification_id=notification_id,
                recipient=recipient,
                status="failed",
                error_message=error_msg,
            )

            return {
                "status": "failed",
                "delivery_id": delivery_id,
                "message": "Failed to create in-app notification",
                "error": error_msg,
            }

    def retry(self, delivery_log_id: str) -> dict:
        """
        Retry sending a failed in-app notification.

        Args:
            delivery_log_id: Delivery log ID to retry

        Returns:
            dict: Retry result
        """
        try:
            delivery_log = self.get_delivery_log(delivery_log_id)
            if not delivery_log:
                return {"status": "failed", "message": "Delivery log not found"}

            if delivery_log["retry_count"] >= delivery_log["max_retries"]:
                return {"status": "failed", "message": "Max retries exceeded"}

            # Update retry count
            try:
                from app.models.notifications.notification_delivery_log import (
                    NotificationDeliveryLog,
                )

                log = NotificationDeliveryLog.query.filter_by(
                    delivery_id=delivery_log_id
                ).first()
                if log:
                    log.retry_count += 1
                    db.session.commit()
            except Exception:
                pass

            # Retry - get notification and resend
            try:
                notif = Notification.query.filter_by(
                    notification_id=delivery_log["notification_id"]
                ).first()
                if notif:
                    # Update delivery log to resent status
                    self.update_delivery_log(delivery_log_id, "sent")
                    return {"status": "sent", "message": "In-app notification retry successful"}
            except Exception:
                pass

            return {"status": "failed", "message": "Retry failed"}

        except Exception as e:
            logger.error(f"Retry failed for delivery {delivery_log_id}: {str(e)}")
            return {"status": "failed", "message": str(e), "error": str(e)}

    def _is_valid_user_id(self, user_id: str) -> bool:
        """
        Validate user ID format (UUID).

        Args:
            user_id: User ID to validate

        Returns:
            bool: Is valid UUID format
        """
        if not isinstance(user_id, str):
            return False

        import re

        uuid_pattern = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
        return bool(re.match(uuid_pattern, user_id.lower()))

    def _update_notification(
        self, notification: Notification, title=None, message=None, detailed_content=None, action_url=None
    ) -> None:
        """
        Update existing notification.

        Args:
            notification: Notification object
            title: New title
            message: New message
            detailed_content: New detailed content
            action_url: New action URL
        """
        if title:
            notification.title = title
        if message:
            notification.message = message
        if detailed_content:
            notification.detailed_content = detailed_content
        if action_url:
            notification.action_url = action_url

        db.session.commit()

    def mark_as_read(self, notification_id: str, user_id: str) -> bool:
        """
        Mark notification as read.

        Args:
            notification_id: Notification ID
            user_id: User ID (for ownership verification)

        Returns:
            bool: Success status
        """
        try:
            notification = Notification.query.filter_by(
                notification_id=notification_id, user_id=user_id
            ).first()

            if not notification:
                return False

            notification.is_read = True
            from datetime import datetime

            notification.read_at = datetime.utcnow()
            db.session.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to mark notification as read: {str(e)}")
            return False

    def delete_notification(self, notification_id: str, user_id: str) -> bool:
        """
        Soft delete notification.

        Args:
            notification_id: Notification ID
            user_id: User ID (for ownership verification)

        Returns:
            bool: Success status
        """
        try:
            notification = Notification.query.filter_by(
                notification_id=notification_id, user_id=user_id
            ).first()

            if not notification:
                return False

            notification.is_deleted = True
            db.session.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to delete notification: {str(e)}")
            return False
