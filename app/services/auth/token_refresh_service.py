"""
Token Refresh Service
Handles JWT token refresh workflow
"""

import logging

from app import db
from app.exceptions import AuthenticationError
from app.models.auth import RefreshToken, User
from app.services.base_service import BaseService
from app.utils.auth import SessionManager, TokenManager

logger = logging.getLogger(__name__)


class TokenRefreshService(BaseService):
    """Service for token refresh"""

    @staticmethod
    def refresh_access_token(refresh_token):
        """
        Refresh access token using refresh token.
        
        Only generates new access token if refresh token is valid (not revoked/expired).

        Args:
            refresh_token: JWT refresh token

        Returns:
            tuple: (new_access_token, expires_in)

        Raises:
            AuthenticationError: If refresh token is invalid/revoked/expired
        """
        try:
            # Check if refresh token exists in database and is valid
            token_record = RefreshToken.query.filter_by(token=refresh_token).first()
            
            if not token_record:
                raise AuthenticationError("Refresh token not found. Please login again.")
            
            if token_record.is_revoked:
                raise AuthenticationError("Refresh token has been revoked. Please login again.")
            
            if token_record.is_expired():
                raise AuthenticationError("Refresh token has expired. Please login again.")
            
            # Verify JWT signature
            payload = TokenManager.verify_token(refresh_token)
            if not payload:
                raise AuthenticationError("Refresh token is invalid or expired. Please login again.")

            # Extract user info
            user_id = payload.get("user_id")
            email = payload.get("email")
            username = payload.get("username")

            if not user_id or not email:
                raise AuthenticationError("Invalid refresh token payload")

            # Get user from database to verify they still exist and are active
            user = User.query.filter_by(user_id=user_id).first()
            if not user or not user.is_active:
                raise AuthenticationError("User account is not active")

            # Generate new access token
            access_token = TokenManager.generate_access_token(user_id, email, username, "student", store_in_db=True)

            # Mark refresh token as used
            token_record.mark_used()

            # Update session in Redis
            SessionManager.create_session(
                user_id, email, username, "student", access_token, refresh_token
            )

            logger.info(f"Token refreshed for user {email}")

            return access_token, 1800  # 30 minutes

        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(f"Token refresh failed: {str(e)}")
            raise AuthenticationError(f"Token refresh failed: {str(e)}")

