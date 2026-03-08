"""
Quiz Routes
All quiz-related API endpoints organized by resource type.

Endpoint map:
  Quiz Management (CRUD)
    POST   /api/v1/quiz                                   - Create quiz
    GET    /api/v1/quiz                                   - List quizzes
    GET    /api/v1/quiz/<course_id>                       - List quizzes for courses
    GET    /api/v1/quiz/detail/<quiz_id>                         - Get quiz details
    PUT    /api/v1/quiz/update/<quiz_id>                         - Update quiz
    DELETE /api/v1/quiz/delete/<quiz_id>                         - Delete quiz

  Question Management
    POST   /api/v1/quiz/questions                         - Create question (single or batch)
    GET    /api/v1/quiz/questions                         - Get quiz questions
    PUT    /api/v1/quiz/update/questions                  - Update question
    PUT    /api/v1/quiz/questions/order                   - Update question order (single or batch)
    DELETE /api/v1/quiz/delete/questions                  - Delete question

  Quiz Attempt Endpoints
    POST   /api/v1/quiz/attempts                          - Start quiz attempt
    POST   /api/v1/quiz/submit/answers/<attempt_id>       - Save/update answer
    POST   /api/v1/quiz/attempts/<attempt_id>/submit      - Submit quiz
    GET    /api/v1/quiz/results                           - Get all answered quizzes (student)
    GET    /api/v1/quiz/<quiz_id>/results                 - Get quiz results (student)

  Grading Endpoints
    POST   /api/v1/quiz/answers/<answer_id>/grade         - Grade essay answer
    GET    /api/v1/quiz/<quiz_id>/submissions/<user_id>   - Get submission for grading

  Analytics Endpoints
    GET    /api/v1/quiz/<quiz_id>/statistics              - Quiz statistics (instructor)
    GET    /api/v1/quiz/questions/<question_id>/analytics - Question analytics
"""

from venv import logger

from flask import Blueprint, request

from app.middleware.auth_middleware import require_auth, require_role
from app.services.quizzes import (
    QuizAnalyticsService,
    QuizAnswerService,
    QuizAttemptService,
    QuizGradingService,
    QuizService,
)
from app.services.quizzes import QuestionService
from app.utils.decorators import handle_exceptions
from app.utils.response import error_response, success_response

bp = Blueprint("quizzes", __name__, url_prefix="/api/v1/quiz")


# ──────────────────────────────────────────────────────────────────────────────
# Helper
# ──────────────────────────────────────────────────────────────────────────────

def _handle_lms_error(e: Exception):
    """Convert LMS exceptions to HTTP responses."""
    from app.exceptions import LMSException

    if isinstance(e, LMSException):
        return error_response(e.message, e.status_code)
    return error_response(str(e), 500)


# ══════════════════════════════════════════════════════════════════════════════
# Quiz Management Endpoints (endpoints 1-4)
# ══════════════════════════════════════════════════════════════════════════════


@bp.route("/", methods=["POST"])
@handle_exceptions
@require_auth
@require_role("teacher", "admin", "superadmin")
def create_quiz():
    """
    Create a new quiz.
    Requires: Teacher or Admin role.

    Request Body:
        title (required), description, passing_score, duration_minutes,
        max_attempts, show_answers_after, shuffle_questions, shuffle_answers,
        available_from, available_until

    Returns:
        201: Created quiz data (quiz_id, title, created_at)
    """
    try:
        if request.is_json:
            data = request.get_json() or {}
        else:
            data = request.get_json(force=True, silent=True) or request.form.to_dict() or {}

        if not data.get("title"):
            return error_response("title is required", 400)

        quiz = QuizService.create_quiz(
            user_id=request.user_id,
            title=data["title"],
            description=data.get("description"),
            passing_score=data.get("passing_score", 70),
            duration_minutes=data.get("duration_minutes"),
            max_attempts=data.get("max_attempts", 1),
            show_answers_after=data.get("show_answers_after", "submission"),
            shuffle_questions=data.get("shuffle_questions", False),
            shuffle_answers=data.get("shuffle_answers", False),
            available_from=data.get("available_from"),
            available_until=data.get("available_until"),
        )
        return success_response(data=quiz, message="Quiz created successfully", status_code=201)

    except Exception as e:
        return _handle_lms_error(e)


