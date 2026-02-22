"""
PasswordResetToken Model
Manages password reset tokens for secure password recovery
"""

from app import db
from datetime import datetime
import uuid


class PasswordResetToken(db.Model):
    """
    PasswordResetToken model for password reset functionality.
    
    Attributes:
        token_id: UUID primary key
        user_id: Foreign key to users table
        reset_token: Unique reset token (32+ chars)
        expires_at: Token expiration (1 hour)
        used_at: When token was used
        is_used: Whether token has been used
        created_at: Token creation timestamp
    """
    
    __tablename__ = 'password_reset_tokens'
    
    # Primary Key
    token_id = db.Column(
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
    
    # Token Information
    reset_token = db.Column(
        db.String(255),
        unique=True,
        nullable=False,
        index=True
    )
    
    # Timestamps
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    expires_at = db.Column(
        db.DateTime,
        nullable=False,
        index=True
    )
    used_at = db.Column(
        db.DateTime,
        nullable=True
    )
    
    # Status
    is_used = db.Column(
        db.Boolean,
        default=False,
        nullable=False,
        index=True
    )
    
    def __repr__(self):
        return f"<PasswordResetToken token_id={self.token_id} user_id={self.user_id}>"
    
    def to_dict(self, include_token=False):
        """Convert password reset token to dictionary representation."""
        data = {
            'token_id': self.token_id,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'used_at': self.used_at.isoformat() if self.used_at else None,
            'is_used': self.is_used,
        }
        
        if include_token:
            data['reset_token'] = self.reset_token
        
        return data
