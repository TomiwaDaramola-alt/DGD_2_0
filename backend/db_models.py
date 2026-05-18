# =============================================================================
# DGD 2.0 — DGD CONSULT AU
# Database Models
# Location: backend/db_models.py
# =============================================================================

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


# -----------------------------------------------------------------------------
# MIXINS
# -----------------------------------------------------------------------------

class TimestampMixin:
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow,
                           onupdate=datetime.utcnow, nullable=False)


class SoftDeleteMixin:
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)
    deleted_at = db.Column(db.DateTime, nullable=True)


class OperationalFlagsMixin:
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    is_locked = db.Column(db.Boolean, default=False, nullable=False)


# -----------------------------------------------------------------------------
# ADMIN
# -----------------------------------------------------------------------------

class Admin(db.Model, TimestampMixin, OperationalFlagsMixin):
    __tablename__ = "admins"
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(128), nullable=False)
    phone = db.Column(db.String(32), nullable=True)
    department = db.Column(db.String(64), default="Operations")
    last_login = db.Column(db.DateTime, nullable=True)
    login_attempts = db.Column(db.Integer, default=0)
    
    staff_members = db.relationship("Staff", backref="owner_admin",
                                     lazy="dynamic", cascade="all, delete-orphan")
    clients = db.relationship("Client", backref="owner_admin",
                               lazy="dynamic", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "department": self.department,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "staff_count": self.staff_members.count(),
            "client_count": self.clients.count()
        }


# -----------------------------------------------------------------------------
# STAFF
# -----------------------------------------------------------------------------

