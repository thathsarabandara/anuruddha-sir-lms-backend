"""
Student Routes
All student management endpoints:
"""

import logging
from flask import Blueprint, request

from app.exceptions import ValidationError
from app.middleware.auth_middleware import require_auth, require_role
from app.services.student.student_service import StudentManagementService
from app.utils.decorators import handle_exceptions, validate_json
from app.utils.response import error_response, success_response

bp = Blueprint("students", __name__, url_prefix="/api/v1/students")
logger = logging.getLogger(__name__)


# ===================== STUDENTS MANAGEMENT =====================

@bp.route("/stats", methods=["GET"])
@handle_exceptions
@require_auth
@require_role("admin", "superadmin")
def student_statistics():
    """
    Get student statistics for admin dashboard
    
    Query Parameters:
        - status: Filter by status (all, active, pending, banned)
    Returns:
        200: Student statistics
        400: Validation error
        401: Unauthorized
        403: Forbidden (not admin)
    """
    try:        
        result = StudentManagementService.get_student_statistics()
        
        return success_response(
            data=result,
            message="Student statistics retrieved successfully",
            status_code=200
        )
        
    except ValidationError as e:
        return error_response(message=str(e), status_code=400)
    except Exception as e:
        logger.error(f"Error retrieving student statistics: {str(e)}", exc_info=True)
        return error_response(message="Failed to retrieve student statistics", status_code=500)
    

@bp.route("/list", methods=["GET"])
@handle_exceptions
@require_auth
@require_role("admin", "superadmin")
def list_students():
    """
    List all students with optional status filtering
    
    Query Parameters:
        - search: Search query for student names or emails
        - status: Filter by status (all, active, pending, banned)
        - page: Page number (default: 1)
        - limit: Items per page (default: 10)
    
    Returns:
        200: List of students
        400: Validation error
        401: Unauthorized
        403: Forbidden (not admin)
    """
    try:
        search_query = request.args.get("search", None)
        status_filter = request.args.get("status", "all")
        page = request.args.get("page", 1, type=int)
        limit = request.args.get("limit", 10, type=int)
        
        # Validate pagination
        if page < 1:
            page = 1
        if limit < 1 or limit > 100:
            limit = 10
        
        result = StudentManagementService.list_students(
            search_query=search_query,
            status_filter=status_filter,
            page=page,
            limit=limit
        )
        
        # Format response to match frontend expectations
        import math
        total_pages = math.ceil(result['total'] / result['limit']) if result['total'] > 0 else 1
        
        formatted_response = {
            'students': result['students'],
            'pagination': {
                'current_page': result['page'],
                'total_pages': total_pages,
                'total_count': result['total'],
                'page_size': result['limit'],
                'has_next': result['page'] < total_pages,
                'has_previous': result['page'] > 1
            }
        }
        
        return success_response(
            data=formatted_response,
            message="Students retrieved successfully",
            status_code=200
        )
        
    except ValidationError as e:
        return error_response(message=str(e), status_code=400)
    except Exception as e:
        logger.error(f"Error listing students: {str(e)}", exc_info=True)
        return error_response(message="Failed to list students", status_code=500)


@bp.route("/activate", methods=["POST"])
@handle_exceptions
@require_auth
@require_role("admin", "superadmin")
def activate_student():
    """
    Activate a student account
    
    Query Parameters:
        - student: Student user ID
    
    Returns:
        200: Student activated
        400: Validation error
        401: Unauthorized
        403: Forbidden (not admin)
        404: Student not found
    """
    try:
        student_id = request.args.get("student")
        if not student_id:
            return error_response("student query parameter is required", 400)
        
        result = StudentManagementService.activate_student(student_id)
        
        return success_response(
            data=result,
            message="Student account activated successfully",
            status_code=200
        )
        
    except ValidationError as e:
        status_code = 404 if "not found" in str(e).lower() else 400
        return error_response(message=str(e), status_code=status_code)
    except Exception as e:
        logger.error(f"Error activating student {student_id}: {str(e)}", exc_info=True)
        return error_response(message="Failed to activate student", status_code=500)


@bp.route("/ban", methods=["POST"])
@handle_exceptions
@require_auth
@require_role("admin", "superadmin")
@validate_json()
def ban_student():
    """
    Ban a student account
    
    Query Parameters:
        - student: Student user ID
    
    Request Body:
        {
            "reason": "string (optional) - reason for banning",
            "ban_duration_hours": "integer (optional) - duration in hours, null for permanent"
        }
    
    Returns:
        200: Student banned
        400: Validation error
        401: Unauthorized
        403: Forbidden (not admin)
        404: Student not found
    """
    try:
        student_id = request.args.get("student")
        if not student_id:
            return error_response("student query parameter is required", 400)
        data = request.get_json() or {}
        if not data and request.form:
            data = request.form.to_dict()
        reason = data.get("reason")
        
        result = StudentManagementService.ban_student(
            student_id=student_id,
            reason=reason,
        )
        
        return success_response(
            data=result,
            message="Student account banned successfully",
            status_code=200
        )
        
    except ValidationError as e:
        status_code = 404 if "not found" in str(e).lower() else 400
        logger.error(f"Validation error banning student {student_id}: {str(e)}", exc_info=True)
        return error_response(message=str(e), status_code=status_code)
    except Exception as e:
        logger.error(f"Error banning student {student_id}: {str(e)}", exc_info=True)
        return error_response(message="Failed to ban student", status_code=500)


