"""
Health Check Service
Contains business logic for health checks
"""

import os
from datetime import datetime

from app import db
from app.services.base_service import BaseService


class HealthCheckService(BaseService):
    """Service for health check operations"""

    @staticmethod
    def get_health_status():
        """
        Get overall health status of the application

        Returns:
            dict: Health status information
        """
        db_status = HealthCheckService._check_database()

        return {
            "status": "healthy",
            "service": os.environ.get("APP_NAME", "LMS Backend"),
            "version": os.environ.get("APP_VERSION", "1.0.0"),
            "timestamp": datetime.utcnow().isoformat(),
            "environment": os.environ.get("FLASK_ENV", "development"),
            "database": db_status,
        }

    @staticmethod
    def get_readiness_status():
        """
        Check if service is ready to accept traffic

        Returns:
            dict: Readiness status with message
            bool: Whether service is ready
        """
        is_ready = HealthCheckService._check_database() == "healthy"

        return {
            "ready": is_ready,
            "message": (
                "Service is ready" if is_ready else "Service not ready - database connection failed"
            ),
            "timestamp": datetime.utcnow().isoformat(),
        }, is_ready

    @staticmethod
    def get_liveness_status():
        """
        Check if service is alive and running

        Returns:
            dict: Liveness status
        """
        return {
            "alive": True,
            "timestamp": datetime.utcnow().isoformat(),
        }

    @staticmethod
    def _check_database():
        """
        Check database connection

        Returns:
            str: 'healthy' if connected, error message otherwise
        """
        try:
            db.session.execute("SELECT 1")
            return "healthy"
        except Exception as e:
            return f"unhealthy: {str(e)}"
