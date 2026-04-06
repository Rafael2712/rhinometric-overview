import re

with open('/app/main.py', 'r') as f:
    content = f.read()

# Add import after telemetry_ingest import
old_import = 'from routers import telemetry_ingest as telemetry_ingest_router'
new_import = old_import + '\nfrom routers import internal_snapshots_v1 as internal_snapshots_v1_router  # Anomaly Engine V1 signal assembler'
content = content.replace(old_import, new_import, 1)

# Add router registration after telemetry_ingest registration
old_router = 'app.include_router(telemetry_ingest_router.router, prefix=f"{settings.API_PREFIX}/telemetry", tags=["Telemetry Ingestion"])  # Task 10: Collector foundation'
new_router = old_router + '\napp.include_router(internal_snapshots_v1_router.router, tags=["Anomaly Engine V1"])  # Phase 11: AI Anomaly Engine signal assembler'
content = content.replace(old_router, new_router, 1)

with open('/app/main.py', 'w') as f:
    f.write(content)

print("OK: main.py patched successfully")
