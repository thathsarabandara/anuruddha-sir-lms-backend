"""
Question Model
Represents quiz questions of various types
"""

from app import db
from datetime import datetime
import uuid


class Question(db.Model):
    """
    Question model for different question types in quizzes.
    
    Attributes:
        question_id: UUID primary key
        quiz_id: Foreign key to Quiz
        question_type: ENUM(multiple_choice, multiple_answer, short_answer, essay, matching, fill_blank)
        question_text: Question content (max text)
        points: Points awarded for correct answer (default: 1)
        difficulty: ENUM(easy, medium, hard) difficulty level
        category: Question category for organization
        explanation: Explanation shown after submission
        question_order: Ordering of question within quiz
        created_at: Question creation timestamp
        updated_at: Last modification timestamp
    """
    
    __tablename__ = 'questions'
    
    # Primary Key
    question_id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False
    )
    
    # Foreign Key
    quiz_id = db.Column(
        db.String(36),
        db.ForeignKey('quizzes.quiz_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    # Question Type and Content
    question_type = db.Column(
        db.Enum('multiple_choice', 'multiple_answer', 'short_answer', 'essay', 'matching', 'fill_blank'),
        nullable=False,
        index=True
    )
    question_text = db.Column(
        db.Text,
        nullable=False
    )
    
    # Question Metadata
    points = db.Column(
        db.Integer,
        default=1,
        nullable=False
    )
    difficulty = db.Column(
        db.Enum('easy', 'medium', 'hard'),
        default='medium',
        nullable=False
    )
    category = db.Column(
        db.String(100),
        nullable=True
    )
    
    # Additional Information
    explanation = db.Column(
        db.Text,
        nullable=True
    )
    question_order = db.Column(
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
    options = db.relationship(
        'QuestionOption',
        backref='question',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    attempt_answers = db.relationship(
        'AttemptAnswer',
        backref='question',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    
    def __repr__(self):
        return f"<Question {self.question_id} - {self.question_type}>"
    
    def to_dict(self):
        """Convert question to dictionary for JSON serialization."""
        return {
            'question_id': self.question_id,
            'quiz_id': self.quiz_id,
            'question_type': self.question_type,
            'question_text': self.question_text,
            'points': self.points,
            'difficulty': self.difficulty,
            'category': self.category,
            'explanation': self.explanation,
            'question_order': self.question_order,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
