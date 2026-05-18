from flask import Flask
from backend import create_app

# Render looks for the variable 'app' inside 'app.py'
app = create_app()

if __name__ == "__main__":
    app.run()
