"""
Database migration script to add staff_metrics table.

This script:
1. Creates the new staff_metrics table
2. Calculates initial metrics for all mapped staff
3. Verifies the migration was successful
"""

import sys
from pathlib import Path

# Add cli directory to path
sys.path.insert(0, str(Path(__file__).parent))

from cli.config import Config
from cli.models import get_engine, get_session, init_database, StaffMetrics
from cli.staff_metrics_calculator import StaffMetricsCalculator


def main():
    """Run migration to add staff_metrics table and calculate initial data."""
    print("=" * 70)
    print("STAFF METRICS TABLE MIGRATION")
    print("=" * 70)
    print()

    # Get database config
    config = Config()
    db_config = config.get_db_config()

    print(f"📊 Database Type: {db_config['type']}")
    if db_config['type'] == 'sqlite':
        print(f"📁 Database Path: {db_config['path']}")
    print()

    # Get engine
    engine = get_engine(db_config)

    # Step 1: Create tables (including new staff_metrics table)
    print("🔧 Step 1: Creating staff_metrics table...")
    try:
        init_database(engine)
        print("   ✅ Table created successfully")
    except Exception as e:
        print(f"   ❌ Error creating table: {e}")
        return False

    # Step 2: Verify table exists
    print("\n🔍 Step 2: Verifying table structure...")
    session = get_session(engine)
    try:
        # Try to query the table
        count = session.query(StaffMetrics).count()
        print(f"   ✅ Table verified (current records: {count})")
    except Exception as e:
        print(f"   ❌ Error verifying table: {e}")
        session.close()
        return False
    finally:
        session.close()

    # Step 3: Calculate initial metrics
    print("\n📊 Step 3: Calculating initial staff metrics...")
    print("   This may take a few minutes depending on data volume...")
    print()

    session = get_session(engine)
    try:
        calculator = StaffMetricsCalculator(session)
        summary = calculator.calculate_all_staff_metrics()

        print("\n✅ Migration completed successfully!")
        print()
        print("📈 Summary:")
        print(f"   - Total staff processed: {summary['processed']}/{summary['total_staff']}")
        print(f"   - New records created: {summary['created']}")
        print(f"   - Existing records updated: {summary['updated']}")
        if summary['failed'] > 0:
            print(f"   - Failed: {summary['failed']}")

        return True

    except Exception as e:
        print(f"\n❌ Error calculating metrics: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        session.close()


if __name__ == "__main__":
    print()
    success = main()
    print()
    print("=" * 70)

    if success:
        print("✅ MIGRATION SUCCESSFUL")
        print()
        print("Next steps:")
        print("1. The staff_metrics table is now available")
        print("2. Access via API: GET /api/staff-metrics/")
        print("3. Frontend can use pre-calculated data for instant loading")
        print("4. Metrics will auto-update on next 'python -m cli extract'")
    else:
        print("❌ MIGRATION FAILED")
        print()
        print("Please check the error messages above and try again.")

    print("=" * 70)
    print()

    sys.exit(0 if success else 1)
