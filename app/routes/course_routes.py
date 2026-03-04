"""
Course Routes
All course-related API endpoints organized by resource type
"""

from flask import Blueprint, request

from app.exceptions import (
    AuthorizationError,
    ConflictError,
    ResourceNotFoundError,
    ValidationError,
)
from app.middleware.auth_middleware import require_auth, require_role
from app.services.courses import (
    CourseActivityService,
    CourseAnalyticsService,
    CourseContentService,
    CourseEnrollmentKeyService,
    CourseEnrollmentService,
    CourseLessonService,
    CourseProgressService,
    CourseReviewService,
    CourseSectionService,
    CourseService,
    CourseStatusService,
)
from app.utils.decorators import handle_exceptions, validate_json
from app.utils.response import error_response, paginated_response, success_response

bp = Blueprint("courses", __name__, url_prefix="/api/v1")


# ──────────────────────────────────────────────────────────────────────────────
# Helper
# ──────────────────────────────────────────────────────────────────────────────

def _handle_lms_error(e: Exception):
    """Convert LMS exceptions to HTTP responses."""
    from app.exceptions import LMSException

    if isinstance(e, LMSException):
        return error_response(e.message, e.status_code)
    return error_response(str(e), 500)


# ──────────────────────────────────────────────────────────────────────────────
# Course CRUD  (endpoints 1, 2, 3, 10, 46, 47)
# ──────────────────────────────────────────────────────────────────────────────


@bp.route("/courses", methods=["POST"])
@handle_exceptions
@require_auth
@require_role("teacher", "admin")
def create_course():
    """
    Create a new course.
    Requires: teacher or admin role.

    Request Body:
        title (required), description, category_id, difficulty, language,
        duration_hours, is_paid, price, course_type, visibility, thumbnail_url

    Returns:
        201: Created course data
    """
    try:
        data = request.get_json() or {}

        if not data.get("title"):
            return error_response("title is required", 400)

        course = CourseService.create_course(
            instructor_id=request.user_id,
            title=data["title"],
            description=data.get("description"),
            category_id=data.get("category_id"),
            difficulty=data.get("difficulty"),
            language=data.get("language", "en"),
            duration_hours=data.get("duration_hours"),
            is_paid=data.get("is_paid", False),
            price=data.get("price"),
            course_type=data.get("course_type", "monthly"),
            visibility=data.get("visibility", "public"),
            thumbnail_url=data.get("thumbnail_url"),
        )
        return success_response(data=course, message="Course created successfully", status_code=201)

    except Exception as e:
        return _handle_lms_error(e)


@bp.route("/courses", methods=["GET"])
@handle_exceptions
def search_courses():
    """
    Search / list published public courses. No authentication required.

    Query Params:
        q, category_id, course_type, difficulty, language, is_paid, page, limit

    Returns:
        200: Paginated course list
    """
    try:
        page = request.args.get("page", 1, type=int)
        limit = request.args.get("limit", 20, type=int)
        limit = max(1, min(limit, 100))

        result = CourseService.search_courses(
            query=request.args.get("q"),
            category_id=request.args.get("category_id"),
            course_type=request.args.get("course_type"),
            difficulty=request.args.get("difficulty"),
            language=request.args.get("language"),
            is_paid=request.args.get("is_paid", type=lambda v: v.lower() == "true") if request.args.get("is_paid") else None,
            page=page,
            limit=limit,
        )
        return paginated_response(
            data=result["courses"],
            total=result["total"],
            page=page,
            page_size=limit,
        )

    except Exception as e:
        return _handle_lms_error(e)


@bp.route("/courses/categories", methods=["GET"])
@handle_exceptions
def get_categories():
    """
    Get all course categories. No authentication required.

    Returns:
        200: List of categories
    """
    try:
        categories = CourseService.get_categories()
        return success_response(data=categories, message="Categories retrieved successfully")

    except Exception as e:
        return _handle_lms_error(e)


@bp.route("/courses/<course_id>", methods=["GET"])
@handle_exceptions
def get_course(course_id):
    """
    Get a single course by ID. No authentication required.

    Returns:
        200: Course data
        404: Not found
    """
    try:
        course = CourseService.get_course(course_id)
        return success_response(data=course, message="Course retrieved successfully")

    except Exception as e:
        return _handle_lms_error(e)


@bp.route("/courses/<course_id>", methods=["PUT"])
@handle_exceptions
@require_auth
def update_course(course_id):
    """
    Update course details. Requires course owner or admin.

    Request Body:
        Any updatable course fields

    Returns:
        200: Updated course data
    """
    try:
        data = request.get_json() or {}
        course = CourseService.update_course(
            course_id=course_id,
            instructor_id=request.user_id,
            user_role=request.user_role,
            **data,
        )
        return success_response(data=course, message="Course updated successfully")

    except Exception as e:
        return _handle_lms_error(e)


@bp.route("/courses/<course_id>", methods=["DELETE"])
@handle_exceptions
@require_auth
def delete_course(course_id):
    """
    Delete a course. Blocked if students are enrolled. Owner or admin only.

    Returns:
        200: Deleted confirmation
        409: Course has active enrollments
    """
    try:
        CourseService.delete_course(
            course_id=course_id,
            instructor_id=request.user_id,
            user_role=request.user_role,
        )
        return success_response(message="Course deleted successfully")

    except Exception as e:
        return _handle_lms_error(e)


# ──────────────────────────────────────────────────────────────────────────────
# Course Status & Visibility  (endpoints 4-9)
# ──────────────────────────────────────────────────────────────────────────────


