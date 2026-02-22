"""
UserProfile Model
Represents user profile information and extended profile data
"""

from app import db
from datetime import datetime
import uuid
import json


class UserProfile(db.Model):
    """
    UserProfile model for extended user profile information.
    
    Attributes:
        profile_id: UUID primary key
        user_id: Foreign key to users table (unique)
        bio: User biography/about section
        profile_picture_url: URL to profile picture on CDN
        phone_verified: Whether phone is verified
        identity_verified: Whether user identity is verified (for teachers/admins)
        location: User's location (city/country)
        organization: User's organization/company
        website_url: User's website URL
        social_links: JSON object with social media links
        created_at: Profile creation timestamp
        updated_at: Last update timestamp
    """
    
    __tablename__ = 'user_profiles'
    
    # Primary Key
    profile_id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False
    )
    
    # Foreign Key
    user_id = db.Column(
        db.String(36),
        db.ForeignKey('users.user_id', ondelete='CASCADE'),
        unique=True,
        nullable=False,
        index=True
    )
    
    # Profile Information
    bio = db.Column(
        db.Text,
        nullable=True
    )
    profile_picture_url = db.Column(
        db.Text,
        nullable=True
    )
    phone_verified = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )
    identity_verified = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )
    
    # Additional Info
    location = db.Column(
        db.String(255),
        nullable=True
    )
    organization = db.Column(
        db.String(255),
        nullable=True
    )
    website_url = db.Column(
        db.String(255),
        nullable=True
    )
    social_links = db.Column(
        db.Text,
        nullable=True
    )
    
    # Timestamps
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    def __repr__(self):
        return f"<UserProfile user_id={self.user_id}>"
    
    def get_social_links(self):
        """Parse social links from JSON."""
        if not self.social_links:
            return {}
        try:
            return json.loads(self.social_links)
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def set_social_links(self, links):
        """Set social links from dict."""
        self.social_links = json.dumps(links) if links else None
    
    def to_dict(self):
        """Convert user profile to dictionary representation."""
        return {
            'profile_id': self.profile_id,
            'user_id': self.user_id,
            'bio': self.bio,
            'profile_picture_url': self.profile_picture_url,
            'phone_verified': self.phone_verified,
            'identity_verified': self.identity_verified,
            'location': self.location,
            'organization': self.organization,
            'website_url': self.website_url,
            'social_links': self.get_social_links(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
