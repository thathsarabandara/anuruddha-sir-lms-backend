"""
QuizAttempt Model
Represents a student's quiz attempt/submission
"""

import uuid
from datetime import datetime

from app import db


class QuizAttempt(db.Model):
    """
    QuizAttempt model for tracking individual student quiz attempts.

    Attributes:
        attempt_id: UUID primary key
        quiz_id: Foreign key to Quiz
        user_id: Foreign key to User (student)
        score: Points earned (nullable until graded)
        total_points: Total possible points
        percentage: Score percentage (nullable until graded)
        passed: Whether student passed (nullable until graded)
        started_at: Attempt start timestamp
        submitted_at: Attempt submission timestamp
        time_taken_minutes: Time spent on quiz
        ip_address: Student IP address
        status: ENUM(in_progress, submitted, graded) attempt status
    """

    __tablename__ = "quiz_attempts"

    # Primary Key
    attempt_id = db.Column(
        db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False
    )

    # Foreign Keys
    quiz_id = db.Column(
        db.String(36),
        db.ForeignKey("quizzes.quiz_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = db.Column(
        db.String(36),
        db.ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Attempt Results
    score = db.Column(db.Integer, nullable=True)
    total_points = db.Column(db.Integer, nullable=True)
    percentage = db.Column(db.Numeric(5, 2), nullable=True)
    passed = db.Column(db.Boolean, nullable=True)

    # Timing
    started_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    submitted_at = db.Column(db.DateTime, nullable=True, index=True)
    time_taken_minutes = db.Column(db.Integer, nullable=True)

    # Session Information
    ip_address = db.Column(db.String(45), nullable=True)
    status = db.Column(
        db.Enum("in_progress", "submitted", "graded"), default="in_progress", nullable=False
    )

    # Relationships
    answers = db.relationship(
        "AttemptAnswer", backref="attempt", lazy="dynamic", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<QuizAttempt {self.attempt_id} - {self.user_id}>"

    def to_dict(self):
        """Convert attempt to dictionary for JSON serialization."""
        return {
            "attempt_id": self.attempt_id,
            "quiz_id": self.quiz_id,
            "user_id": self.user_id,
            "score": self.score,
            "total_points": self.total_points,
            "percentage": float(self.percentage) if self.percentage else None,
            "passed": self.passed,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "submitted_at": self.submitted_at.isoformat() if self.submitted_at else None,
            "time_taken_minutes": self.time_taken_minutes,
            "ip_address": self.ip_address,
            "status": self.status,
        }
