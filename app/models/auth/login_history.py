"""
LoginHistory Model
Tracks successful and failed login history for audit and security
"""

from app import db
from datetime import datetime
import uuid


class LoginHistory(db.Model):
    """
    LoginHistory model for audit logging and session tracking.
    
    Attributes:
        login_id: UUID primary key
        user_id: Foreign key to users table
        ip_address: IP address of login
        user_agent: Browser/client user agent
        device_name: Detected device name
        location: Geographic location
        login_at: Login timestamp
        logout_at: Logout timestamp
        is_successful: Whether login was successful
        failure_reason: Reason if login failed
    """
    
    __tablename__ = 'login_history'
    
    # Primary Key
    login_id = db.Column(
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
    location = db.Column(
        db.String(255),
        nullable=True
    )
    
    # Timestamps
    login_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )
    logout_at = db.Column(
        db.DateTime,
        nullable=True
    )
    
    # Status
    is_successful = db.Column(
        db.Boolean,
        default=True,
        nullable=False
    )
    failure_reason = db.Column(
        db.String(255),
        nullable=True
    )
    
    def __repr__(self):
        return f"<LoginHistory user_id={self.user_id} at {self.login_at}>"
    
    def to_dict(self):
        """Convert login history to dictionary representation."""
        return {
            'login_id': self.login_id,
            'user_id': self.user_id,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'device_name': self.device_name,
            'location': self.location,
            'login_at': self.login_at.isoformat() if self.login_at else None,
            'logout_at': self.logout_at.isoformat() if self.logout_at else None,
            'is_successful': self.is_successful,
            'failure_reason': self.failure_reason,
        }
