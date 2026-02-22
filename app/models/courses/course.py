"""
Course Model
Represents course information including metadata, pricing, and status
"""

from app import db
from datetime import datetime
import uuid


class Course(db.Model):
    """
    Course model containing core course information.
    
    Attributes:
        course_id: UUID primary key
        title: Course title (max 255 chars)
        slug: URL-friendly slug (unique, indexed)
        description: Detailed course description
        category_id: Foreign key to CourseCategory
        instructor_id: Foreign key to User (teacher)
        thumbnail_url: URL to course thumbnail image
        difficulty: Course difficulty level (beginner, intermediate, advanced)
        language: Course language code (default: 'en')
        duration_hours: Estimated total course duration in hours
        is_paid: Boolean indicating if course requires payment
        price: Course price in decimal format (10,2)
        status: ENUM(draft, published, archived) course status
        visibility: ENUM(public, private) course visibility
        course_type: ENUM(monthly, paper, quiz, special) course type
        rating: Average course rating (3,2 decimal precision)
        total_reviews: Count of course reviews
        total_enrollments: Count of enrolled students
        created_at: Course creation timestamp
        updated_at: Last modification timestamp
    """
    
    __tablename__ = 'courses'
    
    # Primary Key
    course_id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False
    )
    
    # Course Basic Info
    title = db.Column(
        db.String(255),
        nullable=False
    )
    slug = db.Column(
        db.String(255),
        unique=True,
        nullable=False,
        index=True
    )
    description = db.Column(
        db.Text,
        nullable=True
    )
    
    # Foreign Keys
    category_id = db.Column(
        db.String(36),
        db.ForeignKey('course_categories.category_id'),
        nullable=True
    )
    instructor_id = db.Column(
        db.String(36),
        db.ForeignKey('users.user_id'),
        nullable=False,
        index=True
    )
    
    # Course Metadata
    thumbnail_url = db.Column(
        db.Text,
        nullable=True
    )
    difficulty = db.Column(
        db.String(20),
        nullable=True
    )
    language = db.Column(
        db.String(10),
        default='en',
        nullable=False
    )
    duration_hours = db.Column(
        db.Integer,
        nullable=True
    )
    
    # Pricing Information
    is_paid = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )
    price = db.Column(
        db.Numeric(10, 2),
        nullable=True
    )
    
    # Status and Visibility
    status = db.Column(
        db.Enum('draft', 'published', 'archived'),
        default='draft',
        nullable=False,
        index=True
    )
    visibility = db.Column(
        db.Enum('public', 'private'),
        default='public',
        nullable=False
    )
    course_type = db.Column(
        db.Enum('monthly', 'paper', 'quiz', 'special'),
        default='monthly',
        index=True
    )
    
    # Ratings and Analytics
    rating = db.Column(
        db.Numeric(3, 2),
        nullable=True
    )
    total_reviews = db.Column(
        db.Integer,
        default=0,
        nullable=False
    )
    total_enrollments = db.Column(
        db.Integer,
        default=0,
        nullable=False
    )
    
    # Timestamps
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    # Relationships
    sections = db.relationship(
        'CourseSection',
        backref='course',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    lessons = db.relationship(
        'CourseLesson',
        backref='course',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    enrollments = db.relationship(
        'CourseEnrollment',
        backref='course',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    reviews = db.relationship(
        'CourseReview',
        backref='course',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    activity_logs = db.relationship(
        'CourseActivityLog',
        backref='course',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    enrollment_keys = db.relationship(
        'CourseEnrollmentKey',
        backref='course',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    status_audits = db.relationship(
        'CourseStatusAudit',
        backref='course',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    contents = db.relationship(
        'LessonContent',
        backref='course',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    
    def __repr__(self):
        return f"<Course {self.course_id} - {self.title}>"
    
    def to_dict(self):
        """Convert course to dictionary for JSON serialization."""
        return {
            'course_id': self.course_id,
            'title': self.title,
            'slug': self.slug,
            'description': self.description,
            'category_id': self.category_id,
            'instructor_id': self.instructor_id,
            'thumbnail_url': self.thumbnail_url,
            'difficulty': self.difficulty,
            'language': self.language,
            'duration_hours': self.duration_hours,
            'is_paid': self.is_paid,
            'price': float(self.price) if self.price else None,
            'status': self.status,
            'visibility': self.visibility,
            'course_type': self.course_type,
            'rating': float(self.rating) if self.rating else None,
            'total_reviews': self.total_reviews,
            'total_enrollments': self.total_enrollments,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
