"""
LessonContent Model
Represents multiple content types per lesson (video, zoom, text, pdf, quiz)
"""

from app import db
from datetime import datetime
import uuid


class LessonContent(db.Model):
    """
    LessonContent model for multiple content items per lesson supporting various types.
    
    Content Types:
        - video: Video content with streaming metadata
        - zoom_live: Live Zoom class sessions
        - text: Text content and rich text
        - pdf: PDF document files
        - quiz: Quiz content linked to quiz table
    
    Attributes:
        content_id: UUID primary key
        lesson_id: Foreign key to CourseLesson
        course_id: Foreign key to Course
        content_type: ENUM(video, zoom_live, text, pdf, quiz)
        title: Content title (max 255 chars)
        description: Content description
        content_order: Ordering within lesson
        
        Video fields:
            video_url, preview_url, thumbnail_url, video_duration_minutes,
            video_file_size_bytes, video_quality_available
        
        Zoom fields:
            zoom_link, zoom_meeting_id, zoom_password, scheduled_date,
            scheduled_duration_minutes, is_recorded, recording_url
        
        Text/PDF fields:
            text_content, pdf_file_url, pdf_file_size_bytes
        
        Quiz fields:
            quiz_id, passing_score, is_mandatory
        
        Timestamps:
            created_at, updated_at
    """
    
    __tablename__ = 'lesson_contents'
    
    # Primary Key
    content_id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False
    )
    
    # Foreign Keys
    lesson_id = db.Column(
        db.String(36),
        db.ForeignKey('course_lessons.lesson_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    course_id = db.Column(
        db.String(36),
        db.ForeignKey('courses.course_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    # Content Type and Ordering
    content_type = db.Column(
        db.Enum('video', 'zoom_live', 'text', 'pdf', 'quiz'),
        nullable=False,
        index=True
    )
    content_order = db.Column(
        db.Integer,
        nullable=True
    )
    
    # Content Basic Info
    title = db.Column(
        db.String(255),
        nullable=False
    )
    description = db.Column(
        db.Text,
        nullable=True
    )
    
    # Video Content Fields
    video_url = db.Column(
        db.String(500),
        nullable=True
    )
    preview_url = db.Column(
        db.String(500),
        nullable=True
    )
    thumbnail_url = db.Column(
        db.Text,
        nullable=True
    )
    video_duration_minutes = db.Column(
        db.Integer,
        nullable=True
    )
    video_file_size_bytes = db.Column(
        db.BigInteger,
        nullable=True
    )
    video_quality_available = db.Column(
        db.String(100),
        nullable=True
    )
    
    # Zoom Live Class Fields
    zoom_link = db.Column(
        db.String(500),
        nullable=True
    )
    zoom_meeting_id = db.Column(
        db.String(100),
        nullable=True
    )
    zoom_password = db.Column(
        db.String(100),
        nullable=True
    )
    scheduled_date = db.Column(
        db.DateTime,
        nullable=True
    )
    scheduled_duration_minutes = db.Column(
        db.Integer,
        nullable=True
    )
    is_recorded = db.Column(
        db.Boolean,
        default=False,
        nullable=True
    )
    recording_url = db.Column(
        db.String(500),
        nullable=True
    )
    
    # Text/PDF Content Fields
    text_content = db.Column(
        db.Text,
        nullable=True
    )
    pdf_file_url = db.Column(
        db.String(500),
        nullable=True
    )
    pdf_file_size_bytes = db.Column(
        db.Integer,
        nullable=True
    )
    
    # Quiz Content Fields
    quiz_id = db.Column(
        db.String(36),
        nullable=True
    )
    passing_score = db.Column(
        db.Integer,
        nullable=True
    )
    is_mandatory = db.Column(
        db.Boolean,
        default=False,
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
    progress_records = db.relationship(
        'LessonContentProgress',
        backref='content',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    
    def __repr__(self):
        return f"<LessonContent {self.content_id} - {self.content_type}>"
    
    def to_dict(self):
        """Convert content to dictionary for JSON serialization."""
        data = {
            'content_id': self.content_id,
            'lesson_id': self.lesson_id,
            'course_id': self.course_id,
            'content_type': self.content_type,
            'title': self.title,
            'description': self.description,
            'content_order': self.content_order,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

        # Include type-specific fields
        if self.content_type == 'video':
            data.update({
                'video_url': self.video_url,
                'preview_url': self.preview_url,
                'thumbnail_url': self.thumbnail_url,
                'video_duration_minutes': self.video_duration_minutes,
                'video_file_size_bytes': self.video_file_size_bytes,
                'video_quality_available': self.video_quality_available,
            })
        elif self.content_type == 'zoom_live':
            data.update({
                'zoom_link': self.zoom_link,
                'zoom_meeting_id': self.zoom_meeting_id,
                'zoom_password': self.zoom_password,
                'scheduled_date': self.scheduled_date.isoformat() if self.scheduled_date else None,
                'scheduled_duration_minutes': self.scheduled_duration_minutes,
                'is_recorded': self.is_recorded,
                'recording_url': self.recording_url,
            })
        elif self.content_type in ['text', 'pdf']:
            data.update({
                'text_content': self.text_content,
                'pdf_file_url': self.pdf_file_url,
                'pdf_file_size_bytes': self.pdf_file_size_bytes,
            })
        elif self.content_type == 'quiz':
            data.update({
                'quiz_id': self.quiz_id,
                'passing_score': self.passing_score,
                'is_mandatory': self.is_mandatory,
            })

        return data
