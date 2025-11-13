"""Configuration management for the application."""

import os
import json
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()


class Config:
    """Application configuration with PCF CUPS support."""

    @classmethod
    def _get_vcap_services(cls):
        """Get VCAP_SERVICES from PCF environment."""
        vcap_services = os.getenv('VCAP_SERVICES')
        if vcap_services:
            return json.loads(vcap_services)
        return {}

    @classmethod
    def _get_service_credentials(cls, service_name):
        """Get credentials from a specific CUPS service."""
        vcap_services = cls._get_vcap_services()

        # Check in user-provided services
        user_provided = vcap_services.get('user-provided', [])
        for service in user_provided:
            if service.get('name') == service_name:
                return service.get('credentials', {})

        return {}

    @classmethod
    def _get_config_value(cls, env_var, service_key, default='', service_name='git-history-config'):
        """
        Get configuration value with precedence:
        1. Environment variable (for local development)
        2. CUPS service credentials (for PCF)
        3. Default value
        """
        # First try environment variable
        value = os.getenv(env_var)
        if value:
            return value

        # Then try CUPS service
        credentials = cls._get_service_credentials(service_name)
        if credentials and service_key in credentials:
            return credentials[service_key]

        # Finally return default
        return default

    # Database configuration
    @property
    def DB_TYPE(self):
        return self._get_config_value('DB_TYPE', 'db_type', 'sqlite')

    @property
    def SQLITE_DB_PATH(self):
        return self._get_config_value('SQLITE_DB_PATH', 'sqlite_db_path', 'git_history.db')

    # MariaDB/MySQL configuration
    @property
    def MARIADB_HOST(self):
        # Check for bound MySQL service in PCF
        vcap_services = self._get_vcap_services()
        mysql_services = vcap_services.get('p-mysql', []) or vcap_services.get('cleardb', [])
        if mysql_services:
            return mysql_services[0].get('credentials', {}).get('hostname', 'localhost')
        return self._get_config_value('MARIADB_HOST', 'mariadb_host', 'localhost')

    @property
    def MARIADB_PORT(self):
        vcap_services = self._get_vcap_services()
        mysql_services = vcap_services.get('p-mysql', []) or vcap_services.get('cleardb', [])
        if mysql_services:
            return int(mysql_services[0].get('credentials', {}).get('port', 3306))
        return int(self._get_config_value('MARIADB_PORT', 'mariadb_port', '3306'))

    @property
    def MARIADB_USER(self):
        vcap_services = self._get_vcap_services()
        mysql_services = vcap_services.get('p-mysql', []) or vcap_services.get('cleardb', [])
        if mysql_services:
            return mysql_services[0].get('credentials', {}).get('username', 'root')
        return self._get_config_value('MARIADB_USER', 'mariadb_user', 'root')

    @property
    def MARIADB_PASSWORD(self):
        vcap_services = self._get_vcap_services()
        mysql_services = vcap_services.get('p-mysql', []) or vcap_services.get('cleardb', [])
        if mysql_services:
            return mysql_services[0].get('credentials', {}).get('password', '')
        return self._get_config_value('MARIADB_PASSWORD', 'mariadb_password', '')

    @property
    def MARIADB_DATABASE(self):
        vcap_services = self._get_vcap_services()
        mysql_services = vcap_services.get('p-mysql', []) or vcap_services.get('cleardb', [])
        if mysql_services:
            return mysql_services[0].get('credentials', {}).get('name', 'git_history')
        return self._get_config_value('MARIADB_DATABASE', 'mariadb_database', 'git_history')

    # Git credentials
    @property
    def GIT_USERNAME(self):
        return self._get_config_value('GIT_USERNAME', 'git_username', '')

    @property
    def GIT_PASSWORD(self):
        return self._get_config_value('GIT_PASSWORD', 'git_password', '')

    # Bitbucket configuration
    @property
    def BITBUCKET_URL(self):
        return self._get_config_value('BITBUCKET_URL', 'bitbucket_url', 'https://bitbucket.org')

    @property
    def BITBUCKET_USERNAME(self):
        return self._get_config_value('BITBUCKET_USERNAME', 'bitbucket_username', '')

    @property
    def BITBUCKET_APP_PASSWORD(self):
        return self._get_config_value('BITBUCKET_APP_PASSWORD', 'bitbucket_app_password', '')

    # Clone directory
    @property
    def CLONE_DIR(self):
        return self._get_config_value('CLONE_DIR', 'clone_dir', './repositories')

    def get_db_config(self):
        """Get database configuration based on DB_TYPE."""
        if self.DB_TYPE.lower() == 'sqlite':
            return {
                'type': 'sqlite',
                'path': self.SQLITE_DB_PATH
            }
        elif self.DB_TYPE.lower() in ['mariadb', 'mysql']:
            return {
                'type': 'mariadb',
                'host': self.MARIADB_HOST,
                'port': self.MARIADB_PORT,
                'user': self.MARIADB_USER,
                'password': self.MARIADB_PASSWORD,
                'database': self.MARIADB_DATABASE
            }
        else:
            raise ValueError(f"Unsupported DB_TYPE: {self.DB_TYPE}")

    def get_clone_dir(self):
        """Get and create clone directory if it doesn't exist."""
        clone_path = Path(self.CLONE_DIR)
        clone_path.mkdir(parents=True, exist_ok=True)
        return clone_path

    def get_git_credentials(self):
        """Get Git credentials."""
        return {
            'username': self.GIT_USERNAME,
            'password': self.GIT_PASSWORD
        }

    def get_bitbucket_config(self):
        """Get Bitbucket configuration."""
        return {
            'url': self.BITBUCKET_URL,
            'username': self.BITBUCKET_USERNAME,
            'password': self.BITBUCKET_APP_PASSWORD
        }
