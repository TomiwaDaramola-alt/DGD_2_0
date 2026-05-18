from app import create_app
from backend.db_models import db, Client

app = create_app()
with app.app_context():
    records = Client.query.all()
    print("\n==================================================")
    print(f" TOTAL REGISTERED CLIENT PROFILES: {len(records)}")
    print("==================================================")
    
    if len(records) == 0:
        print(" ⚠️  Your Client table is currently completely empty.")
    else:
        for c in records:
            print(f" • Username: '{c.portal_username}'")
            print(f"   Ref ID:   '{c.client_ref}'")
            print(f"   Name:     {c.full_name}")
            print(f"   Verified: {c.is_verified} | Active: {c.is_active}")
            print("-" * 35)
    print("==================================================\n")
