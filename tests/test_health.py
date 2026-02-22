"""
Unit tests for health check endpoints
"""

from flask import json


class TestHealthCheck:
    """Test cases for health check endpoints"""

    def test_health_check(self, client):
        """Test the main health check endpoint"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "service" in data
        assert "version" in data

    def test_readiness_check(self, client):
        """Test the readiness check endpoint"""
        response = client.get("/api/v1/health/ready")
        assert response.status_code in (200, 503)  # 200 if ready, 503 if not
        data = json.loads(response.data)
        assert "ready" in data
        assert "message" in data

    def test_liveness_check(self, client):
        """Test the liveness check endpoint"""
        response = client.get("/api/v1/health/live")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["alive"]
        assert "timestamp" in data
