# =============================================================================
# DGD 2.0 — DGD CONSULT AU
# FIXED Admin Routes — Context Variables Verified
# Location: backend/routes_admin.py
# =============================================================================

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from sqlalchemy import func

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.db_models import db, Admin, Staff, Client, Message

admin_bp = Blueprint("admin", __name__, template_folder="../templates")


# -----------------------------------------------------------------------------
# AUTHENTICATION
# -----------------------------------------------------------------------------

@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        
        # PERMANENT FIX: Check both Admin and Staff tables for Username, Email, or Employee ID
        admin = Admin.query.filter((Admin.username == username) | (Admin.email == username)).first()
        
        if not admin:
            # Fallback check against the Staff table if injected as admin there
            staff_admin = Staff.query.filter(
                ((Staff.email == username) | (Staff.employee_id == username)),
                (Staff.role == "admin")
            ).first()
            if staff_admin:
                admin = staff_admin

        if admin and check_password_hash(admin.password_hash if hasattr(admin, 'password_hash') else admin.portal_password_hash, password):
            if not admin.is_active:
                flash("Account deactivated", "warning")
                return render_template("admin_login.html")
            
            session["user_id"] = admin.id
            session["user_type"] = "admin"
            session["user_name"] = admin.full_name
            session["is_admin"] = True
            
            if hasattr(admin, 'last_login'):
                admin.last_login = datetime.utcnow()
            if hasattr(admin, 'login_attempts'):
                admin.login_attempts = 0
            db.session.commit()
            
            flash(f"Welcome, {admin.full_name}", "success")
            return redirect(url_for("admin.dashboard"))
        else:
            if admin and hasattr(admin, 'login_attempts'):
                admin.login_attempts += 1
                db.session.commit()
            flash("Invalid credentials", "warning")
    
    return render_template("admin_login.html")


@admin_bp.route("/logout")
def logout():
    session.clear()
    flash("Session terminated", "info")
    return redirect(url_for("public.index"))


# -----------------------------------------------------------------------------
# DASHBOARD
# -----------------------------------------------------------------------------

@admin_bp.route("/dashboard")
def dashboard():
    """Primary admin interface — Protected via native session checking."""
    if not session.get("is_admin") or session.get("user_type") != "admin":
        flash("Please log in to access the control tower.", "warning")
        return redirect(url_for("admin.login"))
        
    admin_id = session["user_id"]
    
    metrics = {
        "total_staff": Staff.query.filter_by(admin_id=admin_id, is_deleted=False).count(),
        "active_staff": Staff.query.filter_by(
            admin_id=admin_id, is_active=True, is_deleted=False
        ).count(),
        "total_clients": Client.query.filter_by(admin_id=admin_id, is_deleted=False).count(),
        "active_clients": Client.query.filter_by(
            admin_id=admin_id, is_active=True, is_deleted=False
        ).count(),
        "pending_verifications": Client.query.filter_by(
            admin_id=admin_id, is_verified=False, is_deleted=False
        ).count(),
        "unread_messages": Message.query.filter_by(
            direction="inbound", is_read=False
        ).count(),
        "recent_messages": Message.query.filter_by(direction="inbound")
                         .order_by(Message.created_at.desc())
                         .limit(5)
                         .all()
    }
    
    staff_list = Staff.query.filter_by(admin_id=admin_id, is_deleted=False)\
                .order_by(Staff.created_at.desc())\
                .limit(10)\
                .all()
    
    client_list = Client.query.filter_by(admin_id=admin_id, is_deleted=False)\
                  .order_by(Client.created_at.desc())\
                  .limit(10)\
                  .all()
    
    return render_template("admin_panel.html",
                           view_mode="dashboard",
                           metrics=metrics,
                           staff_list=staff_list,
                           client_list=client_list,
                           admin_name=session.get("user_name", "Administrator"))


# -----------------------------------------------------------------------------
# CLIENT MANAGEMENT
# -----------------------------------------------------------------------------

