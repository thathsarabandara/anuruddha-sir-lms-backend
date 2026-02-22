"""
Refund Model
Represents refunds processed against transactions
"""

import uuid
from datetime import datetime

from app import db


class Refund(db.Model):
    """
    Refund model for tracking refund requests and processing

    Attributes:
        refund_id: Unique identifier (UUID)
        transaction_id: Reference to transaction being refunded
        user_id: Reference to user requesting refund
        refund_amount: Amount being refunded
        reason: Reason for refund request
        status: Refund status (pending/processing/completed/failed)
        stripe_refund_id: Stripe refund reference ID
        requested_at: Timestamp when refund was requested
        processed_at: Timestamp when refund was processed
    """

    __tablename__ = "refunds"

    # Primary Key
    refund_id = db.Column(
        db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False
    )

    # Foreign Keys
    transaction_id = db.Column(
        db.String(36), db.ForeignKey("transactions.transaction_id"), nullable=False, index=True
    )

    user_id = db.Column(db.String(36), db.ForeignKey("users.user_id"), nullable=False)

    # Data Fields
    refund_amount = db.Column(db.Numeric(10, 2), nullable=False)

    reason = db.Column(db.String(255), nullable=True)

    status = db.Column(
        db.Enum("pending", "processing", "completed", "failed"),
        default="pending",
        nullable=False,
        index=True,
    )

    stripe_refund_id = db.Column(db.String(255), nullable=True)

    # Timestamps
    requested_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    processed_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        """Serialize refund to dictionary"""
        return {
            "refund_id": self.refund_id,
            "transaction_id": self.transaction_id,
            "user_id": self.user_id,
            "refund_amount": float(self.refund_amount) if self.refund_amount else None,
            "reason": self.reason,
            "status": self.status,
            "stripe_refund_id": self.stripe_refund_id,
            "requested_at": self.requested_at.isoformat() if self.requested_at else None,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
        }

    def __repr__(self):
        return f"<Refund {self.refund_id} - {self.status}>"
