"""
RolePermission Model
Junction table for many-to-many relationship between roles and permissions
"""

from app import db
from datetime import datetime
import uuid


class RolePermission(db.Model):
    """
    RolePermission junction table for many-to-many relationship between roles and permissions.
    
    Attributes:
        role_permission_id: UUID primary key
        role_id: Foreign key to roles table
        permission_id: Foreign key to permissions table
        assigned_at: When the permission was assigned to the role
    """
    
    __tablename__ = 'role_permissions'
    
    # Primary Key
    role_permission_id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True,
        nullable=False
    )
    
    # Foreign Keys
    role_id = db.Column(
        db.String(36),
        db.ForeignKey('roles.role_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    permission_id = db.Column(
        db.String(36),
        db.ForeignKey('permissions.permission_id', ondelete='CASCADE'),
        nullable=False
    )
    
    # Metadata
    assigned_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    
    # Unique constraint: role can have only one of each permission
    __table_args__ = (
        db.UniqueConstraint('role_id', 'permission_id', name='unique_role_permission'),
    )
    
    def __repr__(self):
        return f"<RolePermission role_id={self.role_id} permission_id={self.permission_id}>"
    
    def to_dict(self):
        """Convert role permission to dictionary representation."""
        return {
            'role_permission_id': self.role_permission_id,
            'role_id': self.role_id,
            'permission_id': self.permission_id,
            'assigned_at': self.assigned_at.isoformat() if self.assigned_at else None,
        }
