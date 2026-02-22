"""
CourseCategory Model
Represents course categories for organization and filtering
"""

import uuid
from datetime import datetime

from app import db


class CourseCategory(db.Model):
    """
    CourseCategory model for organizing courses by category.

    Attributes:
        category_id: UUID primary key
        name: Unique category name (max 100 chars)
        description: Category description
        icon_url: URL to category icon
        slug: URL-friendly category slug (unique, indexed)
        created_at: Category creation timestamp
    """

    __tablename__ = "course_categories"

    # Primary Key
    category_id = db.Column(
        db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False
    )

    # Category Information
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    icon_url = db.Column(db.Text, nullable=True)
    slug = db.Column(db.String(100), unique=True, nullable=False, index=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    courses = db.relationship(
        "Course", backref="category", lazy="dynamic", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<CourseCategory {self.category_id} - {self.name}>"

    def to_dict(self):
        """Convert category to dictionary for JSON serialization."""
        return {
            "category_id": self.category_id,
            "name": self.name,
            "description": self.description,
            "icon_url": self.icon_url,
            "slug": self.slug,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
