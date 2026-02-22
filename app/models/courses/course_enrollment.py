"""
CourseEnrollment Model
Represents student enrollment in courses
"""

import uuid
from datetime import datetime

from app import db


class CourseEnrollment(db.Model):
    """
    CourseEnrollment model for managing student enrollments in courses.

    Attributes:
        enrollment_id: UUID primary key
        course_id: Foreign key to Course
        user_id: Foreign key to User (student)
        enrollment_method: ENUM(payment, enrollment_key) enrollment method
        key_id: Foreign key to CourseEnrollmentKey (if key-based enrollment)
        progress: Completion percentage (0-100)
        status: ENUM(enrolled, in_progress, completed, dropped) enrollment status
        enrolled_at: Enrollment timestamp
        completed_at: Completion timestamp (if completed)
        last_accessed: Last access timestamp
        total_time_spent_minutes: Total study time in minutes
    """

    __tablename__ = "course_enrollments"

    # Primary Key
    enrollment_id = db.Column(
        db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False
    )

    # Foreign Keys
    course_id = db.Column(
        db.String(36),
        db.ForeignKey("courses.course_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = db.Column(
        db.String(36),
        db.ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    key_id = db.Column(db.String(36), db.ForeignKey("course_enrollment_keys.key_id"), nullable=True)

    # Enrollment Information
    enrollment_method = db.Column(
        db.Enum("payment", "enrollment_key"), default="payment", nullable=False, index=True
    )
    progress = db.Column(db.Integer, default=0, nullable=False)
    status = db.Column(
        db.Enum("enrolled", "in_progress", "completed", "dropped"),
        default="enrolled",
        nullable=False,
        index=True,
    )

    # Enrollment Timestamps
    enrolled_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    completed_at = db.Column(db.DateTime, nullable=True)
    last_accessed = db.Column(db.DateTime, nullable=True)

    # Learning Time
    total_time_spent_minutes = db.Column(db.Integer, default=0, nullable=False)

    __table_args__ = (db.UniqueConstraint("user_id", "course_id", name="unique_user_course"),)

    def __repr__(self):
        return f"<CourseEnrollment {self.enrollment_id} - {self.user_id}>"

    def to_dict(self):
        """Convert enrollment to dictionary for JSON serialization."""
        return {
            "enrollment_id": self.enrollment_id,
            "course_id": self.course_id,
            "user_id": self.user_id,
            "enrollment_method": self.enrollment_method,
            "key_id": self.key_id,
            "progress": self.progress,
            "status": self.status,
            "enrolled_at": self.enrolled_at.isoformat() if self.enrolled_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None,
            "total_time_spent_minutes": self.total_time_spent_minutes,
        }
