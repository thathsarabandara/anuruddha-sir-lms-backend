"""
WhatsApp Notification Channel
Handles WhatsApp notification delivery via custom WhatsApp server
"""

import logging
import re
import requests

from flask import current_app

from app.services.notifications.channels.base_channel import BaseNotificationChannel

logger = logging.getLogger(__name__)


class WhatsAppChannel(BaseNotificationChannel):
    """
    WhatsApp notification channel using custom WhatsApp server.

    Sends real-time notifications via WhatsApp with rate limiting
    and delivery confirmation.
    """

    def __init__(self):
        """Initialize WhatsApp channel."""
        super().__init__("whatsapp")
        self.whatsapp_server_url = current_app.config.get(
            "WHATSAPP_GATEWAY_URL"
        ) or "http://localhost:3000/api"
        self.max_message_length = 1024  # WhatsApp message limit

    def send(
        self,
        recipient: str,
        content: str = None,
        messageType: str = "NOTIFICATION",
        priority: str = "NORMAL",
        notification_id: str = None,
        **kwargs,
    ) -> dict:
        """
        Send WhatsApp notification.

        Args:
            recipient: Recipient phone number (E.164 format: +1234567890)
            content: Message content
            messageType: Type of message (e.g., "NOTIFICATION", "OTP", "ALERT"  etc.)
            template_name: Optional template name for WhatsApp approved templates
            subject: Subject (unused for WhatsApp)
            **kwargs: Additional parameters

        Returns:
            dict: Send result
        """
        if not self._is_valid_phone(recipient):
            return {
                "status": "failed",
                "message": "Invalid phone number",
                "error": f"Invalid recipient format. Use E.164 format: {recipient}",
            }

        try:
            # Truncate message if exceeds limit
            if len(content) > self.max_message_length:
                content = content[: self.max_message_length]
                logger.warning(
                    f"WhatsApp message truncated for {recipient} "
                    f"(max length: {self.max_message_length})"
                )

            # Send via custom WhatsApp server
            payload = {
                "phone": recipient,
                "content": content,
                "messageType": messageType,
                "priority": priority,
            }

            response = requests.post(
                f"{self.whatsapp_server_url}/send",
                json=payload,
                timeout=10,
            )
            response.raise_for_status()

            result = response.json()
            is_success = result.get("status") == "sent" or response.status_code == 200

            # Log successful delivery
            delivery_id = self.log_delivery(
                notification_id=notification_id,
                recipient=recipient,
                status="sent" if is_success else "failed",
                error_message=None,
            )

            logger.info(
                f"WhatsApp message sent to {recipient} "
                f"(delivery_id: {delivery_id})"
            )

            return {
                "status": "sent" if is_success else "failed",
                "delivery_id": delivery_id,
                "message": f"WhatsApp message sent to {recipient}",
                "server_response": result,
            }

        except requests.exceptions.RequestException as e:
            error_msg = f"Failed to send WhatsApp message: {str(e)}"
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
                "message": "Failed to send WhatsApp message",
                "error": error_msg,
            }
        except Exception as e:
            error_msg = f"Failed to send WhatsApp message: {str(e)}"
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
                "message": "Failed to send WhatsApp message",
                "error": error_msg,
            }

    def retry(self, delivery_log_id: str) -> dict:
        """
        Retry sending a failed WhatsApp message.

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
                recipient=delivery_log["recipient_phone"],
                notification_id=delivery_log["notification_id"],
            )

        except Exception as e:
            logger.error(f"Retry failed for delivery {delivery_log_id}: {str(e)}")
            return {"status": "failed", "message": str(e), "error": str(e)}

    def _is_valid_phone(self, phone: str) -> bool:
        """
        Validate phone number in E.164 format.

        Args:
            phone: Phone number to validate

        Returns:
            bool: Is valid E.164 format
        """
        if not isinstance(phone, str):
            return False

        # E.164 format: +[country code][number]
        pattern = r"^\+[1-9]\d{1,14}$"
        return re.match(pattern, phone) is not None

    def send_otp(
        self,
        recipient: str,
        otp_code: str,
        expires_in_mins: int = 5,
        notification_id: str = None,
    ) -> dict:
        """
        Send OTP via WhatsApp.

        Special handler for OTP delivery with standard format.

        Args:
            recipient: Recipient phone number
            otp_code: OTP code
            expires_in_mins: OTP expiration time in minutes
            notification_id: Associated notification ID

        Returns:
            dict: Send result
        """
        content = (
            f"Your OTP is: {otp_code}. Valid for {expires_in_mins} minutes. "
            "Do not share with anyone."
        )
        return self.send(
            recipient=recipient,
                content=content,
                notification_id=notification_id,
                template_name="otp_verification",
        )

    def send_security_alert(
        self,
        recipient: str,
        alert_type: str,
        details: dict = None,
    ) -> dict:
        """
        Send security alert via WhatsApp.

        Special handler for security-related notifications.

        Args:
            recipient: Recipient phone number
            alert_type: Type of alert (failed_login, account_locked, etc.)
            details: Additional details dict
            notification_id: Associated notification ID

        Returns:
            dict: Send result
        """
        if alert_type == "failed_login":
            attempt_number = details.get("attempt_number", 1) if details else 1
            content = (
                f"Alert: Failed login attempt #{attempt_number} on your account. "
                "If this wasn't you, change your password immediately."
            )
        elif alert_type == "account_locked":
            ban_duration = details.get("ban_duration", "24 hours") if details else "24 hours"
            content = (
                f"Your account has been locked for {ban_duration} due to multiple failed login attempts. "
                "Contact support if you need help."
            )
        else:
            content = f"Security Alert: {alert_type}"

        return self.send(
            recipient=recipient,
            content=content,
            messageType="ALERT",
            priority="HIGH",
        )
