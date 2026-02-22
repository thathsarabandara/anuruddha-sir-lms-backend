"""
Quiz Model
Represents quiz/assessment information and settings
"""

import uuid
from datetime import datetime

from app import db


class Quiz(db.Model):
    """
    Quiz model containing quiz assessment information and configuration.

    Attributes:
        quiz_id: UUID primary key
        course_id: Foreign key to Course
        title: Quiz title (max 255 chars)
        description: Quiz description and instructions
        passing_score: Minimum score to pass (default: 70)
        duration_minutes: Quiz time limit in minutes
        max_attempts: Maximum number of attempts allowed (default: 1)
        show_answers_after: ENUM(submission, later, never) - when to show answers
        shuffle_questions: Randomize question order per attempt
        shuffle_answers: Randomize answer options per attempt
        available_from: Quiz start availability timestamp
        available_until: Quiz end availability timestamp
        created_at: Quiz creation timestamp
        updated_at: Last modification timestamp
    """

    __tablename__ = "quizzes"

    # Primary Key
    quiz_id = db.Column(
        db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False
    )

    # Foreign Key
    course_id = db.Column(
        db.String(36),
        db.ForeignKey("courses.course_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Quiz Information
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)

    # Quiz Configuration
    passing_score = db.Column(db.Integer, default=70, nullable=False)
    duration_minutes = db.Column(db.Integer, nullable=True)
    max_attempts = db.Column(db.Integer, default=1, nullable=False)

    # Display Settings
    show_answers_after = db.Column(
        db.Enum("submission", "later", "never"), default="submission", nullable=False
    )
    shuffle_questions = db.Column(db.Boolean, default=False, nullable=False)
    shuffle_answers = db.Column(db.Boolean, default=False, nullable=False)

    # Availability
    available_from = db.Column(db.DateTime, nullable=True)
    available_until = db.Column(db.DateTime, nullable=True, index=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    questions = db.relationship(
        "Question", backref="quiz", lazy="dynamic", cascade="all, delete-orphan"
    )
    attempts = db.relationship(
        "QuizAttempt", backref="quiz", lazy="dynamic", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Quiz {self.quiz_id} - {self.title}>"

    def to_dict(self):
        """Convert quiz to dictionary for JSON serialization."""
        return {
            "quiz_id": self.quiz_id,
            "course_id": self.course_id,
            "title": self.title,
            "description": self.description,
            "passing_score": self.passing_score,
            "duration_minutes": self.duration_minutes,
            "max_attempts": self.max_attempts,
            "show_answers_after": self.show_answers_after,
            "shuffle_questions": self.shuffle_questions,
            "shuffle_answers": self.shuffle_answers,
            "available_from": self.available_from.isoformat() if self.available_from else None,
            "available_until": self.available_until.isoformat() if self.available_until else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
