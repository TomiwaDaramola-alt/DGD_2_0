import sys
import os

# FORCE INJECT HARD KEYS DIRECTLY INTO RUNTIME ENVIRONMENT
os.environ['PAYSTACK_PUBLIC_KEY'] = 'pk_test_a49bd26daf79787b5fde3f01f093a548c00e7665'
os.environ['PAYSTACK_SECRET_KEY'] = 'sk_test_453e6852331b7018e76017922453975adfa26b65'
os.environ['FLASK_ENV'] = 'production'

# Ensure project root is in the system path
base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, base_dir)

# Force create the instance folder path
instance_path = os.path.join(base_dir, 'instance')
os.makedirs(instance_path, exist_ok=True)

from backend import create_app

# Build the application instance
app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
