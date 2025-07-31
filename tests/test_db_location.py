#!/usr/bin/env python3
"""
Database location and connectivity test for HackerIot Workshop System.

This script tests:
1. Database file existence and accessibility
2. Basic connectivity to SQLite database
3. Table existence verification
4. Simple query execution

This is typically the first test to run to ensure your database setup is correct.
"""

# Fix imports from parent directory
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
import json
from pathlib import Path

from config import Config

def verify_database_location():
    """Verify the database can be found and accessed."""
    print("=== Database Location Verification ===")
    print("=" * 40)
    
    # Show configuration
    print(f"Database folder: {Config.DB_FOLDER}")
    print(f"Database name: {Config.DB_NAME}")
    print(f"Full database path: {Config.DATABASE_PATH}")
    print(f"SQLAlchemy URL: {Config.DATABASE_URL}")
    
    # Check folder exists
    if os.path.exists(Config.DB_FOLDER):
        print(f"[OK] Database folder exists")
        
        # List all .db files in the folder
        db_files = [f for f in os.listdir(Config.DB_FOLDER) if f.endswith('.db')]
        if db_files:
            print(f"Database files found:")
            for db_file in db_files:
                file_path = os.path.join(Config.DB_FOLDER, db_file)
                size = os.path.getsize(file_path)
                status = "[TARGET]" if db_file == Config.DB_NAME else "[OTHER]"
                print(f"   {status} {db_file} ({size:,} bytes)")
        else:
            print("[WARNING] No .db files found in folder")
    else:
        print(f"[ERROR] Database folder does not exist: {Config.DB_FOLDER}")
        return False
    
    # Check specific database file
    if os.path.exists(Config.DATABASE_PATH):
        print(f"[OK] Target database file found")
        
        file_size = os.path.getsize(Config.DATABASE_PATH)
        print(f"Database size: {file_size:,} bytes")
        
        if file_size == 0:
            print("[WARNING] Database file is empty (0 bytes)")
            return False
        
        # Test connection
        try:
            print("Testing database connection...")
            conn = sqlite3.connect(Config.DATABASE_PATH)
            cursor = conn.cursor()
            
            # Test basic query
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            print(f"Found {len(tables)} tables:")
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
                count = cursor.fetchone()[0]
                print(f"   {table[0]}: {count} records")
            
            # Check if foreign keys are enabled
            cursor.execute("PRAGMA foreign_keys")
            fk_enabled = cursor.fetchone()[0]
            fk_status = "[ENABLED]" if fk_enabled else "[DISABLED]"
            print(f"Foreign keys: {fk_status}")
            
            conn.close()
            print("[OK] Database connection successful!")
            return True
            
        except Exception as e:
            print(f"[ERROR] Database connection failed: {e}")
            return False
    else:
        print(f"[ERROR] Database file not found: {Config.DATABASE_PATH}")
        
        # Suggest solutions
        print("\nPossible solutions:")
        print("1. Check if the database file name is correct")
        print("2. Verify the folder path in config.py")
        print("3. Make sure you have the right database file")
        
        return False

def test_flask_connection():
    """Test Flask-SQLAlchemy connection."""
    print("\n=== Testing Flask Connection ===")
    print("=" * 30)
    
    try:
        from flask import Flask
        from models import db, Users
        
        app = Flask(__name__)
        app.config.from_object(Config)
        
        db.init_app(app)
        
        with app.app_context():
            # Test query
            user_count = Users.query.count()
            print(f"Users in database: {user_count}")
            
            if user_count > 0:
                sample_user = Users.query.first()
                print(f"Sample user: {sample_user.Name} ({sample_user.Email})")
        
        print("[OK] Flask-SQLAlchemy connection successful!")
        return True
        
    except Exception as e:
        print(f"[ERROR] Flask connection failed: {e}")
        return False

if __name__ == "__main__":
    db_ok = verify_database_location()
    
    if db_ok:
        flask_ok = test_flask_connection()
        
        if flask_ok:
            print("\n*** Everything looks good! ***")
            print("Your database is properly configured and accessible.")
            print("\nNext steps:")
            print("- Run: python tests/test_database.py (full connectivity test)")
            print("- Run: python migrate_user_table.py (add Supabase columns)")
            print("- Start your Flask app: python app.py")
        else:
            print("\n[WARNING] Database found but Flask connection failed")
            print("Check your models.py and requirements")
    else:
        print("\n[ERROR] Database location issues found")
        print("Please fix the database path configuration first") 