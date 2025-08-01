"""
Simple Configuration with Database Selector
"""
import os
from db_selector import DatabaseSelector

class Config:
    """Application configuration"""
    
    # Flask Configuration
    DEBUG = os.environ.get("DEBUG", "False").lower() in ("true", "1", "yes")  # Default to False for production
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")
    
    # Production URLs (configurable via environment variables)
    FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")  # Frontend callback URL
    API_URL = os.environ.get("API_URL", "http://localhost:5000")  # API base URL
    
    # Database - Uses DatabaseSelector to choose SQLite or Azure SQL  
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    @staticmethod
    def _get_database_uri():
        """Lazy loading of database URL"""
        return DatabaseSelector.get_database_url()
    
    def __init__(self):
        """Initialize configuration with lazy-loaded database URI"""
        # Set database URI when Config is instantiated, not at class definition
        self.SQLALCHEMY_DATABASE_URI = self._get_database_uri()
    
    # Supabase Integration
    SUPABASE_URL = os.environ.get("SUPABASE_URL")
    SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
    
    @classmethod
    def get_db_info(cls):
        """Get information about current database configuration"""
        try:
            return DatabaseSelector.get_db_info()
        except ValueError as e:
            # Handle case where environment variables aren't set yet
            return {'db_type': 'not_configured', 'error': str(e), 'status': 'missing_env_vars'}