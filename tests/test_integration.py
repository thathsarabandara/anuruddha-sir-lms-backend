"""
Integration tests for API endpoints
"""

import json


class TestHealthEndpoints:
    """Test cases for health check endpoints"""

    def test_health_endpoint_response_format(self, client):
        """Test health endpoint returns proper format"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, dict)

    def test_readiness_endpoint_available(self, client):
        """Test readiness endpoint is available"""
        response = client.get("/api/v1/health/ready")
        assert response.status_code in [200, 503]

    def test_liveness_endpoint_available(self, client):
        """Test liveness endpoint is available"""
        response = client.get("/api/v1/health/live")
        assert response.status_code == 200


class TestAPIBasics:
    """Test basic API functionality"""

    def test_nonexistent_endpoint_returns_404(self, client):
        """Test that accessing nonexistent endpoint returns 404"""
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404

    def test_health_endpoint_includes_data(self, client):
        """Test that health endpoint includes necessary data"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = json.loads(response.data)
        # Should have at least one of these fields
        assert any(
            field in data
            for field in ["status", "service", "version", "timestamp"]
        )
