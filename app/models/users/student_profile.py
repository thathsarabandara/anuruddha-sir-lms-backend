"""
StudentProfile Model
Stores student-specific registration and profile information
"""

import uuid
from datetime import datetime

from app import db


class StudentProfile(db.Model):
    """
    Extended profile for users with the 'student' role.

    Attributes:
        profile_id:      UUID primary key
        user_id:         FK to users.user_id (1-to-1)
        whatsapp_number: WhatsApp contact number
        date_of_birth:   Student's date of birth
        grade_level:     Current grade/year (e.g. "1", "2", "3", "4 , "5")
        school:          Name of the school or institution
        address:         Physical address
        parent_name:     Parent / guardian name
        parent_contact:  Parent / guardian phone number
        created_at:      Row creation timestamp
        updated_at:      Last update timestamp
    """

    __tablename__ = "student_profiles"

    profile_id = db.Column(
        db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False
    )
    user_id = db.Column(
        db.String(36),
        db.ForeignKey("users.user_id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    # Contact
    whatsapp_number = db.Column(db.String(20), nullable=True)

    # Academic info
    date_of_birth = db.Column(db.Date, nullable=True)
    grade_level = db.Column(db.String(100), nullable=True)
    school = db.Column(db.String(255), nullable=True)

    # Address
    address = db.Column(db.Text, nullable=True)

    # Guardian info
    parent_name = db.Column(db.String(200), nullable=True)
    parent_contact = db.Column(db.String(20), nullable=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationship back to User
    user = db.relationship("User", backref=db.backref("student_profile", uselist=False))

    def __repr__(self):
        return f"<StudentProfile user_id={self.user_id}>"

    def to_dict(self):
        return {
            "profile_id": self.profile_id,
            "user_id": self.user_id,
            "whatsapp_number": self.whatsapp_number,
            "date_of_birth": self.date_of_birth.isoformat() if self.date_of_birth else None,
            "grade_level": self.grade_level,
            "school": self.school,
            "address": self.address,
            "parent_name": self.parent_name,
            "parent_contact": self.parent_contact,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
