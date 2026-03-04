"""
OTP Verification Service
Handles OTP verification for registration, password reset, and login
"""

import logging
from datetime import datetime

from app import config, db
from app.exceptions import ValidationError
from app.models.auth import OTPRequest, User
from app.services.base_service import BaseService
from app.services.notifications.notification_service import NotificationService
from app.utils.auth import OTPManager, PasswordManager, SessionManager, TokenManager

logger = logging.getLogger(__name__)


class OTPVerificationService(BaseService):
    """Service for OTP verification"""

    @staticmethod
    def verify_otp(otp_code, verification_token,):
        """
        Verify OTP code for account activation

        Args:
            otp_code: OTP code to verify
            verification_token: Verification token

        Returns:
            dict: User data with verified status

        Raises:
            ValidationError: If OTP is invalid or expired
        """
        try:
            # Validate OTP format
            OTPManager.validate_otp_code(otp_code)

            # Get OTP from database and Redis
            otp_request = OTPRequest.query.filter_by(
                verification_token=verification_token
            ).first()

            if not otp_request:
                raise ValidationError("Invalid verification token")

            # Check if already used
            if otp_request.is_used:
                raise ValidationError("Verification token has already been used")

            # Check if expired
            if OTPManager.check_otp_expiry(otp_request.expires_at):
                raise ValidationError("OTP has expired. Please request a new one.")

            # Check attempt count
            if otp_request.attempt_count >= otp_request.max_attempts:
                raise ValidationError("Maximum OTP verification attempts exceeded")

            # Verify OTP code (compare with hashed)
            if not PasswordManager.verify_password(otp_code, otp_request.otp_code_hash):
                otp_request.attempt_count += 1
                db.session.commit()
                raise ValidationError(
                    f"Invalid OTP code. {otp_request.max_attempts - otp_request.attempt_count} attempts remaining"
                )

            # Mark OTP as verified and used
            otp_request.is_verified = True
            otp_request.is_used = True
            otp_request.verified_at = datetime.utcnow()

            # Get user and mark email as verified — do NOT activate yet;
            # account stays inactive until an admin approves it.
            user = User.query.filter_by(email=otp_request.email).first()
            if not user:
                raise ValidationError("User not found")

            user.email_verified = True
            # user.is_active remains False

            # Advance approval_status from 'pending_verification' → 'pending_approval'
            from app.models.auth.user_account_status import UserAccountStatus
            status_record = UserAccountStatus.query.filter_by(user_id=user.user_id).first()
            if status_record and status_record.approval_status == "pending_verification":
                status_record.approval_status = "pending_approval"

            db.session.commit()

            # Delete OTP from Redis
            SessionManager.delete_otp(verification_token)

            # Send registration pending admin review notification
            try:
                NotificationService().send_registration_pending_admin_review(
                    user.id, 
                    currrent_year=datetime.utcnow().year, 
                    platform_url=config.get("FRONTEND_URL"), 
                    preferences_url=config.get("PREFERENCES_URL")+"/nofication/prefences", 
                    recipient_name=user.first_name or user.username, 
                    recipient_name=user.username, 
                    messagType="NOTIFICATION", 
                    priority="NORMAL", 
                    channels=['email', 'whatsapp']
                    )
                
            except Exception as exc:
                logger.error(f"Failed to send registration pending notification: {str(exc)}")

            logger.info(f"OTP verified for user {user.email} — awaiting admin approval")

            return {
                "user_id": user.user_id,
                "email": user.email,
                "username": user.username,
                "first_name": user.first_name,
                "account_status": "pending_approval",
                "verified": True,
                "message": "Email verified. Your account is pending admin approval. You will be notified once approved.",
            }

        except ValidationError:
            db.session.rollback()
            raise
        except Exception as e:
            db.session.rollback()
            logger.error(f"OTP verification failed: {str(e)}")
            raise ValidationError(f"OTP verification failed: {str(e)}")
