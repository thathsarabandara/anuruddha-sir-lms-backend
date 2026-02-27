"""OTP Manager Utility"""

import logging
import random
import secrets
from datetime import datetime, timedelta

from app.exceptions import ValidationError

logger = logging.getLogger(__name__)

# Notification type key used when querying DB templates
OTP_NOTIFICATION_TYPE = "otp_verification"


class OTPManager:
    """Manages OTP generation, storage, and verification"""

    @staticmethod
    def generate_otp_code(length=6):
        """Generate a random OTP code"""
        return "".join(str(random.randint(0, 9)) for _ in range(length))

    @staticmethod
    def generate_verification_token(length=32):
        """Generate a cryptographically secure verification token"""
        return secrets.token_urlsafe(length)

    @staticmethod
    def generate_reset_token(length=32):
        """Generate a password reset token"""
        return secrets.token_urlsafe(length)

    @staticmethod
    def validate_otp_code(otp_code):
        """Validate OTP code format"""
        if not otp_code or not isinstance(otp_code, str):
            raise ValidationError("OTP must be a string")
        if not otp_code.isdigit():
            raise ValidationError("OTP must contain only digits")
        if len(otp_code) != 6:
            raise ValidationError("OTP must be 6 digits long")
        return otp_code

    @staticmethod
    def check_otp_expiry(expires_at):
        """Check if OTP has expired"""
        return datetime.utcnow() > expires_at

    @staticmethod
    def get_otp_expiry_time(minutes=5):
        """Get OTP expiry time (default: 5 minutes)"""
        return datetime.utcnow() + timedelta(minutes=minutes)

    @staticmethod
    def get_reset_token_expiry_time(hours=1):
        """Get password reset token expiry time (default: 1 hour)"""
        return datetime.utcnow() + timedelta(hours=hours)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _get_template(channel: str):
        """
        Fetch the active OTP notification template for the given channel
        from the database.

        Args:
            channel: 'email' or 'whatsapp'

        Returns:
            NotificationTemplate instance or None
        """
        try:
            from app.models.notifications.notification_template import NotificationTemplate

            template = (
                NotificationTemplate.query.filter_by(
                    notification_type=OTP_NOTIFICATION_TYPE,
                    channel=channel,
                    is_active=True,
                )
                .order_by(NotificationTemplate.version.desc())
                .first()
            )
            return template
        except Exception as exc:
            logger.error("Failed to fetch OTP template for channel '%s': %s", channel, exc)
            return None

    @staticmethod
    def _render(template_content: str, variables: dict) -> str:
        """Render a Jinja2 template string with the provided variables."""
        from app.utils.notification_helpers import NotificationTemplateRenderer

        return NotificationTemplateRenderer.render_template(template_content, variables)

    # ------------------------------------------------------------------
    # Public send method
    # ------------------------------------------------------------------

    def send_otp(
        self,
        email: str,
        otp_phone: str | None,
        otp_code: str,
        username: str = "",
        expiry_minutes: int = 5,
    ) -> dict:
        """
        Send OTP code via email and (optionally) WhatsApp using DB templates.

        Templates are fetched from the ``notification_templates`` table
        (notification_type='otp_verification').  If no template is found
        for a channel a plain-text fallback is used so delivery is never
        silently dropped.

        Args:
            email:          Recipient e-mail address.
            otp_phone:      Recipient phone in E.164 format, or None / empty
                            to skip WhatsApp delivery.
            otp_code:       The 6-digit OTP string.
            username:       Optional display name rendered inside the template.
            expiry_minutes: How many minutes the OTP is valid (default 5).

        Returns:
            dict: ``{"email": <result>, "whatsapp": <result or None>}``
        """
        # Map to the variable names used in the seeded templates
        template_vars = {
            "recipient_name": username or email,
            "otp_code": otp_code,
            "expires_in": f"{expiry_minutes} minutes",
        }

        results = {"email": None, "whatsapp": None}

        # ---- Email -------------------------------------------------------
        try:
            from app.services.notifications.channels.email_channel import EmailChannel

            email_template = self._get_template("email")

            if email_template:
                subject = self._render(
                    email_template.subject or "Your OTP Code", template_vars
                )
                html_body = (
                    self._render(email_template.template_html, template_vars)
                    if email_template.template_html
                    else None
                )
                text_body = (
                    self._render(email_template.template_text, template_vars)
                    if email_template.template_text
                    else None
                )
            else:
                logger.warning(
                    "No active email template found for '%s'; using plain-text fallback.",
                    OTP_NOTIFICATION_TYPE,
                )
                subject = "Your OTP Code"
                html_body = None
                text_body = (
                    f"Hello {username or email},\n\n"
                    f"Your OTP code is: {otp_code}\n\n"
                    f"This code expires in {expiry_minutes} minutes.\n\n"
                    "If you did not request this, please ignore this message."
                )

            results["email"] = EmailChannel().send(
                recipient=email,
                subject=subject,
                content=text_body,
                html_content=html_body,
            )
            logger.info("OTP email dispatched to %s", email)

        except Exception as exc:
            logger.error("Failed to send OTP email to %s: %s", email, exc)
            results["email"] = {"status": "failed", "error": str(exc)}

        # ---- WhatsApp ----------------------------------------------------
        if otp_phone:
            try:
                from app.services.notifications.channels.whatsapp_channel import WhatsAppChannel

                wa_template = self._get_template("whatsapp")

                if wa_template:
                    wa_body = self._render(
                        wa_template.template_text or "", template_vars
                    )
                else:
                    logger.warning(
                        "No active WhatsApp template found for '%s'; using plain-text fallback.",
                        OTP_NOTIFICATION_TYPE,
                    )
                    wa_body = (
                        f"Hello {username or ''},\n"
                        f"Your OTP code is: *{otp_code}*\n"
                        f"Valid for {expiry_minutes} minutes. Do not share it with anyone."
                    )

                results["whatsapp"] = WhatsAppChannel().send(
                    recipient=otp_phone,
                    content=wa_body,
                    messageType="OTP",
                    priority="HIGH",
                )
                logger.info("OTP WhatsApp message dispatched to %s", otp_phone)

            except Exception as exc:
                logger.error("Failed to send OTP WhatsApp to %s: %s", otp_phone, exc)
                results["whatsapp"] = {"status": "failed", "error": str(exc)}

        return results