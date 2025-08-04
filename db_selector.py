"""
Simple Database Selector - Chooses SQLite or Azure SQL based on environment flag
Supports both pyodbc and pymssql for Azure SQL connections
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
        
        try:
            if db_type == "azure":
                url = DatabaseSelector._get_azure_url()
                print(f"🔗 Database: Using Azure SQL with {DatabaseSelector._get_azure_driver_type()} driver")
                return url
            else:
                url = DatabaseSelector._get_sqlite_url()
                print(f"🔗 Database: Using SQLite")
                return url
        except Exception as e:
            print(f"❌ Database configuration error: {e}")
            raise
    
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
    def _get_azure_driver_type():
        """
        Determine which SQL Server driver to use:
        - In production environment (FLASK_ENV=production), use pymssql
        - Otherwise, use pyodbc
        - Can be overridden with AZURE_SQL_DRIVER_TYPE environment variable
        """
        # Allow manual override
        driver_type = os.environ.get("AZURE_SQL_DRIVER_TYPE")
        if driver_type:
            return driver_type.lower()
        
        # Auto-detect based on environment
        flask_env = os.environ.get("FLASK_ENV", "").lower()
        if flask_env == "production":
            return "pymssql"
        else:
            return "pyodbc"
    
    @staticmethod
    def _get_azure_url():
        """Get Azure SQL database URL - supports both pyodbc and pymssql"""
        server = os.environ.get("AZURE_SQL_SERVER")
        database = os.environ.get("AZURE_SQL_DATABASE")
        username = os.environ.get("AZURE_SQL_USERNAME")
        password = os.environ.get("AZURE_SQL_PASSWORD")
        
        # Validate required credentials
        if not all([server, database, username, password]):
            raise ValueError(
                "Azure SQL configuration incomplete. Required environment variables: "
                "AZURE_SQL_SERVER, AZURE_SQL_DATABASE, AZURE_SQL_USERNAME, AZURE_SQL_PASSWORD"
            )
        
        # Determine driver type
        driver_type = DatabaseSelector._get_azure_driver_type()
        
        # URL encode credentials
        encoded_password = quote_plus(password)
        encoded_username = quote_plus(username)
        
        if driver_type == "pymssql":
            # Use pymssql - simpler connection string, no ODBC driver needed
            # IMPORTANT: For Azure SQL, use username@servername format (without .database.windows.net)
            server_short = server.replace('.database.windows.net', '')
            azure_username = f"{username}@{server_short}"
            encoded_azure_username = quote_plus(azure_username)
            
            return (
                f"mssql+pymssql://{encoded_azure_username}:{encoded_password}"
                f"@{server}/{database}"
                f"?timeout=30"
                f"&charset=utf8"
            )
        else:
            # Use pyodbc (default for development)
            driver = os.environ.get("AZURE_SQL_DRIVER", "ODBC Driver 17 for SQL Server")
            encoded_driver = quote_plus(driver)
            
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
        
        info = {
            "db_type": db_type,
            "database_url": DatabaseSelector._mask_password(db_url),
            "status": "configured"
        }
        
        # Add driver type info for Azure SQL
        if db_type == "azure":
            info["driver_type"] = DatabaseSelector._get_azure_driver_type()
            info["is_production"] = os.environ.get("FLASK_ENV", "").lower() == "production"
        
        return info
    
    @staticmethod
    def test_connection():
        """Test database connection"""
        try:
            from sqlalchemy import create_engine, text
            url = DatabaseSelector.get_database_url()
            
            print(f"🧪 Testing connection: {DatabaseSelector._mask_password(url)}")
            
            # Create engine with short timeout for testing
            engine = create_engine(url, pool_timeout=10, pool_recycle=3600)
            
            # Test connection
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1 as test"))
                test_value = result.scalar()
                
            if test_value == 1:
                print("✅ Database connection successful!")
                return True
            else:
                print("❌ Database connection test failed")
                return False
                
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False
    
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