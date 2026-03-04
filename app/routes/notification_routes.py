"""
Notification Routes
All notification endpoints for users and admins
"""

from flask import Blueprint, request, current_app
from app.exceptions import ValidationError, ResourceNotFoundError, AuthorizationError, ConflictError
from app.middleware.auth_middleware import require_auth, require_role
from app.services.notifications import (
    UserNotificationService,
    NotificationPreferencesService,
    AdminNotificationService,
)
from app.utils.decorators import handle_exceptions, validate_json
from app.utils.helpers import get_page_and_limit, get_offset_from_page
from app.utils.response import error_response, success_response

bp = Blueprint("notifications", __name__, url_prefix="/api/v1/notifications")


# ===================== User Notification Endpoints =====================


@bp.route("", methods=["GET"])
@handle_exceptions
@require_auth
def get_user_notifications():
    """
    Get user notifications with pagination and filtering.

    Query Parameters:
        limit: Items per page (default: 20, max: 100)
        offset: Pagination offset (default: 0)
        filter: Filter type (unread, read, all - default: all)
        sort: Sort order (newest, oldest - default: newest)

    Returns:
        200: List of notifications with pagination info
        401: Unauthorized
    """
    try:
        user_id = request.user_id
        limit = request.args.get("limit", 20, type=int)
        offset = request.args.get("offset", 0, type=int)
        filter_type = request.args.get("filter", "all")
        sort = request.args.get("sort", "newest")

        # Validate pagination
        limit = max(1, min(limit, 100))
        offset = max(0, offset)

        result = UserNotificationService.get_user_notifications(
            user_id=user_id,
            limit=limit,
            offset=offset,
            filter_type=filter_type,
            sort=sort,
        )

        return success_response(
            data={
                "notifications": result["notifications"],
                "pagination": {
                    "limit": limit,
                    "offset": offset,
                    "total": result["total"],
                },
            },
            message="Notifications retrieved successfully",
        )

    except Exception as e:
        return error_response(str(e), 500)


@bp.route("/<notification_id>", methods=["GET"])
@handle_exceptions
@require_auth
def get_notification_detail(notification_id):
    """
    Get detailed information about a notification.

    Path Parameters:
        notification_id: Notification ID

    Returns:
        200: Notification details
        401: Unauthorized
        404: Notification not found
    """
    try:
        user_id = request.user_id
        notification = UserNotificationService.get_notification_detail(notification_id, user_id)

        return success_response(data=notification, message="Notification retrieved successfully")

    except ResourceNotFoundError as e:
        return error_response(e.message, e.status_code)
    except Exception as e:
        return error_response(str(e), 500)


@bp.route("/<notification_id>/read", methods=["PUT"])
@handle_exceptions
@require_auth
def mark_notification_as_read(notification_id):
    """
    Mark a notification as read.

    Path Parameters:
        notification_id: Notification ID

    Returns:
        200: Notification marked as read
        401: Unauthorized
        404: Notification not found
    """
    try:
        user_id = request.user_id
        notification = UserNotificationService.mark_as_read(notification_id, user_id)

        return success_response(
            data=notification, message="Notification marked as read"
        )

    except ResourceNotFoundError as e:
        return error_response(e.message, e.status_code)
    except Exception as e:
        return error_response(str(e), 500)


@bp.route("/read-all", methods=["PUT"])
@handle_exceptions
@require_auth
def mark_all_notifications_as_read():
    """
    Mark all unread notifications as read for current user.

    Returns:
        200: All notifications marked as read
        401: Unauthorized
    """
    try:
        user_id = request.user_id
        result = UserNotificationService.mark_all_as_read(user_id)

        return success_response(
            data=result, message="All notifications marked as read"
        )

    except Exception as e:
        return error_response(str(e), 500)


@bp.route("/<notification_id>", methods=["DELETE"])
@handle_exceptions
@require_auth
def delete_notification(notification_id):
    """
    Delete a notification (soft delete).

    Path Parameters:
        notification_id: Notification ID

    Returns:
        200: Notification deleted
        401: Unauthorized
        404: Notification not found
    """
    try:
        user_id = request.user_id
        result = UserNotificationService.delete_notification(notification_id, user_id)

        return success_response(data=result, message=result.get("message"))

    except ResourceNotFoundError as e:
        return error_response(e.message, e.status_code)
    except Exception as e:
        return error_response(str(e), 500)


@bp.route("/unread-count", methods=["GET"])
@handle_exceptions
@require_auth
def get_unread_count():
    """
    Get count of unread notifications.

    Returns:
        200: Unread notification count and breakdown by type
        401: Unauthorized
    """
    try:
        user_id = request.user_id
        result = UserNotificationService.get_unread_count(user_id)

        return success_response(data=result, message="Unread count retrieved successfully")

    except Exception as e:
        return error_response(str(e), 500)


# ===================== Notification Preferences Endpoints =====================


@bp.route("/preferences", methods=["GET"])
@handle_exceptions
@require_auth
def get_notification_preferences():
    """
    Get notification preferences for current user.

    Returns:
        200: User notification preferences
        401: Unauthorized
    """
    try:
        user_id = request.user_id
        preferences = NotificationPreferencesService.get_preferences(user_id)

        return success_response(data=preferences, message="Preferences retrieved successfully")

    except Exception as e:
        return error_response(str(e), 500)


