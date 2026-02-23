"""
Token Manager Utility
Handles JWT token generation, verification, and management
"""

import secrets
from datetime import datetime, timedelta

import jwt
from flask import current_app

from app.exceptions import AuthenticationError


class TokenManager:
    """Manages JWT token creation, verification, and validation"""

    @staticmethod
    def generate_access_token(user_id, email, username, role):
        """Generate a JWT access token"""
        try:
            payload = {
                "user_id": user_id,
                "email": email,
                "username": username,
                "role": role,
                "iat": datetime.utcnow(),
                "exp": datetime.utcnow()
                + current_app.config.get("JWT_ACCESS_TOKEN_EXPIRES", timedelta(minutes=30)),
            }

            secret_key = current_app.config.get("SECRET_KEY", "your-secret-key")
            algorithm = current_app.config.get("JWT_ALGORITHM", "HS256")

            token = jwt.encode(payload, secret_key, algorithm=algorithm)
            return token
        except Exception as e:
            raise AuthenticationError(f"Failed to generate access token: {str(e)}")

    @staticmethod
    def generate_refresh_token(user_id, email, username):
        """Generate a JWT refresh token"""
        try:
            payload = {
                "user_id": user_id,
                "email": email,
                "username": username,
                "token_type": "refresh",
                "iat": datetime.utcnow(),
                "exp": datetime.utcnow()
                + current_app.config.get("JWT_REFRESH_TOKEN_EXPIRES", timedelta(days=7)),
            }

            secret_key = current_app.config.get("SECRET_KEY", "your-secret-key")
            algorithm = current_app.config.get("JWT_ALGORITHM", "HS256")

            token = jwt.encode(payload, secret_key, algorithm=algorithm)
            return token
        except Exception as e:
            raise AuthenticationError(f"Failed to generate refresh token: {str(e)}")

    @staticmethod
    def verify_token(token):
        """Verify and decode JWT token"""
        try:
            secret_key = current_app.config.get("SECRET_KEY", "your-secret-key")
            algorithm = current_app.config.get("JWT_ALGORITHM", "HS256")

            payload = jwt.decode(token, secret_key, algorithms=[algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token has expired")
        except jwt.InvalidTokenError:
            raise AuthenticationError("Invalid token")
        except Exception as e:
            raise AuthenticationError(f"Token verification failed: {str(e)}")

    @staticmethod
    def decode_token_unsafe(token):
        """Decode token without verifying signature"""
        try:
            payload = jwt.decode(token, options={"verify_signature": False})
            return payload
        except Exception as e:
            raise AuthenticationError(f"Failed to decode token: {str(e)}")

    @staticmethod
    def get_token_expiry_time(token):
        """Get token expiry time"""
        try:
            payload = TokenManager.verify_token(token)
            return datetime.fromtimestamp(payload["exp"])
        except Exception:
            return None
