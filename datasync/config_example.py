"""
Configuration example for data synchronization.

Copy this file to config.py and update with your actual database credentials.
"""

# SQLite Source Database
SQLITE_URL = "sqlite:///git_history.db"

# MariaDB/MySQL Target Database
MARIADB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'database': 'gpt',
    'user': 'your_username',
    'password': 'your_password',
}

# Build MariaDB connection URL
MARIADB_URL = f"mysql+pymysql://{MARIADB_CONFIG['user']}:{MARIADB_CONFIG['password']}@{MARIADB_CONFIG['host']}:{MARIADB_CONFIG['port']}/{MARIADB_CONFIG['database']}"

# Sync Options
SYNC_OPTIONS = {
    'batch_size': 1000,  # Batch size for bulk operations
    'skip_existing': True,  # Skip records that already exist
    'verify_fk': True,  # Verify foreign key relationships
    'save_mappings': True,  # Save ID mappings to JSON
}
