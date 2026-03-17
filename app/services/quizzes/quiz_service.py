"""
Quiz Service
Handles core quiz CRUD operations including creation, retrieval, update, and deletion.
Ownership is verified via the quiz's parent course instructor_id.
"""

import logging
import uuid
from datetime import datetime

from app import db
from app.exceptions import AuthorizationError, ResourceNotFoundError, ValidationError
from app.models.courses.course import Course
from app.models.courses.lesson_content import LessonContent
from app.models.quizzes.quiz import Quiz
from app.models.quizzes.quiz_course import QuizCourse
from app.services.health.base_service import BaseService

logger = logging.getLogger(__name__)


def parse_datetime(date_input):
    """
    Parse various date/time formats and return a standardized datetime object.
    Supports multiple common formats.
    
    Args:
        date_input: Date string in various formats (ISO, Unix timestamp, etc.)
        
    Returns:
        datetime: Parsed datetime object, or None if invalid
    """
    if not date_input or not str(date_input).strip():
        return None
    
    date_str = str(date_input).strip()
    
    # List of formats to try
    formats = [
        # ISO formats
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f",
        # Date only
        "%Y-%m-%d",
        # US format
        "%m/%d/%Y %H:%M:%S",
        "%m/%d/%Y %H:%M",
        "%m/%d/%Y",
        # DD/MM/YYYY format
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y %H:%M",
        "%d/%m/%Y",
    ]
    
    # Try Unix timestamp (seconds)
    try:
        timestamp = float(date_str)
        if 0 < timestamp < 10000000000:  # Reasonable Unix timestamp range
            return datetime.fromtimestamp(timestamp)
    except (ValueError, TypeError):
        pass
    
    # Try ISO format with Z and +00:00 replacement
    try:
        cleaned = date_str.replace("Z", "+00:00")
        return datetime.fromisoformat(cleaned)
    except (ValueError, AttributeError):
        pass
    
    # Try each format
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    # If nothing worked, log and return None
    logger.warning(f"Could not parse datetime: {date_str}")
    return None


