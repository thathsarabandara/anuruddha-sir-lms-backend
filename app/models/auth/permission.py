"""
Permission Model
Represents permissions that can be assigned to roles
"""

import uuid
from datetime import datetime

from app import db


class Permission(db.Model):
    """
    Permission model for fine-grained access control.

    Attributes:
        permission_id: UUID primary key
        permission_name: Unique permission name (e.g., 'create_course', 'view_users')
        description: Permission description
        module: Module this permission belongs to (e.g., 'courses', 'users', 'payments')
        created_at: Permission creation timestamp
    """

    __tablename__ = "permissions"

    # Primary Key
    permission_id = db.Column(
        db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False
    )

    # Permission Information
    permission_name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    module = db.Column(db.String(50), nullable=True, index=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    roles = db.relationship(
        "RolePermission", backref="permission", lazy=True, cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Permission {self.permission_name}>"

    def to_dict(self):
        """Convert permission to dictionary representation."""
        return {
            "permission_id": self.permission_id,
            "permission_name": self.permission_name,
            "description": self.description,
            "module": self.module,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