@bp.route("/", methods=["GET"])
@handle_exceptions
@require_auth
@require_role("teacher", "admin", "superadmin")
def list_all_quizzes():
    """
    List all quizzes in the system.
    Requires: Authenticated user (typically for admin/instructor overview).

    Returns:
        200: List of all quiz data
    """
    try:
        quizzes = QuizService.get_all_quizzes(
            user_id=request.user_id
        )
        return success_response(data=quizzes, message="Quizzes retrieved successfully")

    except Exception as e:
        return _handle_lms_error(e)


@bp.route("/", methods=["GET"])
@handle_exceptions
@require_auth
@require_role("teacher", "admin", "superadmin")
def list_quizzes(course_id):
    """
    List all quizzes for a course.
    Requires: Authenticated user.

    URL Params:
        course_id (str): UUID of the course

    Returns:
        200: List of quiz data
    """
    try:
        course_id = request.args.get("course_id") or course_id
        quizzes = QuizService.get_quizzes_for_course(
            course_id,
            user_id=request.user_id,
        )
        return success_response(data=quizzes, message="Quizzes retrieved successfully")

    except Exception as e:
        response = {
            "status": "error",
            "message": "Failed to retrieve quizzes",
        }
        return _handle_lms_error(e)


@bp.route("/details", methods=["GET"])
@handle_exceptions
@require_auth
def get_quiz_details():
    """
    Get detailed information for a specific quiz.
    Requires: Authenticated user (enrolled students or instructor).

    Query Params:
        quiz_id (str): Quiz UUID

    Returns:
        200: Quiz data with total_questions, total_points, and settings
        404: Quiz not found
    """
    try:
        quiz_id = request.args.get("quiz_id")
        if not quiz_id:
            return error_response("quiz_id is required", 400)
        
        quiz = QuizService.get_quiz(
            quiz_id=quiz_id,
        )
        return success_response(data=quiz, message="Quiz retrieved successfully")

    except Exception as e:
        return _handle_lms_error(e)


@bp.route("/update", methods=["PUT"])
@handle_exceptions
@require_auth
@require_role("teacher", "admin", "superadmin")
def update_quiz():
    """
    Update quiz fields. Only the course instructor or admin may update.

    URL Params:
        quiz_id (str): Quiz UUID

    Request Body:
        Any updatable quiz fields (title, description, passing_score, etc.)

    Returns:
        200: Updated quiz data
        403: Not authorized
        404: Quiz not found
    """
    try:
        if request.is_json:
            data = request.get_json() or {}
        else:
            data = request.get_json(force=True, silent=True) or request.form.to_dict() or {}

        quiz_id = request.args.get("quiz_id") or quiz_id
        quiz = QuizService.update_quiz(
            quiz_id=quiz_id,
            user_id=request.user_id,
            user_role=request.user_role,
            **data,
        )
        return success_response(data=quiz, message="Quiz updated successfully")

    except Exception as e:
        return _handle_lms_error(e)


@bp.route("/delete", methods=["DELETE"])
@handle_exceptions
@require_auth
def delete_quiz():
    """
    Delete a quiz (cascades to questions, attempts, answers).
    Only the course instructor or admin may delete.

    URL Params:
        quiz_id (str): Quiz UUID

    Returns:
        200: Deletion confirmation
        403: Not authorized
        404: Quiz not found
    """
    try:
        quiz_id = request.args.get("quiz_id")

        QuizService.delete_quiz(
            quiz_id=quiz_id,
            user_id=request.user_id,
            user_role=request.user_role,
        )
        return success_response(message="Quiz deleted successfully")

    except Exception as e:
        return _handle_lms_error(e)


# ══════════════════════════════════════════════════════════════════════════════
# Question Management Endpoints (endpoints 5-8)
# ══════════════════════════════════════════════════════════════════════════════


