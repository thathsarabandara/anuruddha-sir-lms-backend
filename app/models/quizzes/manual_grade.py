"""
ManualGrade Model
Represents manual grading for essay/short answer questions
"""

import uuid
from datetime import datetime

from app import db


class ManualGrade(db.Model):
    """
    ManualGrade model for instructor manual grading of essay/short answer questions.

    Attributes:
        grade_id: UUID primary key
        answer_id: Foreign key to AttemptAnswer
        graded_by: Foreign key to User (instructor/grader)
        points_awarded: Points given by instructor
        feedback: Grading feedback/comments
        graded_at: Timestamp when answer was graded
    """

    __tablename__ = "manual_grades"

    # Primary Key
    grade_id = db.Column(
        db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False
    )

    # Foreign Keys
    answer_id = db.Column(
        db.String(36),
        db.ForeignKey("attempt_answers.answer_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    graded_by = db.Column(db.String(36), db.ForeignKey("users.user_id"), nullable=False, index=True)

    # Grading Information
    points_awarded = db.Column(db.Integer, nullable=True)
    feedback = db.Column(db.Text, nullable=True)

    # Timestamps
    graded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<ManualGrade {self.grade_id} - {self.answer_id}>"

    def to_dict(self):
        """Convert grade to dictionary for JSON serialization."""
        return {
            "grade_id": self.grade_id,
            "answer_id": self.answer_id,
            "graded_by": self.graded_by,
            "points_awarded": self.points_awarded,
            "feedback": self.feedback,
            "graded_at": self.graded_at.isoformat() if self.graded_at else None,
        }