class Staff(db.Model, TimestampMixin, SoftDeleteMixin, OperationalFlagsMixin):
    __tablename__ = "staff"
    
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey("admins.id"), nullable=False)
    
    employee_id = db.Column(db.String(32), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(32), nullable=True)
    emergency_contact = db.Column(db.String(128), nullable=True)
    emergency_phone = db.Column(db.String(32), nullable=True)
    
    role = db.Column(db.String(64), nullable=False)
    department = db.Column(db.String(64), default="General")
    employment_type = db.Column(db.String(32), default="full_time")
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    hourly_rate_cents = db.Column(db.Integer, default=0)
    
    certifications_json = db.Column(db.Text, default="[]")
    skills_json = db.Column(db.Text, default="[]")
    
    shift_pattern = db.Column(db.String(64), default="standard")
    max_hours_week = db.Column(db.Integer, default=40)
    preferred_days_json = db.Column(db.Text, default="[]")
    
    current_status = db.Column(db.String(32), default="active")
    last_shift_date = db.Column(db.Date, nullable=True)
    total_hours_logged = db.Column(db.Float, default=0.0)
    performance_rating = db.Column(db.Float, nullable=True)
    review_date = db.Column(db.Date, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    
    assigned_clients = db.relationship("Client", backref="assigned_staff",
                                        lazy="dynamic")
    shift_logs = db.relationship("ShiftLog", backref="staff_member",
                                  lazy="dynamic", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            "id": self.id,
            "employee_id": self.employee_id,
            "full_name": self.full_name,
            "email": self.email,
            "phone": self.phone,
            "role": self.role,
            "department": self.department,
            "employment_type": self.employment_type,
            "current_status": self.current_status,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "hourly_rate_cents": self.hourly_rate_cents,
            "total_hours_logged": self.total_hours_logged,
            "performance_rating": self.performance_rating,
            "assigned_client_count": self.assigned_clients.count(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "admin_id": self.admin_id
        }
# -----------------------------------------------------------------------------
# CLIENT
# -----------------------------------------------------------------------------

class Client(db.Model, TimestampMixin, SoftDeleteMixin, OperationalFlagsMixin):
    __tablename__ = "clients"
    
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey("admins.id"), nullable=False)
    staff_id = db.Column(db.Integer, db.ForeignKey("staff.id"), nullable=True)
    
    client_ref = db.Column(db.String(32), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    phone = db.Column(db.String(32), nullable=True)
    date_of_birth = db.Column(db.Date, nullable=True)
    address_json = db.Column(db.Text, default="{}")
    
    service_type = db.Column(db.String(64), default="consultation")
    service_status = db.Column(db.String(32), default="intake")
    intake_date = db.Column(db.Date, nullable=True)
    discharge_date = db.Column(db.Date, nullable=True)
    
    id_type = db.Column(db.String(32), nullable=True)
    id_number_hash = db.Column(db.String(256), nullable=True)
    id_verified = db.Column(db.Boolean, default=False)
    id_verified_at = db.Column(db.DateTime, nullable=True)
    id_verified_by = db.Column(db.Integer, nullable=True)
    
    portal_username = db.Column(db.String(64), unique=True, nullable=True)
    portal_password_hash = db.Column(db.String(256), nullable=True)
    last_portal_login = db.Column(db.DateTime, nullable=True)
    preferred_contact = db.Column(db.String(32), default="email")
    
    billing_frequency = db.Column(db.String(32), default="monthly")
    payment_method_json = db.Column(db.Text, default="{}")
    outstanding_balance_cents = db.Column(db.Integer, default=0)
    
    last_contact_date = db.Column(db.Date, nullable=True)
    next_scheduled_contact = db.Column(db.Date, nullable=True)
    engagement_notes = db.Column(db.Text, nullable=True)
    
    messages = db.relationship("Message", backref="client",
                              lazy="dynamic", cascade="all, delete-orphan")
    invoices = db.relationship("Invoice", backref="client",
                                lazy="dynamic", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            "id": self.id,
            "client_ref": self.client_ref,
            "full_name": self.full_name,
            "email": self.email,
            "phone": self.phone,
            "service_type": self.service_type,
            "service_status": self.service_status,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "id_verified": self.id_verified,
            "outstanding_balance_cents": self.outstanding_balance_cents,
            "last_contact_date": str(self.last_contact_date) if self.last_contact_date else None,
            "assigned_staff_id": self.staff_id,
            "admin_id": self.admin_id,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


# -----------------------------------------------------------------------------
# SHIFT LOG
# -----------------------------------------------------------------------------

class ShiftLog(db.Model, TimestampMixin):
    __tablename__ = "shift_logs"
    
    id = db.Column(db.Integer, primary_key=True)
    staff_id = db.Column(db.Integer, db.ForeignKey("staff.id"), nullable=False)
    
    shift_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=True)
    shift_type = db.Column(db.String(32), default="regular")
    location = db.Column(db.String(128), nullable=True)
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id"), nullable=True)
    
    hours_worked = db.Column(db.Float, default=0.0)
    break_minutes = db.Column(db.Integer, default=0)
    notes = db.Column(db.Text, nullable=True)
    approved_by = db.Column(db.Integer, db.ForeignKey("admins.id"), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)


# -----------------------------------------------------------------------------
# MESSAGE
# -----------------------------------------------------------------------------

class Message(db.Model, TimestampMixin):
    __tablename__ = "messages"
    
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id"), nullable=True)
    staff_id = db.Column(db.Integer, db.ForeignKey("staff.id"), nullable=True)
    admin_id = db.Column(db.Integer, db.ForeignKey("admins.id"), nullable=True)
    
    direction = db.Column(db.String(16), nullable=False)
    channel = db.Column(db.String(32), nullable=False)
    category = db.Column(db.String(64), default="general")
    
    subject = db.Column(db.String(256), nullable=True)
    body = db.Column(db.Text, nullable=False)
    sender_name = db.Column(db.String(128), nullable=True)
    sender_email = db.Column(db.String(120), nullable=True)
    sender_phone = db.Column(db.String(32), nullable=True)
    
    formspree_id = db.Column(db.String(64), nullable=True)
    formspree_endpoint = db.Column(db.String(256), nullable=True)
    
    is_read = db.Column(db.Boolean, default=False)
    read_at = db.Column(db.DateTime, nullable=True)
    read_by = db.Column(db.Integer, nullable=True)
    requires_followup = db.Column(db.Boolean, default=False)
    followup_assigned_to = db.Column(db.Integer, nullable=True)


# -----------------------------------------------------------------------------
# INVOICE
# -----------------------------------------------------------------------------

class Invoice(db.Model, TimestampMixin):
    __tablename__ = "invoices"
    
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id"), nullable=False)
    
    invoice_number = db.Column(db.String(32), unique=True, nullable=False)
    issue_date = db.Column(db.Date, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    
    subtotal_cents = db.Column(db.Integer, default=0)
    tax_cents = db.Column(db.Integer, default=0)
    total_cents = db.Column(db.Integer, default=0)
    amount_paid_cents = db.Column(db.Integer, default=0)
    
    status = db.Column(db.String(32), default="draft")
    line_items_json = db.Column(db.Text, default="[]")


__all__ = ["db", "Admin", "Staff", "Client", "ShiftLog", "Message", "Invoice"]
