"""
User Model
Represents user accounts with authentication and profile information
"""

from app import db
from datetime import datetime
import uuid


class User(db.Model):
    """
    User model for authentication and profile management.
    
    Attributes:
        user_id: UUID primary key (CHAR(36))
        username: Unique username auto-generated as {first_name}_{last_4_chars_of_user_id}
        email: Unique email address
        password_hash: Bcrypt hashed password (10+ rounds)
        first_name: User's first name
        last_name: User's last name
        phone: Optional phone number for OTP verification
        profile_picture_url: Optional profile picture URL
        bio: Optional user bio
        email_verified: Whether email is verified
        phone_verified: Whether phone is verified
        is_active: Whether user account is active
        created_at: Account creation timestamp
        updated_at: Last update timestamp
        last_login: Last successful login timestamp
        deleted_at: Soft deletion timestamp
    """
    
    __tablename__ = 'users'
    
    # Primary Key
    user_id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False
    )
    
    # Authentication Fields
    username = db.Column(
        db.String(100),
        unique=True,
        nullable=False,
        index=True
    )
    email = db.Column(
        db.String(255),
        unique=True,
        nullable=False,
        index=True
    )
    password_hash = db.Column(
        db.String(255),
        nullable=False
    )
    
    # Profile Information
    first_name = db.Column(
        db.String(100),
        nullable=False
    )
    last_name = db.Column(
        db.String(100),
        nullable=False
    )
    phone = db.Column(
        db.String(20),
        nullable=True
    )
    profile_picture_url = db.Column(
        db.Text,
        nullable=True
    )
    bio = db.Column(
        db.Text,
        nullable=True
    )
    
    # Verification Status
    email_verified = db.Column(
        db.Boolean,
        default=False,
        nullable=False,
        index=True
    )
    phone_verified = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )
    
    # Account Status
    is_active = db.Column(
        db.Boolean,
        default=True,
        nullable=False,
        index=True
    )
    
    # Timestamps
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    last_login = db.Column(
        db.DateTime,
        nullable=True
    )
    deleted_at = db.Column(
        db.DateTime,
        nullable=True
    )
    
    # Relationships
    roles = db.relationship(
        'UserRole',
        backref='user',
        lazy=True,
        cascade='all, delete-orphan'
    )
    account_status = db.relationship(
        'UserAccountStatus',
        backref='user',
        uselist=False,
        cascade='all, delete-orphan'
    )
    login_history = db.relationship(
        'LoginHistory',
        backref='user',
        lazy=True,
        cascade='all, delete-orphan'
    )
    login_failures = db.relationship(
        'LoginFailure',
        backref='user',
        lazy=True,
        cascade='all, delete-orphan'
    )
    otp_requests = db.relationship(
        'OTPRequest',
        backref='user',
        lazy=True,
        cascade='all, delete-orphan'
    )
    password_reset_tokens = db.relationship(
        'PasswordResetToken',
        backref='user',
        lazy=True,
        cascade='all, delete-orphan'
    )
    email_verification_tokens = db.relationship(
        'EmailVerificationToken',
        backref='user',
        lazy=True,
        cascade='all, delete-orphan'
    )
    
    def __repr__(self):
        return f"<User {self.username} ({self.email})>"
    
    def to_dict(self, include_password=False):
        """Convert user to dictionary representation."""
        data = {
            'user_id': self.user_id,
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'phone': self.phone,
            'profile_picture_url': self.profile_picture_url,
            'bio': self.bio,
            'email_verified': self.email_verified,
            'phone_verified': self.phone_verified,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
        }
        
        if include_password:
            data['password_hash'] = self.password_hash
        
        return data
