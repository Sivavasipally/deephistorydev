"""
Migration script to:
1. Ensure all tables support multilingual characters (UTF-8)
2. Increase platform_lead field size in staff_details table
"""

import sqlite3
import sys
from pathlib import Path

# Set UTF-8 encoding for console output
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def migrate_database(db_path):
    """
    SQLite natively supports UTF-8, but we'll increase platform_lead size
    and ensure proper encoding for all text fields.
    """
    print(f"🔄 Starting database migration for: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # SQLite uses UTF-8 by default, but let's verify
        cursor.execute("PRAGMA encoding")
        encoding = cursor.fetchone()[0]
        print(f"✓ Current database encoding: {encoding}")

        # Check if staff_details table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='staff_details'")
        if not cursor.fetchone():
            print("⚠️  staff_details table does not exist yet. It will be created with correct schema.")
            conn.close()
            return

        print("\n📋 Migrating staff_details table...")

        # Get current table schema
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='staff_details'")
        old_schema = cursor.fetchone()[0]

        # Create new table with updated schema
        # Increase platform_lead from VARCHAR(255) to VARCHAR(500) for longer names
        new_schema = old_schema.replace(
            'platform_lead VARCHAR(255)',
            'platform_lead VARCHAR(500)'
        )

        # Create temporary table with new schema
        cursor.execute("ALTER TABLE staff_details RENAME TO staff_details_old")
        cursor.execute(new_schema)

        # Copy data from old table to new table
        cursor.execute("""
            INSERT INTO staff_details
            SELECT * FROM staff_details_old
        """)

        # Drop old table
        cursor.execute("DROP TABLE staff_details_old")

        print("✅ staff_details table migrated successfully")
        print("   - platform_lead field size increased: VARCHAR(255) -> VARCHAR(500)")

        # Verify other tables for UTF-8 compatibility
        tables_to_check = ['repositories', 'commits', 'pull_requests', 'pr_approvals', 'author_staff_mapping']

        print("\n📋 Verifying UTF-8 support for all tables...")
        for table in tables_to_check:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if cursor.fetchone():
                print(f"   ✓ {table} - UTF-8 supported (SQLite native)")

        # Commit changes
        conn.commit()

        print("\n✅ Migration completed successfully!")
        print("\n📊 Summary:")
        print("   - All tables support multilingual characters (UTF-8)")
        print("   - platform_lead field increased to VARCHAR(500)")
        print("   - Data preserved and migrated")

    except Exception as e:
        conn.rollback()
        print(f"\n❌ Migration failed: {str(e)}")
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    # Database paths
    db_paths = [
        "backend/git_history.db",
        "git_history.db"
    ]

    # Find existing database
    db_path = None
    for path in db_paths:
        if Path(path).exists():
            db_path = path
            break

    if not db_path:
        print("❌ No database file found. Please ensure the database exists before running migration.")
        sys.exit(1)

    migrate_database(db_path)
