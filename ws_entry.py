import sys
import os

# Ensure project root is in the system path
base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, base_dir)

# KILL SWITCH: Force create the instance folder with absolute paths before Flask boots
instance_path = os.path.join(base_dir, 'instance')
os.makedirs(instance_path, exist_ok=True)

from backend import create_app

# Build the application instance
app = create_app()

# Fallback configurations for production environments
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_fallback_key_99182')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

if __name__ == "__main__":
    # Bind to the dynamic port Render assigns
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
