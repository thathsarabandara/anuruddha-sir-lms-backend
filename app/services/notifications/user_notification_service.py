"""
User Notification Service
Handle user notification retrieval, marking as read/deleted
"""

import logging
from datetime import datetime

from app import db
from app.exceptions import ResourceNotFoundError
from app.models.notifications.notification import Notification
from app.services.base_service import BaseService

logger = logging.getLogger(__name__)


class UserNotificationService(BaseService):
    """Service for user notification management."""

    @staticmethod
    def get_user_notifications(
        user_id: str,
        limit: int = 20,
        offset: int = 0,
        filter_type: str = None,
        sort: str = "newest",
    ) -> dict:
        """
        Get user notifications with pagination and filtering.

        Args:
            user_id: User ID
            limit: Number of notifications to return
            offset: Pagination offset
            filter_type: Filter by type (unread, read, all)
            sort: Sort order (newest, oldest)

        Returns:
            dict: Paginated notification list with total count
        """
        try:
            query = Notification.query.filter_by(user_id=user_id, is_deleted=False)

            # Apply filter
            if filter_type == "unread":
                query = query.filter_by(is_read=False)
            elif filter_type == "read":
                query = query.filter_by(is_read=True)

            # Get total count
            total = query.count()

            # Apply sorting
            if sort == "oldest":
                query = query.order_by(Notification.created_at.asc())
            else:  # newest (default)
                query = query.order_by(Notification.created_at.desc())

            # Apply pagination
            notifications = query.limit(limit).offset(offset).all()

            return {
                "notifications": [notif.to_dict() for notif in notifications],
                "total": total,
                "limit": limit,
                "offset": offset,
            }

        except Exception as e:
            logger.error(f"Failed to get user notifications: {str(e)}")
            raise Exception(f"Failed to retrieve notifications: {str(e)}")

    @staticmethod
    def get_notification_detail(notification_id: str, user_id: str) -> dict:
        """
        Get detailed information about a notification.

        Args:
            notification_id: Notification ID
            user_id: User ID (for ownership verification)

        Returns:
            dict: Notification details

        Raises:
            ResourceNotFoundError: If notification not found
        """
        try:
            notification = Notification.query.filter_by(
                notification_id=notification_id, user_id=user_id, is_deleted=False
            ).first()

            if not notification:
                raise ResourceNotFoundError("Notification", notification_id)

            return notification.to_dict()

        except ResourceNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to get notification details: {str(e)}")
            raise Exception(f"Failed to retrieve notification: {str(e)}")

    @staticmethod
    def mark_as_read(notification_id: str, user_id: str) -> dict:
        """
        Mark notification as read.

        Args:
            notification_id: Notification ID
            user_id: User ID (for ownership verification)

        Returns:
            dict: Updated notification

        Raises:
            ResourceNotFoundError: If notification not found
        """
        try:
            notification = Notification.query.filter_by(
                notification_id=notification_id, user_id=user_id
            ).first()

            if not notification:
                raise ResourceNotFoundError("Notification", notification_id)

            notification.is_read = True
            notification.read_at = datetime.utcnow()

            db.session.commit()
            logger.info(f"Notification {notification_id} marked as read")

            return notification.to_dict()

        except ResourceNotFoundError:
            raise
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to mark notification as read: {str(e)}")
            raise Exception(f"Failed to update notification: {str(e)}")

    @staticmethod
    def mark_all_as_read(user_id: str) -> dict:
        """
        Mark all unread notifications as read for user.

        Args:
            user_id: User ID

        Returns:
            dict: Count of updated notifications
        """
        try:
            updated_count = (
                Notification.query.filter_by(user_id=user_id, is_read=False, is_deleted=False)
                .update(
                    {
                        Notification.is_read: True,
                        Notification.read_at: datetime.utcnow(),
                    }
                )
            )

            db.session.commit()
            logger.info(f"Marked {updated_count} notifications as read for user {user_id}")

            return {"updated_count": updated_count}

        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to mark all notifications as read: {str(e)}")
            raise Exception(f"Failed to update notifications: {str(e)}")

    @staticmethod
    def delete_notification(notification_id: str, user_id: str) -> dict:
        """
        Soft delete a notification.

        Args:
            notification_id: Notification ID
            user_id: User ID (for ownership verification)

        Returns:
            dict: Deletion confirmation

        Raises:
            ResourceNotFoundError: If notification not found
        """
        try:
            notification = Notification.query.filter_by(
                notification_id=notification_id, user_id=user_id
            ).first()

            if not notification:
                raise ResourceNotFoundError("Notification", notification_id)

            notification.is_deleted = True
            db.session.commit()

            logger.info(f"Notification {notification_id} deleted")

            return {"message": "Notification deleted successfully"}

        except ResourceNotFoundError:
            raise
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to delete notification: {str(e)}")
            raise Exception(f"Failed to delete notification: {str(e)}")

    @staticmethod
    def get_unread_count(user_id: str) -> dict:
        """
        Get count of unread notifications.

        Args:
            user_id: User ID

        Returns:
            dict: Unread count and breakdown by type
        """
        try:
            # Total unread
            total_unread = Notification.query.filter_by(
                user_id=user_id, is_read=False, is_deleted=False
            ).count()

            # Breakdown by type
            by_type = {}
            results = (
                db.session.query(
                    Notification.type, db.func.count(Notification.notification_id).label("count")
                )
                .filter_by(user_id=user_id, is_read=False, is_deleted=False)
                .group_by(Notification.type)
                .all()
            )

            for result in results:
                by_type[result[0]] = result[1]

            return {"total_unread": total_unread, "by_type": by_type}

        except Exception as e:
            logger.error(f"Failed to get unread count: {str(e)}")
            raise Exception(f"Failed to retrieve unread count: {str(e)}")

    @staticmethod
    def get_notification_by_type(user_id: str, notification_type: str, limit: int = 50) -> dict:
        """
        Get notifications filtered by type.

        Args:
            user_id: User ID
            notification_type: Type of notifications to retrieve
            limit: Maximum number to return

        Returns:
            dict: Filtered notifications
        """
        try:
            notifications = (
                Notification.query.filter_by(
                    user_id=user_id, type=notification_type, is_deleted=False
                )
                .order_by(Notification.created_at.desc())
                .limit(limit)
                .all()
            )

            return {
                "notification_type": notification_type,
                "notifications": [notif.to_dict() for notif in notifications],
                "count": len(notifications),
            }

        except Exception as e:
            logger.error(f"Failed to get notifications by type: {str(e)}")
            raise Exception(f"Failed to retrieve notifications: {str(e)}")
