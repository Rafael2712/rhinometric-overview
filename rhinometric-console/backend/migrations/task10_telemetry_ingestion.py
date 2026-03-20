#!/usr/bin/env python3
"""Task 10 — DB migration: Add telemetry_token, telemetry_status, last_telemetry_at columns."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import engine
from sqlalchemy import text

def migrate():
    with engine.begin() as conn:
        # Create telemetry_status enum
        result = conn.execute(text(
            "SELECT 1 FROM pg_type WHERE typname = 'telemetry_status_enum'"
        ))
        if not result.fetchone():
            conn.execute(text(
                "CREATE TYPE telemetry_status_enum AS ENUM "
                "('NOT_CONFIGURED', 'CONFIGURED', 'CONNECTED', 'RECEIVING_DATA', 'STALE', 'ERROR')"
            ))
            print("  Created telemetry_status_enum")
        else:
            print("  telemetry_status_enum already exists")

        # Add telemetry_token column
        result = conn.execute(text(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name='external_services' AND column_name='telemetry_token'"
        ))
        if not result.fetchone():
            conn.execute(text(
                "ALTER TABLE external_services "
                "ADD COLUMN telemetry_token VARCHAR(128) UNIQUE"
            ))
            conn.execute(text(
                "CREATE INDEX ix_external_services_telemetry_token "
                "ON external_services (telemetry_token) WHERE telemetry_token IS NOT NULL"
            ))
            print("  Added telemetry_token column + index")
        else:
            print("  telemetry_token column already exists")

        # Add telemetry_status column
        result = conn.execute(text(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name='external_services' AND column_name='telemetry_status'"
        ))
        if not result.fetchone():
            conn.execute(text(
                "ALTER TABLE external_services "
                "ADD COLUMN telemetry_status telemetry_status_enum NOT NULL DEFAULT 'NOT_CONFIGURED'"
            ))
            print("  Added telemetry_status column")
        else:
            print("  telemetry_status column already exists")

        # Add last_telemetry_at column
        result = conn.execute(text(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name='external_services' AND column_name='last_telemetry_at'"
        ))
        if not result.fetchone():
            conn.execute(text(
                "ALTER TABLE external_services "
                "ADD COLUMN last_telemetry_at TIMESTAMPTZ"
            ))
            print("  Added last_telemetry_at column")
        else:
            print("  last_telemetry_at column already exists")

        # Backfill telemetry_status for existing services
        conn.execute(text("""
            UPDATE external_services
            SET telemetry_status = 'CONFIGURED'
            WHERE monitoring_mode = 'TELEMETRY_ENABLED'
              AND telemetry_status = 'NOT_CONFIGURED'
        """))
        print("  Backfilled telemetry_status for existing telemetry-enabled services")

    print("Migration complete.")

if __name__ == "__main__":
    migrate()
