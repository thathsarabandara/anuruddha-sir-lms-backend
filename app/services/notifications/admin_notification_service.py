"""
Admin Notification Service
Handle bulk notifications and delivery tracking
"""

import logging
import uuid
from datetime import datetime

from app import db
from app.exceptions import ResourceNotFoundError, ValidationError
from app.models.notifications.notification_batch import NotificationBatch
from app.services.health.base_service import BaseService

logger = logging.getLogger(__name__)


class AdminNotificationService(BaseService):
    """Service for admin notification management."""

    @staticmethod
    def send_bulk_notification(
        title: str,
        content: str,
        channels: list,
        recipients: dict,
        scheduled_for: datetime = None,
        created_by: str = None,
    ) -> dict:
        """
        Create and schedule bulk notification.

        Args:
            title: Notification title
            content: Notification content
            channels: List of channels (email, whatsapp, in_app)
            recipients: Recipients dict with 'type' and filters:
                {
                    'type': 'filtered|all',
                    'filters': {...}  # if type is filtered
                }
            send_immediately: Send right away or schedule
            scheduled_for: Schedule time (if not sending immediately)
            created_by: Admin user ID

        Returns:
            dict: Batch information

        Raises:
            ValidationError: If input is invalid
        """
        try:
            # Validate inputs
            if not title or not content:
                raise ValidationError("Title and content are required")

            if not channels or len(channels) == 0:
                raise ValidationError("At least one channel must be selected")

            for channel in channels:
                if channel not in ["email", "whatsapp", "in_app"]:
                    raise ValidationError(f"Invalid channel: {channel}")

            if recipients.get("type") not in ["all", "filtered"]:
                raise ValidationError("Recipients type must be 'all' or 'filtered'")

            # Get recipient count
            recipient_count = AdminNotificationService._calculate_recipient_count(recipients)

            if recipient_count == 0:
                raise ValidationError("No matching recipients found")

            # Create batch record
            batch = NotificationBatch(
                batch_id=str(uuid.uuid4()),
                title=title,
                content=content,
                created_by=created_by,
                total_recipients=recipient_count,
                sent_count=0,
                failed_count=0,
                scheduled_for=scheduled_for,
                status="scheduled",
            )

            db.session.add(batch)
            db.session.commit()

            logger.info(
                f"Bulk notification batch created: {batch.batch_id} "
                f"({recipient_count} recipients, channels: {channels})"
            )

            return {
                "batch_id": batch.batch_id,
                "title": title,
                "recipient_count": recipient_count,
                "channels": channels,
                "status": "scheduled",
                "scheduled_for": scheduled_for,
                "created_at": batch.created_at.isoformat(),
            }

        except ValidationError:
            raise
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to create bulk notification: {str(e)}")
            raise Exception(f"Failed to create notification: {str(e)}")

    @staticmethod
    def get_batch_status(batch_id: str) -> dict:
        """
        Get status of a notification batch.

        Args:
            batch_id: Batch ID

        Returns:
            dict: Batch status and delivery metrics

        Raises:
            ResourceNotFoundError: If batch not found
        """
        try:
            batch = NotificationBatch.query.filter_by(batch_id=batch_id).first()

            if not batch:
                raise ResourceNotFoundError("Batch", batch_id)

            # Calculate delivery rate
            delivery_rate = 0
            if batch.total_recipients > 0:
                delivery_rate = int((batch.sent_count / batch.total_recipients) * 100)

            return {
                "batch_id": batch.batch_id,
                "title": batch.title,
                "total_recipients": batch.total_recipients,
                "sent": batch.sent_count,
                "failed": batch.failed_count,
                "pending": batch.total_recipients - batch.sent_count - batch.failed_count,
                "delivery_rate": delivery_rate,
                "status": batch.status,
                "scheduled_for": batch.scheduled_for.isoformat() if batch.scheduled_for else None,
                "sent_at": batch.sent_at.isoformat() if batch.sent_at else None,
                "created_at": batch.created_at.isoformat(),
            }

        except ResourceNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to get batch status: {str(e)}")
            raise Exception(f"Failed to retrieve batch status: {str(e)}")

    @staticmethod
    def get_batch_history(
        limit: int = 50,
        offset: int = 0,
        status: str = None,
    ) -> dict:
        """
        Get history of notification batches.

        Args:
            limit: Pagination limit
            offset: Pagination offset
            status: Filter by status (scheduled, sending, sent, failed)

        Returns:
            dict: Batch history with pagination
        """
        try:
            query = NotificationBatch.query

            if status:
                if status not in ["scheduled", "sending", "sent", "failed"]:
                    raise ValidationError("Invalid status filter")
                query = query.filter_by(status=status)

            total = query.count()
            batches = (
                query.order_by(NotificationBatch.created_at.desc())
                .limit(limit)
                .offset(offset)
                .all()
            )

            return {
                "batches": [
                    {
                        "batch_id": b.batch_id,
                        "title": b.title,
                        "total_recipients": b.total_recipients,
                        "sent": b.sent_count,
                        "failed": b.failed_count,
                        "status": b.status,
                        "created_at": b.created_at.isoformat(),
                    }
                    for b in batches
                ],
                "total": total,
                "limit": limit,
                "offset": offset,
            }

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Failed to get batch history: {str(e)}")
            raise Exception(f"Failed to retrieve batch history: {str(e)}")

    @staticmethod
    def update_batch_status(
        batch_id: str, status: str, sent_count: int = None, failed_count: int = None
    ) -> dict:
        """
        Update batch delivery status.

        Args:
            batch_id: Batch ID
            status: New status
            sent_count: Updated sent count
            failed_count: Updated failed count

        Returns:
            dict: Updated batch

        Raises:
            ResourceNotFoundError: If batch not found
            ValidationError: If status invalid
        """
        try:
            batch = NotificationBatch.query.filter_by(batch_id=batch_id).first()

            if not batch:
                raise ResourceNotFoundError("Batch", batch_id)

            if status not in ["scheduled", "sending", "sent", "failed"]:
                raise ValidationError("Invalid status")

            batch.status = status

            if sent_count is not None:
                batch.sent_count = sent_count

            if failed_count is not None:
                batch.failed_count = failed_count

            if status == "sent":
                batch.sent_at = datetime.utcnow()

            db.session.commit()

            logger.info(f"Batch {batch_id} status updated to {status}")

            return AdminNotificationService.get_batch_status(batch_id)

        except (ResourceNotFoundError, ValidationError):
            raise
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to update batch status: {str(e)}")
            raise Exception(f"Failed to update batch: {str(e)}")

    @staticmethod
    def _calculate_recipient_count(recipients: dict) -> int:
        """
        Calculate number of recipients based on filters.

        Args:
            recipients: Recipients filter dict

        Returns:
            int: Recipient count
        """
        try:
            if recipients.get("type") == "all":
                # Count all users (simplified - adjust based on your User model)
                from app.models.auth import User

                return User.query.filter_by(is_active=True).count()

            elif recipients.get("type") == "filtered":
                filters = recipients.get("filters", {})

                # Build query based on filters
                from app.models.auth import User

                query = User.query.filter_by(is_active=True)

                if "role" in filters:
                    query = query.filter_by(role=filters["role"])

                if "country" in filters:
                    # Adjust based on your User model
                    pass

                return query.count()

            return 0

        except Exception as e:
            logger.error(f"Failed to calculate recipient count: {str(e)}")
            return 0

    @staticmethod
    def preview_bulk_notification(recipients: dict) -> dict:
        """
        Preview bulk notification recipients.

        Args:
            recipients: Recipients filter dict

        Returns:
            dict: Preview information and sample recipients
        """
        try:
            count = AdminNotificationService._calculate_recipient_count(recipients)

            # Get sample recipients (first 5)
            if recipients.get("type") == "all":
                from app.models.auth import User

                sample = User.query.filter_by(is_active=True).limit(5).all()

            elif recipients.get("type") == "filtered":
                from app.models.auth import User

                query = User.query.filter_by(is_active=True)
                filters = recipients.get("filters", {})

                if "role" in filters:
                    query = query.filter_by(role=filters["role"])

                sample = query.limit(5).all()
            else:
                sample = []

            return {
                "total_recipients": count,
                "sample_recipients": [
                    {
                        "user_id": u.user_id,
                        "email": getattr(u, "email", None),
                        "first_name": getattr(u, "first_name", None),
                    }
                    for u in sample
                ],
            }

        except Exception as e:
            logger.error(f"Failed to preview recipients: {str(e)}")
            raise Exception(f"Failed to preview recipients: {str(e)}")
