"""
EmailVerificationToken Model
Manages email verification tokens for account activation
"""

from app import db
from datetime import datetime
import uuid


class EmailVerificationToken(db.Model):
    """
    EmailVerificationToken model for email verification during registration.
    
    Attributes:
        token_id: UUID primary key
        user_id: Foreign key to users table
        token_hash: Hashed verification token
        expires_at: Token expiration (24 hours)
        verified_at: When email was verified
        created_at: Token creation timestamp
    """
    
    __tablename__ = 'email_verification_tokens'
    
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
    token_hash = db.Column(
        db.String(255),
        unique=True,
        nullable=False
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
    verified_at = db.Column(
        db.DateTime,
        nullable=True
    )
    
    def __repr__(self):
        return f"<EmailVerificationToken token_id={self.token_id} user_id={self.user_id}>"
    
    def to_dict(self):
        """Convert email verification token to dictionary representation."""
        return {
            'token_id': self.token_id,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'verified_at': self.verified_at.isoformat() if self.verified_at else None,
        }
