"""
CourseStatusAudit Model
Track course status and visibility changes
"""

import uuid
from datetime import datetime

from app import db


class CourseStatusAudit(db.Model):
    """
    CourseStatusAudit model for auditing course status and visibility changes.

    Attributes:
        audit_id: UUID primary key
        course_id: Foreign key to Course
        changed_by: Foreign key to User (admin/teacher who made change)
        previous_status: Previous course status (draft, published, archived)
        new_status: New course status (draft, published, archived)
        previous_visibility: Previous visibility (public, private)
        new_visibility: New visibility (public, private)
        change_type: Type of change (publish, unpublish, archive, etc.)
        change_reason: Optional reason for the change
        ip_address: IP address of change initiator
        user_agent: User agent of change initiator
        changed_at: Timestamp of change (indexed)
    """

    __tablename__ = "course_status_audit"

    # Primary Key
    audit_id = db.Column(
        db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False
    )

    # Foreign Keys
    course_id = db.Column(
        db.String(36),
        db.ForeignKey("courses.course_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    changed_by = db.Column(
        db.String(36),
        db.ForeignKey("users.user_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # Status Changes
    previous_status = db.Column(db.Enum("draft", "published", "archived"), nullable=True)
    new_status = db.Column(db.Enum("draft", "published", "archived"), nullable=True)

    # Visibility Changes
    previous_visibility = db.Column(db.Enum("public", "private"), nullable=True)
    new_visibility = db.Column(db.Enum("public", "private"), nullable=True)

    # Change Details
    change_type = db.Column(db.String(50), nullable=False, index=True)
    change_reason = db.Column(db.Text, nullable=True)

    # Request Information
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(500), nullable=True)

    # Timestamps
    changed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self):
        return f"<CourseStatusAudit {self.audit_id} - {self.change_type}>"

    def to_dict(self):
        """Convert audit to dictionary for JSON serialization."""
        return {
            "audit_id": self.audit_id,
            "course_id": self.course_id,
            "changed_by": self.changed_by,
            "previous_status": self.previous_status,
            "new_status": self.new_status,
            "previous_visibility": self.previous_visibility,
            "new_visibility": self.new_visibility,
            "change_type": self.change_type,
            "change_reason": self.change_reason,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "changed_at": self.changed_at.isoformat() if self.changed_at else None,
        }
