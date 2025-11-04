"""Configuration management for the application."""

import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()


class Config:
    """Application configuration."""

    # Database configuration
    DB_TYPE = os.getenv('DB_TYPE', 'sqlite')

    # SQLite configuration
    SQLITE_DB_PATH = os.getenv('SQLITE_DB_PATH', 'git_history.db')

    # MariaDB configuration
    MARIADB_HOST = os.getenv('MARIADB_HOST', 'localhost')
    MARIADB_PORT = int(os.getenv('MARIADB_PORT', '3306'))
    MARIADB_USER = os.getenv('MARIADB_USER', 'root')
    MARIADB_PASSWORD = os.getenv('MARIADB_PASSWORD', '')
    MARIADB_DATABASE = os.getenv('MARIADB_DATABASE', 'git_history')

    # Git credentials
    GIT_USERNAME = os.getenv('GIT_USERNAME', '')
    GIT_PASSWORD = os.getenv('GIT_PASSWORD', '')

    # Clone directory
    CLONE_DIR = os.getenv('CLONE_DIR', './repositories')

    @classmethod
    def get_db_config(cls):
        """Get database configuration based on DB_TYPE."""
        if cls.DB_TYPE.lower() == 'sqlite':
            return {
                'type': 'sqlite',
                'path': cls.SQLITE_DB_PATH
            }
        elif cls.DB_TYPE.lower() == 'mariadb':
            return {
                'type': 'mariadb',
                'host': cls.MARIADB_HOST,
                'port': cls.MARIADB_PORT,
                'user': cls.MARIADB_USER,
                'password': cls.MARIADB_PASSWORD,
                'database': cls.MARIADB_DATABASE
            }
        else:
            raise ValueError(f"Unsupported DB_TYPE: {cls.DB_TYPE}")

    @classmethod
    def get_clone_dir(cls):
        """Get and create clone directory if it doesn't exist."""
        clone_path = Path(cls.CLONE_DIR)
        clone_path.mkdir(parents=True, exist_ok=True)
        return clone_path

    @classmethod
    def get_git_credentials(cls):
        """Get Git credentials."""
        return {
            'username': cls.GIT_USERNAME,
            'password': cls.GIT_PASSWORD
        }
