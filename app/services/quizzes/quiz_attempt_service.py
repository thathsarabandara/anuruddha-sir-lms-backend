"""
Quiz Attempt Service
Handles starting quiz attempts and retrieving attempt data.
Enforces max_attempts, availability windows, and enrollment checks.
"""

import logging
import uuid
from datetime import datetime, timedelta, timezone

from app import db
from app.exceptions import AuthorizationError, ConflictError, ResourceNotFoundError, ValidationError
from app.models.courses.course_enrollment import CourseEnrollment
from app.models.quizzes.question import Question
from app.models.quizzes.question_option import QuestionOption
from app.models.quizzes.quiz import Quiz
from app.models.quizzes.quiz_attempt import QuizAttempt
from app.services.health.base_service import BaseService

logger = logging.getLogger(__name__)


class QuizAttemptService(BaseService):
    """Service for quiz attempt lifecycle management."""

    # ──────────────────────────────────────────────────────────────────────────
    # Start Attempt
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def start_attempt(quiz_id: str, user_id: str, user_role: str, ip_address: str = None, course_id: str = None) -> dict:
        """
        Start a new quiz attempt for an enrolled student.

        Validates:
        - Quiz exists and is within its availability window
        - User is enrolled in the quiz's course (unless teacher/admin)
        - User has not exceeded max_attempts
        - No existing in_progress attempt for this quiz

        Args:
            quiz_id: Quiz UUID
            user_id: Student's user ID
            user_role: User's role
            ip_address: Optional IP address for logging

        Returns:
            dict: Attempt data with questions (without correct answers)

        Raises:
            ResourceNotFoundError: Quiz not found
            AuthorizationError: User not enrolled
            ConflictError: Max attempts exceeded or attempt already in progress
            ValidationError: Quiz not yet available or has expired
        """
        try:
            quiz = Quiz.query.get(quiz_id)
            if not quiz:
                raise ResourceNotFoundError("Quiz not found")

            now = datetime.now(timezone.utc).replace(tzinfo=None)

            # Availability window check
            if quiz.available_from and now < quiz.available_from:
                raise ValidationError(
                    f"Quiz is not yet available. Opens at {quiz.available_from.isoformat()}"
                )
            if quiz.available_until and now > quiz.available_until:
                raise ValidationError("Quiz availability has expired")

            # Enrollment check (students only)
            if user_role not in ("teacher", "admin"):
                enrollment = CourseEnrollment.query.filter_by(
                    course_id=quiz.course_id, user_id=user_id
                ).first()
                if not enrollment or enrollment.status == "dropped":
                    raise AuthorizationError("You must be enrolled in this course to take the quiz")

            # Check for already in-progress attempt
            in_progress = QuizAttempt.query.filter_by(
                quiz_id=quiz_id, user_id=user_id, status="in_progress"
            ).first()
            if in_progress:
                raise ConflictError(
                    "You already have an in-progress attempt for this quiz",
                )

            # Max attempts check
            completed_attempts = QuizAttempt.query.filter(
                QuizAttempt.quiz_id == quiz_id,
                QuizAttempt.user_id == user_id,
                QuizAttempt.status.in_(["submitted", "graded"]),
            ).count()

            if quiz.max_attempts and completed_attempts >= quiz.max_attempts:
                raise ConflictError(
                    f"Maximum attempts ({quiz.max_attempts}) reached for this quiz"
                )

            attempt = QuizAttempt(
                attempt_id=str(uuid.uuid4()),
                quiz_id=quiz_id,
                user_id=user_id,
                started_at=now,
                ip_address=ip_address,
                status="in_progress",
            )
            db.session.add(attempt)
            db.session.commit()
            logger.info("Quiz attempt %s started by user %s", attempt.attempt_id, user_id)

            # Build question list (no correct-answer hints)
            questions = QuizAttemptService._build_question_list(quiz)

            expires_at = None
            if quiz.duration_minutes:
                expires_at = (now + timedelta(minutes=quiz.duration_minutes)).isoformat()

            return {
                "attempt_id": attempt.attempt_id,
                "quiz_id": quiz_id,
                "user_id": user_id,
                "started_at": attempt.started_at.isoformat(),
                "expires_at": expires_at,
                "questions": questions,
            }

        except (ResourceNotFoundError, AuthorizationError, ConflictError, ValidationError):
            db.session.rollback()
            raise
        except Exception as exc:
            db.session.rollback()
            logger.error("Error starting attempt for quiz %s: %s", quiz_id, str(exc), exc_info=True)
            raise

    # ──────────────────────────────────────────────────────────────────────────
    # Get Attempts
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def get_attempt(attempt_id: str, user_id: str, user_role: str) -> dict:
        """
        Retrieve a single quiz attempt.

        Args:
            attempt_id: Attempt UUID
            user_id: Requesting user's ID
            user_role: Requesting user's role

        Returns:
            dict: Attempt data

        Raises:
            ResourceNotFoundError: If attempt not found
            AuthorizationError: If not the attempt owner or admin/instructor
        """
        attempt = QuizAttempt.query.get(attempt_id)
        if not attempt:
            raise ResourceNotFoundError("Attempt not found")

        if user_role not in ("admin", "teacher") and attempt.user_id != user_id:
            raise AuthorizationError("Access denied")

        return attempt.to_dict()

    @staticmethod
    def get_student_attempts(quiz_id: str, user_id: str) -> list:
        """
        Retrieve all submitted/graded attempts for a student on a specific quiz.

        Args:
            quiz_id: Quiz UUID
            user_id: Student's user ID

        Returns:
            list: List of attempt dicts
        """
        quiz = Quiz.query.get(quiz_id)
        if not quiz:
            raise ResourceNotFoundError("Quiz not found")

        attempts = (
            QuizAttempt.query.filter(
                QuizAttempt.quiz_id == quiz_id,
                QuizAttempt.user_id == user_id,
                QuizAttempt.status.in_(["submitted", "graded"]),
            )
            .order_by(QuizAttempt.submitted_at.desc())
            .all()
        )
        return [a.to_dict() for a in attempts]

    @staticmethod
    def get_all_student_attempts(user_id: str) -> list:
        """
        Retrieve all submitted/graded quiz attempts for a student across all quizzes.

        Args:
            user_id: Student's user ID

        Returns:
            list: List of attempt dicts grouped and sorted by quiz
        """
        from app.models.quizzes.quiz import Quiz

        attempts = (
            QuizAttempt.query.filter(
                QuizAttempt.user_id == user_id,
                QuizAttempt.status.in_(["submitted", "graded"]),
            )
            .order_by(QuizAttempt.submitted_at.desc())
            .all()
        )

        # Group attempts by quiz
        grouped = {}
        for attempt in attempts:
            quiz = Quiz.query.get(attempt.quiz_id)
            if quiz:
                quiz_key = attempt.quiz_id
                if quiz_key not in grouped:
                    grouped[quiz_key] = {
                        "quiz_id": attempt.quiz_id,
                        "quiz_title": quiz.title,
                        "attempts": [],
                    }
                grouped[quiz_key]["attempts"].append(attempt.to_dict())

        return list(grouped.values())

    # ──────────────────────────────────────────────────────────────────────────
    # Internal helpers
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _build_question_list(quiz: Quiz) -> list:
        """Build and optionally shuffle the question list for an attempt."""
        import random

        questions = (
            Question.query.filter_by(quiz_id=quiz.quiz_id)
            .order_by(Question.question_order.asc(), Question.created_at.asc())
            .all()
        )

        if quiz.shuffle_questions:
            random.shuffle(questions)

        result = []
        for q in questions:
            q_dict = {
                "question_id": q.question_id,
                "question_text": q.question_text,
                "question_type": q.question_type,
                "points": q.points,
                "options": [],
            }

            options = (
                QuestionOption.query.filter_by(question_id=q.question_id)
                .order_by(QuestionOption.option_order.asc())
                .all()
            )

            if quiz.shuffle_answers:
                import random as _r
                options = list(options)
                _r.shuffle(options)

            q_dict["options"] = [
                {
                    "option_id": opt.option_id,
                    "option_text": opt.option_text,
                    "option_order": opt.option_order,
                }
                for opt in options
            ]

            result.append(q_dict)

        return result