@admin_bp.route("/clients")
def client_list_view():
    if not session.get("is_admin") or session.get("user_type") != "admin":
        flash("Unauthorized access window.", "warning")
        return redirect(url_for("admin.login"))
        
    admin_id = session["user_id"]
    
    status_filter = request.args.get("status", "")
    verified_filter = request.args.get("verified", "")
    search_term = request.args.get("search", "").strip()
    
    query = Client.query.filter_by(admin_id=admin_id, is_deleted=False)
    
    if status_filter:
        query = query.filter_by(service_status=status_filter)
    if verified_filter == "true":
        query = query.filter_by(is_verified=True)
    elif verified_filter == "false":
        query = query.filter_by(is_verified=False)
    if search_term:
        query = query.filter(
            (Client.full_name.ilike(f"%{search_term}%")) |
            (Client.client_ref.ilike(f"%{search_term}%")) |
            (Client.email.ilike(f"%{search_term}%"))
        )
    
    clients = query.order_by(Client.created_at.desc()).all()
    
    return render_template("admin_clients.html",
                           clients=clients,
                           filters={"status": status_filter,
                                   "verified": verified_filter,
                                   "search": search_term},
                           admin_name=session.get("user_name", "Administrator"))


@admin_bp.route("/client/<int:client_id>")
def client_detail(client_id):
    if not session.get("is_admin") or session.get("user_type") != "admin":
        return redirect(url_for("admin.login"))
        
    client = Client.query.get_or_404(client_id)
    
    if client.admin_id != session["user_id"]:
        flash("Unauthorized access", "warning")
        return redirect(url_for("admin.dashboard"))
    
    messages = client.messages.order_by(Message.created_at.desc()).all()
    
    return render_template("admin_client_detail.html",
                           client=client,
                           messages=messages,
                           admin_name=session.get("user_name", "Administrator"))


@admin_bp.route("/client/<int:client_id>/verify", methods=["POST"])
def client_verify(client_id):
    if not session.get("is_admin") or session.get("user_type") != "admin":
        return jsonify({"error": "Unauthorized"}), 403
        
    client = Client.query.get_or_404(client_id)
    
    if client.admin_id != session["user_id"]:
        return jsonify({"error": "Unauthorized"}), 403
    
    client.is_verified = True
    client.id_verified = True
    client.id_verified_at = datetime.utcnow()
    client.id_verified_by = session["user_id"]
    db.session.commit()
    
    flash(f"Client {client.full_name} verified.", "success")
    return redirect(url_for("admin.client_detail", client_id=client.id))


# -----------------------------------------------------------------------------
# STAFF MANAGEMENT
# -----------------------------------------------------------------------------

@admin_bp.route("/staff/new", methods=["GET", "POST"])
def staff_create():
    if not session.get("is_admin") or session.get("user_type") != "admin":
        return redirect(url_for("admin.login"))
        
    if request.method == "POST":
        employee_id = request.form.get("employee_id", "").strip().upper()
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        role = request.form.get("role", "").strip()
        department = request.form.get("department", "General").strip()
        
        if Staff.query.filter_by(employee_id=employee_id).first():
            flash(f"Employee ID '{employee_id}' already exists", "warning")
            return redirect(url_for("admin.staff_create"))
        
        if Staff.query.filter_by(email=email).first():
            flash(f"Email '{email}' already registered", "warning")
            return redirect(url_for("admin.staff_create"))
        
        new_staff = Staff(
            admin_id=session["user_id"],
            employee_id=employee_id,
            full_name=full_name,
            email=email,
            phone=phone,
            role=role,
            department=department,
            is_active=True,
            is_verified=False,
            current_status="active"
        )
        
        db.session.add(new_staff)
        db.session.commit()
        flash(f"Staff member {full_name} created successfully", "success")
        return redirect(url_for("admin.dashboard"))
    
    return render_template("admin_panel.html", 
                           view_mode="staff_create",
                           admin_name=session.get("user_name", "Administrator"))


@admin_bp.route("/staff/<int:staff_id>")
def staff_detail(staff_id):
    if not session.get("is_admin") or session.get("user_type") != "admin":
        return redirect(url_for("admin.login"))
        
    staff = Staff.query.get_or_404(staff_id)
    
    if staff.admin_id != session["user_id"]:
        flash("Unauthorized", "warning")
        return redirect(url_for("admin.dashboard"))
    
    assigned_clients = staff.assigned_clients.filter_by(is_deleted=False).all()
    
    return render_template("admin_staff_detail.html",
                           staff=staff,
                           assigned_clients=assigned_clients,
                           admin_name=session.get("user_name", "Administrator"))


# -----------------------------------------------------------------------------
# MESSAGES
# -----------------------------------------------------------------------------

