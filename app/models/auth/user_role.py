"""
UserRole Model
Junction table for many-to-many relationship between users and roles
"""

import uuid
from datetime import datetime

from app import db


class UserRole(db.Model):
    """
    UserRole junction table for many-to-many relationship between users and roles.

    Attributes:
        user_role_id: UUID primary key
        user_id: Foreign key to users table
        role_id: Foreign key to roles table
        assigned_at: When the role was assigned
        assigned_by: User ID of who assigned this role (admin)
    """

    __tablename__ = "user_roles"

    # Primary Key
    user_role_id = db.Column(
        db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False
    )

    # Foreign Keys
    user_id = db.Column(
        db.String(36),
        db.ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role_id = db.Column(db.String(36), db.ForeignKey("roles.role_id"), nullable=False, index=True)

    # Metadata
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    assigned_by = db.Column(db.String(36), nullable=True)

    # Unique constraint: user can have only one of each role
    __table_args__ = (db.UniqueConstraint("user_id", "role_id", name="unique_user_role"),)

    def __repr__(self):
        return f"<UserRole user_id={self.user_id} role_id={self.role_id}>"

    def to_dict(self):
        """Convert user role to dictionary representation."""
        return {
            "user_role_id": self.user_role_id,
            "user_id": self.user_id,
            "role_id": self.role_id,
            "assigned_at": self.assigned_at.isoformat() if self.assigned_at else None,
            "assigned_by": self.assigned_by,
        }