@bp.route("/questions", methods=["POST"])
@handle_exceptions
@require_auth
def create_question():
    """
    Create one or multiple questions (with options) for a quiz.
    Only the course instructor or admin may create questions.

    Query/Body Params:
        quiz_id (str): Quiz UUID (can be in query or body)

    Request Body:
        Single question format:
            {
                "question_type": "multiple_choice|multiple_answer|short_answer|essay|matching|fill_blank",
                "question_text": "Question content",
                "points": 1 (optional, default 1),
                "difficulty": "easy|medium|hard" (optional, default medium),
                "category": "string" (optional),
                "explanation": "string" (optional),
                "question_order": int (optional),
                "options": [{option_text, is_correct, option_order}] (optional)
            }
        
        Batch format (array):
            [
                { question object 1 },
                { question object 2 },
                ...
            ]

    Returns:
        201: Created question data (single or array)
        400: Validation error
        403: Not authorized
        404: Quiz not found
    """
    try:
        if request.is_json:
            data = request.get_json() or {}
        else:
            data = request.get_json(force=True, silent=True) or request.form.to_dict() or {}

        quiz_id = request.args.get("quiz_id") or data.get("quiz_id")

        if not quiz_id:
            return error_response("quiz_id is required", 400)

        # Check if it's a batch request (array of questions)
        if isinstance(data, list):
            questions = []
            for q_data in data:
                if not q_data.get("question_type"):
                    return error_response("question_type is required for all questions", 400)
                if not q_data.get("question_text"):
                    return error_response("question_text is required for all questions", 400)

                question = QuestionService.create_question(
                    quiz_id=quiz_id,
                    user_id=request.user_id,
                    user_role=request.user_role,
                    question_type=q_data["question_type"],
                    question_text=q_data["question_text"],
                    points=q_data.get("points", 1),
                    difficulty=q_data.get("difficulty", "medium"),
                    category=q_data.get("category"),
                    explanation=q_data.get("explanation"),
                    question_order=q_data.get("question_order"),
                    options=q_data.get("options"),
                )
                questions.append(question)
            
            return success_response(
                data=questions,
                message=f"Successfully created {len(questions)} questions",
                status_code=201
            )
        else:
            # Single question request
            if not data.get("question_type"):
                return error_response("question_type is required", 400)
            if not data.get("question_text"):
                return error_response("question_text is required", 400)

            question = QuestionService.create_question(
                quiz_id=quiz_id,
                user_id=request.user_id,
                user_role=request.user_role,
                question_type=data["question_type"],
                question_text=data["question_text"],
                points=data.get("points", 1),
                difficulty=data.get("difficulty", "medium"),
                category=data.get("category"),
                explanation=data.get("explanation"),
                question_order=data.get("question_order"),
                options=data.get("options"),
            )
            return success_response(data=question, message="Question created successfully", status_code=201)

    except Exception as e:
        return _handle_lms_error(e)


@bp.route("/questions", methods=["GET"])
@handle_exceptions
@require_auth
def get_quiz_questions():
    """
    Retrieve all questions for a quiz.
    Only accessible to:
    - Quiz instructor/admin
    - Students who have started an attempt on this quiz
    
    Instructors/admins receive is_correct on options.
    Students receive questions without correct-answer indicators.

    Query Params:
        quiz_id (str): Quiz UUID (required)
        include_answers (bool): Include is_correct flag (instructor/admin only)

    Returns:
        200: List of question objects with options
        403: User has not started an attempt (students only)
        400: quiz_id is required
    """
    try:
        quiz_id = request.args.get("quiz_id")
        if not quiz_id:
            return error_response("quiz_id is required", 400)
        
        if request.user_role == "student":
            from app.models.quizzes.quiz_attempt import QuizAttempt
            attempt = QuizAttempt.query.filter_by(
                quiz_id=quiz_id,
                user_id=request.user_id
            ).first()
            
            if not attempt:
                return error_response("You must start a quiz attempt before viewing questions", 403)

        include_answers = False
        if request.user_role in ("teacher", "admin", "superadmin"):
            include_answers = True

        questions = QuestionService.get_quiz_questions(quiz_id, include_answers=include_answers)
        return success_response(data=questions, message="Questions retrieved successfully")

    except Exception as e:
        return _handle_lms_error(e)


