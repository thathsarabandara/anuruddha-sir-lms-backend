"""
CertificateSharingLog Model
Tracks certificate sharing activities across platforms
"""

from app import db
from datetime import datetime
import uuid

class CertificateSharingLog(db.Model):
    """
    Certificate sharing log model for tracking sharing activities
    
    Attributes:
        sharing_id: Unique identifier (UUID)
        certificate_id: Reference to certificate
        shared_by: User ID of sharer
        platform: Platform shared to (linkedin/twitter/email/etc)
        recipient_email: Email of recipient (for email sharing)
        shared_at: Timestamp of sharing
    """
    
    __tablename__ = 'certificate_sharing_log'
    
    # Primary Key
    sharing_id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False
    )
    
    # Foreign Keys
    certificate_id = db.Column(
        db.String(36),
        db.ForeignKey('certificates.certificate_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    shared_by = db.Column(
        db.String(36),
        db.ForeignKey('users.user_id'),
        nullable=False
    )
    
    # Data Fields
    platform = db.Column(
        db.String(50),
        nullable=True
    )
    
    recipient_email = db.Column(
        db.String(255),
        nullable=True
    )
    
    # Timestamps
    shared_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )
    
    def to_dict(self):
        """Serialize sharing log to dictionary"""
        return {
            'sharing_id': self.sharing_id,
            'certificate_id': self.certificate_id,
            'shared_by': self.shared_by,
            'platform': self.platform,
            'recipient_email': self.recipient_email,
            'shared_at': self.shared_at.isoformat() if self.shared_at else None
        }
    
    def __repr__(self):
        return f'<CertificateSharingLog {self.sharing_id}>'
