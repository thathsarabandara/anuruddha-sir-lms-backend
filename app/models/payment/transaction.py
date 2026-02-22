"""
Transaction Model
Represents payment transactions for course purchases
"""

import uuid
from datetime import datetime

from app import db


class Transaction(db.Model):
    """
    Transaction model for payment processing and recording

    Attributes:
        transaction_id: Unique identifier (UUID)
        user_id: Reference to user making payment
        course_id: Reference to course being purchased
        amount: Base amount before discount/tax
        currency: Currency code (default USD)
        discount: Discount amount applied
        tax: Tax amount calculated
        total: Final total amount
        coupon_id: Reference to applied coupon
        payment_method_type: Type of payment method
        payment_method_token: Tokenized payment method
        stripe_transaction_id: Stripe transaction reference
        status: Transaction status (pending/completed/failed/refunded)
        failure_reason: Reason for failure if status is failed
        processed_at: Timestamp when transaction was processed
        created_at: Timestamp when transaction was created
        updated_at: Timestamp of last update
    """

    __tablename__ = "transactions"

    # Primary Key
    transaction_id = db.Column(
        db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False
    )

    # Foreign Keys
    user_id = db.Column(
        db.String(36),
        db.ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    course_id = db.Column(db.String(36), db.ForeignKey("courses.course_id"), nullable=False)

    coupon_id = db.Column(db.String(36), db.ForeignKey("coupons.coupon_id"), nullable=True)

    # Data Fields - Payment Details
    amount = db.Column(db.Numeric(10, 2), nullable=False)

    currency = db.Column(db.String(3), default="USD", nullable=False)

    discount = db.Column(db.Numeric(10, 2), default=0, nullable=False)

    tax = db.Column(db.Numeric(10, 2), default=0, nullable=False)

    total = db.Column(db.Numeric(10, 2), nullable=True)

    # Data Fields - Payment Method
    payment_method_type = db.Column(db.String(50), nullable=True)

    payment_method_token = db.Column(db.String(255), nullable=True)

    stripe_transaction_id = db.Column(db.String(255), nullable=True)

    # Data Fields - Status
    status = db.Column(
        db.Enum("pending", "completed", "failed", "refunded"),
        default="pending",
        nullable=False,
        index=True,
    )

    failure_reason = db.Column(db.Text, nullable=True)

    # Timestamps
    processed_at = db.Column(db.DateTime, nullable=True, index=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    invoice = db.relationship(
        "Invoice", backref="transaction", uselist=False, cascade="all, delete-orphan", lazy=True
    )

    refunds = db.relationship(
        "Refund", backref="transaction", cascade="all, delete-orphan", lazy=True
    )

    def to_dict(self):
        """Serialize transaction to dictionary"""
        return {
            "transaction_id": self.transaction_id,
            "user_id": self.user_id,
            "course_id": self.course_id,
            "coupon_id": self.coupon_id,
            "amount": float(self.amount) if self.amount else None,
            "currency": self.currency,
            "discount": float(self.discount) if self.discount else None,
            "tax": float(self.tax) if self.tax else None,
            "total": float(self.total) if self.total else None,
            "payment_method_type": self.payment_method_type,
            "stripe_transaction_id": self.stripe_transaction_id,
            "status": self.status,
            "failure_reason": self.failure_reason,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<Transaction {self.transaction_id} - {self.status}>"