@bp.route("/update/questions", methods=["PUT"])
@handle_exceptions
@require_auth
@require_role("teacher", "admin", "superadmin")
def update_question():
    """
    Update a question and optionally replace its options.
    Only the course instructor or admin may update.

    URL Params:
        question_id (str): Question UUID

    Request Body:
        Any updatable question fields; include 'options' list to replace options.

    Returns:
        200: Updated question data
        403: Not authorized
        404: Question not found
    """
    try:
        if request.is_json:
            data = request.get_json() or {}
        else:
            data = request.get_json(force=True, silent=True) or request.form.to_dict() or {}

        question_id = request.args.get("question_id") or question_id

        question = QuestionService.update_question(
            question_id=question_id,
            user_id=request.user_id,
            user_role=request.user_role,
            **data,
        )
        return success_response(data=question, message="Question updated successfully")

    except Exception as e:
        return _handle_lms_error(e)


@bp.route("/delete/questions", methods=["DELETE"])
@handle_exceptions
@require_auth
def delete_question():
    """
    Delete a question (cascades to its options and attempt answers).
    Only the course instructor or admin may delete.

    URL Params:
        question_id (str): Question UUID

    Returns:
        200: Deletion confirmation
        403: Not authorized
        404: Question not found
    """
    try:
        question_id = request.args.get("question_id")
        QuestionService.delete_question(
            question_id=question_id,
            user_id=request.user_id,
            user_role=request.user_role,
        )
        return success_response(message="Question deleted successfully")

    except Exception as e:
        return _handle_lms_error(e)


@bp.route("/questions/order", methods=["PUT"])
@handle_exceptions
@require_auth
@require_role("teacher", "admin", "superadmin")
def update_question_order():
    """
    Update the display order of one or multiple questions within a quiz.
    Only the course instructor or admin may update.

    Request Body (Single):
        {
            "question_id": "question_uuid",
            "question_order": 3
        }

    Request Body (Batch):
        [
            {"question_id": "question_uuid_1", "question_order": 1},
            {"question_id": "question_uuid_2", "question_order": 2},
            {"question_id": "question_uuid_3", "question_order": 3}
        ]

    Returns:
        200: Updated question(s) with new order
        400: Invalid or missing question_order / question_id
        403: Not authorized
        404: Question not found
    """
    try:
        if request.is_json:
            data = request.get_json() or {}
        else:
            data = request.get_json(force=True, silent=True) or request.form.to_dict() or {}

        # Handle batch request (array of questions)
        if isinstance(data, list):
            updated_questions = []
            for q_data in data:
                question_id = q_data.get("question_id")
                question_order = q_data.get("question_order")

                if not question_id:
                    return error_response("question_id is required for all questions", 400)
                if question_order is None:
                    return error_response("question_order is required for all questions", 400)

                try:
                    question_order = int(question_order)
                except (ValueError, TypeError):
                    return error_response("question_order must be an integer", 400)

                if question_order < 0:
                    return error_response("question_order must be a positive integer", 400)

                question = QuestionService.update_question_order(
                    question_id=question_id,
                    user_id=request.user_id,
                    user_role=request.user_role,
                    question_order=question_order,
                )
                updated_questions.append(question)

            return success_response(
                data=updated_questions,
                message=f"Successfully updated order for {len(updated_questions)} questions"
            )
        else:
            # Single question request
            question_id = data.get("question_id")
            question_order = data.get("question_order")

            if not question_id:
                return error_response("question_id is required", 400)
            if question_order is None:
                return error_response("question_order is required", 400)

            try:
                question_order = int(question_order)
            except (ValueError, TypeError):
                return error_response("question_order must be an integer", 400)

            if question_order < 0:
                return error_response("question_order must be a positive integer", 400)

            question = QuestionService.update_question(
                question_id=question_id,
                user_id=request.user_id,
                user_role=request.user_role,
                question_order=question_order,
            )
            return success_response(data=question, message="Question order updated successfully")

    except Exception as e:
        return _handle_lms_error(e)

