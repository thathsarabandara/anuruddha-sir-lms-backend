"""
Quiz-Course Association Model
Represents the many-to-many relationship between quizzes and courses.
Allows one quiz to be assigned to multiple courses.
"""

import uuid
from datetime import datetime

from app import db


class QuizCourse(db.Model):
    """
    Junction table for many-to-many relationship between Quiz and Course.
    
    Attributes:
        quiz_course_id: UUID primary key
        quiz_id: Foreign key to Quiz
        course_id: Foreign key to Course
        assigned_at: Timestamp when quiz was assigned to course
    """

    __tablename__ = "quiz_courses"

    # Primary Key
    quiz_course_id = db.Column(
        db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False
    )

    # Foreign Keys
    quiz_id = db.Column(
        db.String(36), db.ForeignKey("quizzes.quiz_id", ondelete="CASCADE"), nullable=False
    )
    course_id = db.Column(
        db.String(36), db.ForeignKey("courses.course_id", ondelete="CASCADE"), nullable=False
    )

    # Timestamps
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Constraints
    __table_args__ = (db.UniqueConstraint("quiz_id", "course_id", name="uq_quiz_course"),)

    def __repr__(self):
        return f"<QuizCourse {self.quiz_id} - {self.course_id}>"

    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            "quiz_course_id": self.quiz_course_id,
            "quiz_id": self.quiz_id,
            "course_id": self.course_id,
            "assigned_at": self.assigned_at.isoformat() if self.assigned_at else None,
        }
