"""Fix the author_staff_mapping table to add AUTO_INCREMENT to id field."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from .config import Config
from .models import get_engine, Base, AuthorStaffMapping
from sqlalchemy import inspect, text

def fix_mapping_table():
    """Fix the author_staff_mapping table by recreating it with proper schema."""
    try:
        config = Config()
        db_config = config.get_db_config()
        engine = get_engine(db_config)
        is_sqlite = db_config['type'] == 'sqlite'

        print("Database type:", "SQLite" if is_sqlite else "MySQL")
        print("Checking author_staff_mapping table...")

        # Check if table exists
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        if 'author_staff_mapping' not in tables:
            print("Table does not exist. Creating it...")
            AuthorStaffMapping.__table__.create(engine)
            print("[OK] Table created successfully!")
        else:
            print("Table exists. Recreating to fix structure...")

            with engine.connect() as conn:
                # Backup existing data
                result = conn.execute(text("SELECT * FROM author_staff_mapping"))
                existing_data = result.fetchall()
                print(f"Found {len(existing_data)} existing mappings. Backing up...")

                # Drop and recreate table
                conn.execute(text("DROP TABLE author_staff_mapping"))
                conn.commit()

                print("Creating new table with correct structure...")
                AuthorStaffMapping.__table__.create(engine)

                # Restore data (if any)
                if existing_data:
                    print(f"Restoring {len(existing_data)} mappings...")
                    for row in existing_data:
                        if is_sqlite:
                            # SQLite: Skip id column (will auto-generate)
                            insert_sql = """
                            INSERT INTO author_staff_mapping
                                (author_name, author_email, bank_id_1, staff_id, staff_name, mapped_date, notes)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                            """
                            conn.execute(text(insert_sql), (
                                row[1], row[2], row[3], row[4], row[5], row[6], row[7]
                            ))
                        else:
                            # MySQL
                            insert_sql = """
                            INSERT INTO author_staff_mapping
                                (author_name, author_email, bank_id_1, staff_id, staff_name, mapped_date, notes)
                            VALUES (:an, :ae, :bi, :si, :sn, :md, :nt)
                            """
                            conn.execute(text(insert_sql), {
                                'an': row[1], 'ae': row[2], 'bi': row[3],
                                'si': row[4], 'sn': row[5], 'md': row[6], 'nt': row[7]
                            })
                    conn.commit()
                    print(f"[OK] Restored {len(existing_data)} mappings")

        print("\n" + "="*60)
        print("Database fix complete!")
        print("="*60)

    except Exception as e:
        print(f"[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_mapping_table()
