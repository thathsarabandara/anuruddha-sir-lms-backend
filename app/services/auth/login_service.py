"""
Login Service
Handles user authentication and login workflow
"""

import logging
from datetime import datetime, timedelta

from flask import current_app

from app import db
from app.exceptions import AuthenticationError, ValidationError
from app.models.auth import LoginHistory, User, UserAccountStatus, Role, UserRole
from app.models.auth.user_role import UserRole
from app.services.base_service import BaseService
from app.utils.auth import PasswordManager, SessionManager, TokenManager
from app.utils.validators import validate_email

logger = logging.getLogger(__name__)


class LoginService(BaseService):
    """Service for user authentication"""

    MAX_LOGIN_ATTEMPTS = 3
    BAN_DURATION_HOURS = 24


    @staticmethod
    def _send_account_locked_notification(user, failed_attempts: int, ban_expires_at):
        """Send account-locked notification via email and WhatsApp.

        This is a best-effort method — any failure is logged but never re-raised
        so that the authentication flow is never blocked by a notification error.
        """
        try:
            from app.services.notifications import NotificationService

            service = NotificationService()
            service.send_account_locked(
                user_id=user.user_id,
                failed_attempts=failed_attempts,
                ban_duration_hours=LoginService.BAN_DURATION_HOURS,
                ban_expires_at=ban_expires_at,
                recipient_name=f"{user.first_name} {user.last_name}".strip() or user.email,
                support_url=current_app.config.get("SUPPORT_URL", "#"),
                message_type="OTP",
                priority="HIGH",
                channels=["email", "whatsapp"],
            )
            logger.info("account_locked notification sent to user %s", user.user_id)

        except Exception as exc:
            logger.error(
                "_send_account_locked_notification failed for user %s: %s", user.user_id, exc, exc_info=True
            )


    @staticmethod
    def _send_login_notification(user, ip_address, user_agent):
        """Send suspicious login alert notification via email and WhatsApp.

        This is a best-effort method — any failure is logged but never re-raised
        so that the authentication flow is never blocked by a notification error.
        """
        try:
            from app.services.notifications import NotificationService

            service = NotificationService()
            service.send_suspicious_login_alert(
                user_id=user.user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                recipient_name=f"{user.first_name} {user.last_name}".strip() or user.email,
                support_url=current_app.config.get("SUPPORT_URL", "#"),
                message_type="OTP",
                priority="HIGH",
                channels=["email", "whatsapp"], 
            )
            logger.info("suspicious_login_alert notification sent to user %s", user.user_id)

        except Exception as exc:
            logger.error(
                "_send_login_notification failed for user %s: %s", user.user_id, exc, exc_info=True
            )

    @staticmethod
    def login_user(email, password, ip_address=None, user_agent=None, device_name=None):
        """
        Authenticate user and issue tokens

        Args:
            email: User email or username
            password: User password
            ip_address: Client IP address
            user_agent: Client user agent
            device_name: Optional device name

        Returns:
            tuple: (user_dict, access_token, refresh_token)

        Raises:
            AuthenticationError: If authentication fails
        """
        try:
            # Find user by email or username
            user = User.query.filter(
                (User.email == email) | (User.username == email)
            ).first()
            account_status = UserAccountStatus.query.filter_by(user_id=user.user_id).first() if user else None

            if not user:
                # Track attempt globally by email
                SessionManager.track_login_attempt(email, ip_address)
                raise AuthenticationError("Invalid email or password")

            # Check if account is verified
            if not user.email_verified or not account_status.is_active:
                raise AuthenticationError("Account has not been verified")

            if account_status and account_status.is_banned:
                if account_status.ban_expires_at > datetime.utcnow():
                    remaining_hours = (
                        account_status.ban_expires_at - datetime.utcnow()
                    ).seconds / 3600
                    raise AuthenticationError(
                        f"Account is banned. Try again in {remaining_hours:.0f} hours"
                    )
                else:
                    # Ban has expired, lift it
                    account_status.is_banned = False
                    account_status.failed_login_attempts = 0
                    db.session.commit()

            # Verify password
            if not PasswordManager.verify_password(password, user.password_hash):
                # Increment failed attempts
                if not account_status:
                    account_status = UserAccountStatus(user_id=user.user_id)
                    db.session.add(account_status)

                account_status.failed_login_attempts += 1
                account_status.last_failed_attempt_at = datetime.utcnow()

                # Ban account after max attempts
                if account_status.failed_login_attempts >= LoginService.MAX_LOGIN_ATTEMPTS:
                    account_status.is_banned = True
                    account_status.ban_reason = "Too many failed login attempts"
                    account_status.banned_at = datetime.utcnow()
                    account_status.ban_expires_at = datetime.utcnow() + timedelta(
                        hours=LoginService.BAN_DURATION_HOURS
                    )

                db.session.commit()

                # Send ban notification if account was just locked
                if account_status.failed_login_attempts >= LoginService.MAX_LOGIN_ATTEMPTS:
                    LoginService._send_account_locked_notification(
                        user=user,
                        failed_attempts=account_status.failed_login_attempts,
                        ban_expires_at=account_status.ban_expires_at,
                    )
                    remaining_attempts = LoginService.MAX_LOGIN_ATTEMPTS - account_status.failed_login_attempts
                

                if remaining_attempts <= 0:
                    raise AuthenticationError("Account locked due to too many failed attempts")

                raise AuthenticationError(
                    f"Invalid email or password. {remaining_attempts} attempts remaining"
                )

            # Clear failed login attempts on successful login
            if account_status:
                account_status.failed_login_attempts = 0
                account_status.last_failed_attempt_at = None

            roleid = UserRole.query.filter_by(user_id=user.user_id).first()
            if roleid:
                role_name = Role.query.filter_by(role_id=roleid.role_id).first().role_name
            # Generate tokens and store them in database
            access_token = TokenManager.generate_access_token(
                user.user_id, user.email, user.username, role_name, store_in_db=True
            )
            refresh_token = TokenManager.generate_refresh_token(
                user.user_id, user.email, user.username, store_in_db=True
            )

            # Update last login
            user.last_login = datetime.utcnow()

            # Log login  history
            login_record = LoginHistory(
                user_id=user.user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                device_name=device_name,
                is_successful=True,
            )

            LoginService._send_login_notification(user, ip_address, user_agent)

            db.session.add(login_record)
            db.session.commit()

            # Create session in Redis
            SessionManager.create_session(
                user.user_id, user.email, user.username, "student", access_token, refresh_token
            )

            logger.info(f"User logged in: {email} (ID: {user.user_id})")

            return {
                "user_id": user.user_id,
                "email": user.email,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": "student",
                "verified": user.email_verified,
            }, access_token, refresh_token

        except AuthenticationError:
            # Log failed attempt
            try:
                user = User.query.filter(
                    (User.email == email) | (User.username == email)
                ).first()
                if user:
                    login_failed = LoginHistory(
                        user_id=user.user_id,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        is_successful=False,
                        failure_reason="Invalid credentials",
                    )
                    db.session.add(login_failed)
                    db.session.commit()
            except Exception:
                pass
            raise
        except Exception as e:
            logger.error(f"Login failed: {str(e)}")
            raise AuthenticationError(f"Login failed: {str(e)}")