@bp.route("/courses/<course_id>/publish", methods=["PUT"])
@handle_exceptions
@require_auth
def publish_course(course_id):
    """Publish a draft course. Owner or admin only."""
    try:
        data = request.get_json() or {}
        course = CourseStatusService.publish_course(
            course_id, request.user_id, request.user_role, reason=data.get("reason")
        )
        return success_response(data=course, message="Course published successfully")

    except Exception as e:
        return _handle_lms_error(e)


@bp.route("/courses/<course_id>/unpublish", methods=["PUT"])
@handle_exceptions
@require_auth
def unpublish_course(course_id):
    """Unpublish a course (revert to draft). Owner or admin only."""
    try:
        data = request.get_json() or {}
        course = CourseStatusService.unpublish_course(
            course_id, request.user_id, request.user_role, reason=data.get("reason")
        )
        return success_response(data=course, message="Course unpublished successfully")

    except Exception as e:
        return _handle_lms_error(e)


@bp.route("/courses/<course_id>/archive", methods=["PUT"])
@handle_exceptions
@require_auth
def archive_course(course_id):
    """Archive a course. Owner or admin only."""
    try:
        data = request.get_json() or {}
        course = CourseStatusService.archive_course(
            course_id, request.user_id, request.user_role, reason=data.get("reason")
        )
        return success_response(data=course, message="Course archived successfully")

    except Exception as e:
        return _handle_lms_error(e)


@bp.route("/courses/<course_id>/unarchive", methods=["PUT"])
@handle_exceptions
@require_auth
def unarchive_course(course_id):
    """Unarchive a course. Owner or admin only."""
    try:
        data = request.get_json() or {}
        course = CourseStatusService.unarchive_course(
            course_id, request.user_id, request.user_role, reason=data.get("reason")
        )
        return success_response(data=course, message="Course unarchived successfully")

    except Exception as e:
        return _handle_lms_error(e)


@bp.route("/courses/<course_id>/private", methods=["PUT"])
@handle_exceptions
@require_auth
def set_course_private(course_id):
    """Set course visibility to private. Owner or admin only."""
    try:
        data = request.get_json() or {}
        course = CourseStatusService.set_private(
            course_id, request.user_id, request.user_role, reason=data.get("reason")
        )
        return success_response(data=course, message="Course set to private")

    except Exception as e:
        return _handle_lms_error(e)


@bp.route("/courses/<course_id>/public", methods=["PUT"])
@handle_exceptions
@require_auth
def set_course_public(course_id):
    """Set course visibility to public. Owner or admin only."""
    try:
        data = request.get_json() or {}
        course = CourseStatusService.set_public(
            course_id, request.user_id, request.user_role, reason=data.get("reason")
        )
        return success_response(data=course, message="Course set to public")

    except Exception as e:
        return _handle_lms_error(e)


# ──────────────────────────────────────────────────────────────────────────────
# Enrollment  (endpoints 11-14)
# ──────────────────────────────────────────────────────────────────────────────


@bp.route("/courses/<course_id>/enroll", methods=["POST"])
@handle_exceptions
@require_auth
def enroll_in_course(course_id):
    """
    Enroll the authenticated user in a course.

    Request Body:
        enrollment_method: 'payment' | 'enrollment_key'
        enrollment_key: Required if enrollment_method is 'enrollment_key'

    Returns:
        201: Enrollment data
    """
    try:
        data = request.get_json() or {}
        enrollment = CourseEnrollmentService.enroll_student(
            course_id=course_id,
            user_id=request.user_id,
            enrollment_method=data.get("enrollment_method", "payment"),
            enrollment_key=data.get("enrollment_key"),
        )
        return success_response(
            data=enrollment, message="Enrolled successfully", status_code=201
        )

    except Exception as e:
        return _handle_lms_error(e)


@bp.route("/courses/<course_id>/enroll", methods=["DELETE"])
@handle_exceptions
@require_auth
def unenroll_from_course(course_id):
    """
    Unenroll from a course. Student can only unenroll themselves; admin can unenroll anyone.

    Query Params:
        user_id: Target user to unenroll (admin only)

    Returns:
        200: Unenrollment confirmation
    """
    try:
        target_user_id = request.args.get("user_id", request.user_id)
        CourseEnrollmentService.unenroll_student(
            course_id=course_id,
            user_id=target_user_id,
            requesting_user_id=request.user_id,
            user_role=request.user_role,
        )
        return success_response(message="Unenrolled successfully")

    except Exception as e:
        return _handle_lms_error(e)


@bp.route("/users/my-courses", methods=["GET"])
@handle_exceptions
@require_auth
def get_my_courses():
    """
    Get the authenticated user's enrolled courses.

    Query Params:
        status: Filter by enrollment status
        page, limit: Pagination

    Returns:
        200: Paginated enrolled course list
    """
    try:
        page = request.args.get("page", 1, type=int)
        limit = request.args.get("limit", 20, type=int)
        limit = max(1, min(limit, 100))

        result = CourseEnrollmentService.get_my_courses(
            user_id=request.user_id,
            status=request.args.get("status"),
            page=page,
            limit=limit,
        )
        return paginated_response(
            data=result["courses"],
            total=result["total"],
            page=page,
            page_size=limit,
        )

    except Exception as e:
        return _handle_lms_error(e)


