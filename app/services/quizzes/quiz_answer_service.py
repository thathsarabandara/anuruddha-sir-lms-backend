"""
Quiz Answer Service
Handles saving individual answers during a quiz attempt and final quiz submission.
Performs automatic grading for objective question types.
"""

import logging
import uuid
from datetime import datetime, timezone

from app import db
from app.exceptions import AuthorizationError, ConflictError, ResourceNotFoundError, ValidationError
from app.models.quizzes.attempt_answer import AttemptAnswer
from app.models.quizzes.question import Question
from app.models.quizzes.question_option import QuestionOption
from app.models.quizzes.quiz import Quiz
from app.models.quizzes.quiz_attempt import QuizAttempt
from app.services.base_service import BaseService

logger = logging.getLogger(__name__)

# Question types graded automatically
AUTO_GRADED_TYPES = ("multiple_choice", "multiple_answer", "fill_blank", "matching")


class QuizAnswerService(BaseService):
    """Service for saving answers and submitting quizzes."""

    # ──────────────────────────────────────────────────────────────────────────
    # Save / Upsert Answer
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def save_answer(
        attempt_id: str,
        user_id: str,
        question_id: str,
        answer,
        time_taken_seconds: int = None,
    ) -> dict:
        """
        Save (or update) a student's answer for one question within an attempt.
        Does NOT auto-grade; grading happens at submission time.

        Args:
            attempt_id: Attempt UUID
            user_id: Student's user ID (ownership check)
            question_id: Question UUID
            answer: Option UUID string (MCQ) or text string (short/essay/fill)
            time_taken_seconds: Optional time spent on this question

        Returns:
            dict: Saved answer metadata

        Raises:
            ResourceNotFoundError: Attempt or question not found
            AuthorizationError: Attempt does not belong to user
            ConflictError: Attempt is no longer in_progress
            ValidationError: Question does not belong to this quiz
        """
        try:
            attempt = QuizAttempt.query.get(attempt_id)
            if not attempt:
                raise ResourceNotFoundError("Attempt not found")

            if attempt.user_id != user_id:
                raise AuthorizationError("This attempt does not belong to you")

            if attempt.status != "in_progress":
                raise ConflictError("Cannot save answers - quiz has already been submitted")

            # Enforce time limit
            quiz = Quiz.query.get(attempt.quiz_id)
            if quiz and quiz.duration_minutes:
                elapsed = (datetime.utcnow() - attempt.started_at).total_seconds() / 60
                if elapsed > quiz.duration_minutes:
                    raise ConflictError("Quiz time limit exceeded. Please submit the quiz.")

            question = Question.query.get(question_id)
            if not question:
                raise ResourceNotFoundError("Question not found")

            if question.quiz_id != attempt.quiz_id:
                raise ValidationError("Question does not belong to this quiz")

            if answer is None:
                raise ValidationError("answer is required")

            # Upsert answer
            existing = AttemptAnswer.query.filter_by(
                attempt_id=attempt_id, question_id=question_id
            ).first()

            now = datetime.utcnow()

            if existing:
                existing.user_answer = str(answer)
                if time_taken_seconds is not None:
                    existing.time_taken_seconds = time_taken_seconds
                existing.answered_at = now
                saved_at = now
            else:
                new_answer = AttemptAnswer(
                    answer_id=str(uuid.uuid4()),
                    attempt_id=attempt_id,
                    question_id=question_id,
                    user_answer=str(answer),
                    time_taken_seconds=time_taken_seconds,
                    answered_at=now,
                )
                db.session.add(new_answer)
                saved_at = now

            db.session.commit()

            return {
                "question_id": question_id,
                "saved_at": saved_at.isoformat(),
            }

        except (ResourceNotFoundError, AuthorizationError, ConflictError, ValidationError):
            db.session.rollback()
            raise
        except Exception as exc:
            db.session.rollback()
            logger.error("Error saving answer for attempt %s: %s", attempt_id, str(exc), exc_info=True)
            raise

    # ──────────────────────────────────────────────────────────────────────────
    # Submit Quiz
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def submit_quiz(attempt_id: str, user_id: str) -> dict:
        """
        Finalize a quiz attempt. Auto-grades objective questions and calculates
        score, percentage, and pass/fail status.

        Args:
            attempt_id: Attempt UUID
            user_id: Student's user ID (ownership check)

        Returns:
            dict: Full submission result with per-question breakdown

        Raises:
            ResourceNotFoundError: Attempt not found
            AuthorizationError: Attempt does not belong to user
            ConflictError: Already submitted
        """
        try:
            attempt = QuizAttempt.query.get(attempt_id)
            if not attempt:
                raise ResourceNotFoundError("Attempt not found")

            if attempt.user_id != user_id:
                raise AuthorizationError("This attempt does not belong to you")

            if attempt.status != "in_progress":
                raise ConflictError("Quiz has already been submitted")

            quiz = Quiz.query.get(attempt.quiz_id)
            if not quiz:
                raise ResourceNotFoundError("Quiz not found")

            submitted_at = datetime.utcnow()

            # Calculate time taken
            time_delta = submitted_at - attempt.started_at
            time_taken_minutes = int(time_delta.total_seconds() / 60)

            # Get all questions and the student's answers
            questions = Question.query.filter_by(quiz_id=attempt.quiz_id).all()
            answers_map = {
                a.question_id: a
                for a in AttemptAnswer.query.filter_by(attempt_id=attempt_id).all()
            }

            total_points = sum(q.points or 0 for q in questions)
            score = 0
            results = []
            has_manual_questions = False

            for q in questions:
                ans = answers_map.get(q.question_id)
                user_answer_text = ans.user_answer if ans else None
                is_correct = None
                points_earned = 0
                correct_answer_text = None

                if q.question_type in AUTO_GRADED_TYPES:
                    is_correct, points_earned, correct_answer_text = QuizAnswerService._auto_grade(
                        q, user_answer_text
                    )
                    score += points_earned
                    if ans:
                        ans.is_correct = is_correct
                        ans.points_earned = points_earned
                else:
                    # Manual grading required (essay / short_answer)
                    has_manual_questions = True
                    if ans:
                        ans.is_correct = None
                        ans.points_earned = None

                results.append(
                    {
                        "question_id": q.question_id,
                        "question_text": q.question_text,
                        "question_type": q.question_type,
                        "user_answer": user_answer_text,
                        "correct_answer": correct_answer_text if quiz.show_answers_after == "submission" else None,
                        "points_earned": points_earned,
                        "explanation": q.explanation if quiz.show_answers_after == "submission" else None,
                    }
                )

            # Percentage and pass status
            percentage = round((score / total_points * 100), 2) if total_points else 0.0
            passed = percentage >= (quiz.passing_score or 70) if not has_manual_questions else None

            # Update attempt record
            attempt.score = score
            attempt.total_points = total_points
            attempt.percentage = percentage
            attempt.passed = passed
            attempt.submitted_at = submitted_at
            attempt.time_taken_minutes = time_taken_minutes
            attempt.status = "submitted" if has_manual_questions else "graded"

            db.session.commit()
            logger.info("Quiz attempt %s submitted by user %s", attempt_id, user_id)

            return {
                "attempt_id": attempt_id,
                "score": score,
                "total_points": total_points,
                "percentage": float(percentage),
                "passed": passed,
                "submitted_at": submitted_at.isoformat(),
                "time_taken_minutes": time_taken_minutes,
                "pending_manual_grading": has_manual_questions,
                "results": results,
            }

        except (ResourceNotFoundError, AuthorizationError, ConflictError):
            db.session.rollback()
            raise
        except Exception as exc:
            db.session.rollback()
            logger.error("Error submitting quiz attempt %s: %s", attempt_id, str(exc), exc_info=True)
            raise

    # ──────────────────────────────────────────────────────────────────────────
    # Auto-grading helpers
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _auto_grade(question: Question, user_answer: str):
        """
        Auto-grade an objective question.

        Returns:
            (is_correct: bool, points_earned: int, correct_answer_text: str)
        """
        options = QuestionOption.query.filter_by(question_id=question.question_id).all()
        correct_options = [o for o in options if o.is_correct]
        correct_ids = {o.option_id for o in correct_options}
        correct_texts = [o.option_text for o in correct_options]
        correct_answer_text = ", ".join(correct_texts)

        if not user_answer:
            return False, 0, correct_answer_text

        if question.question_type == "multiple_choice":
            is_correct = user_answer.strip() in correct_ids
            points = question.points if is_correct else 0
            return is_correct, points, correct_answer_text

        if question.question_type == "multiple_answer":
            # Expect comma-separated option_ids
            submitted = {a.strip() for a in user_answer.split(",") if a.strip()}
            is_correct = submitted == correct_ids
            points = question.points if is_correct else 0
            return is_correct, points, correct_answer_text

        if question.question_type in ("fill_blank", "matching"):
            # Case-insensitive text comparison against correct option texts
            submitted = user_answer.strip().lower()
            is_correct = any(c.option_text.strip().lower() == submitted for c in correct_options)
            points = question.points if is_correct else 0
            return is_correct, points, correct_answer_text

        return None, 0, correct_answer_text
