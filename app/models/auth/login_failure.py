"""
LoginFailure Model
Tracks failed login attempts for security monitoring
"""

from app import db
from datetime import datetime
import uuid


class LoginFailure(db.Model):
    """
    LoginFailure model for tracking failed login attempts.
    
    Attributes:
        failure_id: UUID primary key
        user_id: Foreign key to users table
        email: Email address of login attempt
        ip_address: IP address of the failed attempt
        user_agent: Browser/client user agent
        device_name: Detected device name
        failed_at: Timestamp of failed login
        reason: Reason for failure
    """
    
    __tablename__ = 'login_failures'
    
    # Primary Key
    failure_id = db.Column(
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
    
    # Login Information
    email = db.Column(
        db.String(255),
        nullable=False,
        index=True
    )
    ip_address = db.Column(
        db.String(45),
        nullable=True
    )
    user_agent = db.Column(
        db.Text,
        nullable=True
    )
    device_name = db.Column(
        db.String(255),
        nullable=True
    )
    
    # Timestamps & Reason
    failed_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )
    reason = db.Column(
        db.String(100),
        nullable=True
    )
    
    def __repr__(self):
        return f"<LoginFailure user_id={self.user_id} at {self.failed_at}>"
    
    def to_dict(self):
        """Convert login failure to dictionary representation."""
        return {
            'failure_id': self.failure_id,
            'user_id': self.user_id,
            'email': self.email,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'device_name': self.device_name,
            'failed_at': self.failed_at.isoformat() if self.failed_at else None,
            'reason': self.reason,
        }
