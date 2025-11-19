"""Migration script to create current_year_staff_metrics table."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text, inspect
from cli.config import Config
from cli.models import get_engine, get_session, Base, CurrentYearStaffMetrics


def create_current_year_staff_metrics_table():
    """Create the current_year_staff_metrics table."""

    print("=" * 80)
    print("DATABASE MIGRATION: Creating Current Year Staff Metrics Table")
    print("=" * 80)

    config = Config()
    db_config = config.get_db_config()
    engine = get_engine(db_config)

    # Determine database type
    db_type = db_config.get('type', 'sqlite')
    print(f"\nDatabase Type: {db_type}")

    # Check if table already exists using inspector (works for both MySQL and SQLite)
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    if 'current_year_staff_metrics' in existing_tables:
        print("\n[SKIP] Table 'current_year_staff_metrics' already exists!")
        print("       No migration needed.")
        return True

    print("\n[OK] Table does not exist. Creating new table...")

    # Create the table using SQLAlchemy (works for both MySQL and SQLite)
    CurrentYearStaffMetrics.__table__.create(engine)

    print("\n[OK] Table 'current_year_staff_metrics' created successfully!")

    print("\n" + "=" * 80)
    print("MIGRATION COMPLETE")
    print("=" * 80)
    print("\nNext steps:")
    print("  1. Run: python -m cli calculate-metrics --staff")
    print("  2. This will populate both staff_metrics and current_year_staff_metrics tables")

    return True


if __name__ == "__main__":
    create_current_year_staff_metrics_table()
