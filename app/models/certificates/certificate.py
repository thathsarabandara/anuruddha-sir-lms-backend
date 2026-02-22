"""
Certificate Model
Represents issued certificates for course completions and assessments
"""

import uuid
from datetime import datetime

from app import db


class Certificate(db.Model):
    """
    Certificate model for storing issued certificates

    Attributes:
        certificate_id: Unique identifier (UUID)
        course_id: Reference to course
        user_id: Reference to user (owner)
        template_id: Reference to certificate template
        certificate_code: Unique code for verification
        certificate_title: Title of the certificate
        student_name: Name of the student on certificate
        course_title: Name of the course on certificate
        instructor_name: Name of the instructor on certificate
        earned_score: Score earned by student
        issued_date: Date certificate was issued
        expires_date: Optional expiration date
        issued_at: Timestamp certificate was issued
        revoked_at: Optional revocation timestamp
        revocation_reason: Reason for revocation if revoked
        status: Certificate status (issued/revoked/expired)
        verification_count: Number of times verified
        last_verified: Last verification timestamp
    """

    __tablename__ = "certificates"

    # Primary Key
    certificate_id = db.Column(
        db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False
    )

    # Foreign Keys
    course_id = db.Column(
        db.String(36), db.ForeignKey("courses.course_id"), nullable=True, index=True
    )

    user_id = db.Column(
        db.String(36),
        db.ForeignKey("users.user_id", ondelete="CASCADE"),
    )

    template_id = db.Column(
        db.String(36), db.ForeignKey("certificate_templates.template_id"), nullable=True
    )

    # Data Fields
    certificate_code = db.Column(db.String(50), nullable=False, unique=True, index=True)

    certificate_title = db.Column(db.String(255), nullable=True)

    student_name = db.Column(db.String(255), nullable=True)

    course_title = db.Column(db.String(255), nullable=True)

    instructor_name = db.Column(db.String(255), nullable=True)

    earned_score = db.Column(db.Integer, nullable=True)

    issued_date = db.Column(db.Date, nullable=True, index=True)

    expires_date = db.Column(db.Date, nullable=True)

    status = db.Column(
        db.Enum("issued", "revoked", "expired"), default="issued", nullable=False, index=True
    )

    verification_count = db.Column(db.Integer, default=0, nullable=False)

    # Timestamps
    issued_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    revoked_at = db.Column(db.DateTime, nullable=True)

    last_verified = db.Column(db.DateTime, nullable=True)

    # Data Fields (continued)
    revocation_reason = db.Column(db.Text, nullable=True)

    # Relationships
    verification_logs = db.relationship(
        "CertificateVerificationLog", backref="certificate", cascade="all, delete-orphan", lazy=True
    )

    sharing_logs = db.relationship(
        "CertificateSharingLog", backref="certificate", cascade="all, delete-orphan", lazy=True
    )

    def to_dict(self):
        """Serialize certificate to dictionary"""
        return {
            "certificate_id": self.certificate_id,
            "course_id": self.course_id,
            "user_id": self.user_id,
            "template_id": self.template_id,
            "certificate_code": self.certificate_code,
            "certificate_title": self.certificate_title,
            "student_name": self.student_name,
            "course_title": self.course_title,
            "instructor_name": self.instructor_name,
            "earned_score": self.earned_score,
            "issued_date": str(self.issued_date) if self.issued_date else None,
            "expires_date": str(self.expires_date) if self.expires_date else None,
            "status": self.status,
            "verification_count": self.verification_count,
            "issued_at": self.issued_at.isoformat() if self.issued_at else None,
            "revoked_at": self.revoked_at.isoformat() if self.revoked_at else None,
            "last_verified": self.last_verified.isoformat() if self.last_verified else None,
            "revocation_reason": self.revocation_reason,
        }

    def __repr__(self):
        return f"<Certificate {self.certificate_code} - {self.student_name}>"
