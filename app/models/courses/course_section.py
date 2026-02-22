"""
CourseSection Model
Represents sections that group lessons within a course
"""

import uuid
from datetime import datetime

from app import db


class CourseSection(db.Model):
    """
    CourseSection model for organizing lessons into course sections.

    Attributes:
        section_id: UUID primary key
        course_id: Foreign key to Course
        title: Section title (max 255 chars)
        description: Section description
        section_order: Ordering of section within course
        created_at: Section creation timestamp
        updated_at: Last modification timestamp
    """

    __tablename__ = "course_sections"

    # Primary Key
    section_id = db.Column(
        db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False
    )

    # Foreign Key
    course_id = db.Column(
        db.String(36),
        db.ForeignKey("courses.course_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Section Information
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    section_order = db.Column(db.Integer, nullable=True, index=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    lessons = db.relationship(
        "CourseLesson", backref="section", lazy="dynamic", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<CourseSection {self.section_id} - {self.title}>"

    def to_dict(self):
        """Convert section to dictionary for JSON serialization."""
        return {
            "section_id": self.section_id,
            "course_id": self.course_id,
            "title": self.title,
            "description": self.description,
            "section_order": self.section_order,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
