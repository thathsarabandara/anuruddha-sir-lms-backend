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


@bp.route("/activate", methods=["POST"])
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


@bp.route("/ban", methods=["POST"])
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


# ===================== TEACHER MANAGEMENT (ADMIN) =====================

@bp.route("/create", methods=["POST"])
@handle_exceptions
@require_auth
@require_role("admin", "superadmin")
@validate_json()
def create_teacher():
    """
    Create a new verified teacher account directly (admin only)
    
    Request Body:
        {
            "first_name": "string (required)",
            "last_name": "string (required)",
            "email": "string (required, unique)",
            "phone": "string (optional)",
            "date_of_birth": "YYYY-MM-DD (optional)",
            "subject_expertise": "string (optional)",
            "years_of_experience": "integer (optional)",
            "qualifications": "string (optional)",
            "professional_bio": "string (optional)",
            "address": "string (optional)"
        }
    
    Returns:
        201: Teacher created with temporary password
        400: Validation error
        401: Unauthorized
        403: Forbidden (not admin)
        409: Email already exists
    """
    try:
        data = request.get_json(force=True, silent=True) or {}
        if not data and request.form:
            data = request.form.to_dict()     
        
        result = TeacherManagementService.create_verified_teacher(
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
            email=data.get("email"),
            phone=data.get("phone"),
            date_of_birth=data.get("date_of_birth"),
            subject_expertise=data.get("subject_expertise"),
            years_of_experience=data.get("years_of_experience"),
            qualifications=data.get("qualifications"),
            professional_bio=data.get("professional_bio"),
            address=data.get("address")
        )
        
        return success_response(
            data=result,
            message="Teacher account created successfully. Credentials sent via email and WhatsApp.",
            status_code=201
        )
        
    except ValidationError as e:
        status_code = 409 if "already exists" in str(e).lower() else 400
        return error_response(message=str(e), status_code=status_code)
    except Exception as e:
        logger.error(f"Error creating teacher: {str(e)}", exc_info=True)
        return error_response(message="Failed to create teacher", status_code=500)


@bp.route("/reset-password", methods=["POST"])
@handle_exceptions
@require_auth
@require_role("admin", "superadmin")
@validate_json()
def reset_teacher_password():
    """
    Reset teacher password and send credentials via email and WhatsApp
    
    Request Body:
        {
            "send_notification": "boolean (optional, default: true)"
        }
    
    Returns:
        200: Password reset and notification sent
        404: Teacher not found
        401: Unauthorized
        403: Forbidden (not admin)
    """
    try:
        teacher_id = request.args.get("teacher")
        if not teacher_id:
            return error_response("teacher query parameter is required", 400)
        
        send_notification = request.args.get("send_notification", "true").lower() == "true"
        
        result = TeacherManagementService.reset_teacher_password(
            teacher_id=teacher_id,
            send_notification=send_notification
        )
        
        return success_response(
            data=result,
            message="Teacher password reset successfully. New credentials sent to teacher.",
            status_code=200
        )
        
    except ValidationError as e:
        status_code = 404 if "not found" in str(e).lower() else 400
        return error_response(message=str(e), status_code=status_code)
    except Exception as e:
        logger.error(f"Error resetting teacher password: {str(e)}", exc_info=True)
        return error_response(message="Failed to reset teacher password", status_code=500)


@bp.route("/details", methods=["PUT"])
@handle_exceptions
@require_auth
@require_role("admin", "superadmin")
@validate_json()
def edit_teacher_details():
    """
    Edit teacher profile details (admin only)
    
    Request Body:
        {
            "first_name": "string (optional)",
            "last_name": "string (optional)",
            "phone": "string (optional)",
            "date_of_birth": "YYYY-MM-DD (optional)",
            "subject_expertise": "string (optional)",
            "years_of_experience": "integer (optional)",
            "qualifications": "string (optional)",
            "professional_bio": "string (optional)",
            "address": "string (optional)"
        }
    
    Returns:
        200: Details updated
        400: Validation error
        404: Teacher not found
        401: Unauthorized
        403: Forbidden (not admin)
    """
    try:
        teacher_id = request.args.get("teacher")
        if not teacher_id:
            return error_response("teacher query parameter is required", 400)
        
        data = request.get_json(force=True, silent=True) or {}
        if not data and request.form:
            data = request.form.to_dict()   
        
        result = TeacherManagementService.edit_teacher_details(
            teacher_id=teacher_id,
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
            phone=data.get("phone"),
            date_of_birth=data.get("date_of_birth"),
            subject_expertise=data.get("subject_expertise"),
            years_of_experience=data.get("years_of_experience"),
            qualifications=data.get("qualifications"),
            professional_bio=data.get("professional_bio"),
            address=data.get("address")
        )
        
        return success_response(
            data=result,
            message="Teacher details updated successfully",
            status_code=200
        )
        
    except ValidationError as e:
        status_code = 404 if "not found" in str(e).lower() else 400
        return error_response(message=str(e), status_code=status_code)
    except Exception as e:
        logger.error(f"Error editing teacher details: {str(e)}", exc_info=True)
        return error_response(message="Failed to edit teacher details", status_code=500)