@admin_bp.route("/messages")
def message_inbox():
    if not session.get("is_admin") or session.get("user_type") != "admin":
        return redirect(url_for("admin.login"))
        
    page = request.args.get("page", 1, type=int)
    per_page = 20
    show_unread_only = request.args.get("unread") == "1"
    
    query = Message.query.filter_by(direction="inbound")
    if show_unread_only:
        query = query.filter_by(is_read=False)
    
    messages = query.order_by(Message.created_at.desc())\
             .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template("admin_panel.html",
                           view_mode="message_inbox",
                           messages=messages,
                           show_unread_only=show_unread_only,
                           admin_name=session.get("user_name", "Administrator"))


@admin_bp.route("/message/<int:message_id>/read", methods=["POST"])
def message_mark_read(message_id):
    if not session.get("is_admin") or session.get("user_type") != "admin":
        return jsonify({"error": "Unauthorized"}), 403
        
    message = Message.query.get_or_404(message_id)
    message.is_read = True
    message.read_at = datetime.utcnow()
    message.read_by = session["user_id"]
    db.session.commit()
    flash("Message marked as read", "success")
    return redirect(url_for("admin.message_inbox"))


# -----------------------------------------------------------------------------
# SETUP BOOTSTRAP (PREMIUM INLINE CONTROL TOWER SYSTEM SETUP)
# -----------------------------------------------------------------------------

