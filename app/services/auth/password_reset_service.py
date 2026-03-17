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
from app.services.health.base_service import BaseService
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
            str: reset_token

        Raises:
            ValidationError: If user not found
        """
        try:
            # Find user
            user = User.query.filter_by(email=email).first()
            if not user:
                # Don't reveal if email exists - security best practice
                logger.warning(f"Password reset requested for non-existent email: {email}")
                return "nonexistent"

            # Generate reset token (token-based, no OTP)
            reset_token = OTPManager.generate_reset_token()
            reset_expiry = OTPManager.get_reset_token_expiry_time()

            # Create password reset token record
            otp_request = OTPRequest(
                user_id=user.user_id,
                email=email,
                verification_token=reset_token,
                otp_code_hash="",  # Empty since we're using token-based reset
                purpose="password_reset",
                channel="both",  # Email and WhatsApp
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

            # Send password reset token notification via email
            PasswordResetService._send_password_reset_token_notification(
                user=user,
                reset_token=reset_token,
                expires_at=reset_expiry,
            )

            logger.info(f"Password reset initiated for {email}")

            return reset_token

        except Exception as e:
            logger.error(f"Password reset initiation failed: {str(e)}")
            raise ValidationError(f"Password reset failed: {str(e)}")
    
    @staticmethod
    def _send_password_reset_confirmation_notification(user):
        """Send password reset confirmation notification via email and WhatsApp."""
        try:
            from app.services.notifications.notification_service import NotificationService

            reset_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

            service = NotificationService(current_app)
            service.send_password_reset_confirmation(
                user_id=user.user_id,
                current_year=str(datetime.utcnow().year),
                platform_url=current_app.config.get("FRONTEND_URL", "#"),
                preferences_url=current_app.config.get("PREFERENCES_URL", "#"),
                recipient_name=f"{user.first_name} {user.last_name}".strip() or user.email,
                reset_time=reset_time,
                support_url=current_app.config.get("SUPPORT_URL", "#"),
                unsubscribe_url=current_app.config.get("UNSUBSCRIBE_URL", "#"),
                message_type="NOTIFICATION",
                priority="NORMAL",
                channels=["email", "whatsapp"],
            )

            logger.info(f"Password reset confirmation sent to {user.email}")

        except Exception as exc:
            logger.error(
                "_send_password_reset_confirmation_notification failed: %s", exc, exc_info=True
            )

    @staticmethod
    def _send_password_reset_token_notification(user, reset_token, expires_at):
        """Send password reset token notification via email and WhatsApp."""
        try:
            from app.services.notifications.notification_service import NotificationService

            reset_url = f"{current_app.config.get('FRONTEND_URL', '#')}/password-reset?token={reset_token}"
            expiry_time = expires_at.strftime("%Y-%m-%d %H:%M UTC") if expires_at else "N/A"

            service = NotificationService(current_app)
            service.send_password_reset_request(
                user_id=user.user_id,
                current_year=str(datetime.utcnow().year),
                expiry_time=expiry_time,
                ip_address="N/A",
                platform_url=current_app.config.get("FRONTEND_URL", "#"),
                preferences_url=current_app.config.get("PREFERENCES_URL", "#"),
                recipient_name=f"{user.first_name} {user.last_name}".strip() or user.email,
                reset_url=reset_url,
                unsubscribe_url=current_app.config.get("UNSUBSCRIBE_URL", "#"),
                message_type="NOTIFICATION",
                priority="NORMAL",
                channels=["email", "whatsapp"],
            )

            logger.info(f"Password reset token notification sent to {user.email}")

        except Exception as exc:
            logger.error(
                "_send_password_reset_token_notification failed: %s", exc, exc_info=True
            )

    @staticmethod
    def reset_password(reset_token, new_password, confirm_password):
        """
        Reset password with token verification (no OTP required)

        Args:
            reset_token: Password reset token
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

            # Get OTP request (password reset token record)
            otp_request = OTPRequest.query.filter_by(
                verification_token=reset_token, purpose="password_reset"
            ).first()

            if not otp_request:
                raise ValidationError("Invalid or expired reset token")

            # Check if expired
            if OTPManager.check_otp_expiry(otp_request.expires_at):
                raise ValidationError("Reset token has expired")

            # Check if already used
            if otp_request.is_used:
                raise ValidationError("Reset token has already been used")

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

            # Send password reset confirmation notification via email
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

    @staticmethod
    def verify_reset_token(reset_token):
        """
        Verify if a password reset token is valid and not expired.

        Args:
            reset_token: Password reset token

        Returns:
            dict: Token verification status and user email

        Raises:
            ValidationError: If token is invalid or expired
        """
        try:
            # Get OTP request
            otp_request = OTPRequest.query.filter_by(
                verification_token=reset_token, purpose="password_reset"
            ).first()

            if not otp_request:
                raise ValidationError("Invalid or expired reset token")

            # Check if expired
            if OTPManager.check_otp_expiry(otp_request.expires_at):
                raise ValidationError("Reset token has expired")

            # Check if already used
            if otp_request.is_used:
                raise ValidationError("Reset token has already been used")

            # Get user to verify they exist
            user = User.query.filter_by(user_id=otp_request.user_id).first()
            if not user:
                raise ValidationError("User not found")

            # Calculate remaining expiry time
            remaining_seconds = int(
                (otp_request.expires_at - datetime.utcnow()).total_seconds()
            )

            logger.info(f"Reset token verified for {user.email}")

            return {
                "is_valid": True,
                "email": user.email,
                "user_id": user.user_id,
                "expires_in": remaining_seconds,
                "message": "Reset token is valid. You can now reset your password.",
            }

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Reset token verification failed: {str(e)}")
            raise ValidationError(f"Reset token verification failed: {str(e)}")


   