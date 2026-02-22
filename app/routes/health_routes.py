"""
Health Check Routes
API endpoints for health monitoring
"""

from flask import Blueprint, jsonify

from app.services.health_service import HealthCheckService

bp = Blueprint("health", __name__, url_prefix="/api/v1/health")


@bp.route("", methods=["GET"])
@bp.route("/", methods=["GET"])
def health_check():
    """
    GET /api/v1/health
    Main health check endpoint

    Returns:
        200: {status: "healthy", service, version, timestamp, environment, database}
    """
    data = HealthCheckService.get_health_status()
    return jsonify(data), 200


@bp.route("/ready", methods=["GET"])
def readiness_check():
    """
    GET /api/v1/health/ready
    Readiness probe - indicates if service is ready for traffic

    Returns:
        200: Service ready {ready: true, message, timestamp}
        503: Service not ready {ready: false, message, timestamp}
    """
    data, is_ready = HealthCheckService.get_readiness_status()
    status_code = 200 if is_ready else 503
    return jsonify(data), status_code


@bp.route("/live", methods=["GET"])
def liveness_check():
    """
    GET /api/v1/health/live
    Liveness probe - indicates if service is running

    Returns:
        200: {alive: true, timestamp}
    """
    data = HealthCheckService.get_liveness_status()
    return jsonify(data), 200
