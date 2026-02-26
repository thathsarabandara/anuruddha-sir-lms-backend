"""
Notification Template Service
Handle notification template management and rendering
"""

import json
import logging
import uuid

from flask import current_app

from app import db
from app.exceptions import ConflictError, ResourceNotFoundError, ValidationError
from app.models.notifications.notification_template import NotificationTemplate
from app.services.base_service import BaseService
from app.services.notifications.channels import EmailChannel, InAppChannel, WhatsAppChannel
from app.utils.notification_helpers import (
    NotificationChannelSelector,
    NotificationTemplateRenderer,
    NotificationVariableValidator,
)

logger = logging.getLogger(__name__)


class NotificationTemplateService(BaseService):
    """Service for managing notification templates."""

    @staticmethod
    def get_all_templates(
        notification_type: str = None,
        channel: str = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict:
        """
        Get notification templates with optional filtering.

        Args:
            notification_type: Filter by notification type
            channel: Filter by channel
            limit: Pagination limit
            offset: Pagination offset

        Returns:
            dict: Templates with pagination info
        """
        try:
            query = NotificationTemplate.query.filter_by(is_active=True)

            if notification_type:
                query = query.filter_by(notification_type=notification_type)

            if channel:
                query = query.filter_by(channel=channel)

            total = query.count()
            templates = query.order_by(NotificationTemplate.created_at.desc()).limit(limit).offset(offset).all()

            return {
                "templates": [NotificationTemplateService._template_to_dict(t) for t in templates],
                "total": total,
                "limit": limit,
                "offset": offset,
            }

        except Exception as e:
            logger.error(f"Failed to get templates: {str(e)}")
            raise Exception(f"Failed to retrieve templates: {str(e)}")

    @staticmethod
    def get_template_by_id(template_id: str) -> dict:
        """
        Get template details by ID.

        Args:
            template_id: Template ID

        Returns:
            dict: Template details

        Raises:
            ResourceNotFoundError: If template not found
        """
        try:
            template = NotificationTemplate.query.filter_by(template_id=template_id).first()

            if not template:
                raise ResourceNotFoundError("Template", template_id)

            return NotificationTemplateService._template_to_dict(template)

        except ResourceNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to get template: {str(e)}")
            raise Exception(f"Failed to retrieve template: {str(e)}")

    @staticmethod
    def create_template(
        notification_type: str,
        channel: str,
        subject: str = None,
        template_html: str = None,
        template_text: str = None,
        variables: list = None,
    ) -> dict:
        """
        Create a new notification template.

        Args:
            notification_type: Type of notification
            channel: Delivery channel (email, whatsapp, in_app)
            subject: Email subject
            template_html: HTML template content
            template_text: Plain text template content
            variables: List of variable definitions

        Returns:
            dict: Created template

        Raises:
            ValidationError: If input is invalid
            ConflictError: If template already exists
        """
        try:
            # Validate inputs
            if not notification_type or not channel:
                raise ValidationError("notification_type and channel are required")

            if channel not in ["email", "whatsapp", "in_app"]:
                raise ValidationError("Invalid channel. Must be: email, whatsapp, in_app")

            # Check if template already exists for this type/channel
            existing = NotificationTemplate.query.filter_by(
                notification_type=notification_type,
                channel=channel,
            ).first()

            if existing:
                raise ConflictError(
                    f"Template for {notification_type}/{channel} already exists"
                )

            # Validate variables if provided
            if variables:
                try:
                    if isinstance(variables, str):
                        variables = json.loads(variables)
                    NotificationVariableValidator.validate_against_schema({}, variables)
                except Exception as e:
                    raise ValidationError(f"Invalid variables schema: {str(e)}")

            # Create template
            template = NotificationTemplate(
                template_id=str(uuid.uuid4()),
                notification_type=notification_type,
                channel=channel,
                subject=subject,
                template_html=template_html,
                template_text=template_text,
                variables=variables,
                version=1,
                is_active=True,
            )

            db.session.add(template)
            db.session.commit()

            logger.info(f"Template created: {notification_type}/{channel}")

            return NotificationTemplateService._template_to_dict(template)

        except (ValidationError, ConflictError):
            raise
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to create template: {str(e)}")
            raise Exception(f"Failed to create template: {str(e)}")

    @staticmethod
    def update_template(
        template_id: str,
        subject: str = None,
        template_html: str = None,
        template_text: str = None,
        is_active: bool = None,
    ) -> dict:
        """
        Update an existing template (creates new version).

        Args:
            template_id: Template ID
            subject: New subject
            template_html: New HTML content
            template_text: New plain text content
            is_active: Activate/deactivate template

        Returns:
            dict: Updated template

        Raises:
            ResourceNotFoundError: If template not found
        """
        try:
            template = NotificationTemplate.query.filter_by(template_id=template_id).first()

            if not template:
                raise ResourceNotFoundError("Template", template_id)

            # Update fields
            if subject is not None:
                template.subject = subject
            if template_html is not None:
                template.template_html = template_html
            if template_text is not None:
                template.template_text = template_text
            if is_active is not None:
                template.is_active = is_active

            db.session.commit()

            logger.info(f"Template {template_id} updated")

            return NotificationTemplateService._template_to_dict(template)

        except ResourceNotFoundError:
            raise
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to update template: {str(e)}")
            raise Exception(f"Failed to update template: {str(e)}")

    @staticmethod
    def test_template(template_id: str, variables: dict) -> dict:
        """
        Test template rendering with sample data.

        Args:
            template_id: Template ID
            variables: Sample variables for rendering

        Returns:
            dict: Preview HTML and text

        Raises:
            ResourceNotFoundError: If template not found
            ValidationError: If rendering fails
        """
        try:
            template = NotificationTemplate.query.filter_by(template_id=template_id).first()

            if not template:
                raise ResourceNotFoundError("Template", template_id)

            # Validate variables against schema
            template_vars = template.get_variables()
            is_valid, errors = NotificationVariableValidator.validate_against_schema(
                variables, template_vars
            )

            if not is_valid:
                raise ValidationError(f"Variable validation failed: {', '.join(errors)}")

            # Render templates
            preview_html = None
            preview_text = None

            if template.template_html:
                preview_html = NotificationTemplateRenderer.render_template(
                    template.template_html, variables
                )

            if template.template_text:
                preview_text = NotificationTemplateRenderer.render_template(
                    template.template_text, variables
                )

            return {
                "preview_html": preview_html,
                "preview_text": preview_text,
                "subject": NotificationTemplateRenderer.render_template(template.subject or "", variables),
            }

        except (ResourceNotFoundError, ValidationError):
            raise
        except Exception as e:
            logger.error(f"Failed to test template: {str(e)}")
            raise Exception(f"Template rendering failed: {str(e)}")

    @staticmethod
    def send_notification_from_template(
        template_id: str,
        recipient_user_id: str,
        recipient_email: str = None,
        recipient_phone: str = None,
        variables: dict = None,
        notification_id: str = None,
    ) -> dict:
        """
        Send notification using a template.

        Args:
            template_id: Template ID
            recipient_user_id: Recipient user ID
            recipient_email: Recipient email (for email channel)
            recipient_phone: Recipient phone (for WhatsApp channel)
            variables: Variables for template rendering
            notification_id: Associated notification ID

        Returns:
            dict: Delivery results for all channels
        """
        try:
            template = NotificationTemplate.query.filter_by(template_id=template_id).first()

            if not template:
                raise ResourceNotFoundError("Template", template_id)

            if not template.is_active:
                raise ValidationError("Template is not active")

            variables = variables or {}

            # Render content
            rendered_subject = (
                NotificationTemplateRenderer.render_template(template.subject or "", variables)
                if template.subject
                else None
            )
            rendered_html = (
                NotificationTemplateRenderer.render_template(template.template_html, variables)
                if template.template_html
                else None
            )
            rendered_text = (
                NotificationTemplateRenderer.render_template(template.template_text, variables)
                if template.template_text
                else None
            )

            results = {"channel_results": {}}

            # Send via appropriate channels
            if template.channel == "email" and recipient_email:
                channel = EmailChannel()
                result = channel.send(
                    recipient=recipient_email,
                    subject=rendered_subject,
                    content=rendered_text,
                    html_content=rendered_html,
                    notification_id=notification_id,
                )
                results["channel_results"]["email"] = result

            elif template.channel == "whatsapp" and recipient_phone:
                channel = WhatsAppChannel()
                result = channel.send(
                    recipient=recipient_phone,
                    content=rendered_text or rendered_html,
                    notification_id=notification_id,
                )
                results["channel_results"]["whatsapp"] = result

            elif template.channel == "in_app":
                channel = InAppChannel()
                result = channel.send(
                    recipient=recipient_user_id,
                    content=rendered_text,
                    subject=rendered_subject,
                    notification_id=notification_id,
                    title=rendered_subject,
                    detailed_content=rendered_html,
                )
                results["channel_results"]["in_app"] = result

            return results

        except (ResourceNotFoundError, ValidationError):
            raise
        except Exception as e:
            logger.error(f"Failed to send notification from template: {str(e)}")
            raise Exception(f"Failed to send notification: {str(e)}")

    @staticmethod
    def _template_to_dict(template: NotificationTemplate) -> dict:
        """
        Convert template to dictionary.

        Args:
            template: NotificationTemplate instance

        Returns:
            dict: Template as dictionary
        """
        return {
            "template_id": template.template_id,
            "notification_type": template.notification_type,
            "channel": template.channel,
            "subject": template.subject,
            "template_html": template.template_html,
            "template_text": template.template_text,
            "variables": template.get_variables(),
            "version": template.version,
            "is_active": template.is_active,
            "created_at": template.created_at.isoformat(),
            "updated_at": template.updated_at.isoformat(),
        }
