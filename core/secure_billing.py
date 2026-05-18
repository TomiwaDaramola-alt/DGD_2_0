# =============================================================================
# DGD 2.0 — DGD CONSULT AU
# Secure Billing Module: Abstract Payment Integration Infrastructure
# Location: core/secure_billing.py
#
# Purpose: Defines the interface contract and data structures for payment
# processing. Does not implement specific gateway logic — instead provides
# the architectural foundation for plugging in Stripe, PayPal, or other
# processors without modifying business logic elsewhere.
# =============================================================================

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod
import uuid


# -----------------------------------------------------------------------------
# Payment Domain Enumerations
# -----------------------------------------------------------------------------

class PaymentStatus(Enum):
    """Lifecycle states for a payment transaction."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    DISPUTED = "disputed"
    CANCELLED = "cancelled"


class PaymentMethod(Enum):
    """Supported payment instrument types."""
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    BANK_TRANSFER = "bank_transfer"
    DIRECT_DEBIT = "direct_debit"
    CASH = "cash"
    CHEQUE = "cheque"


class BillingFrequency(Enum):
    """Recurring billing cadence options."""
    ONE_TIME = "one_time"
    WEEKLY = "weekly"
    FORTNIGHTLY = "fortnightly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUALLY = "annually"


# -----------------------------------------------------------------------------
# Data Transfer Objects (DTOs)
# -----------------------------------------------------------------------------

@dataclass
class BillingAddress:
    """Standardized address structure for invoicing and compliance."""
    line_1: str
    line_2: Optional[str] = None
    city: str = ""
    state: str = ""
    postal_code: str = ""
    country: str = "AU"
    
    def to_dict(self) -> Dict[str, str]:
        return {
            "line_1": self.line_1,
            "line_2": self.line_2 or "",
            "city": self.city,
            "state": self.state,
            "postal_code": self.postal_code,
            "country": self.country
        }


@dataclass
class PaymentInstrument:
    """
    Tokenized representation of a payment method.
    Never stores raw card numbers — only tokens and metadata.
    """
    instrument_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    method_type: PaymentMethod = PaymentMethod.CREDIT_CARD
    token_reference: Optional[str] = None  # Gateway-provided token
    last_four_digits: Optional[str] = None
    expiry_month: Optional[int] = None
    expiry_year: Optional[int] = None
    card_brand: Optional[str] = None  # visa, mastercard, amex, etc.
    is_default: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    
    def is_expired(self) -> bool:
        """Check if instrument has passed expiry date."""
        if not self.expiry_month or not self.expiry_year:
            return False
        now = datetime.now()
        return (self.expiry_year < now.year or 
                (self.expiry_year == now.year and self.expiry_month < now.month))


@dataclass
class LineItem:
    """Individual chargeable item on an invoice or transaction."""
    item_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ""
    quantity: float = 1.0
    unit_price_cents: int = 0  # Always store currency in smallest unit
    tax_rate_percent: float = 10.0  # Australian GST default
    sku_reference: Optional[str] = None
    
    @property
    def subtotal_cents(self) -> int:
        """Calculate line total before tax."""
        return int(self.quantity * self.unit_price_cents)
    
    @property
    def tax_amount_cents(self) -> int:
        """Calculate tax component."""
        return int(self.subtotal_cents * (self.tax_rate_percent / 100))
    
    @property
    def total_cents(self) -> int:
        """Calculate inclusive total."""
        return self.subtotal_cents + self.tax_amount_cents


@dataclass
class TransactionRecord:
    """
    Immutable record of a payment attempt.
    Created before gateway interaction and updated with result.
    """
    transaction_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    client_id: int = 0
    staff_id: Optional[int] = None  # Who authorized/serviced
    invoice_reference: Optional[str] = None
    
    amount_cents: int = 0
    currency: str = "AUD"
    status: PaymentStatus = PaymentStatus.PENDING
    
    instrument: Optional[PaymentInstrument] = None
    line_items: List[LineItem] = field(default_factory=list)
    
    gateway_reference: Optional[str] = None
    gateway_response: Optional[Dict[str, Any]] = None
    failure_reason: Optional[str] = None
    
    created_at: datetime = field(default_factory=datetime.now)
    processed_at: Optional[datetime] = None
    
    @property
    def total_amount_cents(self) -> int:
        """Sum all line items."""
        return sum(item.total_cents for item in self.line_items)


# -----------------------------------------------------------------------------
# Abstract Gateway Interface (Strategy Pattern)
# -----------------------------------------------------------------------------

class PaymentGateway(ABC):
    """
    Abstract base class for all payment processor integrations.
    Concrete implementations must override all abstract methods.
    
    This design allows the application to swap payment providers
    without changing any billing logic in route handlers.
    """
    
    @abstractmethod
    def initialize(self, config: Dict[str, str]) -> bool:
        """
        Configure gateway with API keys, endpoints, and environment settings.
        Returns True if initialization successful.
        """
        pass
    
    @abstractmethod
    def charge(self, transaction: TransactionRecord) -> TransactionRecord:
        """
        Execute a charge against the gateway.
        Must update transaction.status and transaction.gateway_reference.
        """
        pass
    
    @abstractmethod
    def refund(self, transaction: TransactionRecord, 
               amount_cents: Optional[int] = None) -> TransactionRecord:
        """
        Process a partial or full refund.
        If amount_cents is None, refund full amount.
        """
        pass
    
    @abstractmethod
    def tokenize_instrument(self, instrument: PaymentInstrument) -> PaymentInstrument:
        """
        Convert raw payment details to a secure token.
        Never persists raw card data — return tokenized version only.
        """
        pass
    
    @abstractmethod
    def validate_instrument(self, instrument: PaymentInstrument) -> bool:
        """
        Pre-flight validation without charging.
        Checks format, expiry, and gateway acceptance.
        """
        pass


# -----------------------------------------------------------------------------
# Billing Manager (Facade Pattern)
# -----------------------------------------------------------------------------

class BillingManager:
    """
    High-level billing coordinator.
    Business logic calls this class — never interacts with gateways directly.
    
    Responsibilities:
    - Transaction lifecycle management
    - Instrument storage and retrieval
    - Invoice generation and tracking
    - Reconciliation reporting
    """
    
    def __init__(self):
        self._gateway: Optional[PaymentGateway] = None
        self._transaction_log: List[TransactionRecord] = []
        self._instruments: Dict[str, PaymentInstrument] = {}
    
    def set_gateway(self, gateway: PaymentGateway, 
                    config: Dict[str, str]) -> bool:
        """
        Inject and initialize a payment gateway implementation.
        Call this during application startup.
        """
        self._gateway = gateway
        return gateway.initialize(config)
    
    def create_transaction(self, client_id: int,
                           line_items: List[LineItem],
                           instrument_id: Optional[str] = None) -> TransactionRecord:
        """
        Build a new transaction record in PENDING state.
        Does not execute charge — call process_transaction() next.
        """
        tx = TransactionRecord(
            client_id=client_id,
            line_items=line_items,
            instrument=self._instruments.get(instrument_id) if instrument_id else None
        )
        self._transaction_log.append(tx)
        return tx
    
    def process_transaction(self, transaction: TransactionRecord) -> TransactionRecord:
        """
        Execute charge through configured gateway.
        Updates and returns the transaction with final status.
        """
        if not self._gateway:
            transaction.status = PaymentStatus.FAILED
            transaction.failure_reason = "No payment gateway configured"
            return transaction
        
        if not transaction.instrument:
            transaction.status = PaymentStatus.FAILED
            transaction.failure_reason = "No payment instrument attached"
            return transaction
        
        # Pre-validate instrument
        if not self._gateway.validate_instrument(transaction.instrument):
            transaction.status = PaymentStatus.FAILED
            transaction.failure_reason = "Instrument validation failed"
            return transaction
        
        # Execute charge through gateway
        result = self._gateway.charge(transaction)
        result.processed_at = datetime.now()
        return result
    
    def store_instrument(self, instrument: PaymentInstrument) -> str:
        """
        Tokenize and persist a payment instrument for future use.
        Returns the instrument_id for reference.
        """
        if self._gateway:
            instrument = self._gateway.tokenize_instrument(instrument)
        self._instruments[instrument.instrument_id] = instrument
        return instrument.instrument_id
    
    def get_client_transactions(self, client_id: int) -> List[TransactionRecord]:
        """Retrieve all transaction history for a specific client."""
        return [tx for tx in self._transaction_log if tx.client_id == client_id]
    
    def generate_reconciliation_report(self, 
                                        start_date: datetime,
                                        end_date: datetime) -> Dict[str, Any]:
        """
        Aggregate transaction data for accounting reconciliation.
        Returns summary statistics and itemized breakdown.
        """
        period_tx = [
            tx for tx in self._transaction_log
            if start_date <= tx.created_at <= end_date
        ]
        
        completed = [tx for tx in period_tx 
                    if tx.status == PaymentStatus.COMPLETED]
        
        return {
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
            "total_transactions": len(period_tx),
            "completed_count": len(completed),
            "total_revenue_cents": sum(tx.total_amount_cents for tx in completed),
            "total_fees_cents": 0,  # Placeholder for gateway fee calculation
            "net_revenue_cents": sum(tx.total_amount_cents for tx in completed),
            "currency": "AUD",
            "status_breakdown": {
                status.value: sum(1 for tx in period_tx if tx.status == status)
                for status in PaymentStatus
            }
        }


# -----------------------------------------------------------------------------
# Stub Gateway Implementation
# For development and testing without live payment processing
# -----------------------------------------------------------------------------

class StubGateway(PaymentGateway):
    """
    No-op gateway that simulates payment operations.
    Always succeeds. Use for development and CI testing.
    """
    
    def initialize(self, config: Dict[str, str]) -> bool:
        return True
    
    def charge(self, transaction: TransactionRecord) -> TransactionRecord:
        transaction.status = PaymentStatus.COMPLETED
        transaction.gateway_reference = f"STUB-{uuid.uuid4().hex[:12].upper()}"
        return transaction
    
    def refund(self, transaction: TransactionRecord, 
               amount_cents: Optional[int] = None) -> TransactionRecord:
        transaction.status = PaymentStatus.REFUNDED
        return transaction
    
    def tokenize_instrument(self, instrument: PaymentInstrument) -> PaymentInstrument:
        instrument.token_reference = f"tok_stub_{uuid.uuid4().hex[:16]}"
        return instrument
    
    def validate_instrument(self, instrument: PaymentInstrument) -> bool:
        return not instrument.is_expired()


# =============================================================================
# Module Exports
# =============================================================================

__all__ = [
    "PaymentStatus",
    "PaymentMethod",
    "BillingFrequency",
    "BillingAddress",
    "PaymentInstrument",
    "LineItem",
    "TransactionRecord",
    "PaymentGateway",
    "BillingManager",
    "StubGateway"
]
