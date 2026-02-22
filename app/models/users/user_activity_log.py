"""
UserActivityLog Model
Tracks user activities for audit trail and analytics
"""

from app import db
from datetime import datetime
import uuid
import json


class UserActivityLog(db.Model):
    """
    UserActivityLog model for tracking all user actions.
    
    Attributes:
        activity_id: UUID primary key
        user_id: Foreign key to users table
        action: Type of action (login, logout, course_enrolled, etc)
        description: Human-readable description of action
        resource_type: Type of resource affected (course, quiz, certificate, etc)
        resource_id: ID of the affected resource
        ip_address: IP address from which action was performed
        user_agent: Browser/client user agent
        metadata: JSON object with additional action details
        created_at: Action timestamp
    """
    
    __tablename__ = 'user_activity_log'
    
    # Primary Key
    activity_id = db.Column(
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
    
    # Activity Information
    action = db.Column(
        db.String(100),
        nullable=False,
        index=True
    )
    description = db.Column(
        db.Text,
        nullable=True
    )
    
    # Resource Information
    resource_type = db.Column(
        db.String(100),
        nullable=True
    )
    resource_id = db.Column(
        db.String(36),
        nullable=True
    )
    
    # Request Information
    ip_address = db.Column(
        db.String(45),
        nullable=True
    )
    user_agent = db.Column(
        db.Text,
        nullable=True
    )
    
    # Additional Data
    metadata = db.Column(
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
        return f"<UserActivityLog user_id={self.user_id} action={self.action}>"
    
    def get_metadata(self):
        """Parse metadata from JSON."""
        if not self.metadata:
            return {}
        try:
            return json.loads(self.metadata)
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def set_metadata(self, data):
        """Set metadata from dict."""
        self.metadata = json.dumps(data) if data else None
    
    def to_dict(self):
        """Convert activity log to dictionary representation."""
        return {
            'activity_id': self.activity_id,
            'user_id': self.user_id,
            'action': self.action,
            'description': self.description,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'metadata': self.get_metadata(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
