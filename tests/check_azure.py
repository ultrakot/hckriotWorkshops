#!/usr/bin/env python3
"""
Quick Azure SQL Connection Checker
"""
import os
import sys

def check_azure_connection():
    """Test Azure SQL connection step by step"""
    
    print("🔍 Azure SQL Connection Checker")
    print("=" * 40)
    
    # Step 1: Check pyodbc
    try:
        import pyodbc
        print("✅ pyodbc library installed")
    except ImportError:
        print("❌ pyodbc not installed - run: pip install pyodbc")
        return False
    
    # Step 2: Check ODBC drivers
    drivers = pyodbc.drivers()
    if "ODBC Driver 17 for SQL Server" in drivers:
        print("✅ ODBC Driver 17 for SQL Server found")
    else:
        print("❌ ODBC Driver 17 for SQL Server not found")
        print(f"   Available drivers: {', '.join(drivers)}")
        return False
    
    # Step 3: Set test environment
    os.environ['DB_TYPE'] = 'azure'
    os.environ['AZURE_SQL_SERVER'] = 'hakeriotserver.database.windows.net'
    os.environ['AZURE_SQL_DATABASE'] = 'HackeriotDB'
    os.environ['AZURE_SQL_USERNAME'] = 'Hadmin'
    os.environ['AZURE_SQL_PASSWORD'] = 'kEWL91rl'
    
    # Step 4: Test URL generation
    try:
        from db_selector import DatabaseSelector
        db_url = DatabaseSelector.get_database_url()
        print("✅ Connection string generated")
        print(f"   🔗 {DatabaseSelector._mask_password(db_url)}")
    except Exception as e:
        print(f"❌ Connection string failed: {e}")
        return False
    
    # Step 5: Test actual connection
    try:
        from sqlalchemy import create_engine, text
        print("\n🔌 Testing database connection...")
        
        engine = create_engine(db_url, connect_args={"timeout": 10})
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1 as test"))
            test_value = result.fetchone()[0]
            print(f"✅ Connection successful! Test result: {test_value}")
            return True
            
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Connection failed: {error_msg}")
        
        # Specific error help
        if "timeout" in error_msg.lower():
            print("\n🔧 Network/Firewall Issue:")
            print("   • Check Azure SQL firewall rules")
            print("   • Add your IP to allowed list")
            print("   • Verify server is running")
        elif "login failed" in error_msg.lower():
            print("\n🔧 Authentication Issue:")
            print("   • Check username/password")
            print("   • Verify database exists")
        elif "driver" in error_msg.lower():
            print("\n🔧 Driver Issue:")
            print("   • Install ODBC Driver 17 for SQL Server")
        
        return False

if __name__ == "__main__":
    success = check_azure_connection()
    sys.exit(0 if success else 1)