import os
import sys
import traceback

os.environ['FLASK_ENV'] = 'production'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from backend import create_app

app = create_app()

# FORCE DEBUG ERROR OUTPUT
app.config['PROPAGATE_EXCEPTIONS'] = True
app.config['TRAP_HTTP_EXCEPTIONS'] = True

@app.errorhandler(Exception)
def handle_exception(e):
    traceback.print_exc()
    return f"""
    <h1>APPLICATION ERROR</h1>
    <pre>{str(e)}</pre>
    """, 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
