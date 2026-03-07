"""
Quiz Grading Service
Handles manual grading of essay/short-answer questions and
retrieving full submissions for instructor review.
"""

import logging
import uuid
from datetime import datetime

from app import db
from app.exceptions import AuthorizationError, ConflictError, ResourceNotFoundError, ValidationError
from app.models.courses.course import Course
from app.models.quizzes.attempt_answer import AttemptAnswer
from app.models.quizzes.manual_grade import ManualGrade
from app.models.quizzes.question import Question
from app.models.quizzes.quiz import Quiz
from app.models.quizzes.quiz_attempt import QuizAttempt
from app.services.base_service import BaseService

logger = logging.getLogger(__name__)


class QuizGradingService(BaseService):
    """Service for manual grading of subjective quiz answers."""

    # ──────────────────────────────────────────────────────────────────────────
    # Grade an answer
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def grade_answer(
        answer_id: str,
        grader_id: str,
        grader_role: str,
        points_awarded: int,
        feedback: str = None,
    ) -> dict:
        """
        Manually grade an essay/short-answer question.

        After grading, recalculates the attempt's total score and updates
        attempt.status to 'graded' if all manual questions are now graded.

        Args:
            answer_id: AttemptAnswer UUID
            grader_id: Instructor/admin user ID
            grader_role: User's role
            points_awarded: Points granted (must be <= question.points)
            feedback: Optional grading feedback/comments

        Returns:
            dict: Grade record data

        Raises:
            ResourceNotFoundError: Answer not found
            AuthorizationError: User is not course instructor or admin
            ValidationError: points_awarded out of range
        """
        try:
            answer = AttemptAnswer.query.get(answer_id)
            if not answer:
                raise ResourceNotFoundError("Answer not found")

            question = Question.query.get(answer.question_id)
            attempt = QuizAttempt.query.get(answer.attempt_id)
            quiz = Quiz.query.get(attempt.quiz_id) if attempt else None

            if not question or not attempt or not quiz:
                raise ResourceNotFoundError("Related quiz data not found")

            # Authorization: grader must be the course instructor or admin
            if grader_role != "admin":
                course = Course.query.get(quiz.course_id)
                if not course or course.instructor_id != grader_id:
                    raise AuthorizationError("Only the course instructor can grade answers")

            if points_awarded is None:
                raise ValidationError("points_awarded is required")

            if points_awarded < 0:
                raise ValidationError("points_awarded cannot be negative")

            if question.points and points_awarded > question.points:
                raise ValidationError(
                    f"points_awarded ({points_awarded}) cannot exceed question points ({question.points})"
                )

            # Upsert manual grade record
            existing_grade = ManualGrade.query.filter_by(answer_id=answer_id).first()
            if existing_grade:
                existing_grade.points_awarded = points_awarded
                existing_grade.feedback = feedback
                existing_grade.graded_by = grader_id
                existing_grade.graded_at = datetime.utcnow()
                grade = existing_grade
            else:
                grade = ManualGrade(
                    grade_id=str(uuid.uuid4()),
                    answer_id=answer_id,
                    graded_by=grader_id,
                    points_awarded=points_awarded,
                    feedback=feedback,
                    graded_at=datetime.utcnow(),
                )
                db.session.add(grade)

            # Update the answer record
            answer.points_earned = points_awarded
            answer.is_correct = points_awarded > 0

            db.session.flush()

            # Recalculate attempt score and check if fully graded
            QuizGradingService._recalculate_attempt_score(attempt, quiz)

            db.session.commit()
            logger.info("Answer %s graded by user %s (%d pts)", answer_id, grader_id, points_awarded)

            return grade.to_dict()

        except (ResourceNotFoundError, AuthorizationError, ValidationError):
            db.session.rollback()
            raise
        except Exception as exc:
            db.session.rollback()
            logger.error("Error grading answer %s: %s", answer_id, str(exc), exc_info=True)
            raise

    # ──────────────────────────────────────────────────────────────────────────
    # Get submission for grading
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def get_submission_for_grading(quiz_id: str, student_id: str, grader_id: str, grader_role: str) -> dict:
        """
        Retrieve a student's latest submission for instructor grading review.

        Args:
            quiz_id: Quiz UUID
            student_id: Target student's user ID
            grader_id: Instructor's user ID
            grader_role: Instructor's role

        Returns:
            dict: Submission data with all answers and grading status

        Raises:
            ResourceNotFoundError: Quiz or submission not found
            AuthorizationError: Not the course instructor/admin
        """
        quiz = Quiz.query.get(quiz_id)
        if not quiz:
            raise ResourceNotFoundError("Quiz not found")

        if grader_role != "admin":
            course = Course.query.get(quiz.course_id)
            if not course or course.instructor_id != grader_id:
                raise AuthorizationError("Only the course instructor can view submissions")

        # Get the most recent submitted/graded attempt
        attempt = (
            QuizAttempt.query.filter(
                QuizAttempt.quiz_id == quiz_id,
                QuizAttempt.user_id == student_id,
                QuizAttempt.status.in_(["submitted", "graded"]),
            )
            .order_by(QuizAttempt.submitted_at.desc())
            .first()
        )

        if not attempt:
            raise ResourceNotFoundError("No submission found for this student")

        # Build answer list
        answers = AttemptAnswer.query.filter_by(attempt_id=attempt.attempt_id).all()
        answer_list = []
        for ans in answers:
            question = Question.query.get(ans.question_id)
            grade = ManualGrade.query.filter_by(answer_id=ans.answer_id).first()

            answer_list.append(
                {
                    "answer_id": ans.answer_id,
                    "question_id": ans.question_id,
                    "question_text": question.question_text if question else None,
                    "question_type": question.question_type if question else None,
                    "max_points": question.points if question else None,
                    "user_answer": ans.user_answer,
                    "points_earned": ans.points_earned,
                    "is_correct": ans.is_correct,
                    "feedback": grade.feedback if grade else None,
                    "is_graded": grade is not None,
                    "graded_at": grade.graded_at.isoformat() if grade else None,
                }
            )

        return {
            "submission_id": attempt.attempt_id,
            "quiz_id": quiz_id,
            "user_id": student_id,
            "submitted_at": attempt.submitted_at.isoformat() if attempt.submitted_at else None,
            "score": attempt.score,
            "total_points": attempt.total_points,
            "percentage": float(attempt.percentage) if attempt.percentage else None,
            "passed": attempt.passed,
            "status": attempt.status,
            "answers": answer_list,
        }

    # ──────────────────────────────────────────────────────────────────────────
    # Internal helpers
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _recalculate_attempt_score(attempt: QuizAttempt, quiz: Quiz) -> None:
        """
        Recompute total score and determine whether the attempt is fully graded.
        Updates attempt in-place (caller must commit).
        """
        all_answers = AttemptAnswer.query.filter_by(attempt_id=attempt.attempt_id).all()
        total_earned = sum(a.points_earned or 0 for a in all_answers)
        all_graded = all(a.points_earned is not None or a.is_correct is not None for a in all_answers)

        questions = Question.query.filter_by(quiz_id=quiz.quiz_id).all()
        total_points = sum(q.points or 0 for q in questions)
        percentage = round((total_earned / total_points * 100), 2) if total_points else 0.0

        attempt.score = total_earned
        attempt.total_points = total_points
        attempt.percentage = percentage

        if all_graded:
            attempt.passed = percentage >= (quiz.passing_score or 70)
            attempt.status = "graded"