@bp.route("/preferences", methods=["PUT"])
@handle_exceptions
@require_auth
@validate_json()
def update_notification_preferences():
    """
    Update notification preferences for current user.

    Request Body:
        {
            "channels": {
                "email": {"enabled": bool, "digest": "instant|daily|weekly|never"},
                "sms": {"enabled": bool},
                "in_app": {"enabled": bool}
            },
            "quiet_hours": {
                "start": "HH:MM",
                "end": "HH:MM"
            },
            "notification_types": {
                "notification_type": {
                    "email": bool,
                    "sms": bool,
                    "in_app": bool
                }
            }
        }

    Returns:
        200: Preferences updated successfully
        400: Invalid preferences
        401: Unauthorized
    """
    try:
        user_id = request.user_id
        data = request.get_json()

        preferences = NotificationPreferencesService.update_preferences(user_id, data)

        return success_response(data=preferences, message="Preferences updated successfully")

    except ValidationError as e:
        return error_response(e.message, e.status_code)
    except Exception as e:
        return error_response(str(e), 500)


@bp.route("/unsubscribe", methods=["POST"])
@handle_exceptions
@require_auth
@validate_json()
def unsubscribe_notifications():
    """
    Unsubscribe from notifications.

    Request Body:
        {
            "notification_type": "optional - specific type to unsubscribe",
            "channel": "optional - specific channel to disable"
        }

    Returns:
        200: Unsubscribed successfully
        400: Invalid request
        401: Unauthorized
    """
    try:
        user_id = request.user_id
        data = request.get_json()

        notification_type = data.get("notification_type")
        channel = data.get("channel")

        preferences = NotificationPreferencesService.unsubscribe(
            user_id, notification_type, channel
        )

        return success_response(data=preferences, message="Unsubscribed successfully")

    except Exception as e:
        return error_response(str(e), 500)

# ===================== Admin Bulk Notification Endpoints =====================


@bp.route("/send-bulk", methods=["POST"])
@handle_exceptions
@require_auth
@require_role("admin")
@validate_json()
def send_bulk_notification():
    """
    Send bulk notification to multiple users (admin only).

    Request Body:
        {
            "title": "string (required)",
            "content": "string (required)",
            "channels": ["email", "in_app", ...] (required),
            "recipients": {
                "type": "all|filtered",
                "filters": {
                    "role": "student|teacher|admin",
                    "country": "string"
                }
            },
            "scheduled_for": "ISO8601 (optional)"
        }

    Returns:
        201: Bulk notification created
        400: Invalid input
        401: Unauthorized
        403: Admin access required
    """
    try:
        data = request.get_json()

        # Parse scheduled_for if provided
        scheduled_for = None
        if data.get("scheduled_for"):
            from datetime import datetime

            try:
                scheduled_for = datetime.fromisoformat(data["scheduled_for"])
            except ValueError:
                raise ValidationError("Invalid scheduled_for format. Use ISO8601 format.")

        batch = AdminNotificationService.send_bulk_notification(
            title=data.get("title"),
            content=data.get("content"),
            channels=data.get("channels", []),
            recipients=data.get("recipients", {"type": "all"}),
            scheduled_for=scheduled_for,
            created_by=request.user_id,
        )

        return success_response(data=batch, message="Bulk notification created successfully", status_code=201)

    except ValidationError as e:
        return error_response(e.message, e.status_code)
    except Exception as e:
        return error_response(str(e), 500)


@bp.route("/<batch_id>/status", methods=["GET"])
@handle_exceptions
@require_auth
@require_role("admin")
def get_batch_status(batch_id):
    """
    Get status of a notification batch (admin only).

    Path Parameters:
        batch_id: Batch ID

    Returns:
        200: Batch status and delivery metrics
        401: Unauthorized
        403: Admin access required
        404: Batch not found
    """
    try:
        status = AdminNotificationService.get_batch_status(batch_id)

        return success_response(data=status, message="Batch status retrieved successfully")

    except ResourceNotFoundError as e:
        return error_response(e.message, e.status_code)
    except Exception as e:
        return error_response(str(e), 500)


@bp.route("/batch-history", methods=["GET"])
@handle_exceptions
@require_auth
@require_role("admin")
def get_batch_history():
    """
    Get history of notification batches (admin only).

    Query Parameters:
        limit: Items per page (default: 20, max: 100)
        offset: Pagination offset (default: 0)
        status: Filter by status (scheduled, sending, sent, failed)

    Returns:
        200: Batch history with pagination
        401: Unauthorized
        403: Admin access required
    """
    try:
        limit = request.args.get("limit", 20, type=int)
        offset = request.args.get("offset", 0, type=int)
        status = request.args.get("status")

        limit = max(1, min(limit, 100))
        offset = max(0, offset)

        result = AdminNotificationService.get_batch_history(
            limit=limit, offset=offset, status=status
        )

        return success_response(
            data={
                "batches": result["batches"],
                "pagination": {
                    "limit": limit,
                    "offset": offset,
                    "total": result["total"],
                },
            },
            message="Batch history retrieved successfully",
        )

    except Exception as e:
        return error_response(str(e), 500)


@bp.route("/preview-recipients", methods=["POST"])
@handle_exceptions
@require_auth
@require_role("admin")
@validate_json()
def preview_bulk_recipients():
    """
    Preview recipients for bulk notification (admin only).

    Request Body:
        {
            "recipients": {
                "type": "all|filtered",
                "filters": {...}
            }
        }

    Returns:
        200: Preview of recipients
        400: Invalid input
        401: Unauthorized
        403: Admin access required
    """
    try:
        data = request.get_json()
        recipients = data.get("recipients", {"type": "all"})

        preview = AdminNotificationService.preview_bulk_notification(recipients)

        return success_response(
            data=preview, message="Recipient preview generated successfully"
        )

    except Exception as e:
        return error_response(str(e), 500)
