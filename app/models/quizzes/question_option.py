"""
QuestionOption Model
Represents answer options for multiple choice/multiple answer questions
"""

import uuid
from datetime import datetime

from app import db


class QuestionOption(db.Model):
    """
    QuestionOption model for answer options in multiple-choice questions.

    Attributes:
        option_id: UUID primary key
        question_id: Foreign key to Question
        option_text: Text of the answer option
        is_correct: Whether this option is the correct answer
        option_order: Ordering of option within question
        created_at: Option creation timestamp
    """

    __tablename__ = "question_options"

    # Primary Key
    option_id = db.Column(
        db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False
    )

    # Foreign Key
    question_id = db.Column(
        db.String(36),
        db.ForeignKey("questions.question_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Option Content
    option_text = db.Column(db.Text, nullable=False)
    is_correct = db.Column(db.Boolean, default=False, nullable=False)

    # Ordering
    option_order = db.Column(db.Integer, nullable=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<QuestionOption {self.option_id} - {self.option_text[:50]}>"

    def to_dict(self):
        """Convert option to dictionary for JSON serialization."""
        return {
            "option_id": self.option_id,
            "question_id": self.question_id,
            "option_text": self.option_text,
            "is_correct": self.is_correct,
            "option_order": self.option_order,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
