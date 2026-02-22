"""
CertificateTemplate Model
Represents certificate design templates with variables
"""

from app import db
from datetime import datetime
import uuid
import json

class CertificateTemplate(db.Model):
    """
    Certificate template model for managing certificate designs
    
    Attributes:
        template_id: Unique identifier (UUID)
        name: Template name
        description: Template description
        template_image_url: URL to template image
        signature_image_url: URL to signature image
        logo_image_url: URL to logo image
        signature_name: Name of signer
        signature_title: Title of signer
        variables: JSON schema of template variables
        version: Version number of template
        is_active: Whether template is active
        created_by: User ID of template creator
        created_at: Timestamp created
        updated_at: Timestamp last updated
    """
    
    __tablename__ = 'certificate_templates'
    
    # Primary Key
    template_id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False
    )
    
    # Foreign Keys
    created_by = db.Column(
        db.String(36),
        db.ForeignKey('users.user_id'),
        nullable=True
    )
    
    # Data Fields
    name = db.Column(
        db.String(255),
        nullable=False,
        index=True
    )
    
    description = db.Column(
        db.Text,
        nullable=True
    )
    
    template_image_url = db.Column(
        db.Text,
        nullable=True
    )
    
    signature_image_url = db.Column(
        db.Text,
        nullable=True
    )
    
    logo_image_url = db.Column(
        db.Text,
        nullable=True
    )
    
    signature_name = db.Column(
        db.String(255),
        nullable=True
    )
    
    signature_title = db.Column(
        db.String(255),
        nullable=True
    )
    
    variables = db.Column(
        db.JSON,
        nullable=True
    )
    
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
    
    # Relationships
    certificates = db.relationship(
        'Certificate',
        backref='template',
        lazy=True
    )
    
    def get_variables(self):
        """Get template variables safely"""
        if self.variables and isinstance(self.variables, dict):
            return self.variables
        elif self.variables and isinstance(self.variables, str):
            try:
                return json.loads(self.variables)
            except (json.JSONDecodeError, TypeError):
                return {}
        return {}
    
    def set_variables(self, data):
        """Set template variables safely"""
        if isinstance(data, dict):
            self.variables = data
        elif isinstance(data, str):
            try:
                self.variables = json.loads(data)
            except (json.JSONDecodeError, TypeError):
                self.variables = {}
        else:
            self.variables = {}
    
    def to_dict(self):
        """Serialize template to dictionary"""
        return {
            'template_id': self.template_id,
            'name': self.name,
            'description': self.description,
            'template_image_url': self.template_image_url,
            'signature_image_url': self.signature_image_url,
            'logo_image_url': self.logo_image_url,
            'signature_name': self.signature_name,
            'signature_title': self.signature_title,
            'variables': self.get_variables(),
            'version': self.version,
            'is_active': self.is_active,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<CertificateTemplate {self.name} v{self.version}>'
