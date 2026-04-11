"""
DB Migration: Transform alert_rules table from generic metric/operator
model to synthetic monitoring policy model.

Adds new columns, makes legacy columns nullable.
Safe to run multiple times (idempotent).
"""
import sys
sys.path.insert(0, "/app")

from database import SessionLocal, engine
from sqlalchemy import text, inspect

def run_migration():
    """Add new columns to alert_rules table for synthetic monitoring policies."""

    # Columns to add with their types and defaults
    new_columns = [
        ("rule_type",                    "VARCHAR(30)",  "'SERVICE_DOWN'"),
        ("consecutive_failures",         "INTEGER",      "3"),
        ("critical_escalation_failures", "INTEGER",      "6"),
        ("incident_after_seconds",       "INTEGER",      "120"),
        ("latency_threshold_ms",         "DOUBLE PRECISION", "NULL"),
        ("latency_deviation_pct",        "DOUBLE PRECISION", "NULL"),
        ("anomaly_score_threshold",      "DOUBLE PRECISION", "NULL"),
        ("sustained_checks",            "INTEGER",      "3"),
        ("cooldown_seconds",            "INTEGER",      "120"),
        ("is_default",                  "BOOLEAN",      "FALSE"),
        ("description",                 "TEXT",         "NULL"),
        ("config",                      "JSONB",        "NULL"),
    ]

    # Legacy columns to make nullable
    make_nullable = ["metric", "operator", "threshold", "window_minutes", "service_id"]

    with engine.connect() as conn:
        # Check existing columns
        inspector = inspect(engine)
        existing_cols = {c["name"] for c in inspector.get_columns("alert_rules")}
        print(f"Existing columns: {existing_cols}")

        # Add new columns
        for col_name, col_type, default in new_columns:
            if col_name not in existing_cols:
                default_clause = f" DEFAULT {default}" if default != "NULL" else ""
                sql = f"ALTER TABLE alert_rules ADD COLUMN {col_name} {col_type}{default_clause}"
                print(f"  + Adding: {col_name} ({col_type})")
                conn.execute(text(sql))
            else:
                print(f"  = Exists: {col_name}")

        # Make legacy columns nullable (safe: ALTER COLUMN ... DROP NOT NULL)
        for col_name in make_nullable:
            if col_name in existing_cols:
                try:
                    conn.execute(text(
                        f"ALTER TABLE alert_rules ALTER COLUMN {col_name} DROP NOT NULL"
                    ))
                    print(f"  ~ Nullable: {col_name}")
                except Exception as e:
                    # Already nullable — fine
                    print(f"  = Already nullable or error: {col_name}: {e}")

        # Drop FK constraint on service_id if exists (it references external_services)
        # We keep the column but no longer enforce the FK so NULL=global works
        try:
            result = conn.execute(text("""
                SELECT conname FROM pg_constraint
                WHERE conrelid = 'alert_rules'::regclass
                AND contype = 'f'
                AND conname LIKE '%service_id%'
            """)).fetchall()
            for row in result:
                conn.execute(text(
                    f"ALTER TABLE alert_rules DROP CONSTRAINT IF EXISTS {row[0]}"
                ))
                print(f"  - Dropped FK: {row[0]}")
        except Exception as e:
            print(f"  FK drop skipped: {e}")

        # Add index on rule_type
        try:
            conn.execute(text(
                "CREATE INDEX IF NOT EXISTS ix_alert_rules_rule_type ON alert_rules (rule_type)"
            ))
            print("  + Index: ix_alert_rules_rule_type")
        except Exception:
            pass

        conn.commit()
        print("\n✓ Migration complete")

    # Verify
    with engine.connect() as conn:
        inspector2 = inspect(engine)
        final_cols = {c["name"] for c in inspector2.get_columns("alert_rules")}
        print(f"\nFinal columns ({len(final_cols)}): {sorted(final_cols)}")


if __name__ == "__main__":
    run_migration()