@bp.route("/courses/<course_id>/enrollments", methods=["GET"])
@handle_exceptions
@require_auth
def get_course_enrollments(course_id):
    """
    Get all enrollments for a course. Owner or admin only.

    Query Params:
        status, page, limit

    Returns:
        200: Paginated enrollment list
    """
    try:
        page = request.args.get("page", 1, type=int)
        limit = request.args.get("limit", 20, type=int)
        limit = max(1, min(limit, 100))

        result = CourseEnrollmentService.get_course_enrollments(
            course_id=course_id,
            instructor_id=request.user_id,
            user_role=request.user_role,
            page=page,
            limit=limit,
            status=request.args.get("status"),
        )
        return paginated_response(
            data=result["enrollments"],
            total=result["total"],
            page=page,
            page_size=limit,
        )

    except Exception as e:
        return _handle_lms_error(e)


# ──────────────────────────────────────────────────────────────────────────────
# Enrollment Keys  (endpoints 15-18)
# ──────────────────────────────────────────────────────────────────────────────


@bp.route("/courses/<course_id>/enrollment-keys", methods=["POST"])
@handle_exceptions
@require_auth
def create_enrollment_key(course_id):
    """
    Create an enrollment key for a course. Owner or admin only.

    Request Body:
        max_enrollments (required), description, expiry_date

    Returns:
        201: Created key data
    """
    try:
        data = request.get_json() or {}

        if not data.get("max_enrollments"):
            return error_response("max_enrollments is required", 400)

        key = CourseEnrollmentKeyService.create_key(
            course_id=course_id,
            created_by=request.user_id,
            user_role=request.user_role,
            max_enrollments=data["max_enrollments"],
            description=data.get("description"),
            expiry_date=data.get("expiry_date"),
        )
        return success_response(data=key, message="Enrollment key created", status_code=201)

    except Exception as e:
        return _handle_lms_error(e)


@bp.route("/courses/<course_id>/enrollment-keys", methods=["GET"])
@handle_exceptions
@require_auth
def get_enrollment_keys(course_id):
    """
    List enrollment keys for a course. Owner or admin only.

    Query Params:
        is_active, page, limit

    Returns:
        200: Paginated key list
    """
    try:
        page = request.args.get("page", 1, type=int)
        limit = request.args.get("limit", 20, type=int)
        is_active_raw = request.args.get("is_active")
        is_active = None
        if is_active_raw is not None:
            is_active = is_active_raw.lower() == "true"

        result = CourseEnrollmentKeyService.get_keys(
            course_id=course_id,
            user_id=request.user_id,
            user_role=request.user_role,
            is_active=is_active,
            page=page,
            limit=limit,
        )
        return paginated_response(
            data=result["keys"],
            total=result["total"],
            page=page,
            page_size=limit,
        )

    except Exception as e:
        return _handle_lms_error(e)


@bp.route("/courses/<course_id>/enrollment-keys/<key_id>/deactivate", methods=["PUT"])
@handle_exceptions
@require_auth
def deactivate_enrollment_key(course_id, key_id):
    """
    Deactivate an enrollment key. Owner or admin only.

    Returns:
        200: Updated key data
    """
    try:
        key = CourseEnrollmentKeyService.deactivate_key(
            course_id=course_id,
            key_id=key_id,
            user_id=request.user_id,
            user_role=request.user_role,
        )
        return success_response(data=key, message="Enrollment key deactivated")

    except Exception as e:
        return _handle_lms_error(e)


@bp.route("/courses/<course_id>/enrollment-keys/<key_id>/analytics", methods=["GET"])
@handle_exceptions
@require_auth
def get_enrollment_key_analytics(course_id, key_id):
    """
    Get analytics for an enrollment key. Owner or admin only.

    Returns:
        200: Key analytics data
    """
    try:
        analytics = CourseEnrollmentKeyService.get_key_analytics(
            course_id=course_id,
            key_id=key_id,
            user_id=request.user_id,
            user_role=request.user_role,
        )
        return success_response(data=analytics, message="Key analytics retrieved")

    except Exception as e:
        return _handle_lms_error(e)


# ──────────────────────────────────────────────────────────────────────────────
# Sections  (endpoint 19)
# ──────────────────────────────────────────────────────────────────────────────


@bp.route("/courses/<course_id>/sections", methods=["POST"])
@handle_exceptions
@require_auth
def create_section(course_id):
    """
    Create a section in a course. Owner or admin only.

    Request Body:
        title (required), description, section_order

    Returns:
        201: Created section data
    """
    try:
        data = request.get_json() or {}

        if not data.get("title"):
            return error_response("title is required", 400)

        section = CourseSectionService.create_section(
            course_id=course_id,
            instructor_id=request.user_id,
            user_role=request.user_role,
            title=data["title"],
            description=data.get("description"),
            section_order=data.get("section_order"),
        )
        return success_response(data=section, message="Section created", status_code=201)

    except Exception as e:
        return _handle_lms_error(e)


# ──────────────────────────────────────────────────────────────────────────────
# Lessons  (endpoint 20)
# ──────────────────────────────────────────────────────────────────────────────


@bp.route("/courses/<course_id>/sections/<section_id>/lessons", methods=["POST"])
@handle_exceptions
@require_auth
def create_lesson(course_id, section_id):
    """
    Create a lesson within a section. Owner or admin only.

    Request Body:
        title (required), description, duration_minutes, lesson_order

    Returns:
        201: Created lesson data
    """
    try:
        data = request.get_json() or {}

        if not data.get("title"):
            return error_response("title is required", 400)

        lesson = CourseLessonService.create_lesson(
            course_id=course_id,
            section_id=section_id,
            instructor_id=request.user_id,
            user_role=request.user_role,
            title=data["title"],
            description=data.get("description"),
            duration_minutes=data.get("duration_minutes"),
            lesson_order=data.get("lesson_order"),
        )
        return success_response(data=lesson, message="Lesson created", status_code=201)

    except Exception as e:
        return _handle_lms_error(e)


