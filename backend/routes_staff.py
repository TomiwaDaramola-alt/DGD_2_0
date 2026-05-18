# =============================================================================
# DGD 2.0 — DGD CONSULT AU
# FIXED Staff Routes — Single-Factor (Employee ID Only) & No Duplicates
# Location: backend/routes_staff.py
# =============================================================================

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from datetime import datetime, date, timedelta
from sqlalchemy import and_, func

from backend.db_models import db, Staff, Client, ShiftLog, Message

staff_bp = Blueprint("staff", __name__, template_folder="../templates")


# -----------------------------------------------------------------------------
# AUTHENTICATION — EMPLOYEE ID ONLY (NO DUPLICATES)
# -----------------------------------------------------------------------------

@staff_bp.route("/login", methods=["GET", "POST"])
def login():
    # If already logged in, bypass form and forward straight to workspace dashboard
    if session.get("user_id") and session.get("user_type") == "staff":
        return redirect(url_for("staff.dashboard"))

    if request.method == "POST":
        # Extract only the Employee ID from the form submission
        employee_id = request.form.get("employee_id", "").strip()
        
        print("\n=== [STAFF PORTAL SINGLE-FACTOR AUTHENTICATION] ===")
        print(f"-> Extracted Employee ID: '{employee_id}'")
        
        # Query matching the employee ID column (case-insensitive)
        staff = Staff.query.filter(
            (func.lower(Staff.employee_id) == employee_id.lower()) &
            (Staff.is_active == True) &
            (Staff.is_deleted == False)
        ).first()
        
        if staff:
            print(f"-> [SUCCESS] Staff member found: {staff.full_name}")
            print("===================================================\n")
            
            if staff.is_locked:
                flash("Account locked. Contact administrator.", "warning")
                return render_template("staff_login.html")
            
            # Commit session structural variables
            session["user_id"] = staff.id
            session["user_type"] = "staff"
            session["user_name"] = staff.full_name
            session["admin_id"] = staff.admin_id
            
            flash(f"Welcome, {staff.full_name}", "success")
            return redirect(url_for("staff.dashboard"))
        else:
            print("-> [FAILURE] No matching active staff member found.")
            print("===================================================\n")
            flash("Invalid Employee ID.", "warning")
            return render_template("staff_login.html")
            
    return render_template("staff_login.html")


@staff_bp.route("/logout")
def logout():
    session.clear()
    flash("Logged out", "info")
    return redirect(url_for("public.index"))


# -----------------------------------------------------------------------------
# DASHBOARD — RENDERS staff_panel.html WITH view_mode="dashboard"
# -----------------------------------------------------------------------------

@staff_bp.route("/dashboard")
def dashboard():
    """Protected via native session checking to bypass require_auth loop."""
    if not session.get("user_id") or session.get("user_type") != "staff":
        flash("Please log in to access the staff workspace.", "warning")
        return redirect(url_for("staff.login"))

    staff_id = session["user_id"]
    staff = Staff.query.get(staff_id)
    
    today = date.today()
    today_shifts = ShiftLog.query.filter_by(
        staff_id=staff_id,
        shift_date=today
    ).order_by(ShiftLog.start_time).all()
    
    week_end = today + timedelta(days=7)
    upcoming_shifts = ShiftLog.query.filter(
        and_(
            ShiftLog.staff_id == staff_id,
            ShiftLog.shift_date > today,
            ShiftLog.shift_date <= week_end
        )
    ).order_by(ShiftLog.shift_date, ShiftLog.start_time).all()
    
    clients = staff.assigned_clients.filter_by(
        is_active=True, is_deleted=False
    ).order_by(Client.full_name).all()
    
    recent_messages = Message.query.filter(
        (Message.staff_id == staff_id) |
        (Message.direction == "system")
    ).order_by(Message.created_at.desc()).limit(5).all()
    
    week_start = today - timedelta(days=today.weekday())
    week_hours = db.session.query(func.sum(ShiftLog.hours_worked)).filter(
        ShiftLog.staff_id == staff_id,
        ShiftLog.shift_date >= week_start,
        ShiftLog.shift_date <= week_end
    ).scalar() or 0.0
    
    return render_template("staff_panel.html",
                           view_mode="dashboard",
                           staff=staff,
                           today=today,
                           today_shifts=today_shifts,
                           upcoming_shifts=upcoming_shifts,
                           clients=clients,
                           recent_messages=recent_messages,
                           week_hours=week_hours,
                           max_hours=staff.max_hours_week)


# -----------------------------------------------------------------------------
# SHIFT MANAGEMENT — RENDERS staff_panel.html WITH view_mode="shift_log"
# -----------------------------------------------------------------------------

