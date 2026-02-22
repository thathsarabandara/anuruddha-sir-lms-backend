"""
NotificationTemplate Model
Notification templates with dynamic variables
"""

from app import db
from datetime import datetime
import uuid
import json


class NotificationTemplate(db.Model):
    """
    NotificationTemplate model for notification templates with variable support.
    
    Attributes:
        template_id: UUID primary key
        notification_type: Notification type for this template
        channel: Channel (email, sms, whatsapp, in_app)
        subject: Email subject line
        template_html: HTML template content
        template_text: Plain text template content
        variables: JSON schema of variables
        version: Template version number
        is_active: Whether this template is active
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """
    
    __tablename__ = 'notification_templates'
    
    # Primary Key
    template_id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False
    )
    
    # Template Information
    notification_type = db.Column(
        db.String(100),
        nullable=False,
        index=True
    )
    channel = db.Column(
        db.String(50),
        nullable=True
    )
    
    # Template Content
    subject = db.Column(
        db.String(255),
        nullable=True
    )
    template_html = db.Column(
        db.Text,
        nullable=True
    )
    template_text = db.Column(
        db.Text,
        nullable=True
    )
    
    # Variables (JSON schema)
    variables = db.Column(
        db.JSON,
        nullable=True
    )
    
    # Versioning
    version = db.Column(
        db.Integer,
        default=1,
        nullable=False
    )
    is_active = db.Column(
        db.Boolean,
        default=True,
        nullable=False
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
    
    # Unique Constraint
    __table_args__ = (
        db.UniqueConstraint(
            'notification_type',
            'channel',
            'version',
            name='unique_type_channel_version'
        ),
    )
    
    def get_variables(self):
        """Get variables schema safely."""
        if not self.variables:
            return []
        try:
            if isinstance(self.variables, str):
                return json.loads(self.variables)
            return self.variables if isinstance(self.variables, list) else []
        except (json.JSONDecodeError, TypeError):
            return []
    
    def set_variables(self, data):
        """Set variables schema."""
        self.variables = json.dumps(data) if data else None
    
    def __repr__(self):
        return f"<NotificationTemplate {self.template_id} v{self.version}>"
    
    def to_dict(self):
        """Convert template to dictionary for JSON serialization."""
        return {
            'template_id': self.template_id,
            'notification_type': self.notification_type,
            'channel': self.channel,
            'subject': self.subject,
            'template_html': self.template_html,
            'template_text': self.template_text,
            'variables': self.get_variables(),
            'version': self.version,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