# ──────────────────────────────────────────────────────────────────────────────
# Lesson Contents – Video  (endpoints 21, 22)
# ──────────────────────────────────────────────────────────────────────────────


@bp.route("/courses/<course_id>/lessons/<lesson_id>/contents/video", methods=["POST"])
@handle_exceptions
@require_auth
def add_video_content(course_id, lesson_id):
    """
    Add video content to a lesson. Owner or admin only.

    Request Body:
        title (required), video_url (required), description, thumbnail_url,
        preview_url, video_duration_minutes, video_file_size_bytes,
        video_quality_available, content_order

    Returns:
        201: Created content data
    """
    try:
        data = request.get_json() or {}

        for field in ["title", "video_url"]:
            if not data.get(field):
                return error_response(f"{field} is required", 400)

        content = CourseContentService.add_video_content(
            course_id=course_id,
            lesson_id=lesson_id,
            instructor_id=request.user_id,
            user_role=request.user_role,
            title=data["title"],
            video_url=data["video_url"],
            description=data.get("description"),
            thumbnail_url=data.get("thumbnail_url"),
            preview_url=data.get("preview_url"),
            video_duration_minutes=data.get("video_duration_minutes"),
            video_file_size_bytes=data.get("video_file_size_bytes"),
            video_quality_available=data.get("video_quality_available"),
            content_order=data.get("content_order"),
        )
        return success_response(data=content, message="Video content added", status_code=201)

    except Exception as e:
        return _handle_lms_error(e)


@bp.route("/courses/<course_id>/lessons/<lesson_id>/contents/<content_id>/video", methods=["PUT"])
@handle_exceptions
@require_auth
def update_video_content(course_id, lesson_id, content_id):
    """Update video content. Owner or admin only."""
    try:
        data = request.get_json() or {}
        content = CourseContentService.update_video_content(
            course_id=course_id,
            lesson_id=lesson_id,
            content_id=content_id,
            instructor_id=request.user_id,
            user_role=request.user_role,
            **data,
        )
        return success_response(data=content, message="Video content updated")

    except Exception as e:
        return _handle_lms_error(e)


# ──────────────────────────────────────────────────────────────────────────────
# Lesson Contents – Zoom  (endpoints 23, 24)
# ──────────────────────────────────────────────────────────────────────────────


@bp.route("/courses/<course_id>/lessons/<lesson_id>/contents/zoom", methods=["POST"])
@handle_exceptions
@require_auth
def add_zoom_content(course_id, lesson_id):
    """
    Add Zoom live class content to a lesson. Owner or admin only.

    Request Body:
        title (required), zoom_link (required), zoom_meeting_id, zoom_password,
        scheduled_date, scheduled_duration_minutes, description, content_order

    Returns:
        201: Created content data
    """
    try:
        data = request.get_json() or {}

        for field in ["title", "zoom_link"]:
            if not data.get(field):
                return error_response(f"{field} is required", 400)

        # Parse scheduled_date if provided as string
        scheduled_date = None
        if data.get("scheduled_date"):
            from datetime import datetime as dt
            try:
                scheduled_date = dt.fromisoformat(data["scheduled_date"])
            except ValueError:
                return error_response("Invalid scheduled_date format. Use ISO 8601.", 400)

        content = CourseContentService.add_zoom_content(
            course_id=course_id,
            lesson_id=lesson_id,
            instructor_id=request.user_id,
            user_role=request.user_role,
            title=data["title"],
            zoom_link=data["zoom_link"],
            zoom_meeting_id=data.get("zoom_meeting_id"),
            zoom_password=data.get("zoom_password"),
            scheduled_date=scheduled_date,
            scheduled_duration_minutes=data.get("scheduled_duration_minutes"),
            description=data.get("description"),
            content_order=data.get("content_order"),
        )
        return success_response(data=content, message="Zoom content added", status_code=201)

    except Exception as e:
        return _handle_lms_error(e)


@bp.route("/courses/<course_id>/lessons/<lesson_id>/contents/<content_id>/zoom", methods=["PUT"])
@handle_exceptions
@require_auth
def update_zoom_content(course_id, lesson_id, content_id):
    """Update Zoom content. Owner or admin only."""
    try:
        data = request.get_json() or {}
        content = CourseContentService.update_zoom_content(
            course_id=course_id,
            lesson_id=lesson_id,
            content_id=content_id,
            instructor_id=request.user_id,
            user_role=request.user_role,
            **data,
        )
        return success_response(data=content, message="Zoom content updated")

    except Exception as e:
        return _handle_lms_error(e)


# ──────────────────────────────────────────────────────────────────────────────
# Lesson Contents – Text  (endpoints 25, 26, 44)
# ──────────────────────────────────────────────────────────────────────────────


@bp.route("/courses/<course_id>/lessons/<lesson_id>/contents/text", methods=["POST"])
@handle_exceptions
@require_auth
def add_text_content(course_id, lesson_id):
    """
    Add text content to a lesson. Owner or admin only.

    Request Body:
        title (required), text_content (required), description, content_order

    Returns:
        201: Created content data
    """
    try:
        data = request.get_json() or {}

        for field in ["title", "text_content"]:
            if not data.get(field):
                return error_response(f"{field} is required", 400)

        content = CourseContentService.add_text_content(
            course_id=course_id,
            lesson_id=lesson_id,
            instructor_id=request.user_id,
            user_role=request.user_role,
            title=data["title"],
            text_content=data["text_content"],
            description=data.get("description"),
            content_order=data.get("content_order"),
        )
        return success_response(data=content, message="Text content added", status_code=201)

    except Exception as e:
        return _handle_lms_error(e)


