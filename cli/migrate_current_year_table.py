"""Migration script to create current_year_staff_metrics table."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
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

    with engine.connect() as connection:
        # Check if table already exists
        check_table_sql = """
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='current_year_staff_metrics'
        """

        result = connection.execute(text(check_table_sql))
        table_exists = result.fetchone() is not None

        if table_exists:
            print("\n[SKIP] Table 'current_year_staff_metrics' already exists!")
            print("       No migration needed.")
            return True

        print("\n[OK] Table does not exist. Creating new table...")

        # Create the table using SQLAlchemy
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