class QuizService(BaseService):
    """Service for core quiz CRUD operations."""

    # ──────────────────────────────────────────────────────────────────────────
    # Create
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def create_quiz(
        user_id: str,
        title: str,
        description: str = None,
        passing_score: int = 70,
        duration_minutes: int = None,
        max_attempts: int = 1,
        show_answers_after: str = "submission",
        shuffle_questions: bool = False,
        shuffle_answers: bool = False,
        available_from: str = None,
        available_until: str = None,
        total_marks: int = 100,
        course_ids: list = None,
    ) -> dict:
        """
        Create a new quiz optionally assigned to one or more courses.

        Args:
            user_id: Requesting user's ID (from auth middleware)
            title: Quiz title (required)
            description: Quiz description/instructions
            passing_score: Minimum score percentage to pass (default 70)
            duration_minutes: Time limit in minutes (None = unlimited)
            max_attempts: Max number of allowed attempts (default 1)
            show_answers_after: When to reveal answers ('submission'|'later'|'never')
            shuffle_questions: Randomize question order per attempt
            shuffle_answers: Randomize answer options per attempt
            available_from: ISO timestamp for quiz start availability
            available_until: ISO timestamp for quiz end availability
            total_marks: Total marks for the quiz (default 100)
            course_ids: List of course UUIDs to assign quiz to (optional, can be empty or None)

        Returns:
            dict: Created quiz data with assigned courses

        Raises:
            ValidationError: On invalid field values
        """
        try:
            logger.debug("Creating quiz with title '%s' for instructor %s", title, user_id)
            if not title or not title.strip():
                raise ValidationError("Quiz title is required")

            valid_show_after = ("submission", "later", "never")
            if show_answers_after not in valid_show_after:
                raise ValidationError(
                    f"show_answers_after must be one of: {', '.join(valid_show_after)}"
                )
            try:
                if passing_score is not None:
                    passing_score = int(passing_score)
            except (ValueError, TypeError):
                raise ValidationError("passing_score must be a valid integer")

            try:
                if duration_minutes is not None:
                    duration_minutes = int(duration_minutes)
            except (ValueError, TypeError):
                raise ValidationError("duration_minutes must be a valid integer")

            try:
                if max_attempts is not None:
                    max_attempts = int(max_attempts)
            except (ValueError, TypeError):
                raise ValidationError("max_attempts must be a valid integer")

            try:
                if total_marks is not None:
                    total_marks = int(total_marks)
            except (ValueError, TypeError):
                raise ValidationError("total_marks must be a valid integer")

            # Validate numeric ranges
            if passing_score is not None and not (0 <= passing_score <= 100):
                raise ValidationError("passing_score must be between 0 and 100")

            if max_attempts is not None and max_attempts < 1:
                raise ValidationError("max_attempts must be at least 1")

            if total_marks is not None and total_marks < 1:
                raise ValidationError("total_marks must be at least 1")

            # Parse timestamps using flexible parser
            from_dt = parse_datetime(available_from) if available_from else None
            until_dt = parse_datetime(available_until) if available_until else None

            if from_dt and until_dt and from_dt >= until_dt:
                raise ValidationError("available_from must be before available_until")

            quiz = Quiz(
                quiz_id=str(uuid.uuid4()),
                user_id=user_id,
                title=title.strip(),
                description=description,
                passing_score=passing_score if passing_score is not None else 70,
                total_marks=total_marks if total_marks is not None else 100,
                duration_minutes=duration_minutes,
                max_attempts=max_attempts if max_attempts is not None else 1,
                show_answers_after=show_answers_after,
                shuffle_questions=bool(shuffle_questions),
                shuffle_answers=bool(shuffle_answers),
                available_from=from_dt,
                available_until=until_dt,
            )

            db.session.add(quiz)

            db.session.flush()  

            # Assign to courses if provided
            if course_ids:
                if isinstance(course_ids, str):
                    course_ids = [course_ids]
                
                for course_id in course_ids:
                    course = Course.query.filter_by(course_id=course_id).first()
                    quiz_course = QuizCourse.query.filter_by(quiz_id=quiz.quiz_id, course_id=course_id).first()
                    if not course:
                        raise ValidationError(f"Course with ID {course_id} not found")
                    if not quiz_course:
                        quiz_course = QuizCourse(quiz_id=quiz.quiz_id, course_id=course_id)
                        db.session.add(quiz_course)

            db.session.commit()

            logger.info("Quiz %s created by user %s with %s courses", 
                       quiz.quiz_id, user_id, len(course_ids) if course_ids else 0)

            return {
                "quiz_id": quiz.quiz_id,
                "title": quiz.title,
                "course_ids": [qc.course_id for qc in quiz.quiz_courses],
                "created_at": quiz.created_at.isoformat() if quiz.created_at else None,
            }

        except ValidationError:
            db.session.rollback()
            raise
        except Exception as exc:
            db.session.rollback()
            logger.error("Error creating quiz: %s", str(exc), exc_info=True)
            raise

    # ──────────────────────────────────────────────────────────────────────────
    # Read
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def get_quiz(quiz_id: str) -> dict:
        """
        Retrieve quiz details including aggregated question/points counts.

        Args:
            quiz_id: Quiz UUID
            user_id: User UUID

        Returns:
            dict: Quiz data with total_questions and total_points

        Raises:
            ResourceNotFoundError: If quiz not found
        """
        quiz = Quiz.query.get(quiz_id)
        if not quiz:
            raise ResourceNotFoundError("Quiz not found")

        from app.models.quizzes.question import Question
        questions = Question.query.filter_by(quiz_id=quiz_id).all()
        total_questions = len(questions)
        total_points = sum(q.points or 0 for q in questions)

        data = quiz.to_dict()
        data["total_questions"] = total_questions
        data["total_points"] = total_points
        data["settings"] = {
            "shuffle_questions": quiz.shuffle_questions,
            "shuffle_answers": quiz.shuffle_answers,
            "show_answers_after": quiz.show_answers_after,
        }
        return data

    @staticmethod
    def get_quizzes_for_course(course_id: str, user_id: str) -> list:
        """
        Retrieve all quizzes for a given course.

        Args:
            course_id: Course UUID
            user_id: User UUID

        Returns:
            list: List of quiz dicts
        """
        course = Course.query.get(course_id)
        if not course:
            raise ResourceNotFoundError("Course not found")

        course_lessons = LessonContent.query.filter_by(course_id=course_id).all()
        quiz_ids = [lc.quiz_id for lc in course_lessons if lc.content_type == "quiz" and lc.quiz_id]    

        quizzes = Quiz.query.filter(Quiz.quiz_id.in_(quiz_ids)).order_by(Quiz.created_at.desc()).all()
        
        return [q.to_dict() for q in quizzes]

    @staticmethod
    def get_all_quizzes(user_id: str) -> list:
        """
        Retrieve all quizzes in the system.
        Typically used for admin/instructor overview.

        Returns:
            list: List of quiz dicts with associated course info
        """
        quizzes = Quiz.query.filter_by(user_id=user_id).order_by(Quiz.created_at.desc()).all()
        
        return [q.to_dict() for q in quizzes] if quizzes else []

    # ──────────────────────────────────────────────────────────────────────────
    # Update
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def update_quiz(quiz_id: str, user_id: str, user_role: str, **kwargs) -> dict:
        """
        Update quiz fields. Only the course instructor or admin may update.

        Args:
            quiz_id: Quiz UUID
            user_id: Requesting user's ID
            user_role: Requesting user's role
            **kwargs: Updatable fields

        Returns:
            dict: Updated quiz data

        Raises:
            ResourceNotFoundError: If quiz not found
            AuthorizationError: If user is not the course instructor
            ValidationError: On invalid field values
        """
        try:
            quiz = Quiz.query.get(quiz_id)
            if not quiz:
                raise ResourceNotFoundError("Quiz not found")

            allowed_fields = (
                "title", "description", "passing_score", "total_marks", "duration_minutes",
                "max_attempts", "show_answers_after", "shuffle_questions",
                "shuffle_answers", "available_from", "available_until", "is_published",
            )

            for field, value in kwargs.items():
                if field not in allowed_fields:
                    continue
                
                # Validate total_marks
                if field == "total_marks" and value is not None:
                    try:
                        value = int(value)
                        if value < 1:
                            raise ValidationError("total_marks must be at least 1")
                    except (ValueError, TypeError):
                        raise ValidationError("total_marks must be a valid integer")
                
                if field in ("available_from", "available_until") and value:
                    try:
                        value = parse_datetime(value)
                    except ValueError:
                        raise ValidationError(f"Invalid timestamp for {field}")
                setattr(quiz, field, value)

            db.session.commit()
            logger.info("Quiz %s updated by user %s", quiz_id, user_id)
            return quiz.to_dict()

        except (ResourceNotFoundError, AuthorizationError, ValidationError):
            db.session.rollback()
            raise
        except Exception as exc:
            db.session.rollback()
            logger.error("Error updating quiz %s: %s", quiz_id, str(exc), exc_info=True)
            raise

    # ──────────────────────────────────────────────────────────────────────────
    # Delete
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def delete_quiz(quiz_id: str, user_id: str, user_role: str) -> bool:
        """
        Delete a quiz (cascade deletes questions, attempts, answers).

        Args:
            quiz_id: Quiz UUID
            user_id: Requesting user's ID
            user_role: Requesting user's role

        Returns:
            bool: True on success

        Raises:
            ResourceNotFoundError: If quiz not found
            AuthorizationError: If user is not the course instructor
        """
        try:
            quiz = Quiz.query.get(quiz_id)
            if not quiz:
                raise ResourceNotFoundError("Quiz not found")

            if quiz.user_id != user_id and user_role != "superadmin":
                raise AuthorizationError("Access denied. You do not own this quiz")

            db.session.delete(quiz)
            db.session.commit()
            logger.info("Quiz %s deleted by user %s", quiz_id, user_id)
            return True

        except (ResourceNotFoundError, AuthorizationError):
            db.session.rollback()
            raise
        except Exception as exc:
            db.session.rollback()
            logger.error("Error deleting quiz %s: %s", quiz_id, str(exc), exc_info=True)
            raise

    # ──────────────────────────────────────────────────────────────────────────
    # Course Assignment Management
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def assign_courses_to_quiz(
        quiz_id: str, course_ids: list, user_id: str, user_role: str
    ) -> dict:
        """
        Assign one or more courses to a quiz.

        Args:
            quiz_id: Quiz UUID
            course_ids: List of course UUIDs to assign
            user_id: Requesting user's ID
            user_role: Requesting user's role

        Returns:
            dict: Quiz data with assigned courses

        Raises:
            ResourceNotFoundError: If quiz or course not found
            AuthorizationError: If user not authorized
            ValidationError: If validation fails
        """
        try:
            quiz = Quiz.query.filter_by(quiz_id=quiz_id).first()
            if not quiz:
                raise ResourceNotFoundError(f"Quiz with ID {quiz_id} not found")

            if quiz.user_id != user_id and user_role != "superadmin":
                raise AuthorizationError("Access denied. You do not own this quiz")

            if not course_ids:
                raise ValidationError("At least one course_id is required")

            if isinstance(course_ids, str):
                course_ids = [course_ids]

            for course_id in course_ids:
                course = Course.query.filter_by(course_id=course_id).first()
                quiz_course = QuizCourse.query.filter_by(quiz_id=quiz_id, course_id=course_id).first()
                
                if not course:
                    raise ValidationError(f"Course with ID {course_id} not found")

                # Check if already assigned
                if course not in quiz_course:
                    QuizCourse(quiz_id=quiz_id, course_id=course_id)    

            db.session.commit()
            logger.info("Quiz %s assigned to %d courses by user %s", 
                       quiz_id, len(course_ids), user_id)

            return {
                "quiz_id": quiz.quiz_id,
                "title": quiz.title,
                "course_ids": [c.course_id for c in quiz.courses],
            }

        except (ResourceNotFoundError, AuthorizationError, ValidationError):
            db.session.rollback()
            raise
        except Exception as exc:
            db.session.rollback()
            logger.error("Error assigning courses to quiz %s: %s", 
                        quiz_id, str(exc), exc_info=True)
            raise

    @staticmethod
    def remove_courses_from_quiz(
        quiz_id: str, course_ids: list, user_id: str, user_role: str
    ) -> dict:
        """
        Remove one or more courses from a quiz.

        Args:
            quiz_id: Quiz UUID
            course_ids: List of course UUIDs to remove
            user_id: Requesting user's ID
            user_role: Requesting user's role

        Returns:
            dict: Quiz data with remaining assigned courses

        Raises:
            ResourceNotFoundError: If quiz not found
            AuthorizationError: If user not authorized
            ValidationError: If validation fails
        """
        try:
            quiz = Quiz.query.filter_by(quiz_id=quiz_id).first()
            if not quiz:
                raise ResourceNotFoundError(f"Quiz with ID {quiz_id} not found")

            if quiz.user_id != user_id and user_role != "superadmin":
                raise AuthorizationError("Access denied. You do not own this quiz")

            if not course_ids:
                raise ValidationError("At least one course_id is required")

            if isinstance(course_ids, str):
                course_ids = [course_ids]

            for course_id in course_ids:
                course = Course.query.filter_by(course_id=course_id).first()
                if course and course in quiz.courses:
                    quiz.courses.remove(course)

            db.session.commit()
            logger.info("Removed %d courses from quiz %s by user %s", 
                       len(course_ids), quiz_id, user_id)

            return {
                "quiz_id": quiz.quiz_id,
                "title": quiz.title,
                "course_ids": [c.course_id for c in quiz.courses],
            }

        except (ResourceNotFoundError, AuthorizationError, ValidationError):
            db.session.rollback()
            raise
        except Exception as exc:
            db.session.rollback()
            logger.error("Error removing courses from quiz %s: %s", 
                        quiz_id, str(exc), exc_info=True)
            raise

    # ──────────────────────────────────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def verify_quiz_ownership(quiz_id: str, user_id: str, user_role: str) -> Quiz:
        """
        Verify user is the instructor of the quiz's course (or admin).

        Args:
            quiz_id: Quiz UUID
            user_id: Requesting user's ID
            user_role: Requesting user's role

        Returns:
            Quiz: The quiz model instance

        Raises:
            ResourceNotFoundError: If quiz not found
            AuthorizationError: If not authorized
        """
        quiz = Quiz.query.get(quiz_id)
        if not quiz:
            raise ResourceNotFoundError("Quiz not found")

        if quiz.user_id != user_id and user_role != "superadmin":
            course = Course.query.get(quiz.course_id)
            if not course or course.instructor_id != user_id:
                raise AuthorizationError("Access denied. You do not own this quiz")

        return quiz