@bp.route("/courses/<course_id>/lessons/<lesson_id>/contents/<content_id>/text", methods=["PUT"])
@handle_exceptions
@require_auth
def update_text_content(course_id, lesson_id, content_id):
    """Update text content. Owner or admin only."""
    try:
        data = request.get_json() or {}
        content = CourseContentService.update_text_content(
            course_id=course_id,
            lesson_id=lesson_id,
            content_id=content_id,
            instructor_id=request.user_id,
            user_role=request.user_role,
            **data,
        )
        return success_response(data=content, message="Text content updated")

    except Exception as e:
        return _handle_lms_error(e)


@bp.route("/courses/<course_id>/lessons/<lesson_id>/contents/<content_id>/text", methods=["GET"])
@handle_exceptions
@require_auth
def get_text_content(course_id, lesson_id, content_id):
    """
    Get text content. Requires owner or enrollment.

    Returns:
        200: Text content data
    """
    try:
        content = CourseContentService.get_text_content(
            course_id=course_id,
            lesson_id=lesson_id,
            content_id=content_id,
            user_id=request.user_id,
            user_role=request.user_role,
        )
        return success_response(data=content, message="Text content retrieved")

    except Exception as e:
        return _handle_lms_error(e)


# ──────────────────────────────────────────────────────────────────────────────
# Lesson Contents – PDF  (endpoints 27, 28, 43)
# ──────────────────────────────────────────────────────────────────────────────


@bp.route("/courses/<course_id>/lessons/<lesson_id>/contents/pdf", methods=["POST"])
@handle_exceptions
@require_auth
def add_pdf_content(course_id, lesson_id):
    """
    Add PDF content to a lesson. Owner or admin only.

    Request Body:
        title (required), pdf_file_url (required), description,
        pdf_file_size_bytes, content_order

    Returns:
        201: Created content data
    """
    try:
        data = request.get_json() or {}

        for field in ["title", "pdf_file_url"]:
            if not data.get(field):
                return error_response(f"{field} is required", 400)

        content = CourseContentService.add_pdf_content(
            course_id=course_id,
            lesson_id=lesson_id,
            instructor_id=request.user_id,
            user_role=request.user_role,
            title=data["title"],
            pdf_file_url=data["pdf_file_url"],
            description=data.get("description"),
            pdf_file_size_bytes=data.get("pdf_file_size_bytes"),
            content_order=data.get("content_order"),
        )
        return success_response(data=content, message="PDF content added", status_code=201)

    except Exception as e:
        return _handle_lms_error(e)


@bp.route("/courses/<course_id>/lessons/<lesson_id>/contents/<content_id>/pdf", methods=["PUT"])
@handle_exceptions
@require_auth
def update_pdf_content(course_id, lesson_id, content_id):
    """Update PDF content. Owner or admin only."""
    try:
        data = request.get_json() or {}
        content = CourseContentService.update_pdf_content(
            course_id=course_id,
            lesson_id=lesson_id,
            content_id=content_id,
            instructor_id=request.user_id,
            user_role=request.user_role,
            **data,
        )
        return success_response(data=content, message="PDF content updated")

    except Exception as e:
        return _handle_lms_error(e)


@bp.route("/courses/<course_id>/lessons/<lesson_id>/contents/<content_id>/download", methods=["GET"])
@handle_exceptions
@require_auth
def download_pdf_content(course_id, lesson_id, content_id):
    """
    Get PDF download URL. Requires owner or enrollment.

    Returns:
        200: PDF file URL
    """
    try:
        from app.services.courses.course_service import CourseService
        from app.models.courses.lesson_content import LessonContent

        CourseService.verify_owner_or_enrolled(course_id, request.user_id, request.user_role)

        content = LessonContent.query.filter_by(
            content_id=content_id, lesson_id=lesson_id, content_type="pdf"
        ).first()
        if not content:
            return error_response("PDF content not found", 404)

        # Track download
        CourseActivityService.track_activity(
            course_id=course_id,
            user_id=request.user_id,
            activity_type="pdf_download",
            lesson_id=lesson_id,
            content_id=content_id,
        )

        return success_response(
            data={"pdf_file_url": content.pdf_file_url, "title": content.title},
            message="PDF download URL retrieved",
        )

    except Exception as e:
        return _handle_lms_error(e)


# ──────────────────────────────────────────────────────────────────────────────
# Lesson Contents – Quiz  (endpoints 29, 30)
# ──────────────────────────────────────────────────────────────────────────────


@bp.route("/courses/<course_id>/lessons/<lesson_id>/contents/quiz", methods=["POST"])
@handle_exceptions
@require_auth
def add_quiz_content(course_id, lesson_id):
    """
    Add quiz content to a lesson. Owner or admin only.

    Request Body:
        title (required), quiz_id (required), passing_score, is_mandatory,
        description, content_order

    Returns:
        201: Created content data
    """
    try:
        data = request.get_json() or {}

        for field in ["title", "quiz_id"]:
            if not data.get(field):
                return error_response(f"{field} is required", 400)

        content = CourseContentService.add_quiz_content(
            course_id=course_id,
            lesson_id=lesson_id,
            instructor_id=request.user_id,
            user_role=request.user_role,
            title=data["title"],
            quiz_id=data["quiz_id"],
            passing_score=data.get("passing_score"),
            is_mandatory=data.get("is_mandatory", False),
            description=data.get("description"),
            content_order=data.get("content_order"),
        )
        return success_response(data=content, message="Quiz content added", status_code=201)

    except Exception as e:
        return _handle_lms_error(e)


