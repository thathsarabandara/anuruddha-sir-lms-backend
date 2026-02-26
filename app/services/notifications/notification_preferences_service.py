"""
Notification Preferences Service
Handle user notification preferences and settings
"""

import logging

from app import db
from app.exceptions import ResourceNotFoundError, ValidationError
from app.models.notifications.notification_preferences import NotificationPreferences
from app.models.notifications.notification_type_preferences import NotificationTypePreferences
from app.services.base_service import BaseService

logger = logging.getLogger(__name__)


class NotificationPreferencesService(BaseService):
    """Service for managing notification preferences."""

    @staticmethod
    def get_preferences(user_id: str) -> dict:
        """
        Get all notification preferences for user.

        Args:
            user_id: User ID

        Returns:
            dict: User preferences including channels and type-specific settings
        """
        try:
            # Get or create main preferences
            prefs = NotificationPreferences.query.filter_by(user_id=user_id).first()

            if not prefs:
                # Create default preferences
                prefs = NotificationPreferencesService._create_default_preferences(user_id)

            # Get type-specific preferences
            type_prefs = NotificationTypePreferences.query.filter_by(user_id=user_id).all()

            return {
                "channels": {
                    "email": {
                        "enabled": prefs.email_enabled,
                        "digest": prefs.email_digest,
                    },
                    "whatsapp": {
                        "enabled": False,  # WhatsApp disabled by default for privacy
                    },
                    "sms": {
                        "enabled": prefs.sms_enabled,
                    },
                    "in_app": {
                        "enabled": prefs.in_app_enabled,
                    },
                },
                "quiet_hours": {
                    "start": prefs.quiet_hours_start.isoformat() if prefs.quiet_hours_start else None,
                    "end": prefs.quiet_hours_end.isoformat() if prefs.quiet_hours_end else None,
                },
                "notification_types": {
                    type_pref.notification_type: {
                        "email": type_pref.email,
                        "sms": type_pref.sms,
                        "in_app": type_pref.in_app,
                    }
                    for type_pref in type_prefs
                },
            }

        except Exception as e:
            logger.error(f"Failed to get preferences: {str(e)}")
            raise Exception(f"Failed to retrieve preferences: {str(e)}")

    @staticmethod
    def update_preferences(user_id: str, preferences_data: dict) -> dict:
        """
        Update notification preferences for user.

        Args:
            user_id: User ID
            preferences_data: Preferences to update with keys:
                - channels: email, sms, in_app, whatsapp settings
                - quiet_hours: start and end times
                - notification_types: type-specific channel preferences

        Returns:
            dict: Updated preferences

        Raises:
            ValidationError: If preferences are invalid
        """
        try:
            # Get or create preferences
            prefs = NotificationPreferences.query.filter_by(user_id=user_id).first()
            if not prefs:
                prefs = NotificationPreferencesService._create_default_preferences(user_id)

            # Update channel preferences
            channels = preferences_data.get("channels", {})
            if "email" in channels:
                email_prefs = channels["email"]
                if "enabled" in email_prefs:
                    prefs.email_enabled = email_prefs["enabled"]
                if "digest" in email_prefs:
                    if email_prefs["digest"] not in ["instant", "daily", "weekly", "never"]:
                        raise ValidationError("Invalid email digest option")
                    prefs.email_digest = email_prefs["digest"]

            if "sms" in channels:
                if "enabled" in channels["sms"]:
                    prefs.sms_enabled = channels["sms"]["enabled"]

            if "in_app" in channels:
                if "enabled" in channels["in_app"]:
                    prefs.in_app_enabled = channels["in_app"]["enabled"]

            # Update quiet hours
            quiet_hours = preferences_data.get("quiet_hours", {})
            if "start" in quiet_hours:
                prefs.quiet_hours_start = quiet_hours["start"]
            if "end" in quiet_hours:
                prefs.quiet_hours_end = quiet_hours["end"]

            db.session.commit()

            # Update type-specific preferences
            notification_types = preferences_data.get("notification_types", {})
            for notif_type, type_prefs in notification_types.items():
                type_pref = NotificationTypePreferences.query.filter_by(
                    user_id=user_id, notification_type=notif_type
                ).first()

                if not type_pref:
                    type_pref = NotificationTypePreferences(
                        user_id=user_id,
                        notification_type=notif_type,
                    )
                    db.session.add(type_pref)

                if "email" in type_prefs:
                    type_pref.email = type_prefs["email"]
                if "sms" in type_prefs:
                    type_pref.sms = type_prefs["sms"]
                if "in_app" in type_prefs:
                    type_pref.in_app = type_prefs["in_app"]

            db.session.commit()
            logger.info(f"Updated preferences for user {user_id}")

            return NotificationPreferencesService.get_preferences(user_id)

        except ValidationError:
            raise
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to update preferences: {str(e)}")
            raise Exception(f"Failed to update preferences: {str(e)}")

    @staticmethod
    def unsubscribe(user_id: str, notification_type: str = None, channel: str = None) -> dict:
        """
        Unsubscribe from notifications.

        Args:
            user_id: User ID
            notification_type: Specific type to unsubscribe from (optional)
            channel: Specific channel to disable (optional)

        Returns:
            dict: Updated preferences
        """
        try:
            if notification_type and channel:
                # Unsubscribe from specific type/channel
                type_pref = NotificationTypePreferences.query.filter_by(
                    user_id=user_id, notification_type=notification_type
                ).first()

                if type_pref:
                    if channel == "email":
                        type_pref.email = False
                    elif channel == "sms":
                        type_pref.sms = False
                    elif channel == "in_app":
                        type_pref.in_app = False

                    db.session.commit()
                    logger.info(f"Unsubscribed user {user_id} from {notification_type}/{channel}")

            elif channel:
                # Disable entire channel
                prefs = NotificationPreferences.query.filter_by(user_id=user_id).first()
                if prefs:
                    if channel == "email":
                        prefs.email_enabled = False
                    elif channel == "sms":
                        prefs.sms_enabled = False
                    elif channel == "in_app":
                        prefs.in_app_enabled = False

                    db.session.commit()
                    logger.info(f"Disabled {channel} for user {user_id}")

            return NotificationPreferencesService.get_preferences(user_id)

        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to unsubscribe: {str(e)}")
            raise Exception(f"Failed to unsubscribe: {str(e)}")

    @staticmethod
    def _create_default_preferences(user_id: str) -> NotificationPreferences:
        """
        Create default notification preferences for new user.

        Args:
            user_id: User ID

        Returns:
            NotificationPreferences: Newly created preferences
        """
        import uuid

        prefs = NotificationPreferences(
            preference_id=str(uuid.uuid4()),
            user_id=user_id,
            email_enabled=True,
            sms_enabled=False,
            in_app_enabled=True,
            email_digest="daily",
        )

        db.session.add(prefs)
        db.session.commit()

        # Create default type preferences for common notification types
        default_types = [
            "otp_verification",
            "course_enrolled",
            "quiz_result",
            "promotional",
            "payment_confirmed",
        ]

        for notif_type in default_types:
            type_pref = NotificationTypePreferences(
                type_pref_id=str(uuid.uuid4()),
                user_id=user_id,
                notification_type=notif_type,
                email=True,
                sms=False,
                in_app=True,
            )
            db.session.add(type_pref)

        db.session.commit()

        return prefs
