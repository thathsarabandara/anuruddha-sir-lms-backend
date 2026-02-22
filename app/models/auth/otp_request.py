"""
OTPRequest Model
Represents OTP requests for email/phone verification and password reset
"""

from app import db
from datetime import datetime
import uuid


class OTPRequest(db.Model):
    """
    OTPRequest model for managing one-time passwords.
    
    Attributes:
        otp_id: UUID primary key
        user_id: Foreign key to users table (optional)
        email: Email address for OTP delivery
        phone: Phone number for OTP delivery
        verification_token: Unique URL-safe token sent to user
        otp_code_hash: Hashed OTP code (6 digits)
        purpose: Purpose of OTP ('registration', 'password_reset', 'login_verification')
        channel: Delivery channel ('email', 'whatsapp', 'both')
        created_at: OTP creation timestamp
        expires_at: OTP expiration timestamp (5 minutes)
        verified_at: When OTP was verified
        is_verified: Whether OTP has been verified
        is_used: Whether OTP has been used
        attempt_count: Number of verification attempts
        max_attempts: Maximum allowed attempts (default: 3)
    """
    
    __tablename__ = 'otp_requests'
    
    # Primary Key
    otp_id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False
    )
    
    # Foreign Key
    user_id = db.Column(
        db.String(36),
        db.ForeignKey('users.user_id', ondelete='CASCADE'),
        nullable=True,
        index=True
    )
    
    # Contact Information
    email = db.Column(
        db.String(255),
        nullable=True,
        index=True
    )
    phone = db.Column(
        db.String(20),
        nullable=True,
        index=True
    )
    
    # Token & OTP
    verification_token = db.Column(
        db.String(255),
        unique=True,
        nullable=False,
        index=True
    )
    otp_code_hash = db.Column(
        db.String(255),
        nullable=False
    )
    
    # OTP Metadata
    purpose = db.Column(
        db.String(50),
        nullable=False
    )
    channel = db.Column(
        db.String(50),
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
        nullable=False
    )
    verified_at = db.Column(
        db.DateTime,
        nullable=True
    )
    
    # Verification Status
    is_verified = db.Column(
        db.Boolean,
        default=False,
        nullable=False,
        index=True
    )
    is_used = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )
    
    # Attempt Tracking
    attempt_count = db.Column(
        db.Integer,
        default=0,
        nullable=False
    )
    max_attempts = db.Column(
        db.Integer,
        default=3,
        nullable=False
    )
    
    def __repr__(self):
        return f"<OTPRequest {self.otp_id} ({self.purpose})>"
    
    def to_dict(self, include_token=False):
        """Convert OTP request to dictionary representation."""
        data = {
            'otp_id': self.otp_id,
            'user_id': self.user_id,
            'email': self.email,
            'phone': self.phone,
            'purpose': self.purpose,
            'channel': self.channel,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'verified_at': self.verified_at.isoformat() if self.verified_at else None,
            'is_verified': self.is_verified,
            'is_used': self.is_used,
            'attempt_count': self.attempt_count,
            'max_attempts': self.max_attempts,
        }
        
        if include_token:
            data['verification_token'] = self.verification_token
        
        return data
