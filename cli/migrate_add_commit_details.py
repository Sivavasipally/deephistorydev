"""Database migration script to add character counts and file types to commits table."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from cli.config import Config
from cli.models import get_engine

def migrate_database():
    """Add new columns to the commits table."""
    config = Config()
    db_config = config.get_db_config()
    engine = get_engine(db_config)

    print("=" * 60)
    print("  Database Migration: Add Commit Details")
    print("=" * 60)
    print()

    with engine.connect() as conn:
        try:
            # Check if columns already exist
            print("Checking existing schema...")

            # Add chars_added column
            print("Adding chars_added column...")
            try:
                conn.execute(text("""
                    ALTER TABLE commits
                    ADD COLUMN chars_added INTEGER DEFAULT 0
                """))
                conn.commit()
                print("  [OK] Added chars_added column")
            except Exception as e:
                if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                    print("  - chars_added column already exists")
                else:
                    raise

            # Add chars_deleted column
            print("Adding chars_deleted column...")
            try:
                conn.execute(text("""
                    ALTER TABLE commits
                    ADD COLUMN chars_deleted INTEGER DEFAULT 0
                """))
                conn.commit()
                print("  [OK] Added chars_deleted column")
            except Exception as e:
                if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                    print("  - chars_deleted column already exists")
                else:
                    raise

            # Add file_types column
            print("Adding file_types column...")
            try:
                conn.execute(text("""
                    ALTER TABLE commits
                    ADD COLUMN file_types TEXT
                """))
                conn.commit()
                print("  [OK] Added file_types column")
            except Exception as e:
                if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                    print("  - file_types column already exists")
                else:
                    raise

            print()
            print("=" * 60)
            print("  Migration completed successfully!")
            print("=" * 60)
            print()
            print("Note: Existing commits will have:")
            print("  - chars_added = 0")
            print("  - chars_deleted = 0")
            print("  - file_types = NULL")
            print()
            print("To populate these fields for existing commits,")
            print("you will need to re-extract the repository data.")
            print()

        except Exception as e:
            print(f"\n[ERROR] Error during migration: {e}")
            conn.rollback()
            sys.exit(1)

if __name__ == '__main__':
    migrate_database()
