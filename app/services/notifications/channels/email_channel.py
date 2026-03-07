"""
Email Notification Channel
Handles email notification delivery
"""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from flask import current_app

from app.services.notifications.channels.base_channel import BaseNotificationChannel

logger = logging.getLogger(__name__)


class EmailChannel(BaseNotificationChannel):
    """
    Email notification channel using SMTP.

    Sends notifications via email with both HTML and plain text versions.
    Supports template rendering and attachment.
    """

    def __init__(self):
        """Initialize email channel."""
        super().__init__("email")
        self.smtp_server = current_app.config.get("MAIL_SERVER", "localhost")
        self.smtp_port = current_app.config.get("MAIL_PORT", 587)
        self.sender_email = current_app.config.get("MAIL_DEFAULT_SENDER", "noreply@example.com")
        self.sender_password = current_app.config.get("MAIL_PASSWORD")
        self.use_tls = current_app.config.get("MAIL_USE_TLS", True)

    def send(
        self,
        recipient: str,
        subject: str = None,
        content: str = None,
        html_content: str = None,
        notification_id: str = None,
        **kwargs,
    ) -> dict:
        """
        Send email notification.

        Args:
            recipient: Recipient email address
            subject: Email subject
            content: Plain text content
            html_content: HTML content (if provided, used instead of content)
            notification_id: Associated notification ID
            **kwargs: Additional parameters

        Returns:
            dict: Send result
        """
        if not self._is_valid_email(recipient):
            return {
                "status": "failed",
                "message": "Invalid email address",
                "error": f"Invalid recipient: {recipient}",
            }

        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject or "Notification"
            msg["From"] = self.sender_email
            msg["To"] = recipient

            # Add plain text part
            if content:
                msg.attach(MIMEText(content, "plain"))

            # Add HTML part (takes precedence if both provided)
            if html_content:
                msg.attach(MIMEText(html_content, "html"))

            # Send email
            self._send_smtp(msg)

            # Log successful delivery
            delivery_id = self.log_delivery(
                notification_id=notification_id,
                recipient=recipient,
                status="sent",
                error_message=None,
            )

            logger.info(f"Email sent successfully to {recipient} (delivery_id: {delivery_id})")

            return {
                "status": "sent",
                "delivery_id": delivery_id,
                "message": f"Email sent to {recipient}",
            }

        except Exception as e:
            error_msg = f"Failed to send email: {str(e)}"
            logger.error(error_msg)

            # Log failed delivery
            delivery_id = self.log_delivery(
                notification_id=notification_id,
                recipient=recipient,
                status="failed",
                error_message=error_msg,
            )

            return {
                "status": "failed",
                "delivery_id": delivery_id,
                "message": "Failed to send email",
                "error": error_msg,
            }

    def retry(self, delivery_log_id: str) -> dict:
        """
        Retry sending a failed email.

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
                    from app import db

                    db.session.commit()
            except Exception:
                pass

            # Retry sending
            return self.send(
                recipient=delivery_log["recipient_email"],
                notification_id=delivery_log["notification_id"],
            )

        except Exception as e:
            logger.error(f"Retry failed for delivery {delivery_log_id}: {str(e)}")
            return {"status": "failed", "message": str(e), "error": str(e)}

    def _is_valid_email(self, email: str) -> bool:
        """
        Validate email address format.

        Args:
            email: Email address to validate

        Returns:
            bool: Is valid email
        """
        if not isinstance(email, str):
            return False

        import re

        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return re.match(pattern, email) is not None

    def _send_smtp(self, msg):
        """
        Send email via SMTP.

        Args:
            msg: Email message object

        Raises:
            Exception: If SMTP send fails
        """
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()

                if self.sender_password:
                    server.login(self.sender_email, self.sender_password)

                server.send_message(msg)

        except Exception as e:
            raise Exception(f"SMTP error: {str(e)}")
