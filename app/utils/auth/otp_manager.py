"""OTP Manager Utility"""

import random
import secrets
from datetime import datetime, timedelta

from app.exceptions import ValidationError


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

    def send_otp_via_email(self, email, otp_code):
        """Send OTP code via email (placeholder)"""
        # Implement actual email sending logic here
        print(f"Sending OTP {otp_code} to email: {email}")