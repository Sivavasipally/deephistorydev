"""Quick setup script to test database connection and prepare for sync."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text, inspect
import os


def test_sqlite_connection():
    """Test SQLite source database connection."""
    print("\n" + "=" * 80)
    print("TESTING SQLITE CONNECTION")
    print("=" * 80)

    try:
        sqlite_url = "sqlite:///git_history.db"
        engine = create_engine(sqlite_url)

        with engine.connect() as conn:
            # Get table list
            inspector = inspect(engine)
            tables = inspector.get_table_names()

            print(f"\n[OK] Connected to SQLite database")
            print(f"[OK] Found {len(tables)} tables")

            # Get record counts
            counts = {}
            for table in tables:
                try:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    counts[table] = count
                except Exception as e:
                    counts[table] = f"Error: {str(e)}"

            print("\nTable Record Counts:")
            for table, count in sorted(counts.items()):
                print(f"  {table:30s}: {count}")

            return True

    except Exception as e:
        print(f"\n[ERROR] SQLite connection failed: {str(e)}")
        return False


def test_mariadb_connection(mariadb_url=None):
    """Test MariaDB/MySQL target database connection."""
    print("\n" + "=" * 80)
    print("TESTING MARIADB CONNECTION")
    print("=" * 80)

    if not mariadb_url:
        mariadb_url = os.getenv(
            'MARIADB_URL',
            'mysql+pymysql://user:password@localhost:3306/gpt'
        )

    print(f"\nConnection URL: {mariadb_url.split('@')[1] if '@' in mariadb_url else 'Not configured'}")

    try:
        engine = create_engine(mariadb_url)

        with engine.connect() as conn:
            # Test basic query
            result = conn.execute(text("SELECT VERSION()"))
            version = result.scalar()

            print(f"\n[OK] Connected to MariaDB/MySQL")
            print(f"[OK] Version: {version}")

            # Get table list
            inspector = inspect(engine)
            tables = inspector.get_table_names()

            print(f"[OK] Found {len(tables)} tables")

            if tables:
                # Get record counts
                counts = {}
                for table in tables:
                    try:
                        result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                        count = result.scalar()
                        counts[table] = count
                    except Exception as e:
                        counts[table] = f"Error: {str(e)}"

                print("\nTable Record Counts:")
                for table, count in sorted(counts.items()):
                    print(f"  {table:30s}: {count}")
            else:
                print("\n[WARNING] No tables found - run migrations first!")

            return True

    except Exception as e:
        print(f"\n[ERROR] MariaDB connection failed: {str(e)}")
        print("\nTroubleshooting:")
        print("  1. Check database credentials")
        print("  2. Ensure MariaDB/MySQL is running")
        print("  3. Verify database exists")
        print("  4. Check network connectivity")
        print("\nSet MARIADB_URL environment variable:")
        print("  set MARIADB_URL=mysql+pymysql://user:password@host:port/database")
        return False


def check_required_tables():
    """Check if required tables exist in both databases."""
    print("\n" + "=" * 80)
    print("CHECKING REQUIRED TABLES")
    print("=" * 80)

    required_tables = [
        'repositories',
        'commits',
        'pull_requests',
        'pr_approvals',
        'authors',
        'staff_details',
        'author_staff_mapping',
        'staff_metrics',
        'current_year_staff_metrics'
    ]

    # Check SQLite
    try:
        sqlite_engine = create_engine("sqlite:///git_history.db")
        sqlite_inspector = inspect(sqlite_engine)
        sqlite_tables = set(sqlite_inspector.get_table_names())

        print("\nSQLite Tables:")
        for table in required_tables:
            status = "✓" if table in sqlite_tables else "✗"
            print(f"  {status} {table}")

    except Exception as e:
        print(f"\n[ERROR] Cannot check SQLite tables: {str(e)}")
        return False

    # Check MariaDB
    try:
        mariadb_url = os.getenv('MARIADB_URL', 'mysql+pymysql://user:password@localhost:3306/gpt')
        mariadb_engine = create_engine(mariadb_url)
        mariadb_inspector = inspect(mariadb_engine)
        mariadb_tables = set(mariadb_inspector.get_table_names())

        print("\nMariaDB Tables:")
        for table in required_tables:
            status = "✓" if table in mariadb_tables else "✗"
            print(f"  {status} {table}")

        missing = [t for t in required_tables if t not in mariadb_tables]
        if missing:
            print(f"\n[WARNING] Missing tables in MariaDB: {', '.join(missing)}")
            print("\nRun migrations:")
            print("  python cli/migrate_current_year_table.py")
            return False

    except Exception as e:
        print(f"\n[ERROR] Cannot check MariaDB tables: {str(e)}")
        return False

    print("\n[OK] All required tables exist in both databases")
    return True


def main():
    """Run all setup checks."""
    print("\n" + "=" * 80)
    print("DATA SYNC QUICK SETUP")
    print("=" * 80)

    sqlite_ok = test_sqlite_connection()
    mariadb_ok = test_mariadb_connection()

    if sqlite_ok and mariadb_ok:
        tables_ok = check_required_tables()

        if tables_ok:
            print("\n" + "=" * 80)
            print("SETUP COMPLETE - READY TO SYNC")
            print("=" * 80)
            print("\nRun synchronization:")
            print("  python datasync/sync_sqlite_to_mariadb.py")
        else:
            print("\n" + "=" * 80)
            print("SETUP INCOMPLETE")
            print("=" * 80)
            print("\nCreate missing tables first")
    else:
        print("\n" + "=" * 80)
        print("SETUP FAILED")
        print("=" * 80)
        print("\nFix connection issues before proceeding")


if __name__ == "__main__":
    main()
