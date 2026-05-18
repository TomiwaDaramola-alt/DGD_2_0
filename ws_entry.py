import os
import sys
import traceback

print("\n========== BOOT START ==========\n")

try:
    # FORCE PRODUCTION ENVIRONMENT
    os.environ['FLASK_ENV'] = 'production'

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, BASE_DIR)

    print(f"[OK] BASE_DIR = {BASE_DIR}")

    from backend import create_app

    print("[OK] create_app imported")

    app = create_app()

    print("[OK] Flask app created successfully")

except Exception:
    print("[CRITICAL] APPLICATION FAILED TO BOOT")
    traceback.print_exc()
    raise

print("\n========== BOOT SUCCESS ==========\n")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
