"""
Password Reset Service
Handles password reset and change workflows
"""

import logging
import uuid
from datetime import datetime

from flask import current_app

from app import db
from app.exceptions import AuthenticationError, ValidationError
from app.models.auth import OTPRequest, User
from app.services.base_service import BaseService
from app.utils.auth import OTPManager, PasswordManager, SessionManager

logger = logging.getLogger(__name__)

class PasswordResetService(BaseService):
    """Service for password reset and change"""

    @staticmethod
    def initiate_password_reset(email):
        """
        Initiate password reset workflow

        Args:
            email: User email address

        Returns:
            tuple: (reset_token, otp_code)

        Raises:
            ValidationError: If user not found
        """
        try:
            # Find user
            user = User.query.filter_by(email=email).first()
            if not user:
                # Don't reveal if email exists - security best practice
                logger.warning(f"Password reset requested for non-existent email: {email}")
                return "nonexistent@example.com", "000000"  # Dummy values

            # Generate reset token and OTP
            reset_token = OTPManager.generate_reset_token()
            otp_code = OTPManager.generate_otp_code()
            otp_hash = PasswordManager.hash_password(otp_code)
            reset_expiry = OTPManager.get_reset_token_expiry_time()

            # Create OTP request for password reset
            otp_request = OTPRequest(
                user_id=user.user_id,
                email=email,
                verification_token=reset_token,
                otp_code_hash=otp_hash,
                purpose="password_reset",
                channel="both",
                expires_at=reset_expiry,
            )

            db.session.add(otp_request)
            db.session.commit()

            # Store in Redis
            otp_data = {
                "otp_id": otp_request.otp_id,
                "user_id": user.user_id,
                "email": email,
                "purpose": "password_reset",
                "channel": "both",
                "created_at": str(otp_request.created_at),
                "expires_at": str(reset_expiry),
            }
            SessionManager.store_otp(reset_token, otp_data, ttl_hours=1)

            # Send password reset OTP notification via email and WhatsApp
            PasswordResetService._send_password_reset_otp_notification(
                user=user,
                otp_code=otp_code,
                reset_token=reset_token,
                expires_at=reset_expiry,
            )

            logger.info(f"Password reset initiated for {email}")

            return reset_token, otp_code

        except Exception as e:
            logger.error(f"Password reset initiation failed: {str(e)}")
            raise ValidationError(f"Password reset failed: {str(e)}")
    
    @staticmethod
    def _send_password_reset_otp_notification(user, otp_code, reset_token, expires_at):
        """Send password reset OTP notification via email and WhatsApp.

        This is a best-effort method — any failure is logged but never re-raised
        so that the password reset flow is never blocked by a notification error.
        """
        try:
            from app.models.notifications.notification_template import NotificationTemplate
            from app.utils.notification_helpers import NotificationTemplateRenderer

            NOTIF_TYPE = "password_reset_request"
            expiry_time = expires_at.strftime("%Y-%m-%d %H:%M UTC") if expires_at else "N/A"
            reset_url = f"{current_app.config.get('FRONTEND_URL', '#')}/password-reset?token={reset_token}&code={otp_code}"

            template_vars = {
                "recipient_name": (
                    f"{user.first_name} {user.last_name}".strip() or user.email
                ),
                "reset_url": reset_url,
                "expiry_time": expiry_time,
                "ip_address": "N/A",  # Could be captured from request context if needed
                "platform_url": current_app.config.get("FRONTEND_URL", "#"),
                "unsubscribe_url": current_app.config.get("UNSUBSCRIBE_URL", "#"),
                "preferences_url": current_app.config.get("PREFERENCES_URL", "#"),
                "current_year": str(datetime.utcnow().year),
            }

            def _get_tpl(channel):
                return (
                    NotificationTemplate.query
                    .filter_by(
                        notification_type=NOTIF_TYPE,
                        channel=channel,
                        is_active=True,
                    )
                    .order_by(NotificationTemplate.version.desc())
                    .first()
                )

            def _render(content):
                return NotificationTemplateRenderer.render_template(content, template_vars)

            # ── Email ────────────────────────────────────────────────────────
            try:
                from app.services.notifications.channels.email_channel import EmailChannel

                tpl = _get_tpl("email")
                if tpl:
                    EmailChannel().send(
                        recipient=user.email,
                        subject=_render(tpl.subject or "Password Reset Request"),
                        content=_render(tpl.template_text) if tpl.template_text else None,
                        html_content=_render(tpl.template_html) if tpl.template_html else None,
                    )
                    logger.info("password_reset_request email sent to %s", user.email)
                else:
                    logger.warning("No active password_reset_request email template found")
            except Exception as exc:
                logger.error(
                    "password_reset_request email failed for %s: %s", user.email, exc, exc_info=True
                )

            # ── WhatsApp ─────────────────────────────────────────────────────
            if getattr(user, "phone", None):
                try:
                    from app.services.notifications.channels.whatsapp_channel import WhatsAppChannel

                    tpl = _get_tpl("whatsapp")
                    if tpl and tpl.template_text:
                        WhatsAppChannel().send(
                            recipient=user.phone,
                            content=_render(tpl.template_text),
                            messageType="OTP",
                            priority="HIGH",
                        )
                        logger.info("password_reset_request WhatsApp sent to %s", user.phone)
                    else:
                        logger.warning("No active password_reset_request WhatsApp template found")
                except Exception as exc:
                    logger.error(
                        "password_reset_request WhatsApp failed for %s: %s",
                        user.phone, exc, exc_info=True,
                    )

        except Exception as exc:
            logger.error(
                "_send_password_reset_otp_notification failed: %s", exc, exc_info=True
            )

    @staticmethod
    def _send_password_reset_confirmation_notification(user):
        """Send password reset confirmation notification via email and WhatsApp.

        This is a best-effort method — any failure is logged but never re-raised.
        """
        try:
            from app.models.notifications.notification_template import NotificationTemplate
            from app.utils.notification_helpers import NotificationTemplateRenderer

            NOTIF_TYPE = "password_reset_confirmation"
            reset_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

            template_vars = {
                "recipient_name": (
                    f"{user.first_name} {user.last_name}".strip() or user.email
                ),
                "reset_time": reset_time,
                "support_url": current_app.config.get("SUPPORT_URL", "#"),
                "platform_url": current_app.config.get("FRONTEND_URL", "#"),
                "unsubscribe_url": current_app.config.get("UNSUBSCRIBE_URL", "#"),
                "preferences_url": current_app.config.get("PREFERENCES_URL", "#"),
                "current_year": str(datetime.utcnow().year),
            }

            def _get_tpl(channel):
                return (
                    NotificationTemplate.query
                    .filter_by(
                        notification_type=NOTIF_TYPE,
                        channel=channel,
                        is_active=True,
                    )
                    .order_by(NotificationTemplate.version.desc())
                    .first()
                )

            def _render(content):
                return NotificationTemplateRenderer.render_template(content, template_vars)

            # ── Email ────────────────────────────────────────────────────────
            try:
                from app.services.notifications.channels.email_channel import EmailChannel

                tpl = _get_tpl("email")
                if tpl:
                    EmailChannel().send(
                        recipient=user.email,
                        subject=_render(tpl.subject or "Password Reset Successful"),
                        content=_render(tpl.template_text) if tpl.template_text else None,
                        html_content=_render(tpl.template_html) if tpl.template_html else None,
                    )
                    logger.info("password_reset_confirmation email sent to %s", user.email)
                else:
                    logger.warning("No active password_reset_confirmation email template found")
            except Exception as exc:
                logger.error(
                    "password_reset_confirmation email failed for %s: %s", user.email, exc, exc_info=True
                )

            # ── WhatsApp ─────────────────────────────────────────────────────
            if getattr(user, "phone", None):
                try:
                    from app.services.notifications.channels.whatsapp_channel import WhatsAppChannel

                    tpl = _get_tpl("whatsapp")
                    if tpl and tpl.template_text:
                        WhatsAppChannel().send(
                            recipient=user.phone,
                            content=_render(tpl.template_text),
                            messageType="NOTIFICATION",
                            priority="HIGH",
                        )
                        logger.info("password_reset_confirmation WhatsApp sent to %s", user.phone)
                    else:
                        logger.warning("No active password_reset_confirmation WhatsApp template found")
                except Exception as exc:
                    logger.error(
                        "password_reset_confirmation WhatsApp failed for %s: %s",
                        user.phone, exc, exc_info=True,
                    )

        except Exception as exc:
            logger.error(
                "_send_password_reset_confirmation_notification failed: %s", exc, exc_info=True
            )


    @staticmethod
    def reset_password(reset_token, otp_code, new_password, confirm_password):
        """
        Reset password with OTP verification

        Args:
            reset_token: Password reset token
            otp_code: OTP code for verification
            new_password: New password
            confirm_password: Password confirmation

        Returns:
            dict: Reset status

        Raises:
            ValidationError: If reset fails
        """
        try:
            # Validate password
            PasswordManager.validate_password_strength(new_password)

            # Passwords must match
            if new_password != confirm_password:
                raise ValidationError("Passwords do not match")

            # Get OTP request
            otp_request = OTPRequest.query.filter_by(
                verification_token=reset_token, purpose="password_reset"
            ).first()

            if not otp_request:
                raise ValidationError("Invalid or expired reset token")

            # Check if expired
            if OTPManager.check_otp_expiry(otp_request.expires_at):
                raise ValidationError("Reset token has expired")

            # Verify OTP
            if not PasswordManager.verify_password(otp_code, otp_request.otp_code_hash):
                raise ValidationError("Invalid OTP code")

            # Get user
            user = User.query.filter_by(user_id=otp_request.user_id).first()
            if not user:
                raise ValidationError("User not found")

            # Hash new password
            new_password_hash = PasswordManager.hash_password(new_password)

            # Update password
            user.password_hash = new_password_hash
            otp_request.is_used = True

            db.session.commit()

            # Clear OTP from Redis
            SessionManager.delete_otp(reset_token)

            # Send password reset confirmation notification via email and WhatsApp
            PasswordResetService._send_password_reset_confirmation_notification(user)

            logger.info(f"Password reset successful for {user.email}")

            return {
                "status": "success",
                "message": "Password reset successfully. Please login with your new password.",
            }

        except ValidationError:
            db.session.rollback()
            raise
        except Exception as e:
            db.session.rollback()
            logger.error(f"Password reset failed: {str(e)}")
            raise ValidationError(f"Password reset failed: {str(e)}")

    @staticmethod
    def change_password(user_id, current_password, new_password, confirm_password):
        """
        Change password for logged-in user

        Args:
            user_id: User's unique identifier
            current_password: Current password
            new_password: New password
            confirm_password: Password confirmation

        Returns:
            dict: Change status

        Raises:
            AuthenticationError: If authentication fails
            ValidationError: If validation fails
        """
        try:
            # Get user
            user = User.query.filter_by(user_id=user_id).first()
            if not user:
                raise ValidationError("User not found")

            # Verify current password
            if not PasswordManager.verify_password(current_password, user.password_hash):
                raise AuthenticationError("Current password is incorrect")

            # Validate new password
            PasswordManager.validate_password_strength(new_password)

            # Passwords must match
            if new_password != confirm_password:
                raise ValidationError("New passwords do not match")

            # New password must be different from current
            if current_password == new_password:
                raise ValidationError("New password must be different from current password")

            # Hash new password
            new_password_hash = PasswordManager.hash_password(new_password)

            # Update password
            user.password_hash = new_password_hash
            db.session.commit()

            logger.info(f"Password changed for user {user_id}")

            return {"status": "success", "message": "Password changed successfully"}

        except (AuthenticationError, ValidationError):
            raise
        except Exception as e:
            logger.error(f"Password change failed: {str(e)}")
            raise ValidationError(f"Password change failed: {str(e)}")

   