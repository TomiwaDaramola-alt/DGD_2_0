from app import create_app
from backend.db_models import db, Staff

app = create_app()
with app.app_context():
    records = Staff.query.all()
    print("\n==================================================")
    print(f" TOTAL REGISTERED STAFF MEMBERS: {len(records)}")
    print("==================================================")
    
    if len(records) == 0:
        print(" ⚠️  CRITICAL: Your Staff table is completely EMPTY!")
    else:
        for r in records:
            print(f" • Emp ID:  '{r.employee_id}'")
            print(f"   Email:   '{r.email}'")
            print(f"   Active:  {r.is_active} | Deleted: {r.is_deleted}")
            print(f"   Name:    {r.full_name}")
            print("-" * 35)
    print("==================================================\n")
