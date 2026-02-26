"""
Notification Helper Utilities
Template rendering, variable validation, and common functions
"""

import json
import logging
import re
from jinja2 import Template, TemplateError

logger = logging.getLogger(__name__)


class NotificationTemplateRenderer:
    """Handles template rendering with variable substitution."""

    @staticmethod
    def render_template(template_content: str, variables: dict) -> str:
        """
        Render template with variables using Jinja2.

        Args:
            template_content: Template string with Jinja2 syntax
            variables: Dictionary of variables to substitute

        Returns:
            str: Rendered template content

        Raises:
            Exception: If template rendering fails
        """
        if not template_content:
            return ""

        try:
            # Validate variables first
            NotificationTemplateRenderer.validate_variables(variables)

            # Render using Jinja2
            template = Template(template_content)
            rendered = template.render(**variables)

            return rendered
        except TemplateError as e:
            logger.error(f"Template rendering error: {str(e)}")
            raise Exception(f"Failed to render template: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected template error: {str(e)}")
            raise Exception(f"Template rendering failed: {str(e)}")

    @staticmethod
    def validate_variables(variables: dict) -> bool:
        """
        Validate variables dictionary structure.

        Args:
            variables: Variables to validate

        Returns:
            bool: Is valid

        Raises:
            Exception: If validation fails
        """
        if not isinstance(variables, dict):
            raise Exception("Variables must be a dictionary")

        for key, value in variables.items():
            # Check key format (alphanumeric and underscore only)
            if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", key):
                raise Exception(f"Invalid variable name: {key}")

            # Check for suspicious values
            if isinstance(value, str) and len(value) > 10000:
                logger.warning(f"Variable {key} exceeds 10KB limit")

        return True

    @staticmethod
    def sanitize_for_html(text: str) -> str:
        """
        Sanitize text for safe HTML embedding.

        Args:
            text: Text to sanitize

        Returns:
            str: Sanitized text
        """
        if not isinstance(text, str):
            return ""

        replacements = {
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#x27;",
        }

        for char, escape in replacements.items():
            text = text.replace(char, escape)

        return text

    @staticmethod
    def extract_variables_from_template(template_content: str) -> list:
        """
        Extract variable names from template.

        Args:
            template_content: Template string

        Returns:
            list: List of variable names found in template
        """
        if not template_content:
            return []

        # Simple regex to find {{ variable_name }} patterns
        pattern = r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}"
        variables = re.findall(pattern, template_content)

        # Remove duplicates while preserving order
        seen = set()
        result = []
        for var in variables:
            if var not in seen:
                result.append(var)
                seen.add(var)

        return result


class NotificationVariableValidator:
    """Validates variables against template schema."""

    @staticmethod
    def validate_against_schema(variables: dict, schema: list) -> tuple:
        """
        Validate variables against template schema.

        Args:
            variables: Variables to validate
            schema: Schema list from template (list of {name, type, required})

        Returns:
            tuple: (is_valid, errors_list)
        """
        errors = []

        if not schema:
            return True, []

        # Parse schema if it's a JSON string
        if isinstance(schema, str):
            try:
                schema = json.loads(schema)
            except Exception:
                return False, ["Invalid schema format"]

        # Check required variables
        for field in schema:
            field_name = field.get("name")
            field_type = field.get("type", "string")
            is_required = field.get("required", False)

            if is_required and field_name not in variables:
                errors.append(f"Required variable '{field_name}' is missing")
                continue

            if field_name in variables:
                # Validate type
                is_valid_type = NotificationVariableValidator._validate_type(
                    variables[field_name], field_type
                )
                if not is_valid_type:
                    errors.append(f"Variable '{field_name}' has invalid type. Expected: {field_type}")

        # Check for unknown variables
        schema_names = {field.get("name") for field in schema}
        for var_name in variables.keys():
            if var_name not in schema_names:
                logger.warning(f"Variable '{var_name}' not defined in schema")

        return len(errors) == 0, errors

    @staticmethod
    def _validate_type(value, expected_type: str) -> bool:
        """
        Validate value against expected type.

        Args:
            value: Value to validate
            expected_type: Expected type string

        Returns:
            bool: Is valid type
        """
        if expected_type == "string":
            return isinstance(value, str)
        elif expected_type == "integer":
            return isinstance(value, int) and not isinstance(value, bool)
        elif expected_type == "float":
            return isinstance(value, (int, float)) and not isinstance(value, bool)
        elif expected_type == "boolean":
            return isinstance(value, bool)
        elif expected_type == "array":
            return isinstance(value, list)
        elif expected_type == "object":
            return isinstance(value, dict)
        else:
            # Allow any type for unknown types
            return True


class NotificationChannelSelector:
    """Selects appropriate channels based on notification type and preferences."""

    PRIORITY_CHANNELS = {
        "otp_verification": ["whatsapp", "email"],
        "account_locked": ["whatsapp", "email"],
        "account_banned": ["whatsapp", "email"],
        "login_attempt_failed": ["whatsapp", "email"],
        "login_success": ["in_app", "email"],
        "course_enrolled": ["in_app", "email"],
        "quiz_result": ["in_app", "email"],
        "payment_confirmed": ["email", "in_app"],
        "certificate_generated": ["email", "in_app"],
        "promotional": ["email", "in_app"],
    }

    @staticmethod
    def get_channels_for_type(notification_type: str, user_preferences: dict = None) -> list:
        """
        Get recommended channels for notification type.

        Args:
            notification_type: Type of notification
            user_preferences: User notification preferences

        Returns:
            list: List of channel names in priority order
        """
        # Get priority channels for this type
        priority_channels = NotificationChannelSelector.PRIORITY_CHANNELS.get(
            notification_type, ["in_app", "email"]
        )

        # If no user preferences, return default
        if not user_preferences:
            return priority_channels

        # Filter based on user preferences
        available_channels = []

        for channel in priority_channels:
            if channel == "email" and user_preferences.get("email_enabled", True):
                available_channels.append(channel)
            elif channel == "whatsapp" and user_preferences.get("whatsapp_enabled", False):
                available_channels.append(channel)
            elif channel == "in_app" and user_preferences.get("in_app_enabled", True):
                available_channels.append(channel)

        # Fallback to at least in-app if nothing available
        if not available_channels:
            available_channels = ["in_app"]

        return available_channels
