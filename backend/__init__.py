import os
import traceback
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        app = Flask(
            __name__,
            static_folder=os.path.join(base_dir, 'static'),
            template_folder=os.path.join(base_dir, 'templates'),
            static_url_path='/static'
        )

        app.config['SECRET_KEY'] = 'master_switch_secret_9982'

        instance_path = os.path.join(base_dir, 'instance')

        if not os.path.exists(instance_path):
            os.makedirs(instance_path)

        absolute_db_path = os.path.join(instance_path, 'database.db')

        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{absolute_db_path}'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

        db.init_app(app)

        from .routes_public import public_bp
        from .routes_client import client_bp
        from .routes_admin import admin_bp
        from .routes_staff import staff_bp

        app.register_blueprint(public_bp, url_prefix='/')
        app.register_blueprint(client_bp, url_prefix='/client')
        app.register_blueprint(admin_bp, url_prefix='/admin')
        app.register_blueprint(staff_bp, url_prefix='/staff')

        with app.app_context():
            db.create_all()

        @app.route("/health")
        def health():
            return {"status": "healthy"}, 200

        return app

    except Exception:
        traceback.print_exc()
        raise
