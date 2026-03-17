"""
Token Verification Service
Handles JWT token verification and validation
"""

import logging
from datetime import datetime

from app import db
from app.exceptions import AuthenticationError
from app.models.auth import AccessToken, User
from app.models.auth.user_account_status import UserAccountStatus
from app.models.users.student_profile import StudentProfile
from app.models.users.teacher_profile import TeacherProfile
from app.services.health.base_service import BaseService
from app.utils.auth import TokenManager

logger = logging.getLogger(__name__)


class TokenVerificationService(BaseService):
    """Service for token verification"""

    @staticmethod
    def verify_token(access_token, refresh_token=None):
        """
        Verify and validate access token.
        
        If access token is expired, automatically generates a new one using
        the refresh token and returns both along with user info.

        Args:
            access_token: JWT access token
            refresh_token: JWT refresh token (optional, required if access_token expired)
        Returns:
            dict: Token verification status, user info, and optionally new_access_token

        Raises:
            AuthenticationError: If token is invalid or cannot be refreshed
        """
        try:
            # ── Check if access token is revoked in database ──
            access_token_record = AccessToken.query.filter_by(token=access_token).first()
            if access_token_record and access_token_record.is_revoked and not access_token_record.expired_at < datetime.utcnow():
                raise AuthenticationError(
                    "Access token has been revoked. Please login again."
                )

            # Verify access token JWT signature
            payload = TokenManager.verify_token(access_token)

            if payload:
                # ── Access token is valid ──
                user_id = payload.get("user_id")
                email = payload.get("email")
                role = payload.get("role")

                if not user_id:
                    raise AuthenticationError("Invalid token payload")

                # Verify user still exists and is active
                user = User.query.filter_by(user_id=user_id).first()
                user_status = UserAccountStatus.query.filter_by(user_id=user_id).first() if user else None
                if not user or not user_status.is_active or user_status.is_banned:
                    raise AuthenticationError("User account is not active")

                # Calculate remaining time
                exp_timestamp = payload.get("exp")
                expires_in = int(exp_timestamp - datetime.utcnow().timestamp()) if exp_timestamp else 0

                logger.info(f"Token verified for user {email}")

                if role == "student":
                    student_profile = StudentProfile.query.filter_by(user_id=user_id).first()
                    if student_profile:
                        return {
                            "user_id": user_id,
                            "email": email,
                            "role": role,
                            "first_name": user.first_name,
                            "last_name": user.last_name,
                            "grade_level": student_profile.grade_level,
                            "expires_in": expires_in,
                            "phone_number": user.phone,
                            "bio": user.bio,
                            "profile_picture": user.profile_picture,
                            "date_of_birth":  student_profile.date_of_birth.isoformat() if student_profile.date_of_birth else None,
                            "school": student_profile.school,
                            "address": student_profile.address,
                            "parent_name": student_profile.parent_name,
                            "parent_contact": student_profile.parent_contact,
                            "new_access_token": None,
                        }
                elif role == "teacher":
                    teacher_profile = TeacherProfile.query.filter_by(user_id=user_id).first()
                    if teacher_profile:
                        return {
                            "user_id": user_id,
                            "email": email,
                            "role": role,
                            "first_name": user.first_name,
                            "last_name": user.last_name,
                            "qualifications": teacher_profile.qualifications,
                            "subjects_taught": teacher_profile.get_subjects(),
                            "years_of_experience": teacher_profile.years_of_experience,
                            "language_of_instruction": teacher_profile.language_of_instruction,
                            "professional_bio": teacher_profile.professional_bio,
                            "address": teacher_profile.address,
                            "expires_in": expires_in,
                            "phone_number": user.phone,
                            "bio": user.bio,
                            "profile_picture": user.profile_picture,
                            "new_access_token": None,
                        }
                else:
                    return {
                        "valid": True,
                        "user_id": user_id,
                        "email": email,
                        "role": role,
                        "expires_in": expires_in,
                        "new_access_token": None,  # No new token generated
                    }

            else:
                # ── Access token is expired, generate new one using refresh token ──
                if not refresh_token:
                    raise AuthenticationError(
                        "Access token expired. Refresh token required to generate new access token"
                    )

                # Import here to avoid circular dependency
                from app.services.auth.token_refresh_service import TokenRefreshService

                # Generate new access token using refresh token
                new_access_token, expires_in = TokenRefreshService.refresh_access_token(
                    refresh_token
                )

                # Extract user info from refresh token
                refresh_payload = TokenManager.verify_token(refresh_token)
                user_id = refresh_payload.get("user_id")
                email = refresh_payload.get("email")
                role = refresh_payload.get("role")

                if not user_id:
                    raise AuthenticationError("Invalid refresh token payload")

                logger.info(f"Access token expired, new token generated for user {email}")

                return {
                    "valid": True,
                    "user_id": user_id,
                    "email": email,
                    "role": role,
                    "expires_in": expires_in,
                    "new_access_token": new_access_token,  # Return new token to client
                }

        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(f"Token verification failed: {str(e)}")
            raise AuthenticationError(f"Token verification failed: {str(e)}")
