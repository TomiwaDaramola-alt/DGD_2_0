# =============================================================================
# DGD 2.0 — DGD CONSULT AU
# Core Intelligence Module: Localized Rule Engine
# Location: core/intelligence.py
# 
# Purpose: Independent rule evaluation engine. No external AI frameworks.
# Validates data completeness, evaluates business rules, manages operational
# flags, and generates notification cues for the notification subsystem.
# =============================================================================

from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable
import json


# -----------------------------------------------------------------------------
# Data Structures for Rule Definitions
# -----------------------------------------------------------------------------

class RuleSeverity(Enum):
    """Classification hierarchy for rule evaluation outcomes."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    BLOCKING = "blocking"


class RuleCategory(Enum):
    """Domain classification for organizing rule sets."""
    DATA_COMPLETENESS = "data_completeness"
    VALIDATION = "validation"
    COMPLIANCE = "compliance"
    OPERATIONAL = "operational"
    BILLING = "billing"


@dataclass
class RuleResult:
    """
    Standardized output container for every rule evaluation.
    Immutable record of what was checked and what was found.
    """
    rule_id: str
    rule_name: str
    category: RuleCategory
    severity: RuleSeverity
    passed: bool
    message: str
    field_path: Optional[str] = None  # Dot-notation path to affected field
    suggestion: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize for database storage or API transmission."""
        return {
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "category": self.category.value,
            "severity": self.severity.value,
            "passed": self.passed,
            "message": self.message,
            "field_path": self.field_path,
            "suggestion": self.suggestion,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class NotificationCue:
    """
    Trigger object generated when rules detect actionable conditions.
    Consumed by the notification dispatcher (not implemented here).
    """
    cue_id: str
    target_entity: str  # 'staff', 'client', 'admin', 'system'
    target_id: Optional[int]
    priority: RuleSeverity
    title: str
    body: str
    action_required: bool = False
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


# -----------------------------------------------------------------------------
# The Rule Engine Core
# -----------------------------------------------------------------------------

class RuleEngine:
    """
    Centralized rule evaluation system.
    Maintains a registry of callable rules and executes them against data objects.
    
    Design pattern: Registry + Strategy. Rules are registered functions
    that accept a data context and return RuleResult objects.
    """
    
    def __init__(self):
        # Registry maps rule_id to (callable_rule, category, default_severity)
        self._rules: Dict[str, tuple] = {}
        # Operational flags are boolean state markers set by rule outcomes
        self._flags: Dict[str, Any] = {}
        # Notification queue holds cues awaiting dispatch
        self._notification_queue: List[NotificationCue] = []
    
    # -------------------------------------------------------------------------
    # Rule Registration API
    # -------------------------------------------------------------------------
    
    def register_rule(self, rule_id: str, category: RuleCategory,
                    severity: RuleSeverity, rule_func: Callable):
        """
        Explicit rule registration mechanism.
        Associates a validation function with metadata for cataloging.
        """
        self._rules[rule_id] = (rule_func, category, severity)
        return rule_func
    
    def unregister_rule(self, rule_id: str):
        """Remove a rule from the active registry."""
        if rule_id in self._rules:
            del self._rules[rule_id]
    
    # -------------------------------------------------------------------------
    # Flag Management API
    # -------------------------------------------------------------------------
    
    def set_flag(self, flag_name: str, value: Any, 
                 expires: Optional[datetime] = None):
        """
        Set an operational flag. Flags are transient state indicators
        used by other subsystems to make conditional decisions.
        """
        self._flags[flag_name] = {
            "value": value,
            "set_at": datetime.now(),
            "expires_at": expires
        }
    
    def get_flag(self, flag_name: str) -> Optional[Any]:
        """Retrieve flag value if present and not expired."""
        if flag_name not in self._flags:
            return None
        flag = self._flags[flag_name]
        if flag["expires_at"] and datetime.now() > flag["expires_at"]:
            del self._flags[flag_name]
            return None
        return flag["value"]
    
    def clear_flag(self, flag_name: str):
        """Explicitly remove a flag."""
        self._flags.pop(flag_name, None)
    
    # -------------------------------------------------------------------------
    # Evaluation Engine
    # -------------------------------------------------------------------------
    
    def evaluate(self, context: Dict[str, Any], 
                 category_filter: Optional[RuleCategory] = None) -> List[RuleResult]:
        """
        Execute all registered rules against a data context.
        Returns ordered list of RuleResult objects.
        """
        results: List[RuleResult] = []
        
        for rule_id, (rule_func, category, default_severity) in self._rules.items():
            if category_filter and category != category_filter:
                continue
            
            try:
                passed, message, extras = self._safe_execute(rule_func, context)
                severity = RuleSeverity.INFO if passed else default_severity
                
                result = RuleResult(
                    rule_id=rule_id,
                    rule_name=rule_func.__name__,
                    category=category,
                    severity=severity,
                    passed=passed,
                    message=message,
                    field_path=extras.get("field_path"),
                    suggestion=extras.get("suggestion")
                )
                results.append(result)
                
                if not passed and severity in (RuleSeverity.CRITICAL, RuleSeverity.BLOCKING):
                    self._generate_cue(result, context)
                    
            except Exception as e:
                results.append(RuleResult(
                    rule_id=rule_id,
                    rule_name=rule_func.__name__,
                    category=category,
                    severity=RuleSeverity.CRITICAL,
                    passed=False,
                    message=f"Rule engine execution error: {str(e)}",
                    suggestion="Contact system administrator"
                ))
        
        severity_order = {
            RuleSeverity.BLOCKING: 0,
            RuleSeverity.CRITICAL: 1,
            RuleSeverity.WARNING: 2,
            RuleSeverity.INFO: 3
        }
        results.sort(key=lambda r: severity_order.get(r.severity, 99))
        return results
    
    def _safe_execute(self, rule_func: Callable, context: Dict[str, Any]):
        """Ensures consistent return format from all rules: (passed, message, extras_dict)"""
        raw = rule_func(context)
        if isinstance(raw, tuple):
            if len(raw) == 2:
                return raw[0], raw[1], {}
            elif len(raw) >= 3:
                return raw[0], raw[1], raw[2] if isinstance(raw[2], dict) else {}
        return bool(raw), "Rule evaluated", {}
    
    # -------------------------------------------------------------------------
    # Notification Cue Generation
    # -------------------------------------------------------------------------
    
    def _generate_cue(self, result: RuleResult, context: Dict[str, Any]):
        """Convert a critical rule failure into a notification cue."""
        cue = NotificationCue(
            cue_id=f"CUE-{result.rule_id}-{datetime.now().timestamp()}",
            target_entity="admin",
            target_id=context.get("admin_id"),
            priority=result.severity,
            title=f"Rule Violation: {result.rule_name}",
            body=result.message,
            action_required=result.severity == RuleSeverity.BLOCKING,
            metadata=result.to_dict()
        )
        self._notification_queue.append(cue)
    
    def flush_cues(self) -> List[NotificationCue]:
        """Retrieve and clear all pending notification cues."""
        cues = self._notification_queue.copy()
        self._notification_queue.clear()
        return cues
    
    # -------------------------------------------------------------------------
    # Batch Operations
    # -------------------------------------------------------------------------
    
    def evaluate_entity(self, entity_type: str, entity_data: Dict[str, Any],
                       related: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """High-level convenience method for single-entity validation."""
        context = {entity_type: entity_data}
        if related:
            context.update(related)
        
        results = self.evaluate(context)
        all_passed = all(r.passed for r in results)
        self.set_flag(f"{entity_type}_valid", all_passed)
        
        return {
            "entity_type": entity_type,
            "valid": all_passed,
            "results": [r.to_dict() for r in results],
            "critical_count": sum(1 for r in results if r.severity == RuleSeverity.CRITICAL),
            "warning_count": sum(1 for r in results if r.warning == RuleSeverity.WARNING)
        }


# =============================================================================
# Pre-defined Business Rules for DGD CONSULT AU
# =============================================================================

def create_default_engine() -> RuleEngine:
    """
    Factory function that builds a fully configured rule engine
    with all DGD business rules pre-registered.
    """
    engine = RuleEngine()

    # --- RULE DEFINITIONS ---

    def rule_staff_name(ctx):
        """Validate staff member has a full name recorded."""
        staff = ctx.get("staff", {})
        name = staff.get("full_name", "").strip() if staff.get("full_name") else staff.get("name", "").strip()
        if not name:
            return False, "Staff record missing full name", {
                "field_path": "staff.full_name",
                "suggestion": "Enter legal full name as appears on ID"
            }
        if len(name) < 2:
            return False, "Staff name appears incomplete", {
                "field_path": "staff.full_name",
                "suggestion": "Verify name length and completeness"
            }
        return True, "Staff name validated", {}
    
    def rule_staff_role_valid(ctx):
        """Validate staff has a valid organizational role assigning authorization levels."""
        staff = ctx.get("staff", {})
        role = staff.get("role", "").strip()
        valid_roles = ["Admin", "Visa Consultant", "Staff", "Manager"]
        if role not in valid_roles:
            return False, f"Invalid or unregistered staff role: {role}", {
                "field_path": "staff.role",
                "suggestion": "Select a standardized tier profile from dropdown selection mappings"
            }
        return True, "Staff role validated", {}

    def rule_staff_contact(ctx):
        """Validate staff has at least one contact method."""
        staff = ctx.get("staff", {})
        email = staff.get("email", "").strip()
        phone = staff.get("phone", "").strip()
        if not email and not phone:
            return False, "No contact method on file for staff member", {
                "field_path": "staff.email|staff.phone",
                "suggestion": "Provide email or phone for emergency contact"
            }
        return True, "Contact method present", {}
    
    def rule_client_id(ctx):
        """Verify client has submitted identification documentation."""
        client = ctx.get("client", {})
        if not client.get("id_verified", False):
            return False, "Client identity not yet verified", {
                "field_path": "client.id_verified",
                "suggestion": "Request client upload government-issued ID"
            }
        return True, "Client identity verified", {}
    
    def rule_staff_cert(ctx):
        """Check if staff certifications are current (not expired)."""
        staff = ctx.get("staff", {})
        certs = staff.get("certifications", [])
        expired = []
        for cert in certs:
            expiry = cert.get("expiry_date")
            if expiry and isinstance(expiry, str):
                try:
                    expiry_dt = datetime.fromisoformat(expiry.replace("Z", "+00:00"))
                    if expiry_dt < datetime.now():
                        expired.append(cert.get("name", "Unknown Cert"))
                except ValueError:
                    continue
        
        if expired:
            return False, f"Expired certifications: {', '.join(expired)}", {
                "field_path": "staff.certifications",
                "suggestion": "Schedule renewal training immediately"
            }
        return True, "All certifications current", {}
    
    def rule_client_active(ctx):
        """Determine if client has had recent engagement."""
        client = ctx.get("client", {})
        last_contact = client.get("last_contact_date")
        if last_contact:
            try:
                last_dt = datetime.fromisoformat(str(last_contact).replace("Z", "+00:00"))
                days_since = (datetime.now() - last_dt).days
                if days_since > 90:
                    return False, f"No contact in {days_since} days", {
                        "field_path": "client.last_contact_date",
                        "suggestion": "Initiate re-engagement outreach"
                    }
            except ValueError:
                pass
        return True, "Client engagement current", {}

    # --- ENGINE EXPLICIT REGISTRATION PIPELINE ---
    
    engine.register_rule("staff_name_present", RuleCategory.DATA_COMPLETENESS, RuleSeverity.BLOCKING, rule_staff_name)
    engine.register_rule("staff_role_valid", RuleCategory.DATA_COMPLETENESS, RuleSeverity.BLOCKING, rule_staff_role_valid)
    engine.register_rule("staff_contact_present", RuleCategory.DATA_COMPLETENESS, RuleSeverity.CRITICAL, rule_staff_contact)
    engine.register_rule("client_id_verified", RuleCategory.COMPLIANCE, RuleSeverity.CRITICAL, rule_client_id)
    engine.register_rule("staff_certification_current", RuleCategory.COMPLIANCE, RuleSeverity.WARNING, rule_staff_cert)
    engine.register_rule("client_engagement_active", RuleCategory.OPERATIONAL, RuleSeverity.INFO, rule_client_active)
    
    return engine


# =============================================================================
# Module-level singleton configuration
# =============================================================================

__all__ = [
    "RuleEngine",
    "RuleResult",
    "RuleSeverity",
    "RuleCategory",
    "NotificationCue",
    "create_default_engine"
]
