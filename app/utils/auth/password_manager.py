"""Password Manager Utility"""

import bcrypt

from app.exceptions import ValidationError


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
                return False
            return bcrypt.checkpw(
                plain_password.encode("utf-8"), hashed_password.encode("utf-8")
            )
        except Exception as e:
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
