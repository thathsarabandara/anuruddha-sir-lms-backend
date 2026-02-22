"""
Coupon Model
Represents discount coupons for course purchases
"""

from app import db
from datetime import datetime
import uuid
import json

class Coupon(db.Model):
    """
    Coupon model for managing discount codes and promotions
    
    Attributes:
        coupon_id: Unique identifier (UUID)
        coupon_code: Unique coupon code for validation
        discount_type: Type of discount (percentage or fixed)
        discount_value: Value of discount (percentage or amount)
        applicable_courses: JSON list of applicable course IDs
        max_uses: Maximum number of times coupon can be used
        current_uses: Current number of times coupon has been used
        expires_at: Expiration timestamp for coupon
        created_by: User ID of coupon creator
        created_at: Timestamp when coupon was created
    """
    
    __tablename__ = 'coupons'
    
    # Primary Key
    coupon_id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False
    )
    
    # Foreign Keys
    created_by = db.Column(
        db.String(36),
        db.ForeignKey('users.user_id'),
        nullable=True
    )
    
    # Data Fields - Coupon Details
    coupon_code = db.Column(
        db.String(50),
        nullable=False,
        unique=True,
        index=True
    )
    
    discount_type = db.Column(
        db.Enum('percentage', 'fixed'),
        default='percentage',
        nullable=False
    )
    
    discount_value = db.Column(
        db.Numeric(10, 2),
        nullable=False
    )
    
    applicable_courses = db.Column(
        db.JSON,
        nullable=True
    )
    
    # Data Fields - Usage
    max_uses = db.Column(
        db.Integer,
        nullable=True
    )
    
    current_uses = db.Column(
        db.Integer,
        default=0,
        nullable=False
    )
    
    # Data Fields - Expiration
    expires_at = db.Column(
        db.DateTime,
        nullable=True,
        index=True
    )
    
    # Timestamps
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    
    # Relationships
    transactions = db.relationship(
        'Transaction',
        backref='coupon',
        lazy=True
    )
    
    def get_applicable_courses(self):
        """Get applicable courses list safely"""
        if self.applicable_courses and isinstance(self.applicable_courses, list):
            return self.applicable_courses
        elif self.applicable_courses and isinstance(self.applicable_courses, str):
            try:
                return json.loads(self.applicable_courses)
            except (json.JSONDecodeError, TypeError):
                return []
        return []
    
    def set_applicable_courses(self, courses):
        """Set applicable courses list safely"""
        if isinstance(courses, list):
            self.applicable_courses = courses
        elif isinstance(courses, str):
            try:
                self.applicable_courses = json.loads(courses)
            except (json.JSONDecodeError, TypeError):
                self.applicable_courses = []
        else:
            self.applicable_courses = []
    
    def is_valid(self):
        """Check if coupon is still valid"""
        now = datetime.utcnow()
        if self.expires_at and self.expires_at < now:
            return False
        if self.max_uses and self.current_uses >= self.max_uses:
            return False
        return True
    
    def to_dict(self):
        """Serialize coupon to dictionary"""
        return {
            'coupon_id': self.coupon_id,
            'coupon_code': self.coupon_code,
            'discount_type': self.discount_type,
            'discount_value': float(self.discount_value) if self.discount_value else None,
            'applicable_courses': self.get_applicable_courses(),
            'max_uses': self.max_uses,
            'current_uses': self.current_uses,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_valid': self.is_valid()
        }
    
    def __repr__(self):
        return f'<Coupon {self.coupon_code}>'
