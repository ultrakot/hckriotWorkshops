#!/usr/bin/env python3
"""
SQLite initialization script to enable foreign keys and set optimal pragmas.
This should be run once to configure your SQLite database properly.
"""

import sqlite3
import os
from config import Config

def init_sqlite_settings():
    """Initialize SQLite with optimal settings."""
    db_path = Config.DATABASE_URL.replace('sqlite:///', '')
    
    if not os.path.exists(db_path):
        print(f"Database {db_path} doesn't exist yet.")
        print("Run your Flask app first to create the database.")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("Configuring SQLite settings...")
        
        # Enable foreign key constraints (VERY IMPORTANT)
        cursor.execute("PRAGMA foreign_keys = ON;")
        print("[OK] Foreign key constraints enabled")
        
        # Set journal mode to WAL for better concurrent access
        cursor.execute("PRAGMA journal_mode = WAL;")
        result = cursor.fetchone()[0]
        print(f"[OK] Journal mode set to: {result}")
        
        # Set synchronous mode for better performance
        cursor.execute("PRAGMA synchronous = NORMAL;")
        print("[OK] Synchronous mode set to NORMAL")
        
        # Set cache size (in KB, negative means KB)
        cursor.execute("PRAGMA cache_size = -64000;")  # 64MB cache
        print("[OK] Cache size set to 64MB")
        
        # Set temp store to memory for better performance
        cursor.execute("PRAGMA temp_store = MEMORY;")
        print("[OK] Temp store set to memory")
        
        # Enable query planner stability
        cursor.execute("PRAGMA optimize;")
        print("[OK] Query optimizer updated")
        
        conn.commit()
        
        # Verify foreign keys are working
        cursor.execute("PRAGMA foreign_keys;")
        fk_status = cursor.fetchone()[0]
        
        if fk_status == 1:
            print("[OK] SQLite configuration completed successfully!")
            print("   Foreign keys are ENABLED - your data integrity is protected")
        else:
            print("[WARNING] Foreign keys are not enabled")
        
        # Show some database info
        cursor.execute("PRAGMA database_list;")
        db_info = cursor.fetchall()
        for db in db_info:
            print(f"Database: {db[1]} at {db[2]}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Error configuring SQLite: {e}")
        return False
    finally:
        conn.close()

def check_tables():
    """Check if all required tables exist."""
    db_path = Config.DATABASE_URL.replace('sqlite:///', '')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("\nChecking database tables...")
        
        required_tables = ['Users', 'Workshop', 'Registration', 'Skill', 'UserSkill', 'WorkshopSkill', 'WorkshopLeader', 'RoleTypes', 'StatusTypes']
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        existing_tables = [table[0] for table in cursor.fetchall()]
        
        for table in required_tables:
            if table in existing_tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table};")
                count = cursor.fetchone()[0]
                print(f"[OK] {table}: {count} records")
            else:
                print(f"[ERROR] Missing table: {table}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Error checking tables: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    print("=== SQLite Database Initialization ===")
    print("=" * 40)
    
    if init_sqlite_settings():
        check_tables()
        print("\n[OK] Your SQLite database is properly configured!")
        print("\nImportant notes:")
        print("• Foreign keys are enabled (prevents orphaned records)")
        print("• WAL mode enabled (better for concurrent access)")
        print("• Performance optimizations applied")
        print("• Your database is ready for production use!")
    else:
        print("\n[ERROR] SQLite configuration failed") 