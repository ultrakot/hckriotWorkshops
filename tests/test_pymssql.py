#!/usr/bin/env python3
"""
Test script to verify pymssql database connection
Run this to ensure your Azure SQL connection works with pymssql
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_pymssql_direct():
    """Test pymssql connection directly"""
    try:
        import pymssql
        print("✅ pymssql module imported successfully")
        
        server = os.environ.get("AZURE_SQL_SERVER")
        database = os.environ.get("AZURE_SQL_DATABASE") 
        username = os.environ.get("AZURE_SQL_USERNAME")
        password = os.environ.get("AZURE_SQL_PASSWORD")
        
        if not all([server, database, username, password]):
            print("❌ Missing Azure SQL credentials in environment variables")
            print("Required: AZURE_SQL_SERVER, AZURE_SQL_DATABASE, AZURE_SQL_USERNAME, AZURE_SQL_PASSWORD")
            return False
            
        print(f"🔗 Connecting to: {server}/{database} as {username}")
        
        # Test direct pymssql connection - Azure SQL format
        # IMPORTANT: For Azure SQL, use username@servername format (without .database.windows.net)
        server_short = server.replace('.database.windows.net', '')
        azure_username = f"{username}@{server_short}"
        
        print(f"🔗 Using Azure SQL format: {azure_username}@{server}")
        
        conn = pymssql.connect(
            server=server,
            user=azure_username,
            password=password,
            database=database,
            timeout=30,
            login_timeout=30
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT 1 as test")
        result = cursor.fetchone()
        
        if result and result[0] == 1:
            print("✅ Direct pymssql connection successful!")
            cursor.close()
            conn.close()
            return True
        else:
            print("❌ Direct pymssql connection test failed")
            return False
            
    except ImportError:
        print("❌ pymssql not installed. Install with: pip install pymssql")
        return False
    except Exception as e:
        print(f"❌ Direct pymssql connection failed: {e}")
        return False

def test_sqlalchemy_pymssql():
    """Test SQLAlchemy with pymssql"""
    try:
        from db_selector import DatabaseSelector
        print("✅ DatabaseSelector imported successfully")
        
        # Force pymssql driver
        os.environ["AZURE_SQL_DRIVER_TYPE"] = "pymssql"
        os.environ["FLASK_ENV"] = "production"
        
        # Test using DatabaseSelector
        return DatabaseSelector.test_connection()
        
    except Exception as e:
        print(f"❌ SQLAlchemy pymssql test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing pymssql database connection...")
    print("=" * 50)
    
    # Show environment info
    print(f"FLASK_ENV: {os.environ.get('FLASK_ENV', 'not set')}")
    print(f"DB_TYPE: {os.environ.get('DB_TYPE', 'not set')}")
    print(f"AZURE_SQL_DRIVER_TYPE: {os.environ.get('AZURE_SQL_DRIVER_TYPE', 'auto-detect')}")
    print()
    
    # Test 1: Direct pymssql
    print("Test 1: Direct pymssql connection")
    print("-" * 30)
    direct_success = test_pymssql_direct()
    print()
    
    # Test 2: SQLAlchemy with pymssql
    print("Test 2: SQLAlchemy with pymssql")
    print("-" * 30)
    sqlalchemy_success = test_sqlalchemy_pymssql()
    print()
    
    # Summary
    print("=" * 50)
    if direct_success and sqlalchemy_success:
        print("🎉 All tests passed! pymssql is working correctly.")
        sys.exit(0)
    else:
        print("❌ Some tests failed. Check configuration and credentials.")
        sys.exit(1)

if __name__ == "__main__":
    main()