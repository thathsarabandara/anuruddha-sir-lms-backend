"""
Token Manager Utility
Handles JWT token generation, verification, and management
"""

import secrets
from datetime import datetime, timedelta

import jwt
from flask import current_app, request

from app.exceptions import AuthenticationError


class TokenManager:
    """Manages JWT token creation, verification, and validation"""

    @staticmethod
    def generate_access_token(user_id, email, username, role, store_in_db=True):
        """Generate a JWT access token and optionally store it in database"""
        try:
            payload = {
                "user_id": user_id,
                "email": email,
                "username": username,
                "role": role,
                "iat": datetime.utcnow(),
                "exp": datetime.utcnow()+timedelta(days=2)
                + current_app.config.get("JWT_ACCESS_TOKEN_EXPIRES", timedelta(minutes=30)),
            }

            secret_key = current_app.config.get("SECRET_KEY", "your-secret-key")
            algorithm = current_app.config.get("JWT_ALGORITHM", "HS256")

            token = jwt.encode(payload, secret_key, algorithm=algorithm)
            
            # Store token in database if requested
            if store_in_db:
                from app import db
                from app.models.auth.access_token import AccessToken
                
                access_token_record = AccessToken(
                    user_id=user_id,
                    token=token,
                    expires_at=payload["exp"],
                    ip_address=request.remote_addr if request else None,
                    user_agent=request.headers.get("User-Agent") if request else None,
                )
                db.session.add(access_token_record)
                db.session.commit()
            
            return token
        except Exception as e:
            raise AuthenticationError(f"Failed to generate access token: {str(e)}")

    @staticmethod
    def generate_refresh_token(user_id, email, username, store_in_db=True):
        """Generate a JWT refresh token and optionally store it in database"""
        try:
            payload = {
                "user_id": user_id,
                "email": email,
                "username": username,
                "token_type": "refresh",
                "iat": datetime.utcnow(),
                "exp": datetime.utcnow()+ timedelta(days=20)
                + current_app.config.get("JWT_REFRESH_TOKEN_EXPIRES", timedelta(days=7)),
            }

            secret_key = current_app.config.get("SECRET_KEY", "your-secret-key")
            algorithm = current_app.config.get("JWT_ALGORITHM", "HS256")

            token = jwt.encode(payload, secret_key, algorithm=algorithm)
            
            # Store token in database if requested
            if store_in_db:
                from app import db
                from app.models.auth.refresh_token import RefreshToken
                
                refresh_token_record = RefreshToken(
                    user_id=user_id,
                    token=token,
                    expires_at=payload["exp"],
                    ip_address=request.remote_addr if request else None,
                    user_agent=request.headers.get("User-Agent") if request else None,
                )
                db.session.add(refresh_token_record)
                db.session.commit()
            
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
            return None  # Return None for expired tokens instead of raising
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
            if payload:
                return datetime.fromtimestamp(payload["exp"])
            return None
        except Exception:
            return None

    @staticmethod
    def is_refresh_token_valid(token):
        """Check if refresh token exists in DB and is valid (not revoked or expired)"""
        try:
            from app.models.auth.refresh_token import RefreshToken
            
            refresh_token_record = RefreshToken.query.filter_by(token=token).first()
            if not refresh_token_record:
                return False
            
            return refresh_token_record.is_valid()
        except Exception:
            return False
