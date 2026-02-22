"""
Services Module
Business logic layer containing all application logic separated from HTTP concerns.

Pattern:
    - Services contain core business logic
    - Services are independent of Flask/HTTP
    - Routes call services and handle HTTP
    - Services return data, not responses

Example:
    from app.services.health_service import HealthCheckService

    data = HealthCheckService.get_health_status()
    return jsonify(data), 200
"""

from app.services.health_service import HealthCheckService

__all__ = ["HealthCheckService"]