@admin_bp.route("/setup", methods=["GET", "POST"])
def setup():
    existing = Admin.query.first()
    if existing:
        flash("System already initialized", "info")
        return redirect(url_for("admin.login"))
    
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        full_name = request.form.get("full_name", "").strip()
        
        if not all([username, email, password, full_name]):
            flash("All fields required", "warning")
            return redirect(url_for("admin.setup"))
        
        admin = Admin(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            full_name=full_name,
            is_active=True,
            is_verified=True
        )
        db.session.add(admin)
        db.session.commit()
        
        flash("Root Admin created! Please login.", "success")
        return redirect(url_for("admin.login"))
    
    # Renders fully built-in premium interface using your custom form styles
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Control Tower — Admin Setup | DGD CONSULT AU</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
                background: #050505;
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
                position: relative;
                overflow: hidden;
            }
            body::before {
                content: '';
                position: absolute;
                top: -50%;
                left: -50%;
                width: 200%;
                height: 200%;
                background: radial-gradient(circle at 30% 30%, rgba(124, 58, 237, 0.08) 0%, transparent 50%),
                            radial-gradient(circle at 70% 70%, rgba(236, 72, 153, 0.06) 0%, transparent 50%);
                pointer-events: none;
            }
            .login-wrapper {
                width: 100%;
                max-width: 440px;
                position: relative;
                z-index: 1;
            }
            .brand-header {
                text-align: center;
                margin-bottom: 36px;
            }
            .brand-logo {
                width: 80px;
                height: 80px;
                background: linear-gradient(135deg, #7c3aed, #ec4899);
                border-radius: 24px;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                font-size: 36px;
                margin-bottom: 20px;
                box-shadow: 0 8px 40px rgba(124, 58, 237, 0.3);
                position: relative;
            }
            .brand-logo::after {
                content: '';
                position: absolute;
                inset: -3px;
                border-radius: 26px;
                background: linear-gradient(135deg, #7c3aed, #ec4899);
                z-index: -1;
                opacity: 0.4;
                filter: blur(12px);
            }
            .brand-header h1 {
                font-family: 'JetBrains Mono', monospace;
                font-size: 24px;
                font-weight: 500;
                color: #fafafa;
                margin-bottom: 8px;
                letter-spacing: 2px;
                text-transform: uppercase;
            }
            .brand-header p {
                color: #525252;
                font-size: 13px;
                letter-spacing: 3px;
                text-transform: uppercase;
            }
            .login-card {
                background: rgba(23, 23, 23, 0.9);
                backdrop-filter: blur(24px);
                border-radius: 24px;
                padding: 44px 40px;
                border: 1px solid rgba(64, 64, 64, 0.3);
                box-shadow: 0 32px 80px rgba(0, 0, 0, 0.6), inset 0 1px 0 rgba(255, 255, 255, 0.05);
            }
            .security-strip {
                display: flex;
                align-items: center;
                gap: 8px;
                margin-bottom: 24px;
                padding-bottom: 20px;
                border-bottom: 1px solid rgba(64, 64, 64, 0.3);
            }
            .security-dot {
                width: 8px;
                height: 8px;
                background: #3b82f6;
                border-radius: 50%;
                box-shadow: 0 0 8px rgba(59, 130, 246, 0.5);
                animation: pulse 2s infinite;
            }
            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.4; }
            }
            .security-text {
                font-family: 'JetBrains Mono', monospace;
                font-size: 11px;
                color: #737373;
                letter-spacing: 1px;
                text-transform: uppercase;
            }
            .card-title {
                font-size: 22px;
                font-weight: 700;
                color: #fafafa;
                margin-bottom: 6px;
            }
            .card-subtitle {
                font-size: 14px;
                color: #737373;
                margin-bottom: 32px;
            }
            .form-group { margin-bottom: 22px; }
            label {
                display: block;
                font-size: 12px;
                font-weight: 500;
                color: #a3a3a3;
                margin-bottom: 8px;
                letter-spacing: 0.5px;
                text-transform: uppercase;
            }
            input[type="text"], input[type="email"], input[type="password"] {
                width: 100%;
                padding: 16px 18px;
                font-size: 15px;
                font-family: 'Inter', sans-serif;
                color: #fafafa;
                background: rgba(10, 10, 10, 0.8);
                border: 1.5px solid rgba(64, 64, 64, 0.4);
                border-radius: 14px;
                outline: none;
                transition: all 0.25s;
                box-sizing: border-box;
            }
            input:focus {
                border-color: #7c3aed;
                background: rgba(10, 10, 10, 1);
                box-shadow: 0 0 0 4px rgba(124, 58, 237, 0.12);
            }
            input::placeholder { color: #525252; }
            .btn-signin {
                width: 100%;
                padding: 18px;
                font-size: 15px;
                font-weight: 600;
                font-family: 'Inter', sans-serif;
                background: linear-gradient(135deg, #7c3aed, #a855f7);
                color: #ffffff;
                border: none;
                border-radius: 14px;
                cursor: pointer;
                margin-top: 8px;
                box-shadow: 0 4px 20px rgba(124, 58, 237, 0.35);
                transition: all 0.2s;
                letter-spacing: 0.5px;
            }
            .btn-signin:hover {
                transform: translateY(-1px);
                box-shadow: 0 8px 30px rgba(124, 58, 237, 0.5);
            }
            .system-status {
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 16px;
                margin-top: 28px;
                padding-top: 24px;
                border-top: 1px solid rgba(64, 64, 64, 0.3);
            }
            .status-item {
                text-align: center;
            }
            .status-value {
                font-family: 'JetBrains Mono', monospace;
                font-size: 18px;
                font-weight: 500;
                color: #fafafa;
            }
            .status-label {
                font-size: 10px;
                color: #525252;
                text-transform: uppercase;
                letter-spacing: 1px;
                margin-top: 2px;
            }
            @media (max-width: 480px) {
                .login-card { padding: 32px 24px; border-radius: 20px; }
                .brand-header h1 { font-size: 20px; }
            }
        </style>
    </head>
    <body>
        <div class="login-wrapper">
            <div class="brand-header">
                <div class="brand-logo">🛠️</div>
                <h1>Control Tower</h1>
                <p>DGD CONSULT AU — System Deployment</p>
            </div>
            
            <div class="login-card">
                <div class="security-strip">
                    <div class="security-dot"></div>
                    <span class="security-text">Initialization Mode — Standby</span>
                </div>
                
                <div class="card-title">Initial Setup</div>
                <div class="card-subtitle">Deploy the root administrator profile credentials below.</div>
                
                <form method="POST" action="">
                    <div class="form-group">
                        <label for="full_name">Full Administrative Name</label>
                        <input type="text" id="full_name" name="full_name" required placeholder="e.g. Master Admin">
                    </div>
                    <div class="form-group">
                        <label for="username">Root Username</label>
                        <input type="text" id="username" name="username" required placeholder="e.g. rootadmin">
                    </div>
                    <div class="form-group">
                        <label for="email">System Email</label>
                        <input type="email" id="email" name="email" required placeholder="admin@dgdconsult.com">
                    </div>
                    <div class="form-group">
                        <label for="password">Create Secret Password</label>
                        <input type="password" id="password" name="password" required placeholder="••••••••">
                    </div>
                    <button type="submit" class="btn-signin">Deploy Admin Profile</button>
                </form>
                
                <div class="system-status">
                    <div class="status-item">
                        <div class="status-value">v2.0</div>
                        <div class="status-label">Build</div>
                    </div>
                    <div class="status-item">
                        <div class="status-value">AU-SYD</div>
                        <div class="status-label">Region</div>
                    </div>
                    <div class="status-item">
                        <div class="status-value">SETUP</div>
                        <div class="status-label">Status</div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