@staff_bp.route("/shift/log", methods=["GET", "POST"])
def shift_log():
    if not session.get("user_id") or session.get("user_type") != "staff":
        flash("Unauthorized workspace access attempt.", "warning")
        return redirect(url_for("staff.login"))

    staff_id = session["user_id"]
    staff = Staff.query.get(staff_id)
    today = date.today()
    
    if request.method == "POST":
        shift_date = request.form.get("shift_date")
        start_time = request.form.get("start_time")
        end_time = request.form.get("end_time")
        break_minutes = request.form.get("break_minutes", "0")
        location = request.form.get("location", "").strip()
        client_id = request.form.get("client_id") or None
        notes = request.form.get("notes", "").strip()
        
        hours = 0.0
        if start_time and end_time:
            start_dt = datetime.strptime(f"{shift_date} {start_time}", "%Y-%m-%d %H:%M")
            end_dt = datetime.strptime(f"{shift_date} {end_time}", "%Y-%m-%d %H:%M")
            duration = (end_dt - start_dt).total_seconds() / 3600
            break_hours = int(break_minutes) / 60
            hours = max(0, duration - break_hours)
        
        shift = ShiftLog(
            staff_id=staff_id,
            shift_date=datetime.strptime(shift_date, "%Y-%m-%d").date() if shift_date else today,
            start_time=datetime.strptime(start_time, "%H:%M").time() if start_time else None,
            end_time=datetime.strptime(end_time, "%H:%M").time() if end_time else None,
            hours_worked=round(hours, 2),
            break_minutes=int(break_minutes) if break_minutes.isdigit() else 0,
            location=location,
            client_id=int(client_id) if client_id else None,
            notes=notes,
            shift_type="regular"
        )
        
        db.session.add(shift)
        staff.total_hours_logged = (staff.total_hours_logged or 0) + hours
        staff.last_shift_date = shift.shift_date
        db.session.commit()
        
        flash(f"Shift logged: {hours:.2f} hours", "success")
        return redirect(url_for("staff.dashboard"))
    
    assigned_clients = staff.assigned_clients.filter_by(is_active=True).all()
    recent_shifts = ShiftLog.query.filter_by(staff_id=staff_id)\
                    .order_by(ShiftLog.shift_date.desc())\
                    .limit(10).all()
    
    return render_template("staff_panel.html",
                           view_mode="shift_log",
                           staff=staff,
                           today=today,
                           assigned_clients=assigned_clients,
                           recent_shifts=recent_shifts)


# -----------------------------------------------------------------------------
# CLIENT INTERACTION — RENDERS staff_panel.html WITH view_mode="client_detail"
# -----------------------------------------------------------------------------

@staff_bp.route("/client/<int:client_id>/note", methods=["POST"])
def client_add_note(client_id):
    if not session.get("user_id") or session.get("user_type") != "staff":
        return redirect(url_for("staff.login"))

    staff_id = session["user_id"]
    staff = Staff.query.get(staff_id)
    
    client = Client.query.filter_by(
        id=client_id,
        staff_id=staff_id,
        is_deleted=False
    ).first()
    
    if not client:
        flash("Client not found or not assigned", "warning")
        return redirect(url_for("staff.dashboard"))
    
    note_text = request.form.get("note", "").strip()
    if note_text:
        message = Message(
            client_id=client_id,
            staff_id=staff_id,
            direction="outbound",
            channel="internal",
            category="note",
            body=note_text,
            sender_name=staff.full_name,
            requires_followup=False
        )
        db.session.add(message)
        client.last_contact_date = datetime.utcnow().date()
        client.engagement_notes = (client.engagement_notes or "") + f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M')}] {staff.full_name}: {note_text}"
        db.session.commit()
        flash("Note added", "success")
    
    return redirect(url_for("staff.client_detail", client_id=client_id))


@staff_bp.route("/client/<int:client_id>")
def client_detail(client_id):
    if not session.get("user_id") or session.get("user_type") != "staff":
        return redirect(url_for("staff.login"))

    staff_id = session["user_id"]
    
    client = Client.query.filter_by(
        id=client_id,
        staff_id=staff_id,
        is_deleted=False
    ).first_or_404()
    
    messages = client.messages.order_by(Message.created_at.desc()).limit(20).all()
    
    return render_template("staff_panel.html",
                           view_mode="client_detail",
                           staff=Staff.query.get(staff_id),
                           client=client,
                           messages=messages)


# -----------------------------------------------------------------------------
# PROFILE — RENDERS staff_panel.html WITH view_mode="profile"
# -----------------------------------------------------------------------------

@staff_bp.route("/profile", methods=["GET", "POST"])
def profile():
    if not session.get("user_id") or session.get("user_type") != "staff":
        return redirect(url_for("staff.login"))

    staff_id = session["user_id"]
    staff = Staff.query.get(staff_id)
    
    if request.method == "POST":
        staff.phone = request.form.get("phone", staff.phone).strip()
        staff.emergency_contact = request.form.get("emergency_contact", staff.emergency_contact).strip()
        staff.emergency_phone = request.form.get("emergency_phone", staff.emergency_phone).strip()
        db.session.commit()
        flash("Profile updated", "success")
        return redirect(url_for("staff.profile"))
    
    return render_template("staff_panel.html",
                           view_mode="profile",
                           staff=staff)