@bp.route("/courses/<course_id>/lessons/<lesson_id>/contents/<content_id>/quiz", methods=["PUT"])
@handle_exceptions
@require_auth
def update_quiz_content(course_id, lesson_id, content_id):
    """Update quiz content. Owner or admin only."""
    try:
        data = request.get_json() or {}
        content = CourseContentService.update_quiz_content(
            course_id=course_id,
            lesson_id=lesson_id,
            content_id=content_id,
            instructor_id=request.user_id,
            user_role=request.user_role,
            **data,
        )
        return success_response(data=content, message="Quiz content updated")

    except Exception as e:
        return _handle_lms_error(e)


# ──────────────────────────────────────────────────────────────────────────────
# Content – Delete & Notify  (endpoints 31, 32)
# ──────────────────────────────────────────────────────────────────────────────


@bp.route("/courses/<course_id>/lessons/<lesson_id>/contents/<content_id>", methods=["DELETE"])
@handle_exceptions
@require_auth
def delete_content(course_id, lesson_id, content_id):
    """Delete any content item from a lesson. Owner or admin only."""
    try:
        CourseContentService.delete_content(
            course_id=course_id,
            lesson_id=lesson_id,
            content_id=content_id,
            instructor_id=request.user_id,
            user_role=request.user_role,
        )
        return success_response(message="Content deleted successfully")

    except Exception as e:
        return _handle_lms_error(e)


@bp.route("/courses/<course_id>/lessons/<lesson_id>/contents/notify-update", methods=["POST"])
@handle_exceptions
@require_auth
def notify_content_update(course_id, lesson_id):
    """
    Notify enrolled students about a content update. Owner or admin only.
    Tracks the notification activity (full notification dispatch via notification service).

    Returns:
        200: Notification queued
    """
    try:
        from app.services.courses.course_service import CourseService

        CourseService.verify_course_owner(course_id, request.user_id, request.user_role)

        data = request.get_json() or {}
        CourseActivityService.track_activity(
            course_id=course_id,
            user_id=request.user_id,
            activity_type="content_update_notify",
            lesson_id=lesson_id,
            activity_description=data.get("message", "Content updated"),
        )
        return success_response(message="Notification queued for enrolled students")

    except Exception as e:
        return _handle_lms_error(e)


# ──────────────────────────────────────────────────────────────────────────────
# Attendance & Recordings  (endpoints 33-38)
# ──────────────────────────────────────────────────────────────────────────────


@bp.route("/courses/<course_id>/lessons/<lesson_id>/attendance", methods=["GET"])
@handle_exceptions
@require_auth
def get_lesson_attendance(course_id, lesson_id):
    """Get Zoom attendance records for a lesson. Owner or admin only."""
    try:
        data = CourseAnalyticsService.get_lesson_attendance(
            course_id=course_id,
            lesson_id=lesson_id,
            user_id=request.user_id,
            user_role=request.user_role,
        )
        return success_response(data=data, message="Attendance records retrieved")

    except Exception as e:
        return _handle_lms_error(e)


@bp.route("/courses/<course_id>/lessons/<lesson_id>/attendance/export", methods=["GET"])
@handle_exceptions
@require_auth
def export_lesson_attendance(course_id, lesson_id):
    """Export attendance as JSON list (CSV conversion to be handled by client). Owner or admin only."""
    try:
        rows = CourseAnalyticsService.export_attendance(
            course_id=course_id,
            lesson_id=lesson_id,
            user_id=request.user_id,
            user_role=request.user_role,
        )
        return success_response(data=rows, message="Attendance export data ready")

    except Exception as e:
        return _handle_lms_error(e)


@bp.route("/courses/<course_id>/lessons/<lesson_id>/recordings", methods=["POST"])
@handle_exceptions
@require_auth
def add_recording(course_id, lesson_id):
    """
    Add a recording to a Zoom lesson content. Owner or admin only.

    Request Body:
        content_id (required), recording_url (required)

    Returns:
        200: Updated content data
    """
    try:
        data = request.get_json() or {}

        for field in ["content_id", "recording_url"]:
            if not data.get(field):
                return error_response(f"{field} is required", 400)

        content = CourseAnalyticsService.add_recording(
            course_id=course_id,
            lesson_id=lesson_id,
            content_id=data["content_id"],
            instructor_id=request.user_id,
            user_role=request.user_role,
            recording_url=data["recording_url"],
        )
        return success_response(data=content, message="Recording added successfully")

    except Exception as e:
        return _handle_lms_error(e)


@bp.route(
    "/courses/<course_id>/lessons/<lesson_id>/recordings/<recording_id>/distribute",
    methods=["POST"],
)
@handle_exceptions
@require_auth
def distribute_recording(course_id, lesson_id, recording_id):
    """Distribute a recording to enrolled students. Owner or admin only."""
    try:
        result = CourseAnalyticsService.distribute_recording(
            course_id=course_id,
            lesson_id=lesson_id,
            recording_id=recording_id,
            instructor_id=request.user_id,
            user_role=request.user_role,
        )
        return success_response(data=result, message="Recording distributed")

    except Exception as e:
        return _handle_lms_error(e)


