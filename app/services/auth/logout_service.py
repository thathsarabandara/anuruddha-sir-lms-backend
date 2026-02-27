"""
Logout Service
Handles user logout and session termination
"""

import logging
from datetime import datetime

from app import db
from app.exceptions import AuthenticationError
from app.models.auth import AccessToken, LoginHistory, RefreshToken
from app.services.base_service import BaseService
from app.utils.auth import SessionManager

logger = logging.getLogger(__name__)


class LogoutService(BaseService):
    """Service for user logout"""

    @staticmethod
    def logout_user(user_id, access_token, refresh_token=None):
        """
        Logout user and destroy session.
        
        Revokes both the access token and refresh token to prevent reuse.

        Args:
            user_id: User's unique identifier
            access_token: User's access token
            refresh_token: User's refresh token (optional)

        Returns:
            dict: Logout status

        Raises:
            AuthenticationError: If logout fails
        """
        try:
            # ── Revoke access token ──
            if access_token:
                access_token_record = AccessToken.query.filter_by(token=access_token).first()
                if access_token_record and not access_token_record.is_revoked:
                    access_token_record.revoke()
                    logger.info(f"Access token revoked for user {user_id}")

            # ── Revoke refresh token ──
            if refresh_token:
                refresh_token_record = RefreshToken.query.filter_by(token=refresh_token).first()
                if refresh_token_record and not refresh_token_record.is_revoked:
                    refresh_token_record.revoke()
                    logger.info(f"Refresh token revoked for user {user_id}")

            # Extract token suffix for session lookup
            token_suffix = access_token[-16:] if len(access_token) > 16 else access_token

            # Destroy session in Redis
            SessionManager.destroy_session(user_id, token_suffix)

            # Update login history - mark logout time
            login_record = (
                LoginHistory.query.filter_by(user_id=user_id)
                .order_by(LoginHistory.login_at.desc())
                .first()
            )

            if login_record:
                login_record.logout_at = datetime.utcnow()
                db.session.commit()

            logger.info(f"User logged out: {user_id}")

            return {
                "status": "logged_out",
                "cleared_cookies": ["access_token", "refresh_token"],
                "session_destroyed": True,
            }

        except Exception as e:
            logger.error(f"Logout failed: {str(e)}")
            # Don't raise error on logout failure - user should be logged out anyway
            return {
                "status": "logged_out",
                "warning": "Session cleanup encountered an issue",
            }
