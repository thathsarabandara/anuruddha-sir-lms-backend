"""
Login History Service
Handles login history tracking and retrieval
"""

import logging

from app import db
from app.exceptions import ValidationError
from app.models.auth import LoginHistory, User
from app.services.health.base_service import BaseService
from app.utils.helpers import get_page_and_limit, get_offset_from_page

logger = logging.getLogger(__name__)


class LoginHistoryService(BaseService):
    """Service for login history management"""

    @staticmethod
    def get_login_history(user_id, page=1, limit=20):
        """
        Retrieve user's login history

        Args:
            user_id: User's unique identifier
            page: Page number (1-indexed)
            limit: Items per page

        Returns:
            tuple: (history_list, total_count)

        Raises:
            ValidationError: If user not found
        """
        try:
            # Verify user exists
            user = User.query.filter_by(user_id=user_id).first()
            if not user:
                raise ValidationError("User not found")

            # Calculate offset
            offset = get_offset_from_page(page, limit)

            # Get total count
            total = LoginHistory.query.filter_by(user_id=user_id).count()

            # Get paginated results
            login_records = (
                LoginHistory.query.filter_by(user_id=user_id)
                .order_by(LoginHistory.login_at.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )

            # Convert to dict
            history_list = []
            for record in login_records:
                history_list.append({
                    "login_id": record.login_id,
                    "timestamp": record.login_at.isoformat() if record.login_at else None,
                    "ip_address": record.ip_address,
                    "user_agent": record.user_agent,
                    "device": record.device_name or "Unknown",
                    "is_successful": record.is_successful,
                    "logout_time": record.logout_at.isoformat() if record.logout_at else None,
                })

            logger.info(f"Retrieved login history for user {user_id}")

            return history_list, total

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Failed to retrieve login history: {str(e)}")
            raise ValidationError(f"Failed to retrieve login history: {str(e)}")

    @staticmethod
    def clear_old_login_history(user_id, keep_days=90):
        """
        Clear login history older than specified days

        Args:
            user_id: User's unique identifier
            keep_days: Number of days to keep (default: 90)

        Returns:
            dict: Deletion status

        Raises:
            ValidationError: If operation fails
        """
        try:
            from datetime import datetime, timedelta
            
            # Calculate cutoff date
            cutoff_date = datetime.utcnow() - timedelta(days=keep_days)

            # Delete old records
            deleted_count = (
                LoginHistory.query.filter(
                    LoginHistory.user_id == user_id,
                    LoginHistory.login_at < cutoff_date
                )
                .delete()
            )

            db.session.commit()

            logger.info(f"Cleared {deleted_count} old login records for user {user_id}")

            return {
                "status": "success",
                "deleted_count": deleted_count,
                "message": f"Deleted {deleted_count} login records older than {keep_days} days",
            }

        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to clear login history: {str(e)}")
            raise ValidationError(f"Failed to clear login history: {str(e)}")
