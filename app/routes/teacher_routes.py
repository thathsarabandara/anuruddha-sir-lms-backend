"""
Teacher Routes
All teacher management endpoints
"""

import logging
from flask import Blueprint, request

from app.exceptions import ValidationError
from app.middleware.auth_middleware import require_auth, require_role
from app.services.teacher.teacher_service import TeacherManagementService
from app.utils.decorators import handle_exceptions, validate_json
from app.utils.response import error_response, success_response

bp = Blueprint("teachers", __name__, url_prefix="/api/v1/teachers")
logger = logging.getLogger(__name__)

# ===================== TEACHERS MANAGEMENT =====================

@bp.route("/stats", methods=["GET"])
@handle_exceptions
@require_auth
@require_role("admin", "superadmin")
def teacher_stats():
    """
    Get teacher statistics
    
    Returns:
        200: Teacher statistics
        401: Unauthorized
        403: Forbidden (not admin)
    """
    try:
        result = TeacherManagementService.get_teacher_stats()
        
        return success_response(
            data=result,
            message="Teacher statistics retrieved successfully",
            status_code=200
        )
        
    except Exception as e:
        logger.error(f"Error retrieving teacher statistics: {str(e)}", exc_info=True)
        return error_response(message="Failed to retrieve teacher statistics", status_code=500)
    

@bp.route("/list", methods=["GET"])
@handle_exceptions
@require_auth
@require_role("admin", "superadmin")
def list_teachers():
    """
    List all teachers with optional status filtering
    
    Query Parameters:
        - search: Search query for teacher names or emails
        - status: Filter by status (active, pending, banned)
        - page: Page number (default: 1)
        - limit: Items per page (default: 10)
    
    Returns:
        200: List of teachers
        400: Validation error
        401: Unauthorized
        403: Forbidden (not admin)
    """
    try:
        search_query = request.args.get("search", None)
        status_filter = request.args.get("status", None)
        page = request.args.get("page", 1, type=int)
        limit = request.args.get("limit", 10, type=int)
        
        # Validate pagination
        if page < 1:
            page = 1
        if limit < 1 or limit > 100:
            limit = 10
        
        result = TeacherManagementService.list_teachers(
            search_query=search_query,
            status_filter=status_filter,
            page=page,
            limit=limit
        )
        
        return success_response(
            data=result,
            message="Teachers retrieved successfully",
            status_code=200
        )
        
    except ValidationError as e:
        return error_response(message=str(e), status_code=400)
    except Exception as e:
        logger.error(f"Error listing teachers: {str(e)}", exc_info=True)
        return error_response(message="Failed to list teachers", status_code=500)


@bp.route("/teacher/activate", methods=["POST"])
@handle_exceptions
@require_auth
@require_role("admin", "superadmin")
def activate_teacher():
    """
    Activate a teacher account
    
    Query Parameters:
        - teacher: Teacher user ID
    
    Returns:
        200: Teacher activated
        400: Validation error
        401: Unauthorized
        403: Forbidden (not admin)
        404: Teacher not found
    """
    try:
        teacher_id = request.args.get("teacher")
        if not teacher_id:
            return error_response("teacher query parameter is required", 400)
        
        result = TeacherManagementService.activate_teacher(teacher_id)
        
        return success_response(
            data=result,
            message="Teacher account activated successfully",
            status_code=200
        )
        
    except ValidationError as e:
        status_code = 404 if "not found" in str(e).lower() else 400
        return error_response(message=str(e), status_code=status_code)
    except Exception as e:
        logger.error(f"Error activating teacher {teacher_id}: {str(e)}", exc_info=True)
        return error_response(message="Failed to activate teacher", status_code=500)


@bp.route("/teacher/ban", methods=["POST"])
@handle_exceptions
@require_auth
@require_role("admin", "superadmin")
@validate_json()
def ban_teacher():
    """
    Ban a teacher account
    
    Query Parameters:
        - teacher: Teacher user ID
    
    Request Body:
        {
            "reason": "string (optional) - reason for banning",
            "ban_duration_hours": "integer (optional) - duration in hours, null for permanent"
        }
    
    Returns:
        200: Teacher banned
        400: Validation error
        401: Unauthorized
        403: Forbidden (not admin)
        404: Teacher not found
    """
    try:
        teacher_id = request.args.get("teacher")
        if not teacher_id:
            return error_response("teacher query parameter is required", 400)
        
        data = request.get_json() or {}
        reason = data.get("reason")
        ban_duration_hours = data.get("ban_duration_hours")
        
        # Validate ban_duration_hours if provided
        if ban_duration_hours is not None:
            if not isinstance(ban_duration_hours, int) or ban_duration_hours < 1:
                return error_response(
                    message="ban_duration_hours must be a positive integer",
                    status_code=400
                )
        
        result = TeacherManagementService.ban_teacher(
            teacher_id=teacher_id,
            reason=reason,
            ban_duration_hours=ban_duration_hours
        )
        
        return success_response(
            data=result,
            message="Teacher account banned successfully",
            status_code=200
        )
        
    except ValidationError as e:
        status_code = 404 if "not found" in str(e).lower() else 400
        return error_response(message=str(e), status_code=status_code)
    except Exception as e:
        logger.error(f"Error banning teacher {teacher_id}: {str(e)}", exc_info=True)
        return error_response(message="Failed to ban teacher", status_code=500)
