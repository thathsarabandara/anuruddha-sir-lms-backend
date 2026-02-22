"""
UserSuspensionLog Model
Tracks user account suspensions and bans
"""

from app import db
from datetime import datetime
import uuid


class UserSuspensionLog(db.Model):
    """
    UserSuspensionLog model for tracking account suspensions.
    
    Attributes:
        suspension_id: UUID primary key
        user_id: Foreign key to users table (suspended user)
        reason: Reason for suspension
        suspended_by: Admin user_id who performed suspension
        suspended_at: When suspension was applied
        suspended_until: When suspension expires (null for permanent)
        is_active: Whether suspension is currently active
    """
    
    __tablename__ = 'user_suspension_log'
    
    # Primary Key
    suspension_id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False
    )
    
    # Foreign Keys
    user_id = db.Column(
        db.String(36),
        db.ForeignKey('users.user_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    suspended_by = db.Column(
        db.String(36),
        db.ForeignKey('users.user_id'),
        nullable=True
    )
    
    # Suspension Information
    reason = db.Column(
        db.String(255),
        nullable=True
    )
    
    # Timestamps
    suspended_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    suspended_until = db.Column(
        db.DateTime,
        nullable=True,
        index=True
    )
    
    # Status
    is_active = db.Column(
        db.Boolean,
        default=True,
        nullable=False
    )
    
    def __repr__(self):
        return f"<UserSuspensionLog user_id={self.user_id} active={self.is_active}>"
    
    def to_dict(self):
        """Convert suspension log to dictionary representation."""
        return {
            'suspension_id': self.suspension_id,
            'user_id': self.user_id,
            'reason': self.reason,
            'suspended_by': self.suspended_by,
            'suspended_at': self.suspended_at.isoformat() if self.suspended_at else None,
            'suspended_until': self.suspended_until.isoformat() if self.suspended_until else None,
            'is_active': self.is_active,
        }