@bp.route(
    "/courses/<course_id>/lessons/<lesson_id>/recordings/<recording_id>/views",
    methods=["GET"],
)
@handle_exceptions
@require_auth
def get_recording_views(course_id, lesson_id, recording_id):
    """Get recording view statistics. Owner or admin only."""
    try:
        data = CourseAnalyticsService.get_recording_views(
            course_id=course_id,
            lesson_id=lesson_id,
            recording_id=recording_id,
            instructor_id=request.user_id,
            user_role=request.user_role,
        )
        return success_response(data=data, message="Recording views retrieved")

    except Exception as e:
        return _handle_lms_error(e)


@bp.route(
    "/courses/<course_id>/lessons/<lesson_id>/recordings/<recording_id>/reminder",
    methods=["POST"],
)
@handle_exceptions
@require_auth
def send_recording_reminder(course_id, lesson_id, recording_id):
    """Send recording reminder to students who have not viewed it. Owner or admin only."""
    try:
        from app.services.courses.course_service import CourseService

        CourseService.verify_course_owner(course_id, request.user_id, request.user_role)

        CourseActivityService.track_activity(
            course_id=course_id,
            user_id=request.user_id,
            activity_type="recording_reminder_sent",
            lesson_id=lesson_id,
            content_id=recording_id,
        )
        return success_response(message="Recording reminder queued for delivery")

    except Exception as e:
        return _handle_lms_error(e)


# ──────────────────────────────────────────────────────────────────────────────
# Student Content Access  (endpoints 39-45)
# ──────────────────────────────────────────────────────────────────────────────


@bp.route("/courses/<course_id>/content", methods=["GET"])
@handle_exceptions
@require_auth
def get_course_content(course_id):
    """
    Get full course content structure. Requires owner or enrollment.

    Returns:
        200: Course structure with sections, lessons, and contents
    """
    try:
        content = CourseContentService.get_course_content(
            course_id=course_id,
            user_id=request.user_id,
            user_role=request.user_role,
        )
        return success_response(data=content, message="Course content retrieved")

    except Exception as e:
        return _handle_lms_error(e)


@bp.route(
    "/courses/<course_id>/lessons/<lesson_id>/contents/<content_id>/stream",
    methods=["GET"],
)
@handle_exceptions
@require_auth
def stream_video_content(course_id, lesson_id, content_id):
    """
    Get video stream URL for a content item. Requires owner or enrollment.

    Returns:
        200: Streaming URL and metadata
    """
    try:
        from app.services.courses.course_service import CourseService
        from app.models.courses.lesson_content import LessonContent

        CourseService.verify_owner_or_enrolled(course_id, request.user_id, request.user_role)

        content = LessonContent.query.filter_by(
            content_id=content_id, lesson_id=lesson_id, content_type="video"
        ).first()
        if not content:
            return error_response("Video content not found", 404)

        CourseActivityService.track_activity(
            course_id=course_id,
            user_id=request.user_id,
            activity_type="video_play",
            lesson_id=lesson_id,
            content_id=content_id,
        )

        return success_response(
            data={
                "content_id": content.content_id,
                "video_url": content.video_url,
                "preview_url": content.preview_url,
                "thumbnail_url": content.thumbnail_url,
                "video_duration_minutes": content.video_duration_minutes,
                "video_quality_available": content.video_quality_available,
            },
            message="Video stream URL retrieved",
        )

    except Exception as e:
        return _handle_lms_error(e)


@bp.route(
    "/courses/<course_id>/lessons/<lesson_id>/contents/<content_id>/watch-progress",
    methods=["POST"],
)
@handle_exceptions
@require_auth
def update_watch_progress(course_id, lesson_id, content_id):
    """
    Update video watch progress. Requires owner or enrollment.

    Request Body:
        watched_percentage (required), current_position_seconds,
        quality_watched, watch_time_seconds

    Returns:
        200: Updated progress data
    """
    try:
        data = request.get_json() or {}

        if data.get("watched_percentage") is None:
            return error_response("watched_percentage is required", 400)

        progress = CourseProgressService.update_watch_progress(
            course_id=course_id,
            lesson_id=lesson_id,
            content_id=content_id,
            user_id=request.user_id,
            user_role=request.user_role,
            watched_percentage=int(data["watched_percentage"]),
            current_position_seconds=data.get("current_position_seconds", 0),
            quality_watched=data.get("quality_watched"),
            watch_time_seconds=data.get("watch_time_seconds", 0),
        )
        return success_response(data=progress, message="Watch progress updated")

    except Exception as e:
        return _handle_lms_error(e)


@bp.route(
    "/courses/<course_id>/lessons/<lesson_id>/contents/<content_id>/zoom-attendance",
    methods=["POST"],
)
@handle_exceptions
@require_auth
def record_zoom_attendance(course_id, lesson_id, content_id):
    """
    Record Zoom class attendance. Requires owner or enrollment.

    Request Body:
        joined_at, left_at, device_type

    Returns:
        200: Attendance record
    """
    try:
        from datetime import datetime as dt

        data = request.get_json() or {}

        joined_at = None
        left_at = None
        if data.get("joined_at"):
            joined_at = dt.fromisoformat(data["joined_at"])
        if data.get("left_at"):
            left_at = dt.fromisoformat(data["left_at"])

        progress = CourseProgressService.record_zoom_attendance(
            course_id=course_id,
            lesson_id=lesson_id,
            content_id=content_id,
            user_id=request.user_id,
            user_role=request.user_role,
            joined_at=joined_at,
            left_at=left_at,
            device_type=data.get("device_type"),
        )
        return success_response(data=progress, message="Zoom attendance recorded")

    except Exception as e:
        return _handle_lms_error(e)


