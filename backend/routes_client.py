# =============================================================================
# DGD 2.0 — DGD CONSULT AU
# FIXED Client Routes — Template Routing & Context Corrected
# Location: backend/routes_client.py
# =============================================================================

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
import requests

from backend.db_models import db, Client, Message, Invoice, Staff

client_bp = Blueprint("client", __name__, template_folder="../templates")

# =============================================================================
# PAYSTACK CONFIGURATION — USE YOUR REAL KEYS
# =============================================================================

PAYSTACK_PUBLIC_KEY = "pk_test_a49bd26daf79787b5fde3f01f093a548c00e7665"
PAYSTACK_SECRET_KEY = "sk_test_453e6852331b7018e76017922453975adfa26b65"


# -----------------------------------------------------------------------------
# REGISTRATION — WITH PAYSTACK
# -----------------------------------------------------------------------------

@client_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        client_ref = request.form.get("client_ref", "").strip().upper()
        given_names = request.form.get("given_names", "").strip()
        family_name = request.form.get("family_name", "").strip()
        full_name = f"{given_names} {family_name}".strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        country = request.form.get("country", "").strip()
        date_of_birth = request.form.get("date_of_birth")
        service_type = request.form.get("service_type", "consultation")
        preferred_contact = request.form.get("preferred_contact", "email")
        message_body = request.form.get("message", "").strip()
        
        # PAYSTACK VERIFICATION
        paystack_reference = request.form.get("paystack_reference")
        payment_status = "Pending"
        
        if service_type != "consultation" and paystack_reference:
            url = f"https://api.paystack.co/transaction/verify/{paystack_reference}"
            headers = {
                "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
                "Cache-Control": "no-cache",
            }
            try:
                response = requests.get(url, headers=headers, timeout=10).json()
                if response.get("status") and response["data"]["status"] == "success":
                    payment_status = "Paid"
                else:
                    payment_status = "Payment Failed"
            except Exception as e:
                print(f"Paystack verification error: {e}")
                payment_status = "Verification Error"
        elif service_type == "consultation":
            payment_status = "Complimentary"
        
        address = {
            "line_1": request.form.get("address_line_1", "").strip(),
            "line_2": request.form.get("address_line_2", "").strip(),
            "city": request.form.get("city", "").strip(),
            "state": request.form.get("state", "").strip(),
            "postal_code": request.form.get("postal_code", "").strip(),
            "country_residence": country
        }
        
        if not client_ref:
            client_ref = f"DGD-{int(datetime.utcnow().timestamp())}"
        
        if Client.query.filter_by(client_ref=client_ref).first():
            flash("Reference already registered", "warning")
            return redirect(url_for("client.register"))
        
        if email and Client.query.filter_by(email=email).first():
            flash("Email already in use", "warning")
            return redirect(url_for("client.register"))
        
        portal_username = request.form.get("portal_username", email).strip()
        portal_password = request.form.get("portal_password", "")
        
        new_client = Client(
            admin_id=1,
            client_ref=client_ref,
            full_name=full_name,
            email=email,
            phone=phone,
            date_of_birth=datetime.strptime(date_of_birth, "%Y-%m-%d").date() if date_of_birth else None,
            address_json=str(address),
            service_type=service_type,
            service_status="intake",
            intake_date=date.today(),
            preferred_contact=preferred_contact,
            portal_username=portal_username,
            portal_password_hash=generate_password_hash(portal_password) if portal_password else None,
            is_active=True,
            is_verified=True if payment_status in ["Paid", "Complimentary"] else False,
            id_verified=False,
            outstanding_balance_cents=0
        )
        
        new_client.notes = f"Service: {service_type}. Payment: {payment_status}. Ref: {paystack_reference}. Message: {message_body}"
        
        db.session.add(new_client)
        db.session.commit()
        
        welcome = Message(
            client_id=new_client.id,
            direction="system",
            channel="portal",
            category="alert",
            subject="Welcome to DGD CONSULT AU",
            body=f"Your intake record established. Ref: {client_ref}. Payment: {payment_status}.",
            requires_followup=False
        )
        db.session.add(welcome)
        
        if message_body:
            user_inquiry = Message(
                client_id=new_client.id,
                direction="outbound",
                channel="portal",
                category="inquiry",
                subject=f"Intake Notes for {service_type}",
                body=message_body,
                sender_name=full_name,
                sender_email=email,
                sender_phone=phone,
                requires_followup=True
            )
            db.session.add(user_inquiry)
        
        db.session.commit()
        flash(f"Registration successful! Service: {service_type} ({payment_status})", "success")
        return redirect(url_for("client.login"))
    
    return render_template("client_register.html",
                           paystack_key=PAYSTACK_PUBLIC_KEY)


# -----------------------------------------------------------------------------
# AUTHENTICATION
# -----------------------------------------------------------------------------

