"""
TeacherProfile Model
Stores teacher-specific registration and profile information
"""

import json
import uuid
from datetime import datetime

from app import db


class TeacherProfile(db.Model):
    """
    Extended profile for users with the 'teacher' role.

    Attributes:
        profile_id:               UUID primary key
        user_id:                  FK to users.user_id (1-to-1)
        qualifications:           Academic / professional qualifications (text)
        subjects_taught:          JSON array of subjects (e.g. ["Maths","Physics"])
        years_of_experience:      Integer years in teaching
        language_of_instruction:  Primary teaching language (e.g. "English", "Sinhala")
        professional_bio:         Detailed professional biography
        address:                  Physical / mailing address
        created_at:               Row creation timestamp
        updated_at:               Last update timestamp
    """

    __tablename__ = "teacher_profiles"

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

    # Professional info
    qualifications = db.Column(db.Text, nullable=True)
    subjects_taught = db.Column(db.Text, nullable=True)        # JSON array stored as text
    years_of_experience = db.Column(db.Integer, nullable=True)
    language_of_instruction = db.Column(db.String(100), nullable=True)
    professional_bio = db.Column(db.Text, nullable=True)

    # Address
    address = db.Column(db.Text, nullable=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationship back to User
    user = db.relationship("User", backref=db.backref("teacher_profile", uselist=False))

    def __repr__(self):
        return f"<TeacherProfile user_id={self.user_id}>"

    # ── Subject helpers ──────────────────────────────────────────────────────

    def get_subjects(self):
        """Return subjects as a Python list."""
        if not self.subjects_taught:
            return []
        try:
            return json.loads(self.subjects_taught)
        except (json.JSONDecodeError, TypeError):
            return []

    def set_subjects(self, subjects):
        """Persist subjects from a list."""
        self.subjects_taught = json.dumps(subjects) if subjects else None

    # ── Serialisation ────────────────────────────────────────────────────────

    def to_dict(self):
        return {
            "profile_id": self.profile_id,
            "user_id": self.user_id,
            "qualifications": self.qualifications,
            "subjects_taught": self.get_subjects(),
            "years_of_experience": self.years_of_experience,
            "language_of_instruction": self.language_of_instruction,
            "professional_bio": self.professional_bio,
            "address": self.address,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