# ==========================================================================
# Quiz Attempt Endpoints (endpoints 9-12)
# ===========================================================================

@bp.route("/attempts", methods=["POST"])
@handle_exceptions
@require_auth
def start_quiz_attempt():
    """
    Start a new quiz attempt for the authenticated student.
    Validates enrollment, availability window, and attempt limits.

    Request Body:
        quiz_id (required, str): Quiz UUID

    Returns:
        201: Attempt data with shuffled question list and optional expires_at
        403: Not enrolled in course
        409: Max attempts reached or attempt already in progress
        422: Quiz not yet available or expired
    """
    try:
        data = request.get_json() or {}

        if not data.get("quiz_id"):
            return error_response("quiz_id is required", 400)

        ip_address = request.remote_addr
        attempt = QuizAttemptService.start_attempt(
            quiz_id=data["quiz_id"],
            user_id=request.user_id,
            user_role=request.user_role,
            ip_address=ip_address,
        )
        return success_response(data=attempt, message="Quiz attempt started", status_code=201)

    except Exception as e:
        return _handle_lms_error(e)


@bp.route("/submit/answers/<attempt_id>", methods=["POST"])
@handle_exceptions
@require_auth
def save_answer(attempt_id):
    """
    Save (or update) a student's answer for a single question.
    Can be called multiple times per question to auto-save progress.

    URL Params:
        attempt_id (str): QuizAttempt UUID

    Request Body:
        question_id (required): Question UUID
        answer (required): option_id (MCQ) or text (short/essay/fill)
        time_taken_seconds: Optional seconds spent on the question

    Returns:
        200: Save confirmation with timestamp
        403: Attempt not owned by user
        409: Quiz already submitted or time expired
    """
    try:
        data = request.get_json() or {}

        if not data.get("question_id"):
            return error_response("question_id is required", 400)
        if data.get("answer") is None:
            return error_response("answer is required", 400)

        result = QuizAnswerService.save_answer(
            attempt_id=attempt_id,
            user_id=request.user_id,
            question_id=data["question_id"],
            answer=data["answer"],
            time_taken_seconds=data.get("time_taken_seconds"),
        )
        return success_response(data=result, message="Answer saved")

    except Exception as e:
        return _handle_lms_error(e)


@bp.route("/attempts/<attempt_id>/submit", methods=["POST"])
@handle_exceptions
@require_auth
def submit_quiz(attempt_id):
    """
    Finalize a quiz attempt.
    Auto-grades objective questions; essay/short-answer questions are flagged
    for manual grading.

    URL Params:
        attempt_id (str): QuizAttempt UUID

    Returns:
        200: Full result with score, percentage, passed flag, and per-question breakdown
        403: Attempt not owned by user
        409: Already submitted
    """
    try:
        result = QuizAnswerService.submit_quiz(
            attempt_id=attempt_id,
            user_id=request.user_id,
        )
        return success_response(data=result, message="Quiz submitted successfully")

    except Exception as e:
        return _handle_lms_error(e)


@bp.route("/results", methods=["GET"])
@handle_exceptions
@require_auth
def get_all_student_results():
    """
    Get all completed/graded quiz attempts for the authenticated student across all quizzes.

    Returns:
        200: List of attempt summaries organized by quiz
             [{ quiz_id, quiz_title, attempts: [...] }, ...]
    """
    try:
        attempts = QuizAttemptService.get_all_student_attempts(user_id=request.user_id)
        return success_response(data={"attempts": attempts}, message="All quiz results retrieved")

    except Exception as e:
        return _handle_lms_error(e)


@bp.route("/<quiz_id>/results", methods=["GET"])
@handle_exceptions
@require_auth
def get_quiz_results(quiz_id):
    """
    Get all submitted/graded attempts for the authenticated student on this quiz.

    URL Params:
        quiz_id (str): Quiz UUID

    Returns:
        200: List of attempt summaries (score, percentage, passed, submitted_at, time_taken)
    """
    try:
        attempts = QuizAttemptService.get_student_attempts(
            quiz_id=quiz_id,
            user_id=request.user_id,
        )
        return success_response(data={"attempts": attempts}, message="Quiz results retrieved")

    except Exception as e:
        return _handle_lms_error(e)


