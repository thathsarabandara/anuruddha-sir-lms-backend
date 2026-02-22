"""
LessonContentProgress Model
Tracks individual student progress for each lesson content item
"""

from app import db
from datetime import datetime
import uuid


class LessonContentProgress(db.Model):
    """
    LessonContentProgress model tracking student progress per content item.
    
    Attributes:
        progress_id: UUID primary key
        content_id: Foreign key to LessonContent
        lesson_id: Foreign key to CourseLesson
        user_id: Foreign key to User (student)
        course_id: Foreign key to Course
        
        Common Progress Fields:
            is_completed, completed_at, first_accessed, last_accessed
        
        Video-Specific:
            video_watched_percentage, video_current_position_seconds,
            video_watch_count, video_quality_watched, video_total_watch_time_seconds
        
        Zoom-Specific:
            zoom_attended, zoom_joined_at, zoom_left_at,
            zoom_attended_duration_minutes, zoom_device_type
        
        PDF-Specific:
            pdf_downloaded, pdf_download_count
        
        Quiz-Specific:
            quiz_attempted, quiz_score, quiz_attempt_count, quiz_last_attempted
    """
    
    __tablename__ = 'lesson_content_progress'
    
    # Primary Key
    progress_id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False
    )
    
    # Foreign Keys
    content_id = db.Column(
        db.String(36),
        db.ForeignKey('lesson_contents.content_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    lesson_id = db.Column(
        db.String(36),
        db.ForeignKey('course_lessons.lesson_id', ondelete='CASCADE'),
        nullable=False
    )
    user_id = db.Column(
        db.String(36),
        db.ForeignKey('users.user_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    course_id = db.Column(
        db.String(36),
        db.ForeignKey('courses.course_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    # Common Progress Fields
    is_completed = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )
    completed_at = db.Column(
        db.DateTime,
        nullable=True,
        index=True
    )
    first_accessed = db.Column(
        db.DateTime,
        nullable=True
    )
    last_accessed = db.Column(
        db.DateTime,
        nullable=True
    )
    
    # Video-Specific Fields
    video_watched_percentage = db.Column(
        db.Integer,
        default=0,
        nullable=True
    )
    video_current_position_seconds = db.Column(
        db.Integer,
        default=0,
        nullable=True
    )
    video_watch_count = db.Column(
        db.Integer,
        default=0,
        nullable=True
    )
    video_quality_watched = db.Column(
        db.String(20),
        nullable=True
    )
    video_total_watch_time_seconds = db.Column(
        db.Integer,
        default=0,
        nullable=True
    )
    
    # Zoom-Specific Fields
    zoom_attended = db.Column(
        db.Boolean,
        default=False,
        nullable=True
    )
    zoom_joined_at = db.Column(
        db.DateTime,
        nullable=True
    )
    zoom_left_at = db.Column(
        db.DateTime,
        nullable=True
    )
    zoom_attended_duration_minutes = db.Column(
        db.Integer,
        nullable=True
    )
    zoom_device_type = db.Column(
        db.String(50),
        nullable=True
    )
    
    # PDF-Specific Fields
    pdf_downloaded = db.Column(
        db.Boolean,
        default=False,
        nullable=True
    )
    pdf_download_count = db.Column(
        db.Integer,
        default=0,
        nullable=True
    )
    
    # Quiz-Specific Fields
    quiz_attempted = db.Column(
        db.Boolean,
        default=False,
        nullable=True
    )
    quiz_score = db.Column(
        db.Integer,
        nullable=True
    )
    quiz_attempt_count = db.Column(
        db.Integer,
        default=0,
        nullable=True
    )
    quiz_last_attempted = db.Column(
        db.DateTime,
        nullable=True
    )
    
    __table_args__ = (
        db.UniqueConstraint('content_id', 'user_id', name='unique_user_content'),
    )
    
    def __repr__(self):
        return f"<LessonContentProgress {self.progress_id} - {self.user_id}>"
    
    def to_dict(self):
        """Convert progress to dictionary for JSON serialization."""
        return {
            'progress_id': self.progress_id,
            'content_id': self.content_id,
            'lesson_id': self.lesson_id,
            'user_id': self.user_id,
            'course_id': self.course_id,
            'is_completed': self.is_completed,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'first_accessed': self.first_accessed.isoformat() if self.first_accessed else None,
            'last_accessed': self.last_accessed.isoformat() if self.last_accessed else None,
            'video_watched_percentage': self.video_watched_percentage,
            'video_current_position_seconds': self.video_current_position_seconds,
            'video_watch_count': self.video_watch_count,
            'video_quality_watched': self.video_quality_watched,
            'video_total_watch_time_seconds': self.video_total_watch_time_seconds,
            'zoom_attended': self.zoom_attended,
            'zoom_joined_at': self.zoom_joined_at.isoformat() if self.zoom_joined_at else None,
            'zoom_left_at': self.zoom_left_at.isoformat() if self.zoom_left_at else None,
            'zoom_attended_duration_minutes': self.zoom_attended_duration_minutes,
            'zoom_device_type': self.zoom_device_type,
            'pdf_downloaded': self.pdf_downloaded,
            'pdf_download_count': self.pdf_download_count,
            'quiz_attempted': self.quiz_attempted,
            'quiz_score': self.quiz_score,
            'quiz_attempt_count': self.quiz_attempt_count,
            'quiz_last_attempted': self.quiz_last_attempted.isoformat() if self.quiz_last_attempted else None,
        }
