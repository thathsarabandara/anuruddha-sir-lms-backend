"""OTP Manager Utility"""

import logging
import os
import random
import secrets
from datetime import datetime, timedelta

from app.exceptions import ValidationError
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

logger = logging.getLogger(__name__)


class OTPManager:
    """Manages OTP generation, storage, and verification"""

    @staticmethod
    def generate_otp_code(length=6):
        """Generate a random OTP code"""
        return "".join(str(random.randint(0, 9)) for _ in range(length))

    @staticmethod
    def generate_verification_token(length=32):
        """Generate a cryptographically secure verification token"""
        return secrets.token_urlsafe(length)

    @staticmethod
    def generate_reset_token(length=32):
        """Generate a password reset token"""
        return secrets.token_urlsafe(length)

    @staticmethod
    def validate_otp_code(otp_code):
        """Validate OTP code format"""
        if not otp_code or not isinstance(otp_code, str):
            raise ValidationError("OTP must be a string")
        if not otp_code.isdigit():
            raise ValidationError("OTP must contain only digits")
        if len(otp_code) != 6:
            raise ValidationError("OTP must be 6 digits long")
        return otp_code

    @staticmethod
    def check_otp_expiry(expires_at):
        """Check if OTP has expired"""
        return datetime.utcnow() > expires_at

    @staticmethod
    def get_otp_expiry_time(minutes=5):
        """Get OTP expiry time (default: 5 minutes)"""
        return datetime.utcnow() + timedelta(minutes=minutes)

    @staticmethod
    def get_reset_token_expiry_time(hours=1):
        """Get password reset token expiry time (default: 1 hour)"""
        return datetime.utcnow() + timedelta(hours=hours)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _get_jinja_env():
        """
        Get Jinja2 environment configured for loading templates.

        Returns:
            jinja2.Environment instance
        """
        from flask import current_app

        template_dir = os.path.join(current_app.root_path, 'templates')
        return Environment(loader=FileSystemLoader(template_dir))

    @staticmethod
    def _load_template_file(template_path: str) -> str:
        """
        Load a template file from the file system.

        Args:
            template_path: Relative path to template file (e.g., 'notifications/email/otp_verification.html')

        Returns:
            Template file content as string, or None if not found
        """
        try:
            env = OTPManager._get_jinja_env()
            template = env.get_template(template_path)
            return template.module.__loader__.get_source(env, template_path)[0]
        except TemplateNotFound:
            logger.warning("Template file not found: %s", template_path)
            return None
        except Exception as exc:
            logger.error("Failed to load template file '%s': %s", template_path, exc)
            return None

    @staticmethod
    def _render_template(template_content: str, variables: dict) -> str:
        """
        Render a Jinja2 template string with the provided variables.

        Args:
            template_content: Template content as string
            variables: Dictionary of variables for template rendering

        Returns:
            Rendered template string
        """
        try:
            env = OTPManager._get_jinja_env()
            template = env.from_string(template_content)
            return template.render(**variables)
        except Exception as exc:
            logger.error("Failed to render template: %s", exc)
            return template_content