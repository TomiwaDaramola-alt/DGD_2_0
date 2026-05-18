# Location: /storage/emulated/0/DGD_2_0/create_admin.py
from flask import Flask
from backend.db_models import db, Staff
from werkzeug.security import generate_password_hash
import os

# 1. Initialize the temporary Flask context block
temp_app = Flask(__name__)

# Track down the SQLite file
db_path = os.path.join("/storage/emulated/0/DGD_2_0/", "instance", "database.db")
if not os.path.exists(db_path):
    db_path = os.path.join("/storage/emulated/0/DGD_2_0/", "database.db")

temp_app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
temp_app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(temp_app)

with temp_app.app_context():
    # 2. Safety check for duplicates
    existing_admin = Staff.query.filter_by(email="admin@dgdconsult.com").first()
    
    if not existing_admin:
        admin_user = Staff(
            admin_id=1,
            employee_id="ADMIN001",
            full_name="System Administrator",
            email="admin@dgdconsult.com",
            phone="0000000000",
            role="admin",               # FIXED: Satisfies the NOT NULL constraint for role
            emergency_contact="N/A",    # Backup: Satisfies constraint if flagged NOT NULL
            emergency_phone="0000000000",# Backup: Satisfies constraint if flagged NOT NULL
            department="General",
            employment_type="full_time",
            current_status="active",
            is_active=True,
            is_locked=False,
            is_deleted=False,
            max_hours_week=40.0
        )
        
        # Securely hash the admin password
        hashed_password = generate_password_hash("AdminPass123!")
        
        # Set credential variables safely across schema types
        if hasattr(admin_user, 'portal_password_hash'):
            admin_user.portal_password_hash = hashed_password
        if hasattr(admin_user, 'password_hash'):
            admin_user.password_hash = hashed_password
            
        db.session.add(admin_user)
        db.session.commit()
        print("🚀 Success! Master Admin Account 'admin@dgdconsult.com' created with password 'AdminPass123!'")
    else:
        print("⚠️ An admin account with that email already exists in the database.")
