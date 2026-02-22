"""
CourseEnrollmentKey Model
Represents enrollment keys for bulk student enrollment
"""

from app import db
from datetime import datetime
import uuid


class CourseEnrollmentKey(db.Model):
    """
    CourseEnrollmentKey model for managing enrollment keys for bulk student access.
    
    Attributes:
        key_id: UUID primary key
        course_id: Foreign key to Course
        created_by: Foreign key to User (creator admin/teacher)
        key: Unique enrollment key string (max 50 chars)
        max_enrollments: Maximum number of enrollments allowed
        current_usage: Current number of enrollments used
        description: Key description
        expiry_date: Date when key expires (indexed)
        is_active: Whether key is currently active (indexed)
        created_at: Key creation timestamp
        deactivated_at: Key deactivation timestamp
    """
    
    __tablename__ = 'course_enrollment_keys'
    
    # Primary Key
    key_id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False
    )
    
    # Foreign Keys
    course_id = db.Column(
        db.String(36),
        db.ForeignKey('courses.course_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    created_by = db.Column(
        db.String(36),
        db.ForeignKey('users.user_id', ondelete='RESTRICT'),
        nullable=False,
        index=True
    )
    
    # Key Information
    key = db.Column(
        db.String(50),
        unique=True,
        nullable=False,
        index=True
    )
    
    # Enrollment Limits
    max_enrollments = db.Column(
        db.Integer,
        nullable=False
    )
    current_usage = db.Column(
        db.Integer,
        default=0,
        nullable=False
    )
    
    # Additional Settings
    description = db.Column(
        db.Text,
        nullable=True
    )
    expiry_date = db.Column(
        db.Date,
        nullable=True,
        index=True
    )
    is_active = db.Column(
        db.Boolean,
        default=True,
        nullable=False,
        index=True
    )
    
    # Timestamps
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    deactivated_at = db.Column(
        db.DateTime,
        nullable=True
    )
    
    # Relationships
    enrollments = db.relationship(
        'CourseEnrollment',
        backref='key',
        lazy='dynamic'
    )
    
    def __repr__(self):
        return f"<CourseEnrollmentKey {self.key_id} - {self.key}>"
    
    def to_dict(self):
        """Convert key to dictionary for JSON serialization."""
        return {
            'key_id': self.key_id,
            'course_id': self.course_id,
            'created_by': self.created_by,
            'key': self.key,
            'max_enrollments': self.max_enrollments,
            'current_usage': self.current_usage,
            'description': self.description,
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'deactivated_at': self.deactivated_at.isoformat() if self.deactivated_at else None,
        }
