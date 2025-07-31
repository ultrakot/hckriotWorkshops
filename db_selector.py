"""
Simple Database Selector - Chooses SQLite or Azure SQL based on environment flag
"""
import os
from urllib.parse import quote_plus

class DatabaseSelector:
    """Simple class to select database based on environment flag"""
    
    @staticmethod
    def get_database_url():
        """
        Returns database URL based on DB_TYPE environment variable:
        - DB_TYPE=sqlite -> Uses SQLite database
        - DB_TYPE=azure -> Uses Azure SQL database
        """
        db_type = os.environ.get("DB_TYPE", "sqlite").lower()
        
        if db_type == "azure":
            return DatabaseSelector._get_azure_url()
        else:
            return DatabaseSelector._get_sqlite_url()
    
    @staticmethod
    def _get_sqlite_url():
        """Get SQLite database URL"""
        db_folder = os.environ.get("DB_FOLDER")
        db_name = os.environ.get("DB_NAME", "hackeriot.db")
        
        # Require DB_FOLDER to be explicitly set - no hardcoded defaults
        if not db_folder:
            raise ValueError(
                "DB_FOLDER environment variable is required when using SQLite.\n"
                "Set it in your environment or .env file:\n"
                "DB_FOLDER=C:\\path\\to\\your\\database\\folder"
            )
        
        database_path = os.path.join(db_folder, db_name)
        return f"sqlite:///{database_path.replace(os.sep, '/')}"
    
    @staticmethod
    def _get_azure_url():
        """Get Azure SQL database URL"""
        server = os.environ.get("AZURE_SQL_SERVER")
        database = os.environ.get("AZURE_SQL_DATABASE")
        username = os.environ.get("AZURE_SQL_USERNAME")
        password = os.environ.get("AZURE_SQL_PASSWORD")
        driver = os.environ.get("AZURE_SQL_DRIVER", "ODBC Driver 17 for SQL Server")
        
        # Validate required credentials
        if not all([server, database, username, password]):
            raise ValueError(
                "Azure SQL configuration incomplete. Required environment variables: "
                "AZURE_SQL_SERVER, AZURE_SQL_DATABASE, AZURE_SQL_USERNAME, AZURE_SQL_PASSWORD"
            )
        
        # URL encode credentials
        encoded_password = quote_plus(password)
        encoded_username = quote_plus(username)
        encoded_driver = quote_plus(driver)
        
        # Build connection string
        return (
            f"mssql+pyodbc://{encoded_username}:{encoded_password}"
            f"@{server}/{database}"
            f"?driver={encoded_driver}"
            f"&timeout=30"
            f"&Encrypt=yes"
            f"&TrustServerCertificate=no"
        )
    
    @staticmethod
    def get_current_db_type():
        """Get the current database type being used"""
        return os.environ.get("DB_TYPE", "sqlite").lower()
    
    @staticmethod
    def get_db_info():
        """Get information about current database configuration"""
        db_type = DatabaseSelector.get_current_db_type()
        db_url = DatabaseSelector.get_database_url()
        
        return {
            "db_type": db_type,
            "database_url": DatabaseSelector._mask_password(db_url),
            "status": "configured"
        }
    
    @staticmethod
    def _mask_password(url):
        """Mask password in database URL for safe logging"""
        if "://" in url and "@" in url:
            parts = url.split("://")
            if len(parts) == 2:
                protocol = parts[0]
                rest = parts[1]
                if "@" in rest:
                    credentials, server_part = rest.split("@", 1)
                    if ":" in credentials:
                        username, _ = credentials.split(":", 1)
                        return f"{protocol}://{username}:***@{server_part}"
        return url