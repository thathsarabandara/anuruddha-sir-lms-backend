"""
Role Model
Represents user roles in the system
"""

from app import db
from datetime import datetime
import uuid


class Role(db.Model):
    """
    Role model for role-based access control (RBAC).
    
    Attributes:
        role_id: UUID primary key
        role_name: Unique role name (e.g., 'student', 'instructor', 'admin')
        description: Role description
        created_at: Role creation timestamp
    """
    
    __tablename__ = 'roles'
    
    # Primary Key
    role_id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False
    )
    
    # Role Information
    role_name = db.Column(
        db.String(50),
        unique=True,
        nullable=False,
        index=True
    )
    description = db.Column(
        db.Text,
        nullable=True
    )
    
    # Timestamps
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    
    # Relationships
    permissions = db.relationship(
        'RolePermission',
        backref='role',
        lazy=True,
        cascade='all, delete-orphan'
    )
    users = db.relationship(
        'UserRole',
        backref='role',
        lazy=True,
        cascade='all, delete-orphan'
    )
    
    def __repr__(self):
        return f"<Role {self.role_name}>"
    
    def to_dict(self):
        """Convert role to dictionary representation."""
        return {
            'role_id': self.role_id,
            'role_name': self.role_name,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
