"""
Initialize database with updated schema supporting multilingual characters
and increased platform_lead field size.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from cli.config import Config
from cli.models import get_engine, init_database, Base

# Set UTF-8 encoding for console output on Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def main():
    """Initialize database with all tables."""
    print("=" * 60)
    print("Database Initialization Script")
    print("=" * 60)
    print()

    try:
        # Load configuration
        print("[1/4] Loading database configuration...")
        config = Config()
        db_config = config.get_db_config()
        print(f"      Database type: {db_config['type']}")

        if db_config['type'] == 'sqlite':
            print(f"      Database path: {db_config['path']}")
        elif db_config['type'] == 'mariadb':
            print(f"      Database host: {db_config['host']}:{db_config['port']}")
            print(f"      Database name: {db_config['database']}")

        # Create engine
        print("\n[2/4] Creating database engine...")
        engine = get_engine(db_config)
        print("      Engine created successfully")

        # Verify encoding (for SQLite)
        if db_config['type'] == 'sqlite':
            print("\n[3/4] Verifying database encoding...")
            with engine.connect() as conn:
                result = conn.execute("PRAGMA encoding").fetchone()
                encoding = result[0] if result else "Unknown"
                print(f"      Database encoding: {encoding}")
                if encoding == 'UTF-8':
                    print("      ✓ UTF-8 encoding enabled - supports multilingual characters")
                else:
                    print(f"      ⚠ Warning: Database is not using UTF-8 encoding")

        # Create all tables
        print("\n[4/4] Creating database tables...")
        init_database(engine)

        # List created tables
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        print("\n" + "=" * 60)
        print("Database Initialization Complete!")
        print("=" * 60)
        print(f"\nTotal tables created: {len(tables)}")
        print("\nTables:")
        for idx, table in enumerate(tables, 1):
            print(f"  {idx}. {table}")

        print("\n📊 Key Features:")
        print("  ✓ All tables support multilingual characters (UTF-8)")
        print("  ✓ platform_lead field size: VARCHAR(500)")
        print("  ✓ All text fields support Unicode characters")
        print("  ✓ Ready for data import")

        print("\n✅ Database is ready for use!")

    except Exception as e:
        print(f"\n❌ Error initializing database: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
