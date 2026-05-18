from app import create_app

app = create_app()
print("\n==========================================================================")
print("             🌏  DGD CONSULT AU — FULL SITE LINK REGISTRY MAP")
print("==========================================================================")
print(f"{'BLUEPRINT / ENDPOINT':<40} | {'ALLOWED METHODS':<15} | {'URL PATH LINK'}")
print("-" * 82)

# Loop through Flask's internal URL mapping rules sorted by URL path
for rule in sorted(app.url_map.iter_rules(), key=lambda r: r.rule):
    # Skip standard static file asset routes to keep it clean
    if rule.endpoint == 'static':
        continue
        
    methods = ', '.join([m for m in rule.methods if m in ['GET', 'POST']])
    print(f"{rule.endpoint:<40} | {methods:<15} | {rule.rule}")

print("==========================================================================\n")
