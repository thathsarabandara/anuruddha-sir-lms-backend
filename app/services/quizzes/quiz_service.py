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
from app.models.quizzes.quiz import Quiz
from app.services.base_service import BaseService

logger = logging.getLogger(__name__)


class QuizService(BaseService):
    """Service for core quiz CRUD operations."""

    # ──────────────────────────────────────────────────────────────────────────
    # Create
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def create_quiz(
        course_id: str,
        instructor_id: str,
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
    ) -> dict:
        """
        Create a new quiz for a course.

        Args:
            course_id: UUID of the course this quiz belongs to
            instructor_id: Requesting user's ID (must be course instructor or admin)
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

        Returns:
            dict: Created quiz data

        Raises:
            ResourceNotFoundError: If course not found
            AuthorizationError: If user is not the course instructor
            ValidationError: On invalid field values
        """
        try:
            course = Course.query.get(course_id)
            if not course:
                raise ResourceNotFoundError("Course not found")

            if course.instructor_id != instructor_id:
                raise AuthorizationError("Only the course instructor can create quizzes")

            if not title or not title.strip():
                raise ValidationError("Quiz title is required")

            valid_show_after = ("submission", "later", "never")
            if show_answers_after not in valid_show_after:
                raise ValidationError(
                    f"show_answers_after must be one of: {', '.join(valid_show_after)}"
                )

            if passing_score is not None and not (0 <= passing_score <= 100):
                raise ValidationError("passing_score must be between 0 and 100")

            if max_attempts is not None and max_attempts < 1:
                raise ValidationError("max_attempts must be at least 1")

            # Parse timestamps
            from_dt = None
            until_dt = None
            if available_from:
                try:
                    from_dt = datetime.fromisoformat(available_from.replace("Z", "+00:00"))
                except ValueError:
                    raise ValidationError("Invalid available_from timestamp format")
            if available_until:
                try:
                    until_dt = datetime.fromisoformat(available_until.replace("Z", "+00:00"))
                except ValueError:
                    raise ValidationError("Invalid available_until timestamp format")

            if from_dt and until_dt and from_dt >= until_dt:
                raise ValidationError("available_from must be before available_until")

            quiz = Quiz(
                quiz_id=str(uuid.uuid4()),
                course_id=course_id,
                title=title.strip(),
                description=description,
                passing_score=passing_score if passing_score is not None else 70,
                duration_minutes=duration_minutes,
                max_attempts=max_attempts if max_attempts is not None else 1,
                show_answers_after=show_answers_after,
                shuffle_questions=bool(shuffle_questions),
                shuffle_answers=bool(shuffle_answers),
                available_from=from_dt,
                available_until=until_dt,
            )

            db.session.add(quiz)
            db.session.commit()

            logger.info("Quiz %s created for course %s by user %s", quiz.quiz_id, course_id, instructor_id)

            return {
                "quiz_id": quiz.quiz_id,
                "course_id": quiz.course_id,
                "title": quiz.title,
                "created_at": quiz.created_at.isoformat() if quiz.created_at else None,
            }

        except (ResourceNotFoundError, AuthorizationError, ValidationError):
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
    def get_quizzes_for_course(course_id: str) -> list:
        """
        Retrieve all quizzes for a given course.

        Args:
            course_id: Course UUID

        Returns:
            list: List of quiz dicts
        """
        course = Course.query.get(course_id)
        if not course:
            raise ResourceNotFoundError("Course not found")

        quizzes = Quiz.query.filter_by(course_id=course_id).order_by(Quiz.created_at.asc()).all()
        return [q.to_dict() for q in quizzes]

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

            if user_role != "admin":
                course = Course.query.get(quiz.course_id)
                if not course or course.instructor_id != user_id:
                    raise AuthorizationError("Only the course instructor can update this quiz")

            allowed_fields = (
                "title", "description", "passing_score", "duration_minutes",
                "max_attempts", "show_answers_after", "shuffle_questions",
                "shuffle_answers", "available_from", "available_until",
            )

            for field, value in kwargs.items():
                if field not in allowed_fields:
                    continue
                if field in ("available_from", "available_until") and value:
                    try:
                        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
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

            if user_role != "admin":
                course = Course.query.get(quiz.course_id)
                if not course or course.instructor_id != user_id:
                    raise AuthorizationError("Only the course instructor can delete this quiz")

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

        if user_role != "admin":
            course = Course.query.get(quiz.course_id)
            if not course or course.instructor_id != user_id:
                raise AuthorizationError("Access denied. You do not own this quiz")

        return quiz