@client_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        
        client = Client.query.filter_by(
            portal_username=username,
            is_active=True,
            is_deleted=False
        ).first()
        
        if client and client.portal_password_hash:
            if check_password_hash(client.portal_password_hash, password):
                if not client.is_verified:
                    flash("Account pending verification", "warning")
                    return render_template("client_login.html")
                
                session["user_id"] = client.id
                session["user_type"] = "client"
                session["user_name"] = client.full_name
                client.last_portal_login = datetime.utcnow()
                db.session.commit()
                
                flash(f"Welcome, {client.full_name}", "success")
                return redirect(url_for("client.portal"))
            else:
                flash("Invalid credentials", "warning")
        else:
            flash("Account not found", "warning")
    
    return render_template("client_login.html")


@client_bp.route("/logout")
def logout():
    session.clear()
    flash("Logged out", "info")
    return redirect(url_for("public.index"))


# -----------------------------------------------------------------------------
# PORTAL — FIXED: Ensures all context variables are passed
# -----------------------------------------------------------------------------

@client_bp.route("/portal")
def portal():
    if not session.get("user_id") or session.get("user_type") != "client":
        flash("Please log in to access your secure client terminal.", "warning")
        return redirect(url_for("client.login"))

    client_id = session["user_id"]
    client = Client.query.get(client_id)
    
    if not client:
        session.clear()
        flash("Session invalid. Please log in again.", "warning")
        return redirect(url_for("client.login"))
    
    messages = client.messages.order_by(Message.created_at.desc()).limit(10).all()
    invoices = client.invoices.order_by(Invoice.issue_date.desc()).limit(5).all()
    total_outstanding = client.outstanding_balance_cents or 0
    
    assigned_staff = None
    if client.staff_id:
        assigned_staff = Staff.query.get(client.staff_id)
    
    # FIXED: Pass app_name for template compatibility, ensure no missing context
    return render_template("client_portal.html",
                           view_mode="dashboard",
                           client=client,
                           messages=messages,
                           invoices=invoices,
                           total_outstanding=total_outstanding,
                           assigned_staff=assigned_staff,
                           app_name="DGD CONSULT AU")


# -----------------------------------------------------------------------------
# PROFILE — FIXED: Renders client_portal.html with view_mode="profile"
# -----------------------------------------------------------------------------

@client_bp.route("/profile", methods=["GET", "POST"])
def profile():
    if not session.get("user_id") or session.get("user_type") != "client":
        return redirect(url_for("client.login"))

    client_id = session["user_id"]
    client = Client.query.get(client_id)
    
    if not client:
        session.clear()
        flash("Session invalid. Please log in again.", "warning")
        return redirect(url_for("client.login"))
    
    if request.method == "POST":
        client.phone = request.form.get("phone", client.phone).strip()
        client.preferred_contact = request.form.get("preferred_contact", client.preferred_contact)
        
        address = {
            "line_1": request.form.get("address_line_1", "").strip(),
            "line_2": request.form.get("address_line_2", "").strip(),
            "city": request.form.get("city", "").strip(),
            "state": request.form.get("state", "").strip(),
            "postal_code": request.form.get("postal_code", "").strip()
        }
        client.address_json = str(address)
        db.session.commit()
        flash("Profile updated", "success")
        return redirect(url_for("client.portal"))
    
    # FIXED: Render client_portal.html with view_mode for template routing
    return render_template("client_portal.html",
                           view_mode="profile",
                           client=client,
                           app_name="DGD CONSULT AU")


# -----------------------------------------------------------------------------
# MESSAGING
# -----------------------------------------------------------------------------

@client_bp.route("/message/send", methods=["POST"])
def send_message():
    if not session.get("user_id") or session.get("user_type") != "client":
        return redirect(url_for("client.login"))

    client_id = session["user_id"]
    client = Client.query.get(client_id)
    
    subject = request.form.get("subject", "").strip()
    body = request.form.get("body", "").strip()
    
    if body:
        message = Message(
            client_id=client_id,
            direction="outbound",
            channel="portal",
            category="inquiry",
            subject=subject,
            body=body,
            sender_name=client.full_name,
            sender_email=client.email,
            sender_phone=client.phone,
            requires_followup=True
        )
        db.session.add(message)
        db.session.commit()
        flash("Message sent", "success")
    
    return redirect(url_for("client.portal"))


# -----------------------------------------------------------------------------
# INVOICES — FIXED: Renders client_portal.html with view_mode="invoices"
# -----------------------------------------------------------------------------

@client_bp.route("/invoices")
def invoice_list():
    if not session.get("user_id") or session.get("user_type") != "client":
        return redirect(url_for("client.login"))

    client_id = session["user_id"]
    client = Client.query.get(client_id)
    
    if not client:
        session.clear()
        flash("Session invalid. Please log in again.", "warning")
        return redirect(url_for("client.login"))
    
    invoices = client.invoices.order_by(Invoice.issue_date.desc()).all()
    
    # FIXED: Render client_portal.html with view_mode for template routing
    return render_template("client_portal.html",
                           view_mode="invoices",
                           client=client,
                           invoices=invoices,
                           app_name="DGD CONSULT AU")
