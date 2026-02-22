"""
PointTransaction Model
Individual point transactions and activity log
"""

from app import db
from datetime import datetime
import uuid


class PointTransaction(db.Model):
    """
    PointTransaction model for tracking all point transactions and activities.
    
    Attributes:
        transaction_id: UUID primary key
        user_id: Foreign key to User
        points: Points awarded/deducted
        multiplier: Point multiplier (1.0-3.0)
        activity_type: Type of activity
        activity_description: Detailed description
        related_resource_id: Related resource UUID (course, quiz, etc.)
        balance_after: Point balance after transaction
        notes: Additional notes
        created_at: Transaction timestamp
    """
    
    __tablename__ = 'point_transactions'
    
    # Primary Key
    transaction_id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False
    )
    
    # Foreign Key
    user_id = db.Column(
        db.String(36),
        db.ForeignKey('users.user_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    # Transaction Data
    points = db.Column(
        db.Integer,
        nullable=False
    )
    multiplier = db.Column(
        db.Numeric(3, 2),
        default=1.00,
        nullable=False
    )
    
    # Activity Information
    activity_type = db.Column(
        db.String(100),
        nullable=True,
        index=True
    )
    activity_description = db.Column(
        db.Text,
        nullable=True
    )
    related_resource_id = db.Column(
        db.String(36),
        nullable=True
    )
    
    # Audit Data
    balance_after = db.Column(
        db.Integer,
        nullable=True
    )
    notes = db.Column(
        db.Text,
        nullable=True
    )
    
    # Timestamps
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )
    
    def __repr__(self):
        return f"<PointTransaction {self.transaction_id} - {self.points} points>"
    
    def to_dict(self):
        """Convert transaction to dictionary for JSON serialization."""
        return {
            'transaction_id': self.transaction_id,
            'user_id': self.user_id,
            'points': self.points,
            'multiplier': float(self.multiplier),
            'activity_type': self.activity_type,
            'activity_description': self.activity_description,
            'related_resource_id': self.related_resource_id,
            'balance_after': self.balance_after,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
