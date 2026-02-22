"""
CertificateVerificationLog Model
Tracks certificate verification attempts and audits
"""

import uuid
from datetime import datetime

from app import db


class CertificateVerificationLog(db.Model):
    """
    Certificate verification log model for audit trail

    Attributes:
        verification_id: Unique identifier (UUID)
        certificate_id: Reference to certificate
        verified_by: User ID of verifier (optional)
        verification_code: Code used for verification
        verified_at: Timestamp of verification
        ip_address: IP address of verifier
        verification_method: Method used (manual/qr/api)
    """

    __tablename__ = "certificate_verification_log"

    # Primary Key
    verification_id = db.Column(
        db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False
    )

    # Foreign Keys
    certificate_id = db.Column(
        db.String(36),
        db.ForeignKey("certificates.certificate_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    verified_by = db.Column(db.String(36), db.ForeignKey("users.user_id"), nullable=True)

    # Data Fields
    verification_code = db.Column(db.String(50), nullable=True)

    ip_address = db.Column(db.String(45), nullable=True)

    verification_method = db.Column(db.String(50), nullable=True)

    # Timestamps
    verified_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    def to_dict(self):
        """Serialize verification log to dictionary"""
        return {
            "verification_id": self.verification_id,
            "certificate_id": self.certificate_id,
            "verified_by": self.verified_by,
            "verification_code": self.verification_code,
            "ip_address": self.ip_address,
            "verification_method": self.verification_method,
            "verified_at": self.verified_at.isoformat() if self.verified_at else None,
        }

    def __repr__(self):
        return f"<CertificateVerificationLog {self.certificate_id}>"
