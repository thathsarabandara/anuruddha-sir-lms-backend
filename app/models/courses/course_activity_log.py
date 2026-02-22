"""
CourseActivityLog Model
Comprehensive activity tracking for courses
"""

from app import db
from datetime import datetime
import uuid
import json


class CourseActivityLog(db.Model):
    """
    CourseActivityLog model for comprehensive course activity audit trail.
    
    Attributes:
        activity_id: UUID primary key
        course_id: Foreign key to Course
        lesson_id: Foreign key to CourseLesson (optional)
        content_id: Foreign key to LessonContent (optional)
        user_id: Foreign key to User
        activity_type: Type of activity (max 50 chars)
        activity_description: Description of activity
        device_type: Device type (desktop, mobile, tablet)
        browser: Browser user agent
        ip_address: IP address (IPv4/IPv6)
        session_id: Session identifier
        metadata: JSON metadata with activity-specific data
        timestamp: Activity timestamp (indexed)
        created_at: Creation timestamp
    """
    
    __tablename__ = 'course_activity_log'
    
    # Primary Key
    activity_id = db.Column(
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
    lesson_id = db.Column(
        db.String(36),
        db.ForeignKey('course_lessons.lesson_id', ondelete='SET NULL'),
        nullable=True
    )
    content_id = db.Column(
        db.String(36),
        db.ForeignKey('lesson_contents.content_id', ondelete='SET NULL'),
        nullable=True
    )
    user_id = db.Column(
        db.String(36),
        db.ForeignKey('users.user_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    # Activity Information
    activity_type = db.Column(
        db.String(50),
        nullable=False,
        index=True
    )
    activity_description = db.Column(
        db.Text,
        nullable=True
    )
    
    # Device and Network Information
    device_type = db.Column(
        db.String(50),
        nullable=True
    )
    browser = db.Column(
        db.String(100),
        nullable=True
    )
    ip_address = db.Column(
        db.String(45),
        nullable=True
    )
    session_id = db.Column(
        db.String(36),
        nullable=True
    )
    
    # Metadata
    meta_data = db.Column(
        db.Text,
        nullable=True
    )
    
    # Timestamps
    timestamp = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    
    def get_metadata(self):
        """Safely parse JSON metadata."""
        if not self.meta_data:
            return {}
        try:
            return json.loads(self.meta_data)
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def set_metadata(self, data):
        """Serialize metadata to JSON."""
        self.meta_data = json.dumps(data) if data else None
    
    def __repr__(self):
        return f"<CourseActivityLog {self.activity_id} - {self.activity_type}>"
    
    def to_dict(self):
        """Convert activity log to dictionary for JSON serialization."""
        return {
            'activity_id': self.activity_id,
            'course_id': self.course_id,
            'lesson_id': self.lesson_id,
            'content_id': self.content_id,
            'user_id': self.user_id,
            'activity_type': self.activity_type,
            'activity_description': self.activity_description,
            'device_type': self.device_type,
            'browser': self.browser,
            'ip_address': self.ip_address,
            'session_id': self.session_id,
            'metadata': self.get_metadata(),
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