# ===================== STUDENT MANAGEMENT (ADMIN) =====================

@bp.route("/create", methods=["POST"])
@handle_exceptions
@require_auth
@require_role("admin", "superadmin")
@validate_json()
def create_student():
    """
    Create a new verified student account directly (admin only)
    
    Request Body:
        {
            "first_name": "string (required)",
            "last_name": "string (required)",
            "email": "string (required, unique)",
            "phone": "string (optional)",
            "date_of_birth": "YYYY-MM-DD (optional)",
            "grade_level": "string (optional) - e.g., '5', '6', '7-8'",
            "school": "string (optional)",
            "address": "string (optional)",
            "parent_name": "string (optional)",
            "parent_contact": "string (optional)"
        }
    
    Returns:
        201: Student created with temporary password
        400: Validation error
        401: Unauthorized
        403: Forbidden (not admin)
        409: Email already exists
    """
    try:
        data = request.get_json(force=True, silent=True) or {}
        if not data and request.form:
            data = request.form.to_dict()     
        
        result = StudentManagementService.create_verified_student(
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
            email=data.get("email"),
            phone=data.get("phone"),
            date_of_birth=data.get("date_of_birth"),
            grade_level=data.get("grade_level"),
            school=data.get("school"),
            address=data.get("address"),
            parent_name=data.get("parent_name"),
            parent_contact=data.get("parent_contact")
        )
        
        return success_response(
            data=result,
            message="Student account created successfully. Credentials sent via email and WhatsApp.",
            status_code=201
        )
        
    except ValidationError as e:
        status_code = 409 if "already exists" in str(e).lower() else 400
        return error_response(message=str(e), status_code=status_code)
    except Exception as e:
        logger.error(f"Error creating student: {str(e)}", exc_info=True)
        return error_response(message="Failed to create student", status_code=500)


@bp.route("/reset-password", methods=["POST"])
@handle_exceptions
@require_auth
@require_role("admin", "superadmin")
@validate_json()
def reset_student_password():
    """
    Reset student password and send credentials via email and WhatsApp
    
    Request Body:
        {
            "send_notification": "boolean (optional, default: true)"
        }
    
    Returns:
        200: Password reset and notification sent
        404: Student not found
        401: Unauthorized
        403: Forbidden (not admin)
    """
    try:
        student_id = request.args.get("student")
        if not student_id:
            return error_response("student query parameter is required", 400)
        send_notification = request.args.get("send_notification", "true").lower() == "true"
        
        result = StudentManagementService.reset_student_password(
            student_id=student_id,
            send_notification=send_notification
        )
        
        return success_response(
            data=result,
            message="Student password reset successfully. New credentials sent to student.",
            status_code=200
        )
        
    except ValidationError as e:
        status_code = 404 if "not found" in str(e).lower() else 400
        return error_response(message=str(e), status_code=status_code)
    except Exception as e:
        logger.error(f"Error resetting student password: {str(e)}", exc_info=True)
        return error_response(message="Failed to reset student password", status_code=500)


@bp.route("/details", methods=["PUT"])
@handle_exceptions
@require_auth
@require_role("admin", "superadmin")
@validate_json()
def edit_student_details():
    """
    Edit student profile details (admin only)
    
    Request Body:
        {
            "first_name": "string (optional)",
            "last_name": "string (optional)",
            "phone": "string (optional)",
            "date_of_birth": "YYYY-MM-DD (optional)",
            "grade_level": "string (optional) - e.g., '5', '6', '7-8'",
            "school": "string (optional)",
            "address": "string (optional)",
            "parent_name": "string (optional)",
            "parent_contact": "string (optional)"
        }
    
    Returns:
        200: Details updated
        400: Validation error
        404: Student not found
        401: Unauthorized
        403: Forbidden (not admin)
    """
    try:
        student_id = request.args.get("student")
        if not student_id:
            return error_response("student query parameter is required", 400)
        
        data = request.get_json(force=True, silent=True) or {}
        if not data and request.form:
            data = request.form.to_dict()     
        
        result = StudentManagementService.edit_student_details(
            student_id=student_id,
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
            phone=data.get("phone"),
            date_of_birth=data.get("date_of_birth"),
            grade_level=data.get("grade_level"),
            school=data.get("school"),
            address=data.get("address"),
            parent_name=data.get("parent_name"),
            parent_contact=data.get("parent_contact")
        )
        
        return success_response(
            data=result,
            message="Student details updated successfully",
            status_code=200
        )
        
    except ValidationError as e:
        status_code = 404 if "not found" in str(e).lower() else 400
        return error_response(message=str(e), status_code=status_code)
    except Exception as e:
        logger.error(f"Error editing student details: {str(e)}", exc_info=True)
        return error_response(message="Failed to edit student details", status_code=500)

