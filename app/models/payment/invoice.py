"""
Invoice Model
Represents invoices generated from transactions
"""

from app import db
from datetime import datetime
import uuid

class Invoice(db.Model):
    """
    Invoice model for transaction invoicing and record-keeping
    
    Attributes:
        invoice_id: Unique identifier (UUID)
        transaction_id: Reference to transaction (unique one-to-one)
        invoice_number: Unique invoice number for tracking
        user_id: Reference to user (invoice owner)
        subtotal: Subtotal before discount/tax
        discount: Discount applied to invoice
        tax: Tax amount on invoice
        total: Final invoice total
        currency: Currency code
        status: Invoice status (draft/issued/paid/overdue/cancelled)
        issued_date: Date invoice was issued
        due_date: Optional due date for payment
        paid_at: Timestamp when invoice was paid
        created_at: Timestamp when invoice was created
    """
    
    __tablename__ = 'invoices'
    
    # Primary Key
    invoice_id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False
    )
    
    # Foreign Keys
    transaction_id = db.Column(
        db.String(36),
        db.ForeignKey('transactions.transaction_id'),
        nullable=False,
        unique=True
    )
    
    user_id = db.Column(
        db.String(36),
        db.ForeignKey('users.user_id'),
        nullable=False
    )
    
    # Data Fields - Invoice Details
    invoice_number = db.Column(
        db.String(50),
        nullable=False,
        unique=True,
        index=True
    )
    
    subtotal = db.Column(
        db.Numeric(10, 2),
        nullable=True
    )
    
    discount = db.Column(
        db.Numeric(10, 2),
        default=0,
        nullable=False
    )
    
    tax = db.Column(
        db.Numeric(10, 2),
        default=0,
        nullable=False
    )
    
    total = db.Column(
        db.Numeric(10, 2),
        nullable=True
    )
    
    currency = db.Column(
        db.String(3),
        default='USD',
        nullable=False
    )
    
    # Data Fields - Status
    status = db.Column(
        db.Enum('draft', 'issued', 'paid', 'overdue', 'cancelled'),
        default='issued',
        nullable=False,
        index=True
    )
    
    # Data Fields - Dates
    issued_date = db.Column(
        db.Date,
        nullable=True
    )
    
    due_date = db.Column(
        db.Date,
        nullable=True
    )
    
    # Timestamps
    paid_at = db.Column(
        db.DateTime,
        nullable=True
    )
    
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    
    def to_dict(self):
        """Serialize invoice to dictionary"""
        return {
            'invoice_id': self.invoice_id,
            'transaction_id': self.transaction_id,
            'user_id': self.user_id,
            'invoice_number': self.invoice_number,
            'subtotal': float(self.subtotal) if self.subtotal else None,
            'discount': float(self.discount) if self.discount else None,
            'tax': float(self.tax) if self.tax else None,
            'total': float(self.total) if self.total else None,
            'currency': self.currency,
            'status': self.status,
            'issued_date': str(self.issued_date) if self.issued_date else None,
            'due_date': str(self.due_date) if self.due_date else None,
            'paid_at': self.paid_at.isoformat() if self.paid_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Invoice {self.invoice_number}>'
