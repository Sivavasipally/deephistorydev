#!/usr/bin/env python3
"""
Migration script to add cy_pct_others column to current_year_staff_metrics table.
This field tracks percentage of files that are not classified as code, config, or documentation.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text, inspect
from cli.config import Config
from cli.models import get_engine


def add_pct_others_column():
    """Add cy_pct_others column to current_year_staff_metrics table."""
    print("\n" + "=" * 80)
    print("ADDING cy_pct_others COLUMN TO current_year_staff_metrics")
    print("=" * 80)

    config = Config()
    db_config = config.get_db_config()
    engine = get_engine(db_config)

    # Check if table exists
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    if 'current_year_staff_metrics' not in existing_tables:
        print("\n[ERROR] Table 'current_year_staff_metrics' does not exist!")
        return False

    print("\n[OK] Table 'current_year_staff_metrics' exists")

    # Get existing columns
    existing_columns = [col['name'] for col in inspector.get_columns('current_year_staff_metrics')]

    if 'cy_pct_others' in existing_columns:
        print("\n[SKIP] Column 'cy_pct_others' already exists")
        return True

    # Add the column
    with engine.connect() as conn:
        try:
            # Determine SQL syntax based on database type
            if db_config.get('type') == 'sqlite':
                sql = "ALTER TABLE current_year_staff_metrics ADD COLUMN cy_pct_others REAL DEFAULT 0.0"
            else:
                sql = "ALTER TABLE current_year_staff_metrics ADD COLUMN cy_pct_others FLOAT DEFAULT 0.0 COMMENT 'Percentage of other files (no-extension and unclassified)'"

            conn.execute(text(sql))
            conn.commit()
            print("\n[ADD] Column 'cy_pct_others' added successfully")
            print("\n" + "=" * 80)
            print("MIGRATION COMPLETE")
            print("=" * 80)
            print("\nNEXT STEP: Run 'python -m cli calculate-metrics --staff' to populate the field")
            return True
        except Exception as e:
            print(f"\n[ERROR] Failed to add column: {str(e)}")
            return False


if __name__ == "__main__":
    try:
        success = add_pct_others_column()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[FATAL ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
