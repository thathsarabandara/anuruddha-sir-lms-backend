"""
CourseLesson Model
Represents lessons within course sections
"""

from app import db
from datetime import datetime
import uuid


class CourseLesson(db.Model):
    """
    CourseLesson model for individual lessons within a section.
    
    Attributes:
        lesson_id: UUID primary key
        section_id: Foreign key to CourseSection
        course_id: Foreign key to Course
        title: Lesson title (max 255 chars)
        description: Lesson description
        duration_minutes: Estimated lesson duration in minutes
        lesson_order: Ordering of lesson within section
        created_at: Lesson creation timestamp
        updated_at: Last modification timestamp
    """
    
    __tablename__ = 'course_lessons'
    
    # Primary Key
    lesson_id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False
    )
    
    # Foreign Keys
    section_id = db.Column(
        db.String(36),
        db.ForeignKey('course_sections.section_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    course_id = db.Column(
        db.String(36),
        db.ForeignKey('courses.course_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    # Lesson Information
    title = db.Column(
        db.String(255),
        nullable=False
    )
    description = db.Column(
        db.Text,
        nullable=True
    )
    duration_minutes = db.Column(
        db.Integer,
        nullable=True
    )
    lesson_order = db.Column(
        db.Integer,
        nullable=True
    )
    
    # Timestamps
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    # Relationships
    contents = db.relationship(
        'LessonContent',
        backref='lesson',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    
    def __repr__(self):
        return f"<CourseLesson {self.lesson_id} - {self.title}>"
    
    def to_dict(self):
        """Convert lesson to dictionary for JSON serialization."""
        return {
            'lesson_id': self.lesson_id,
            'section_id': self.section_id,
            'course_id': self.course_id,
            'title': self.title,
            'description': self.description,
            'duration_minutes': self.duration_minutes,
            'lesson_order': self.lesson_order,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
