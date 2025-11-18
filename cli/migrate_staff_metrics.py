"""Migration script to add current year metrics columns to staff_metrics table."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from cli.config import Config
from cli.models import get_engine, get_session


def migrate_staff_metrics_table():
    """Add new columns for current year metrics to staff_metrics table."""

    print("=" * 80)
    print("DATABASE MIGRATION: Adding Current Year Metrics Columns")
    print("=" * 80)

    config = Config()
    db_config = config.get_db_config()
    engine = get_engine(db_config)

    # List of new columns to add
    new_columns = [
        ("staff_pc_code", "VARCHAR(100)", "Staff PC code from staff_details"),
        ("default_role", "VARCHAR(255)", "Default role from staff_details"),
        ("current_year", "INTEGER", "Year for which current year metrics are calculated"),
        ("cy_total_commits", "INTEGER DEFAULT 0", "Total commits in current year"),
        ("cy_total_prs", "INTEGER DEFAULT 0", "Total PRs created in current year"),
        ("cy_total_approvals_given", "INTEGER DEFAULT 0", "Total PR approvals given in current year"),
        ("cy_total_code_reviews_given", "INTEGER DEFAULT 0", "Total code reviews given in current year"),
        ("cy_total_code_reviews_received", "INTEGER DEFAULT 0", "Total code reviews received in current year"),
        ("cy_total_repositories", "INTEGER DEFAULT 0", "Number of unique repositories touched in current year"),
        ("cy_total_files_changed", "INTEGER DEFAULT 0", "Total files changed in current year"),
        ("cy_total_lines_changed", "INTEGER DEFAULT 0", "Total lines (added+deleted) in current year"),
        ("cy_total_chars", "INTEGER DEFAULT 0", "Total characters (added+deleted) in current year"),
        ("cy_total_code_churn", "INTEGER DEFAULT 0", "Code churn (lines deleted) in current year"),
        ("cy_different_file_types", "INTEGER DEFAULT 0", "Number of different file types worked in current year"),
        ("cy_different_repositories", "INTEGER DEFAULT 0", "Number of different repositories in current year"),
        ("cy_different_project_keys", "INTEGER DEFAULT 0", "Number of different project keys in current year"),
        ("cy_pct_code", "FLOAT DEFAULT 0.0", "Percentage of code files"),
        ("cy_pct_config", "FLOAT DEFAULT 0.0", "Percentage of config files"),
        ("cy_pct_documentation", "FLOAT DEFAULT 0.0", "Percentage of documentation files"),
        ("cy_avg_commits_monthly", "FLOAT DEFAULT 0.0", "Average commits per month in current year"),
        ("cy_avg_prs_monthly", "FLOAT DEFAULT 0.0", "Average PRs per month in current year"),
        ("cy_avg_approvals_monthly", "FLOAT DEFAULT 0.0", "Average approvals per month in current year"),
        ("cy_file_types_list", "TEXT", "Comma-separated list of file types in current year"),
        ("cy_repositories_list", "TEXT", "Comma-separated list of repositories in current year"),
        ("cy_project_keys_list", "TEXT", "Comma-separated list of project keys in current year"),
        ("cy_start_date", "DATE", "Start date for current year metrics"),
        ("cy_end_date", "DATE", "End date for current year metrics"),
    ]

    with engine.connect() as connection:
        # Check if table exists (SQLite compatible)
        check_table_sql = """
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='staff_metrics'
        """

        result = connection.execute(text(check_table_sql))
        table_exists = result.fetchone() is not None

        if not table_exists:
            print("[ERROR] staff_metrics table does not exist!")
            print("   Please run the extract command first to create the table.")
            return False

        print(f"\n[OK] Found staff_metrics table")
        print(f"\nAdding {len(new_columns)} new columns...")

        added_count = 0
        skipped_count = 0

        for column_name, column_type, comment in new_columns:
            try:
                # Check if column already exists (SQLite compatible)
                check_column_sql = f"""
                    SELECT COUNT(*) as cnt FROM pragma_table_info('staff_metrics')
                    WHERE name = '{column_name}'
                """

                result = connection.execute(text(check_column_sql))
                column_exists = result.scalar() > 0

                if column_exists:
                    print(f"  [SKIP]  {column_name:35s} - Already exists, skipping")
                    skipped_count += 1
                    continue

                # Add the column
                add_column_sql = f"""
                    ALTER TABLE staff_metrics
                    ADD COLUMN {column_name} {column_type}
                """

                connection.execute(text(add_column_sql))
                connection.commit()

                print(f"  [OK]  {column_name:35s} - Added successfully")
                added_count += 1

            except Exception as e:
                print(f"  [ERROR] {column_name:35s} - Error: {str(e)}")
                continue

        print(f"\n" + "=" * 80)
        print(f"MIGRATION COMPLETE")
        print(f"=" * 80)
        print(f"  Added: {added_count} columns")
        print(f"  Skipped: {skipped_count} columns (already exist)")
        print(f"  Total: {len(new_columns)} columns")

        if added_count > 0:
            print(f"\n[OK] New columns added successfully!")
            print(f"\nNext steps:")
            print(f"  1. Run: python -m cli calculate-metrics --staff")
            print(f"  2. This will populate the new columns with current year data")
        else:
            print(f"\n[OK] All columns already exist. No migration needed.")

        return True


if __name__ == "__main__":
    migrate_staff_metrics_table()
