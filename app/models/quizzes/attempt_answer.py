"""
AttemptAnswer Model
Represents a student's answer to a specific question in an attempt
"""

from app import db
from datetime import datetime
import uuid


class AttemptAnswer(db.Model):
    """
    AttemptAnswer model for individual question answers in quiz attempts.
    
    Attributes:
        answer_id: UUID primary key
        attempt_id: Foreign key to QuizAttempt
        question_id: Foreign key to Question
        user_answer: Student's answer (text, option_id, etc.)
        is_correct: Whether answer is correct (nullable for essay/manual grade)
        points_earned: Points earned for this answer
        time_taken_seconds: Time spent on this question
        answered_at: Timestamp when answer was submitted
    """
    
    __tablename__ = 'attempt_answers'
    
    # Primary Key
    answer_id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False
    )
    
    # Foreign Keys
    attempt_id = db.Column(
        db.String(36),
        db.ForeignKey('quiz_attempts.attempt_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    question_id = db.Column(
        db.String(36),
        db.ForeignKey('questions.question_id', ondelete='CASCADE'),
        nullable=False
    )
    
    # Answer Content and Grading
    user_answer = db.Column(
        db.Text,
        nullable=True
    )
    is_correct = db.Column(
        db.Boolean,
        nullable=True,
        index=True
    )
    points_earned = db.Column(
        db.Integer,
        nullable=True
    )
    
    # Timing
    time_taken_seconds = db.Column(
        db.Integer,
        nullable=True
    )
    
    # Timestamps
    answered_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    
    # Relationships
    manual_grades = db.relationship(
        'ManualGrade',
        backref='answer',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    
    def __repr__(self):
        return f"<AttemptAnswer {self.answer_id} - {self.attempt_id}>"
    
    def to_dict(self):
        """Convert answer to dictionary for JSON serialization."""
        return {
            'answer_id': self.answer_id,
            'attempt_id': self.attempt_id,
            'question_id': self.question_id,
            'user_answer': self.user_answer,
            'is_correct': self.is_correct,
            'points_earned': self.points_earned,
            'time_taken_seconds': self.time_taken_seconds,
            'answered_at': self.answered_at.isoformat() if self.answered_at else None,
        }
