"""
Quiz Analytics Service
Provides quiz-level and question-level performance statistics for instructors.
"""

import logging

from sqlalchemy import func

from app import db
from app.exceptions import AuthorizationError, ResourceNotFoundError
from app.models.courses.course import Course
from app.models.quizzes.attempt_answer import AttemptAnswer
from app.models.quizzes.question import Question
from app.models.quizzes.quiz import Quiz
from app.models.quizzes.quiz_attempt import QuizAttempt
from app.services.base_service import BaseService

logger = logging.getLogger(__name__)


class QuizAnalyticsService(BaseService):
    """Service for quiz and question-level analytics."""

    # ──────────────────────────────────────────────────────────────────────────
    # Quiz-level statistics
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def get_quiz_statistics(quiz_id: str, user_id: str, user_role: str) -> dict:
        """
        Return overall quiz performance statistics for an instructor.

        Includes:
        - total_attempts, average_score, pass_rate, average_time_minutes
        - Per-question correct percentage and average time

        Args:
            quiz_id: Quiz UUID
            user_id: Requesting instructor's user ID
            user_role: Requesting user's role

        Returns:
            dict: Quiz statistics data

        Raises:
            ResourceNotFoundError: Quiz not found
            AuthorizationError: Not the course instructor/admin
        """
        quiz = Quiz.query.get(quiz_id)
        if not quiz:
            raise ResourceNotFoundError("Quiz not found")

        if user_role != "admin":
            course = Course.query.get(quiz.course_id)
            if not course or course.instructor_id != user_id:
                raise AuthorizationError("Only the course instructor can view quiz statistics")

        # Aggregate submitted/graded attempts
        attempts = QuizAttempt.query.filter(
            QuizAttempt.quiz_id == quiz_id,
            QuizAttempt.status.in_(["submitted", "graded"]),
        ).all()

        total_attempts = len(attempts)

        if total_attempts == 0:
            return {
                "quiz_id": quiz_id,
                "total_attempts": 0,
                "average_score": 0,
                "pass_rate": 0,
                "average_time_minutes": 0,
                "questions": [],
            }

        average_score = round(
            sum(float(a.percentage or 0) for a in attempts) / total_attempts, 2
        )
        pass_rate = round(
            sum(1 for a in attempts if a.passed) / total_attempts * 100, 2
        )
        average_time = round(
            sum(a.time_taken_minutes or 0 for a in attempts) / total_attempts, 1
        )

        # Per-question stats
        questions = Question.query.filter_by(quiz_id=quiz_id).all()
        question_stats = []
        for q in questions:
            q_answers = AttemptAnswer.query.filter_by(question_id=q.question_id).all()
            answered_count = len(q_answers)

            if answered_count == 0:
                question_stats.append(
                    {
                        "question_id": q.question_id,
                        "question_text": q.question_text,
                        "total_answers": 0,
                        "correct_answers": 0,
                        "correct_percentage": 0,
                        "average_time_seconds": 0,
                    }
                )
                continue

            correct_count = sum(1 for a in q_answers if a.is_correct)
            correct_pct = round(correct_count / answered_count * 100, 2)
            avg_time = round(
                sum(a.time_taken_seconds or 0 for a in q_answers) / answered_count, 1
            )

            question_stats.append(
                {
                    "question_id": q.question_id,
                    "question_text": q.question_text,
                    "total_answers": answered_count,
                    "correct_answers": correct_count,
                    "correct_percentage": correct_pct,
                    "average_time_seconds": avg_time,
                }
            )

        return {
            "quiz_id": quiz_id,
            "total_attempts": total_attempts,
            "average_score": average_score,
            "pass_rate": pass_rate,
            "average_time_minutes": average_time,
            "questions": question_stats,
        }

    # ──────────────────────────────────────────────────────────────────────────
    # Question-level analytics
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def get_question_analytics(question_id: str, user_id: str, user_role: str) -> dict:
        """
        Return detailed analytics for a single question.

        Includes:
        - total_attempts, correct_attempts, correct_percentage
        - average_time_seconds
        - Discrimination index (point-biserial approximation)

        Args:
            question_id: Question UUID
            user_id: Requesting instructor's user ID
            user_role: Requesting user's role

        Returns:
            dict: Question analytics

        Raises:
            ResourceNotFoundError: Question not found
            AuthorizationError: Not the course instructor/admin
        """
        question = Question.query.get(question_id)
        if not question:
            raise ResourceNotFoundError("Question not found")

        quiz = Quiz.query.get(question.quiz_id)
        if not quiz:
            raise ResourceNotFoundError("Quiz not found")

        if user_role != "admin":
            course = Course.query.get(quiz.course_id)
            if not course or course.instructor_id != user_id:
                raise AuthorizationError("Only the course instructor can view question analytics")

        answers = AttemptAnswer.query.filter_by(question_id=question_id).all()
        total = len(answers)

        if total == 0:
            return {
                "question_id": question_id,
                "total_attempts": 0,
                "correct_attempts": 0,
                "correct_percentage": 0,
                "average_time_seconds": 0,
                "difficulty_rating": 0,
                "discrimination_index": 0,
            }

        correct_answers = [a for a in answers if a.is_correct]
        correct_count = len(correct_answers)
        correct_pct = round(correct_count / total * 100, 2)
        avg_time = round(sum(a.time_taken_seconds or 0 for a in answers) / total, 1)

        # Difficulty rating: 0-5 scale (5 = hardest) inversely proportional to correct%
        difficulty_rating = round(5 * (1 - correct_pct / 100), 2)

        # Discrimination index: correlation between correct answer and quiz score
        discrimination_index = QuizAnalyticsService._compute_discrimination(question_id, answers)

        return {
            "question_id": question_id,
            "total_attempts": total,
            "correct_attempts": correct_count,
            "correct_percentage": correct_pct,
            "average_time_seconds": avg_time,
            "difficulty_rating": difficulty_rating,
            "discrimination_index": discrimination_index,
        }

    # ──────────────────────────────────────────────────────────────────────────
    # Internal helpers
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _compute_discrimination(question_id: str, answers: list) -> float:
        """
        Approximate point-biserial discrimination index.
        Returns a value in [0, 1] indicating how well the question differentiates
        high and low scorers (0 = no discrimination, 1 = perfect).
        """
        try:
            if len(answers) < 4:
                return 0.0

            attempt_ids = [a.attempt_id for a in answers]
            attempt_scores = {
                a.attempt_id: float(a.percentage or 0)
                for a in QuizAttempt.query.filter(QuizAttempt.attempt_id.in_(attempt_ids)).all()
            }

            correct_scores = [
                attempt_scores.get(a.attempt_id, 0) for a in answers if a.is_correct
            ]
            incorrect_scores = [
                attempt_scores.get(a.attempt_id, 0) for a in answers if not a.is_correct
            ]

            if not correct_scores or not incorrect_scores:
                return 0.0

            mean_correct = sum(correct_scores) / len(correct_scores)
            mean_incorrect = sum(incorrect_scores) / len(incorrect_scores)

            # Simple upper-lower discrimination index
            all_scores = list(attempt_scores.values())
            all_scores.sort()
            n = len(all_scores)
            upper_cut = all_scores[int(n * 0.67)] if n >= 3 else all_scores[-1]
            lower_cut = all_scores[int(n * 0.33)] if n >= 3 else all_scores[0]

            upper_group = [a for a in answers if attempt_scores.get(a.attempt_id, 0) >= upper_cut]
            lower_group = [a for a in answers if attempt_scores.get(a.attempt_id, 0) <= lower_cut]

            if not upper_group or not lower_group:
                return round((mean_correct - mean_incorrect) / 100, 2)

            p_upper = sum(1 for a in upper_group if a.is_correct) / len(upper_group)
            p_lower = sum(1 for a in lower_group if a.is_correct) / len(lower_group)

            return round(p_upper - p_lower, 2)

        except Exception:
            return 0.0