@bp.route("/courses/<course_id>/lessons/<lesson_id>/complete", methods=["POST"])
@handle_exceptions
@require_auth
def complete_lesson(course_id, lesson_id):
    """
    Mark a lesson as complete for the authenticated student.
    Requires owner or enrollment.

    Returns:
        200: Updated enrollment progress
    """
    try:
        result = CourseProgressService.complete_lesson(
            course_id=course_id,
            lesson_id=lesson_id,
            user_id=request.user_id,
            user_role=request.user_role,
        )
        return success_response(data=result, message="Lesson marked as complete")

    except Exception as e:
        return _handle_lms_error(e)


# ──────────────────────────────────────────────────────────────────────────────
# Progress & Activity  (endpoints 48, 49, 51)
# ──────────────────────────────────────────────────────────────────────────────


@bp.route("/courses/<course_id>/progress", methods=["GET"])
@handle_exceptions
@require_auth
def get_course_progress(course_id):
    """
    Get overall course progress for the authenticated user.
    Requires owner or enrollment.

    Returns:
        200: Progress summary
    """
    try:
        progress = CourseProgressService.get_course_progress(
            course_id=course_id,
            user_id=request.user_id,
            user_role=request.user_role,
        )
        return success_response(data=progress, message="Course progress retrieved")

    except Exception as e:
        return _handle_lms_error(e)


@bp.route("/courses/<course_id>/activity-log", methods=["GET"])
@handle_exceptions
@require_auth
def get_activity_log(course_id):
    """
    Get activity log for the authenticated user in a course.
    Requires owner or enrollment.

    Query Params:
        activity_type, page, limit

    Returns:
        200: Paginated activity log
    """
    try:
        page = request.args.get("page", 1, type=int)
        limit = request.args.get("limit", 50, type=int)
        limit = max(1, min(limit, 200))

        result = CourseActivityService.get_activity_log(
            course_id=course_id,
            user_id=request.user_id,
            user_role=request.user_role,
            activity_type=request.args.get("activity_type"),
            page=page,
            limit=limit,
        )
        return paginated_response(
            data=result["activities"],
            total=result["total"],
            page=page,
            page_size=limit,
        )

    except Exception as e:
        return _handle_lms_error(e)


@bp.route("/courses/<course_id>/track-activity", methods=["POST"])
@handle_exceptions
@require_auth
def track_activity(course_id):
    """
    Track a course activity event. Any authenticated user can log activity.

    Request Body:
        activity_type (required), lesson_id, content_id,
        activity_description, metadata, session_id

    Returns:
        201: Activity log entry
    """
    try:
        data = request.get_json() or {}

        if not data.get("activity_type"):
            return error_response("activity_type is required", 400)

        log = CourseActivityService.track_activity(
            course_id=course_id,
            user_id=request.user_id,
            activity_type=data["activity_type"],
            lesson_id=data.get("lesson_id"),
            content_id=data.get("content_id"),
            activity_description=data.get("activity_description"),
            metadata=data.get("metadata"),
            session_id=data.get("session_id"),
        )
        return success_response(data=log, message="Activity tracked", status_code=201)

    except Exception as e:
        return _handle_lms_error(e)


# ──────────────────────────────────────────────────────────────────────────────
# Analytics  (endpoint 50)
# ──────────────────────────────────────────────────────────────────────────────


@bp.route("/courses/<course_id>/analytics", methods=["GET"])
@handle_exceptions
@require_auth
def get_course_analytics(course_id):
    """
    Get comprehensive analytics for a course. Owner or admin only.

    Returns:
        200: Analytics data
    """
    try:
        analytics = CourseAnalyticsService.get_course_analytics(
            course_id=course_id,
            user_id=request.user_id,
            user_role=request.user_role,
        )
        return success_response(data=analytics, message="Course analytics retrieved")

    except Exception as e:
        return _handle_lms_error(e)


# ──────────────────────────────────────────────────────────────────────────────
# Reviews  (endpoints 52, 53)
# ──────────────────────────────────────────────────────────────────────────────


@bp.route("/courses/<course_id>/reviews", methods=["POST"])
@handle_exceptions
@require_auth
def create_review(course_id):
    """
    Submit a review for a course. Requires enrollment or ownership.

    Request Body:
        rating (required, 1-5), review_text, title, is_anonymous

    Returns:
        201: Created review data
    """
    try:
        data = request.get_json() or {}

        if data.get("rating") is None:
            return error_response("rating is required", 400)

        review = CourseReviewService.create_review(
            course_id=course_id,
            user_id=request.user_id,
            user_role=request.user_role,
            rating=int(data["rating"]),
            review_text=data.get("review_text"),
            title=data.get("title"),
            is_anonymous=data.get("is_anonymous", False),
        )
        return success_response(data=review, message="Review submitted", status_code=201)

    except Exception as e:
        return _handle_lms_error(e)


@bp.route("/courses/<course_id>/reviews", methods=["GET"])
@handle_exceptions
def get_reviews(course_id):
    """
    Get reviews for a course. No authentication required.

    Query Params:
        page, limit, sort (newest|highest|lowest|helpful)

    Returns:
        200: Paginated review list
    """
    try:
        page = request.args.get("page", 1, type=int)
        limit = request.args.get("limit", 20, type=int)
        limit = max(1, min(limit, 100))

        result = CourseReviewService.get_reviews(
            course_id=course_id,
            page=page,
            limit=limit,
            sort=request.args.get("sort", "newest"),
        )
        return paginated_response(
            data=result["reviews"],
            total=result["total"],
            page=page,
            page_size=limit,
        )

    except Exception as e:
        return _handle_lms_error(e)
