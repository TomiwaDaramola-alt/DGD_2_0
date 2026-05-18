# =============================================================================
# DGD 2.0 — DGD CONSULT AU
# Core Package Initialization
# Location: core/__init__.py
#
# Exposes the intelligence and billing modules at package level.
# Import from core import RuleEngine, BillingManager, etc.
# =============================================================================

from .intelligence import (
    RuleEngine,
    RuleResult,
    RuleSeverity,
    RuleCategory,
    NotificationCue,
    create_default_engine
)

from .secure_billing import (
    PaymentStatus,
    PaymentMethod,
    BillingFrequency,
    BillingAddress,
    PaymentInstrument,
    LineItem,
    TransactionRecord,
    PaymentGateway,
    BillingManager,
    StubGateway
)

__all__ = [
    # Intelligence exports
    "RuleEngine",
    "RuleResult", 
    "RuleSeverity",
    "RuleCategory",
    "NotificationCue",
    "create_default_engine",
    # Billing exports
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
