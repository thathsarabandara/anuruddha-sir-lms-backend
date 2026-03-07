"""Password Manager Utility"""

import bcrypt
import logging

from app.exceptions import ValidationError

logger = logging.getLogger(__name__)


class PasswordManager:
    """Manages password hashing and verification"""

    SALT_ROUNDS = 12

    @staticmethod
    def hash_password(password):
        """Hash password using bcrypt"""
        try:
            if not password or not isinstance(password, str):
                raise ValidationError("Password must be a non-empty string")
            salt = bcrypt.gensalt(rounds=PasswordManager.SALT_ROUNDS)
            hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
            return hashed.decode("utf-8")
        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(f"Failed to hash password: {str(e)}")

    @staticmethod
    def verify_password(plain_password, hashed_password):
        """Verify plain password against hashed password"""
        try:
            if not plain_password or not hashed_password:
                logger.debug(f"Password verification failed: empty password or hash")
                return False
            
            # Ensure hashed_password is bytes for bcrypt.checkpw()
            if isinstance(hashed_password, str):
                hashed_password_bytes = hashed_password.encode("utf-8")
            else:
                hashed_password_bytes = hashed_password
            
            plain_password_bytes = plain_password.encode("utf-8")
            result = bcrypt.checkpw(plain_password_bytes, hashed_password_bytes)
            logger.debug(f"Password verification: {result}")
            return result
        except Exception as e:
            logger.error(f"Password verification error: {str(e)}", exc_info=True)
            raise ValidationError(f"Password verification failed: {str(e)}")

    @staticmethod
    def validate_password_strength(password, min_length=8):
        """Validate password strength requirements"""
        if not password or not isinstance(password, str):
            raise ValidationError("Password must be a non-empty string")

        if len(password) < min_length:
            raise ValidationError(f"Password must be at least {min_length} characters long")

        if len(password) > 128:
            raise ValidationError("Password must not exceed 128 characters")

        if not any(char.isupper() for char in password):
            raise ValidationError("Password must contain at least one uppercase letter")

        if not any(char.islower() for char in password):
            raise ValidationError("Password must contain at least one lowercase letter")

        if not any(char.isdigit() for char in password):
            raise ValidationError("Password must contain at least one digit")

        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(char in special_chars for char in password):
            raise ValidationError("Password must contain at least one special character")

        return password
