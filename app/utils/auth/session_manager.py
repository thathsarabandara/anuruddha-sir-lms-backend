"""Session Manager Utility - Handle Redis session management"""

import json
import logging
from datetime import timedelta, datetime

import redis
from flask import current_app

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages user sessions in Redis"""

    @staticmethod
    def get_redis_client():
        """Get Redis client instance"""
        try:
            redis_url = current_app.config.get("REDIS_URL", "redis://localhost:6379/0")
            client = redis.from_url(redis_url, decode_responses=True)
            client.ping()
            return client
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            raise

    @staticmethod
    def create_session(user_id, email, username, role, access_token, refresh_token, ttl_minutes=30):
        """Create a user session in Redis"""
        try:
            redis_client = SessionManager.get_redis_client()

            session_data = {
                "user_id": user_id,
                "email": email,
                "username": username,
                "role": role,
                "access_token": access_token,
                "refresh_token": refresh_token,
                "created_at": str(datetime.utcnow()),
            }

            session_key = f"session:{user_id}:{access_token[-16:]}"
            ttl = timedelta(minutes=ttl_minutes)
            redis_client.setex(
                session_key, int(ttl.total_seconds()), json.dumps(session_data)
            )

            refresh_key = f"refresh_session:{refresh_token[-16:]}"
            refresh_ttl = timedelta(days=7)
            redis_client.setex(refresh_key, int(refresh_ttl.total_seconds()), user_id)

            logger.info(f"Session created for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to create session: {str(e)}")
            return False

    @staticmethod
    def get_session(user_id, token_suffix):
        """Retrieve session from Redis"""
        try:
            redis_client = SessionManager.get_redis_client()
            session_key = f"session:{user_id}:{token_suffix}"
            session_data = redis_client.get(session_key)

            if session_data:
                return json.loads(session_data)
            return None
        except Exception as e:
            logger.error(f"Failed to retrieve session: {str(e)}")
            return None

    @staticmethod
    def destroy_session(user_id, token_suffix):
        """Destroy a user session"""
        try:
            redis_client = SessionManager.get_redis_client()
            session_key = f"session:{user_id}:{token_suffix}"
            redis_client.delete(session_key)
            logger.info(f"Session destroyed for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to destroy session: {str(e)}")
            return False

    @staticmethod
    def store_otp(verification_token, otp_data, ttl_hours=24):
        """Store OTP data in Redis"""
        try:
            redis_client = SessionManager.get_redis_client()
            key = f"otp_token:{verification_token}"
            ttl = timedelta(hours=ttl_hours)

            redis_client.setex(key, int(ttl.total_seconds()), json.dumps(otp_data))
            logger.info(f"OTP stored for token {verification_token[:16]}...")
            return True
        except Exception as e:
            logger.error(f"Failed to store OTP: {str(e)}")
            return False

    @staticmethod
    def get_otp(verification_token):
        """Retrieve OTP data from Redis"""
        try:
            redis_client = SessionManager.get_redis_client()
            key = f"otp_token:{verification_token}"
            otp_data = redis_client.get(key)

            if otp_data:
                return json.loads(otp_data)
            return None
        except Exception as e:
            logger.error(f"Failed to retrieve OTP: {str(e)}")
            return None

    @staticmethod
    def delete_otp(verification_token):
        """Delete OTP from Redis"""
        try:
            redis_client = SessionManager.get_redis_client()
            key = f"otp_token:{verification_token}"
            redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Failed to delete OTP: {str(e)}")
            return False

    @staticmethod
    def track_login_attempt(email, ip_address):
        """Track login attempt for rate limiting"""
        try:
            redis_client = SessionManager.get_redis_client()
            key = f"login_attempts:{email}"
            current_attempts = int(redis_client.get(key) or 0)

            redis_client.setex(key, 300, current_attempts + 1)
            return True
        except Exception as e:
            logger.error(f"Failed to track login attempt: {str(e)}")
            return False

    @staticmethod
    def get_login_attempts(email):
        """Get login attempts for email"""
        try:
            redis_client = SessionManager.get_redis_client()
            key = f"login_attempts:{email}"
            attempts = redis_client.get(key)
            return int(attempts) if attempts else 0
        except Exception as e:
            logger.error(f"Failed to get login attempts: {str(e)}")
            return 0

    @staticmethod
    def clear_login_attempts(email):
        """Clear login attempts for email"""
        try:
            redis_client = SessionManager.get_redis_client()
            key = f"login_attempts:{email}"
            redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Failed to clear login attempts: {str(e)}")
            return False
