#!/usr/bin/env python3
"""
Migration script to add new fields to current_year_staff_metrics table:
- Organizational fields for filtering (location, staff_type, rank, job_function, sub_platform, reporting_manager_name)
- Monthly breakdown fields for charting (monthly_commits, monthly_prs, monthly_approvals)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, inspect, text
from cli.config import Config
from cli.models import get_engine


def add_new_columns():
    """Add new columns to current_year_staff_metrics table."""
    print("\n" + "=" * 80)
    print("MIGRATING CURRENT_YEAR_STAFF_METRICS TABLE")
    print("=" * 80)

    config = Config()
    db_config = config.get_db_config()
    engine = get_engine(db_config)

    # Check if table exists
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    if 'current_year_staff_metrics' not in existing_tables:
        print("\n[ERROR] Table 'current_year_staff_metrics' does not exist!")
        print("Please run: python cli/migrate_current_year_table.py first")
        return False

    print("\n[OK] Table 'current_year_staff_metrics' exists")

    # Get existing columns
    existing_columns = [col['name'] for col in inspector.get_columns('current_year_staff_metrics')]
    print(f"\n[INFO] Found {len(existing_columns)} existing columns")

    # Define new columns to add
    new_columns = {
        'work_location': "VARCHAR(255) COMMENT 'Work location from staff_details'",
        'staff_type': "VARCHAR(100) COMMENT 'Staff type from staff_details'",
        'rank': "VARCHAR(100) COMMENT 'Job rank from staff_details'",
        'job_function': "VARCHAR(255) COMMENT 'Job function from staff_details'",
        'sub_platform': "VARCHAR(255) COMMENT 'Sub-platform from staff_details'",
        'reporting_manager_name': "VARCHAR(255) COMMENT 'Reporting manager name from staff_details'",
        'cy_monthly_commits': "TEXT COMMENT 'JSON: Monthly commits breakdown {month: count}'",
        'cy_monthly_prs': "TEXT COMMENT 'JSON: Monthly PRs breakdown {month: count}'",
        'cy_monthly_approvals': "TEXT COMMENT 'JSON: Monthly approvals breakdown {month: count}'"
    }

    # Add missing columns
    columns_added = 0
    columns_skipped = 0

    with engine.connect() as conn:
        for col_name, col_definition in new_columns.items():
            if col_name in existing_columns:
                print(f"  [SKIP] Column '{col_name}' already exists")
                columns_skipped += 1
            else:
                try:
                    # Determine SQL syntax based on database type
                    if db_config.get('type') == 'sqlite':
                        # SQLite: ALTER TABLE ADD COLUMN (no COMMENT support)
                        sql = f"ALTER TABLE current_year_staff_metrics ADD COLUMN {col_name} {col_definition.split(' COMMENT')[0]}"
                    else:
                        # MySQL/MariaDB: Full syntax with COMMENT
                        sql = f"ALTER TABLE current_year_staff_metrics ADD COLUMN {col_name} {col_definition}"

                    conn.execute(text(sql))
                    conn.commit()
                    print(f"  [ADD] Column '{col_name}' added successfully")
                    columns_added += 1
                except Exception as e:
                    print(f"  [ERROR] Failed to add column '{col_name}': {str(e)}")
                    return False

    print("\n" + "=" * 80)
    print(f"MIGRATION COMPLETE: {columns_added} columns added, {columns_skipped} skipped")
    print("=" * 80)

    if columns_added > 0:
        print("\nNEXT STEPS:")
        print("1. Update staff_metrics_calculator.py to populate new fields")
        print("2. Recalculate metrics: python -m cli calculate-metrics --staff")
        print("3. Verify in frontend: http://localhost:3000/current-year-metrics")

    return True


if __name__ == "__main__":
    try:
        success = add_new_columns()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[FATAL ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
