import os
import traceback
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    try:
        app = Flask(__name__, instance_relative_config=False)

        # CORE CONFIG
        app.config['SECRET_KEY'] = 'master_switch_secret_9982'

        # FORCE ENVIRONMENT
        os.environ['FLASK_ENV'] = 'production'

        # ABSOLUTE SQLITE PATH
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        instance_path = os.path.join(base_dir, 'instance')

        if not os.path.exists(instance_path):
            os.makedirs(instance_path)

        absolute_db_path = os.path.join(instance_path, 'database.db')

        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{absolute_db_path}'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

        db.init_app(app)

        print("[OK] Flask initialized")
        print(f"[OK] Database Path: {absolute_db_path}")

        # CORRECT BLUEPRINT IMPORTS
        try:
            from .routes_public import public_bp
            app.register_blueprint(public_bp, url_prefix='/')
            print("[OK] public_bp loaded")
        except Exception:
            print("[ERROR] public_bp failed")
            traceback.print_exc()

        try:
            from .routes_client import client_bp
            app.register_blueprint(client_bp, url_prefix='/client')
            print("[OK] client_bp loaded")
        except Exception:
            print("[ERROR] client_bp failed")
            traceback.print_exc()

        try:
            from .routes_admin import admin_bp
            app.register_blueprint(admin_bp, url_prefix='/admin')
            print("[OK] admin_bp loaded")
        except Exception:
            print("[ERROR] admin_bp failed")
            traceback.print_exc()

        try:
            from .routes_staff import staff_bp
            app.register_blueprint(staff_bp, url_prefix='/staff')
            print("[OK] staff_bp loaded")
        except Exception:
            print("[ERROR] staff_bp failed")
            traceback.print_exc()

        # CREATE DATABASE
        with app.app_context():
            try:
                db.create_all()
                print("[OK] Database initialized")
            except Exception:
                print("[ERROR] Database creation failed")
                traceback.print_exc()

        # HEALTH ROUTE
        @app.route("/health")
        def health():
            return {
                "status": "healthy",
                "database": absolute_db_path
            }, 200

        return app

    except Exception:
        print("[CRITICAL] Flask factory failed")
        traceback.print_exc()
        raise

# DEBUG ROUTE MAP
def print_routes(app):
    print("\n========== ROUTE MAP ==========")
    for rule in app.url_map.iter_rules():
        print(f"{rule.endpoint:30s} -> {rule}")
    print("================================\n")

