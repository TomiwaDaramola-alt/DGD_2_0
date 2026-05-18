# =============================================================================
# DGD 2.0 — DGD CONSULT AU
# Main Application Factory
# Location: app.py
# =============================================================================

from flask import Flask, session, redirect, url_for, request
from functools import wraps
import os

# Import blueprints
from backend.routes_public import public_bp
from backend.routes_admin import admin_bp
from backend.routes_staff import staff_bp
from backend.routes_client import client_bp
from backend.db_models import db

# =============================================================================
# APP FACTORY
# =============================================================================

def create_app(config_name="development"):
    app = Flask(__name__, 
                template_folder="templates",
                static_folder="static")
    
    # Configuration
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dgd-dev-secret-key-2026")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "DATABASE_URL", "sqlite:///dgd_consult.db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    # Initialize extensions
    db.init_app(app)
    
    # Register blueprints
    app.register_blueprint(public_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(staff_bp, url_prefix="/staff")
    app.register_blueprint(client_bp, url_prefix="/client")
    
    # Context processor for templates
    @app.context_processor
    def inject_globals():
        from datetime import datetime
        return {
            "app_name": "DGD CONSULT AU",
            "year": datetime.now().year
        }
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        return redirect(url_for("public.index"))
    
    @app.errorhandler(500)
    def server_error(e):
        return "Internal Server Error", 500
    
    # Create tables
    with app.app_context():
        db.create_all()
    
    return app


# =============================================================================
# AUTHENTICATION DECORATOR
# =============================================================================

def require_auth(user_type):
    """Decorator to protect routes by user type."""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if "user_type" not in session:
                if user_type == "admin":
                    return redirect(url_for("admin.login"))
                elif user_type == "staff":
                    return redirect(url_for("staff.login"))
                elif user_type == "client":
                    return redirect(url_for("client.login"))
                return redirect(url_for("public.index"))
            
            if session.get("user_type") != user_type:
                return redirect(url_for("public.index"))
            
            return f(*args, **kwargs)
        return wrapper
    return decorator


# =============================================================================
# RUNNER
# =============================================================================

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
