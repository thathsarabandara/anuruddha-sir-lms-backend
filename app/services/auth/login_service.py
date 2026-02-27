"""
Login Service
Handles user authentication and login workflow
"""

import logging
from datetime import datetime, timedelta

from flask import current_app

from app import db
from app.exceptions import AuthenticationError, ValidationError
from app.models.auth import LoginHistory, User, UserAccountStatus, role
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
            from app.models.notifications.notification_template import NotificationTemplate
            from app.utils.notification_helpers import NotificationTemplateRenderer

            NOTIF_TYPE = "account_locked"
            ban_expires_str = (
                ban_expires_at.strftime("%Y-%m-%d %H:%M UTC") if ban_expires_at else "N/A"
            )

            template_vars = {
                "recipient_name": (
                    f"{user.first_name} {user.last_name}".strip() or user.email
                ),
                "failed_attempts": str(failed_attempts),
                "ban_duration_hours": str(LoginService.BAN_DURATION_HOURS),
                "ban_expires_at": ban_expires_str,
                "support_url": current_app.config.get("SUPPORT_URL", "#"),
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
                        subject=_render(tpl.subject or "Your account has been locked"),
                        content=_render(tpl.template_text) if tpl.template_text else None,
                        html_content=_render(tpl.template_html) if tpl.template_html else None,
                    )
                    logger.info("account_locked email sent to %s", user.email)
                else:
                    logger.warning("No active account_locked email template found")
            except Exception as exc:
                logger.error(
                    "account_locked email failed for %s: %s", user.email, exc, exc_info=True
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
                            messageType="ALERT",
                            priority="HIGH",
                        )
                        logger.info("account_locked WhatsApp sent to %s", user.phone)
                    else:
                        logger.warning("No active account_locked WhatsApp template found")
                except Exception as exc:
                    logger.error(
                        "account_locked WhatsApp failed for %s: %s",
                        user.phone, exc, exc_info=True,
                    )

        except Exception as exc:
            logger.error(
                "_send_account_locked_notification failed: %s", exc, exc_info=True
            )

    @staticmethod
    @staticmethod
    def _send_login_notification(user, ip_address, user_agent):
        """Send suspicious login alert notification via email and WhatsApp.

        This is a best-effort method — any failure is logged but never re-raised
        so that the authentication flow is never blocked by a notification error.
        """
        try:
            from app.models.notifications.notification_template import NotificationTemplate
            from app.utils.notification_helpers import NotificationTemplateRenderer

            NOTIF_TYPE = "suspicious_login_alert"
            login_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

            template_vars = {
                "recipient_name": (
                    f"{user.first_name} {user.last_name}".strip() or user.email
                ),
                "ip_address": ip_address,
                "user_agent": user_agent,
                "login_time": login_time,
                "support_url": current_app.config.get("SUPPORT_URL", "#"),
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
                        subject=_render(tpl.subject or "Suspicious login activity detected"),
                        content=_render(tpl.template_text) if tpl.template_text else None,
                        html_content=_render(tpl.template_html) if tpl.template_html else None,
                    )
                    logger.info("suspicious_login_alert email sent to %s", user.email)
                else:
                    logger.warning("No active suspicious_login_alert email template found")
            except Exception as exc:
                logger.error(
                    "suspicious_login_alert email failed for %s: %s", user.email, exc, exc_info=True
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
                            messageType="ALERT",
                            priority="HIGH",
                        )
                        logger.info("suspicious_login_alert WhatsApp sent to %s", user.phone)
                    else:
                        logger.warning("No active suspicious_login_alert WhatsApp template found")
                except Exception as exc:
                    logger.error(
                        "suspicious_login_alert WhatsApp failed for %s: %s",
                        user.phone, exc, exc_info=True,
                    )

        except Exception as exc:
            logger.error(
                "_send_login_notification failed: %s", exc, exc_info=True
            )

    @staticmethod
    def login_user(email, password, ip_address, user_agent, device_name=None):
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

            if not user:
                # Track attempt globally by email
                SessionManager.track_login_attempt(email, ip_address)
                raise AuthenticationError("Invalid email or password")

            # Check if account is verified
            if not user.email_verified or not user.is_active:
                raise AuthenticationError("Account has not been verified")

            # Check account ban status
            account_status = UserAccountStatus.query.filter_by(user_id=user.user_id).first()
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

            # Generate tokens
            access_token = TokenManager.generate_access_token(
                user.user_id, user.email, user.username, "student"  # TODO: Get actual role
            )
            refresh_token = TokenManager.generate_refresh_token(
                user.user_id, user.email, user.username
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
