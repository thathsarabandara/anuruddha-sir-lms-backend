"""
Question Service
Handles CRUD operations for quiz questions and their answer options.
"""

import logging
import uuid

from app import db
from app.exceptions import AuthorizationError, ResourceNotFoundError, ValidationError
from app.models.courses.course import Course
from app.models.quizzes.question import Question
from app.models.quizzes.question_option import QuestionOption
from app.models.quizzes.quiz import Quiz
from app.services.health.base_service import BaseService
from app.utils.s3_handler import S3Handler

logger = logging.getLogger(__name__)

VALID_QUESTION_TYPES = ("multiple_choice", "multiple_answer", "short_answer", "essay", "matching", "fill_blank")
VALID_DIFFICULTIES = ("easy", "medium", "hard")
OPTION_TYPES = ("multiple_choice", "multiple_answer", "matching")


class QuestionService(BaseService):
    """Service for quiz question CRUD and option management."""

    # ──────────────────────────────────────────────────────────────────────────
    # Create
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def create_question(
        quiz_id: str,
        user_id: str,
        user_role: str,
        question_type: str,
        question_text: str,
        points: int = 1,
        difficulty: str = "medium",
        category: str = None,
        explanation: str = None,
        question_order: int = None,
        options: list = None,
        image_url: str = None,
    ) -> dict:
        """
        Create a new question (with optional answer options) for a quiz.

        Args:
            quiz_id: Quiz UUID
            user_id: Requesting instructor's user ID
            user_role: Requesting user's role
            question_type: One of VALID_QUESTION_TYPES
            question_text: The question content
            points: Points awarded for correct answer (default 1)
            difficulty: 'easy' | 'medium' | 'hard'
            category: Optional category label
            explanation: Explanation shown after submission
            question_order: Display order within the quiz
            options: List of {option_text, is_correct, option_order} dicts
                     (required for multiple_choice / multiple_answer / matching)
            image_url: Optional URL to question image

        Returns:
            dict: Created question data including options

        Raises:
            ResourceNotFoundError: If quiz not found
            AuthorizationError: If user is not the course instructor
            ValidationError: On invalid field values
        """
        try:
            quiz = QuestionService._get_quiz_with_auth(quiz_id, user_id, user_role)

            # Validation
            if question_type not in VALID_QUESTION_TYPES:
                raise ValidationError(
                    f"question_type must be one of: {', '.join(VALID_QUESTION_TYPES)}"
                )
            if not question_text or not question_text.strip():
                raise ValidationError("question_text is required")
            if difficulty not in VALID_DIFFICULTIES:
                raise ValidationError(f"difficulty must be one of: {', '.join(VALID_DIFFICULTIES)}")
            if points is not None and points < 0:
                raise ValidationError("points must be non-negative")

            if question_type in OPTION_TYPES and not options:
                raise ValidationError(
                    f"options are required for question_type '{question_type}'"
                )

            if question_type == "multiple_choice" and options:
                correct_count = sum(1 for o in options if o.get("is_correct"))
                if correct_count != 1:
                    raise ValidationError("multiple_choice questions must have exactly one correct option")

            if question_type == "multiple_answer" and options:
                correct_count = sum(1 for o in options if o.get("is_correct"))
                if correct_count < 1:
                    raise ValidationError("multiple_answer questions must have at least one correct option")

            question = Question(
                question_id=str(uuid.uuid4()),
                quiz_id=quiz_id,
                question_type=question_type,
                question_text=question_text.strip(),
                points=points if points is not None else 1,
                difficulty=difficulty,
                category=category,
                explanation=explanation,
                question_order=question_order,
                image_url=image_url,
            )
            db.session.add(question)
            db.session.flush()  # get question_id before adding options

            option_dicts = []
            if options:
                for idx, opt in enumerate(options):
                    if not opt.get("option_text"):
                        raise ValidationError("Each option must have option_text")
                    option = QuestionOption(
                        option_id=str(uuid.uuid4()),
                        question_id=question.question_id,
                        option_text=opt["option_text"],
                        is_correct=bool(opt.get("is_correct", False)),
                        option_order=opt.get("option_order", idx + 1),
                    )
                    db.session.add(option)
                    option_dicts.append(option.to_dict())

            db.session.commit()
            logger.info("Question %s created in quiz %s", question.question_id, quiz_id)

            data = question.to_dict()
            data["options"] = option_dicts
            return data

        except (ResourceNotFoundError, AuthorizationError, ValidationError):
            db.session.rollback()
            raise
        except Exception as exc:
            db.session.rollback()
            logger.error("Error creating question in quiz %s: %s", quiz_id, str(exc), exc_info=True)
            raise

    # ──────────────────────────────────────────────────────────────────────────
    # Read
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def get_quiz_questions(quiz_id: str, include_answers: bool = False) -> list:
        """
        Retrieve all questions for a quiz.

        Args:
            quiz_id: Quiz UUID
            include_answers: Whether to include is_correct flag on options
                             (False for students during active quiz)

        Returns:
            list: List of question dicts with their options

        Raises:
            ResourceNotFoundError: If quiz not found
        """
        quiz = Quiz.query.get(quiz_id)
        if not quiz:
            raise ResourceNotFoundError("Quiz not found")

        questions = (
            Question.query.filter_by(quiz_id=quiz_id)
            .order_by(Question.question_order.asc(), Question.created_at.asc())
            .all()
        )

        result = []
        for q in questions:
            q_dict = q.to_dict()
            options = (
                QuestionOption.query.filter_by(question_id=q.question_id)
                .order_by(QuestionOption.option_order.asc())
                .all()
            )

            opt_list = []
            for opt in options:
                o = opt.to_dict()
                if not include_answers:
                    o.pop("is_correct", None)
                opt_list.append(o)

            q_dict["options"] = opt_list
            result.append(q_dict)

        return result

    @staticmethod
    def get_question(question_id: str) -> dict:
        """
        Retrieve a single question with its options.

        Args:
            question_id: Question UUID

        Returns:
            dict: Question data with options (including is_correct)

        Raises:
            ResourceNotFoundError: If question not found
        """
        question = Question.query.get(question_id)
        if not question:
            raise ResourceNotFoundError("Question not found")

        options = (
            QuestionOption.query.filter_by(question_id=question_id)
            .order_by(QuestionOption.option_order.asc())
            .all()
        )
        data = question.to_dict()
        data["options"] = [o.to_dict() for o in options]
        return data

    # ──────────────────────────────────────────────────────────────────────────
    # Update
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def update_question(question_id: str, user_id: str, user_role: str, **kwargs) -> dict:
        """
        Update a question and optionally replace its options.

        Args:
            question_id: Question UUID
            user_id: Requesting instructor's user ID
            user_role: Requesting user's role
            **kwargs: Updatable fields including optional 'options' list

        Returns:
            dict: Updated question data

        Raises:
            ResourceNotFoundError: If question not found
            AuthorizationError: If user is not the course instructor
            ValidationError: On invalid field values
        """
        try:
            question = Question.query.get(question_id)
            if not question:
                raise ResourceNotFoundError("Question not found")

            QuestionService._get_quiz_with_auth(question.quiz_id, user_id, user_role)

            allowed_fields = (
                "question_type", "question_text", "points",
                "difficulty", "category", "explanation", "question_order", "image_url",
            )
            for field, value in kwargs.items():
                if field in allowed_fields:
                    setattr(question, field, value)

            # Replace options if provided
            new_options = kwargs.get("options")
            if new_options is not None:
                QuestionOption.query.filter_by(question_id=question_id).delete()
                for idx, opt in enumerate(new_options):
                    if not opt.get("option_text"):
                        raise ValidationError("Each option must have option_text")
                    option = QuestionOption(
                        option_id=str(uuid.uuid4()),
                        question_id=question_id,
                        option_text=opt["option_text"],
                        is_correct=bool(opt.get("is_correct", False)),
                        option_order=opt.get("option_order", idx + 1),
                    )
                    db.session.add(option)

            db.session.commit()
            logger.info("Question %s updated by user %s", question_id, user_id)
            return QuestionService.get_question(question_id)

        except (ResourceNotFoundError, AuthorizationError, ValidationError):
            db.session.rollback()
            raise
        except Exception as exc:
            db.session.rollback()
            logger.error("Error updating question %s: %s", question_id, str(exc), exc_info=True)
            raise

    @staticmethod
    def update_question_order(question_id: str, user_id: str, user_role: str, question_order: int) -> dict:
        """Update the display order of a question within its quiz."""
        try:
            if question_order < 0:
                raise ValidationError("question_order must be a positive integer")

            question = Question.query.get(question_id)
            if not question:
                raise ResourceNotFoundError("Question not found")

            QuestionService._get_quiz_with_auth(question.quiz_id, user_id, user_role)

            question.question_order = question_order
            db.session.commit()
            logger.info("Question %s order updated to %s by user %s", question_id, question_order, user_id)
            return QuestionService.get_question(question_id)
        except (ResourceNotFoundError, AuthorizationError, ValidationError):
            db.session.rollback()
            raise
        except Exception as exc:
            db.session.rollback()
            logger.error("Error updating order for question %s: %s", question_id, str(exc), exc_info=True)
            raise

    # ──────────────────────────────────────────────────────────────────────────
    # Delete
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def delete_question(question_id: str, user_id: str, user_role: str) -> bool:
        """
        Delete a question (cascades to its options and attempt answers).

        Args:
            question_id: Question UUID
            user_id: Requesting instructor's user ID
            user_role: Requesting user's role

        Returns:
            bool: True on success

        Raises:
            ResourceNotFoundError: If question not found
            AuthorizationError: If user is not the course instructor
        """
        try:
            question = Question.query.get(question_id)
            if not question:
                raise ResourceNotFoundError("Question not found")

            QuestionService._get_quiz_with_auth(question.quiz_id, user_id, user_role)

            db.session.delete(question)
            db.session.commit()
            logger.info("Question %s deleted by user %s", question_id, user_id)
            return True

        except (ResourceNotFoundError, AuthorizationError):
            db.session.rollback()
            raise
        except Exception as exc:
            db.session.rollback()
            logger.error("Error deleting question %s: %s", question_id, str(exc), exc_info=True)
            raise

    # ──────────────────────────────────────────────────────────────────────────
    # Image Upload
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def upload_question_image(file_obj, quiz_id: str, question_id: str) -> str:
        """
        Upload an image for a question to S3.

        Args:
            file_obj: Flask FileStorage object
            quiz_id: Quiz UUID
            question_id: Question UUID

        Returns:
            str: S3 URL of the uploaded image

        Raises:
            Exception: If upload fails or S3 is not configured
        """
        try:
            if not S3Handler.is_configured():
                raise Exception("S3 is not configured. Image upload is not available.")

            s3_handler = S3Handler()
            
            # Generate filename using quiz_id and question_id
            filename = file_obj.filename
            extension = filename.rsplit(".", 1)[1].lower() if "." in filename else "jpg"
            
            # S3 key structure: quizzes/{quiz_id}/questions/{question_id}/{filename}
            s3_filename = f"{question_id}.{extension}"

            # Create a new FileStorage object with the new filename
            file_obj.filename = s3_filename

            # Upload using S3Handler (modify to use custom path)
            s3_key = f"quizzes/{quiz_id}/questions/{s3_filename}"
            
            # Upload directly to S3
            file_content = file_obj.read()
            file_obj.seek(0)
            
            s3_handler.s3_client.put_object(
                Bucket=s3_handler.bucket_name,
                Key=s3_key,
                Body=file_content,
                ContentType=file_obj.content_type or "image/jpeg",
                ACL="public-read",
            )

            # Generate S3 URL
            from flask import current_app
            s3_url = f"https://{s3_handler.bucket_name}.s3.{current_app.config.get('AWS_S3_REGION', 'us-east-1')}.amazonaws.com/{s3_key}"

            logger.info(f"Question image uploaded to S3: {s3_key}")
            return s3_url

        except Exception as e:
            logger.error(f"Error uploading question image: {str(e)}", exc_info=True)
            raise

    # ──────────────────────────────────────────────────────────────────────────
    # Internal helpers
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _get_quiz_with_auth(quiz_id: str, user_id: str, user_role: str) -> Quiz:
        """Load quiz and verify the requesting user is the course instructor (or admin)."""
        quiz = Quiz.query.get(quiz_id)
        if not quiz:
            raise ResourceNotFoundError("Quiz not found")

        if user_role != "superadmin" and quiz.user_id != user_id:
            raise AuthorizationError("Only the course instructor can manage questions")

        return quiz
