"""
Refresh Token Model
Tracks issued JWT refresh tokens
"""

import uuid
from datetime import datetime

from app import db


class RefreshToken(db.Model):
    """
    Refresh Token model for tracking issued JWT refresh tokens.

    Attributes:
        token_id: UUID primary key
        user_id: Foreign key to User
        token: The JWT refresh token (hashed for security)
        token_jti: JWT ID claim (unique identifier within JWT)
        issued_at: When the token was issued
        expires_at: When the token expires
        is_revoked: Whether the token has been revoked (e.g., on logout)
        revoked_at: When the token was revoked
        is_used: Whether this refresh token has been used to get a new access token
        used_at: When the token was used
        ip_address: IP address from which token was issued
        user_agent: User agent when token was issued
    """

    __tablename__ = "refresh_tokens"

    # Primary Key
    token_id = db.Column(
        db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False
    )

    # Foreign Keys
    user_id = db.Column(
        db.String(36), db.ForeignKey("users.user_id"), nullable=False, index=True
    )

    # Token Data
    token = db.Column(db.Text, nullable=False)  # Full JWT token
    token_jti = db.Column(db.String(255), unique=True, nullable=True, index=True)  # JWT ID claim
    issued_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=False, index=True)
    is_revoked = db.Column(db.Boolean, default=False, nullable=False, index=True)
    revoked_at = db.Column(db.DateTime, nullable=True)

    # Usage Tracking
    is_used = db.Column(db.Boolean, default=False, nullable=False)
    used_at = db.Column(db.DateTime, nullable=True)

    # Request Metadata
    ip_address = db.Column(db.String(45), nullable=True)  # Support IPv6
    user_agent = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f"<RefreshToken {self.token_id} for user {self.user_id}>"

    def revoke(self):
        """Mark token as revoked"""
        self.is_revoked = True
        self.revoked_at = datetime.utcnow()
        db.session.commit()

    def mark_used(self):
        """Mark token as used"""
        self.is_used = True
        self.used_at = datetime.utcnow()
        db.session.commit()

    def is_expired(self):
        """Check if token has expired"""
        return datetime.utcnow() > self.expires_at

    def is_valid(self):
        """Check if token is valid (not expired and not revoked)"""
        return not self.is_expired() and not self.is_revoked