# ══════════════════════════════════════════════════════════════════════════════
# Grading Endpoints (endpoints 13-14)
# ══════════════════════════════════════════════════════════════════════════════


@bp.route("/answers/<answer_id>/grade", methods=["POST"])
@handle_exceptions
@require_auth
@require_role("teacher", "admin")
def grade_answer(answer_id):
    """
    Manually grade an essay or short-answer question.
    Only the course instructor or admin may grade.
    After grading, the attempt score is recalculated automatically.

    URL Params:
        answer_id (str): AttemptAnswer UUID

    Request Body:
        points_awarded (required): Points to award (int, 0 to question.points)
        feedback: Optional grading comment

    Returns:
        200: Grade record data
        400: Validation error (points out of range)
        403: Not authorized
        404: Answer not found
    """
    try:
        data = request.get_json() or {}

        if data.get("points_awarded") is None:
            return error_response("points_awarded is required", 400)

        grade = QuizGradingService.grade_answer(
            answer_id=answer_id,
            grader_id=request.user_id,
            grader_role=request.user_role,
            points_awarded=data["points_awarded"],
            feedback=data.get("feedback"),
        )
        return success_response(data=grade, message="Answer graded successfully")

    except Exception as e:
        return _handle_lms_error(e)


@bp.route("/<quiz_id>/submissions/<user_id>", methods=["GET"])
@handle_exceptions
@require_auth
@require_role("teacher", "admin")
def get_submission_for_grading(quiz_id, user_id):
    """
    Retrieve a student's latest submission for instructor review and grading.

    URL Params:
        quiz_id (str): Quiz UUID
        user_id (str): Student's user UUID

    Returns:
        200: Full submission with all answers, grading status, and feedback
        403: Not authorized
        404: Quiz or submission not found
    """
    try:
        submission = QuizGradingService.get_submission_for_grading(
            quiz_id=quiz_id,
            student_id=user_id,
            grader_id=request.user_id,
            grader_role=request.user_role,
        )
        return success_response(data=submission, message="Submission retrieved successfully")

    except Exception as e:
        return _handle_lms_error(e)


# ══════════════════════════════════════════════════════════════════════════════
# Analytics Endpoints (endpoints 15-16)
# ══════════════════════════════════════════════════════════════════════════════


@bp.route("/<quiz_id>/statistics", methods=["GET"])
@handle_exceptions
@require_auth
@require_role("teacher", "admin")
def get_quiz_statistics(quiz_id):
    """
    Get overall quiz performance statistics.
    Only the course instructor or admin may access.

    URL Params:
        quiz_id (str): Quiz UUID

    Returns:
        200: Statistics including total_attempts, average_score, pass_rate,
             average_time_minutes, and per-question breakdown
        403: Not authorized
        404: Quiz not found
    """
    try:
        stats = QuizAnalyticsService.get_quiz_statistics(
            quiz_id=quiz_id,
            user_id=request.user_id,
            user_role=request.user_role,
        )
        return success_response(data=stats, message="Quiz statistics retrieved successfully")

    except Exception as e:
        return _handle_lms_error(e)


@bp.route("/questions/<question_id>/analytics", methods=["GET"])
@handle_exceptions
@require_auth
@require_role("teacher", "admin")
def get_question_analytics(question_id):
    """
    Get detailed analytics for a single question.
    Only the course instructor or admin may access.

    URL Params:
        question_id (str): Question UUID

    Returns:
        200: Analytics including correct_percentage, average_time_seconds,
             difficulty_rating, and discrimination_index
        403: Not authorized
        404: Question not found
    """
    try:
        analytics = QuizAnalyticsService.get_question_analytics(
            question_id=question_id,
            user_id=request.user_id,
            user_role=request.user_role,
        )
        return success_response(data=analytics, message="Question analytics retrieved successfully")

    except Exception as e:
        return _handle_lms_error(e)
