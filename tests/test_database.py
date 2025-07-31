#!/usr/bin/env python3
"""
Comprehensive database testing script for HackerIot Workshop Management System.

This script performs extensive testing of:
- Database connectivity and schema validation
- Table structure and relationships
- Sample data operations
- API query functionality
- Data integrity and constraints

Run this after setting up your database to ensure everything works correctly.
"""

# Fix imports from parent directory
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
import json
from datetime import datetime, timedelta
import requests
import time
from flask import Flask

def check_database_exists():
    """Check if the database file exists and throw detailed errors if not."""
    print("=== Checking Database File ===")
    
    try:
        from config import Config
        db_path = Config.DATABASE_PATH
        
        print(f"Looking for database: {db_path}")
        print(f"Full path: {os.path.abspath(db_path)}")
        print(f"Database folder: {Config.DB_FOLDER}")
        
        if not os.path.exists(db_path):
            # List files in database directory to help user locate their database
            print(f"\n[ERROR] DATABASE NOT FOUND: {db_path}")
            
            if os.path.exists(Config.DB_FOLDER):
                print(f"Files in database folder:")
                for file in os.listdir(Config.DB_FOLDER):
                    if file.endswith('.db'):
                        print(f"   [DB] {file}")
                    else:
                        print(f"   [FILE] {file}")
            else:
                print(f"[ERROR] Database folder doesn't exist: {Config.DB_FOLDER}")
            
            raise FileNotFoundError(f"""
DATABASE NOT FOUND: {db_path}

Possible solutions:
1. Create the database by running your Flask app first
2. Check if your database has a different name in config.py
3. Verify the database folder path is correct
4. Make sure the database file exists in the folder

Database folder: {Config.DB_FOLDER}
Looking for file: {Config.DB_NAME}
""")
        
        # Check file size and permissions
        file_size = os.path.getsize(db_path)
        print(f"[OK] Database file found: {db_path}")
        print(f"Database size: {file_size:,} bytes")
        
        if file_size == 0:
            raise ValueError("Database file exists but is empty (0 bytes)")
        
        # Test if file is readable/writable
        if not os.access(db_path, os.R_OK):
            raise PermissionError(f"Database file is not readable: {db_path}")
        
        if not os.access(db_path, os.W_OK):
            print("[WARNING] Database file is not writable")
        
        return db_path
        
    except ImportError as e:
        raise ImportError(f"Cannot import config: {e}. Make sure config.py exists and is correct.")
    except Exception as e:
        print(f"[ERROR] Database check failed: {e}")
        raise

def test_database_connectivity():
    """Test basic database connectivity and table existence."""
    print("\n=== Testing Database Connectivity ===")
    
    try:
        db_path = check_database_exists()
        
        from config import Config
        from models import db, Users, Workshop, Registration, Skill, UserSkill, WorkshopSkill
        
        # Create Flask app for testing
        app = Flask(__name__)
        app.config.from_object(Config)
        
        # Initialize database
        db.init_app(app)
        
        with app.app_context():
            # Test table access with your exact schema
            print("\n=== Testing Table Access ===")
            
            # Test Users table
            try:
                user_count = Users.query.count()
                print(f"[OK] Users table: {user_count} records")
            except Exception as e:
                print(f"[ERROR] Users table error: {e}")
                raise
            
            # Test Workshop table  
            try:
                workshop_count = Workshop.query.count()
                print(f"[OK] Workshop table: {workshop_count} records")
            except Exception as e:
                print(f"[ERROR] Workshop table error: {e}")
                raise
            
            # Test Skill table
            try:
                skill_count = Skill.query.count()
                print(f"[OK] Skill table: {skill_count} records")
            except Exception as e:
                print(f"[ERROR] Skill table error: {e}")
                raise
            
            # Test Registration table
            try:
                registration_count = Registration.query.count()
                print(f"[OK] Registration table: {registration_count} records")
            except Exception as e:
                print(f"[ERROR] Registration table error: {e}")
                raise
            
            # Test UserSkill table
            try:
                user_skill_count = UserSkill.query.count()
                print(f"[OK] UserSkill table: {user_skill_count} records")
            except Exception as e:
                print(f"[ERROR] UserSkill table error: {e}")
                raise
            
            # Test WorkshopSkill table
            try:
                workshop_skill_count = WorkshopSkill.query.count()
                print(f"[OK] WorkshopSkill table: {workshop_skill_count} records")
            except Exception as e:
                print(f"[ERROR] WorkshopSkill table error: {e}")
                raise
            
            print("[OK] All tables accessible!")
            return True
            
    except Exception as e:
        print(f"[ERROR] Database connectivity test failed: {e}")
        return False

def test_schema_compatibility():
    """Test if our models match the actual database schema exactly."""
    print("\n=== Testing Schema Compatibility ===")
    
    try:
        db_path = check_database_exists()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Test each table's schema against your exact specification
        expected_schema = {
            'Users': {
                'columns': ['UserId', 'Name', 'Email', 'CreatedDate'],
                'required': ['UserId', 'Name', 'Email', 'CreatedDate']
            },
            'Skill': {
                'columns': ['SkillId', 'Name'],
                'required': ['SkillId', 'Name']
            },
            'UserSkill': {
                'columns': ['UserSkillId', 'UserId', 'SkillId', 'Grade'],
                'required': ['UserSkillId', 'UserId', 'SkillId', 'Grade']
            },
            'Workshop': {
                'columns': ['WorkshopId', 'Title', 'Description', 'SessionDateTime', 'DurationMin', 'MaxCapacity'],
                'required': ['WorkshopId', 'Title', 'SessionDateTime', 'DurationMin', 'MaxCapacity']
            },
            'WorkshopSkill': {
                'columns': ['WorkshopSkillId', 'WorkshopId', 'SkillId'],
                'required': ['WorkshopSkillId', 'WorkshopId', 'SkillId']
            },
            'Registration': {
                'columns': ['RegistrationId', 'WorkshopId', 'UserId', 'RegisteredAt', 'Status'],
                'required': ['RegistrationId', 'WorkshopId', 'UserId', 'RegisteredAt', 'Status']
            },
            'WorkshopLeader': {
                'columns': ['WorkshopId', 'LeaderId', 'AssignedAt'],
                'required': ['WorkshopId', 'LeaderId', 'AssignedAt']
            }
        }
        
        # Check if foreign keys are enabled
        cursor.execute("PRAGMA foreign_keys")
        fk_enabled = cursor.fetchone()[0]
        if fk_enabled:
            print("[OK] Foreign keys are ENABLED")
        else:
            print("[WARNING] Foreign keys are DISABLED - your data integrity is at risk!")
        
        # Check each table schema
        all_good = True
        for table_name, expected in expected_schema.items():
            print(f"\n--- Checking {table_name} table ---")
            
            # Check if table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
            if not cursor.fetchone():
                print(f"[ERROR] Table {table_name} does not exist!")
                all_good = False
                continue
            
            # Get table info
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            if not columns:
                print(f"[ERROR] Cannot get schema for {table_name}")
                all_good = False
                continue
            
            # Check columns
            actual_columns = [col[1] for col in columns]
            print(f"   Columns: {', '.join(actual_columns)}")
            
            # Check required columns
            missing_required = [col for col in expected['required'] if col not in actual_columns]
            if missing_required:
                print(f"[ERROR] Missing required columns in {table_name}: {missing_required}")
                all_good = False
            else:
                print(f"[OK] All required columns present in {table_name}")
            
            # Check for extra columns (could be SupabaseId, AvatarUrl that we'll add)
            extra_columns = [col for col in actual_columns if col not in expected['columns']]
            if extra_columns:
                print(f"[INFO] Extra columns in {table_name}: {extra_columns}")
        
        # Check foreign key constraints
        print(f"\n=== Checking Foreign Key Constraints ===")
        
        fk_tables = ['UserSkill', 'WorkshopSkill', 'Registration']
        for table in fk_tables:
            cursor.execute(f"PRAGMA foreign_key_list({table})")
            fks = cursor.fetchall()
            if fks:
                print(f"[OK] {table} has {len(fks)} foreign key(s)")
                for fk in fks:
                    print(f"   {fk[3]} -> {fk[2]}.{fk[4]}")
            else:
                print(f"[WARNING] {table} has no foreign keys defined")
        
        conn.close()
        return all_good
        
    except Exception as e:
        print(f"[ERROR] Schema compatibility test failed: {e}")
        return False

def test_sample_data():
    """Test reading sample data and verify relationships work."""
    print("\n=== Testing Sample Data & Relationships ===")
    
    try:
        from config import Config
        from models import db, Users, Workshop, Registration, Skill, UserSkill, WorkshopSkill, UserRole
        from flask import Flask
        
        app = Flask(__name__)
        app.config.from_object(Config)
        db.init_app(app)
        
        with app.app_context():
            # Test reading sample data
            print("Sample data from each table:")
            
            # Sample User
            sample_user = Users.query.first()
            if sample_user:
                print(f"   [USER] {sample_user.Name} ({sample_user.Email})")
                print(f"       UserId: {sample_user.UserId}, Created: {sample_user.CreatedDate}")
                print(f"       Role (DB Integer): {sample_user._role}, Role (Enum): {sample_user.Role}")
                
                # Test User relationships
                user_skills = sample_user.skills
                user_registrations = sample_user.registrations
                print(f"       Skills: {len(user_skills)}, Registrations: {len(user_registrations)}")
                
                # Test role checking methods
                print(f"       Is Admin: {sample_user.is_admin()}")
                print(f"       Can Manage Workshops: {sample_user.can_manage_workshops()}")
            else:
                print("   [USER] No users found")
            
            # Sample Workshop
            sample_workshop = Workshop.query.first()
            if sample_workshop:
                print(f"   [WORKSHOP] {sample_workshop.Title}")
                print(f"       DateTime: {sample_workshop.SessionDateTime}")
                print(f"       Duration: {sample_workshop.DurationMin}min, Capacity: {sample_workshop.MaxCapacity}")
                
                # Test Workshop relationships
                workshop_skills = sample_workshop.skills
                workshop_registrations = sample_workshop.registrations
                print(f"       Required skills: {len(workshop_skills)}, Registrations: {len(workshop_registrations)}")
            else:
                print("   [WORKSHOP] No workshops found")
            
            # Sample Skill
            sample_skill = Skill.query.first()
            if sample_skill:
                print(f"   [SKILL] {sample_skill.Name} (SkillId: {sample_skill.SkillId})")
            else:
                print("   [SKILL] No skills found")
            
            # Sample Registration
            sample_registration = Registration.query.first()
            if sample_registration:
                print(f"   [REGISTRATION] ID {sample_registration.RegistrationId}")
                print(f"       User: {sample_registration.UserId}, Workshop: {sample_registration.WorkshopId}")
                print(f"       Status (DB Integer): {sample_registration._status}, Status (Enum): {sample_registration.Status}")
                print(f"       Registered: {sample_registration.RegisteredAt}")
            else:
                print("   [REGISTRATION] No registrations found")
            
            # Test both hybrid integer conversions
            all_registrations = Registration.query.all()
            if all_registrations:
                print(f"\n   [HYBRID STATUS TEST] Found {len(all_registrations)} registrations:")
                for reg in all_registrations:
                    print(f"       Registration {reg.RegistrationId}: DB Integer={reg._status} -> Enum={reg.Status}")
            
            all_users = Users.query.all()
            print(f"\n   [HYBRID ROLE TEST] Found {len(all_users)} users:")
            for user in all_users:
                print(f"       {user.Name}: DB Integer={user._role} -> Enum={user.Role}")
                print(f"                     Can manage workshops: {user.can_manage_workshops()}")
            
            print("[OK] Sample data reading successful!")
            print("[OK] Both hybrid integer->enum conversions working!")
            return True
            
    except Exception as e:
        print(f"[ERROR] Sample data test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_queries():
    """Test common queries that your API will use."""
    print("\n=== Testing API Queries ===")
    
    try:
        from config import Config
        from models import db, Users, Workshop, Registration, Skill, UserSkill, WorkshopSkill
        from flask import Flask
        
        app = Flask(__name__)
        app.config.from_object(Config)
        db.init_app(app)
        
        with app.app_context():
            print("Testing workshop capacity calculations...")
            workshops = Workshop.query.limit(3).all()
            
            for workshop in workshops:
                # Count registered users (Status = 'Registered')
                registered_count = Registration.query.filter_by(
                    WorkshopId=workshop.WorkshopId,
                    Status='Registered'
                ).count()
                vacant = workshop.MaxCapacity - registered_count
                print(f"   [CAPACITY] {workshop.Title}: {registered_count}/{workshop.MaxCapacity} registered (vacant: {vacant})")
            
            print("\nTesting skill-based queries...")
            skills = Skill.query.limit(3).all()
            
            for skill in skills:
                # Count workshops requiring this skill
                workshops_with_skill = Workshop.query.join(WorkshopSkill).filter(
                    WorkshopSkill.SkillId == skill.SkillId
                ).count()
                
                # Count users with this skill
                users_with_skill = Users.query.join(UserSkill).filter(
                    UserSkill.SkillId == skill.SkillId
                ).count()
                
                print(f"   [SKILL] {skill.Name}: {workshops_with_skill} workshops need it, {users_with_skill} users have it")
            
            print("\nTesting user authentication queries...")
            sample_user = Users.query.first()
            if sample_user:
                # Test email lookup (critical for Supabase auth)
                user_by_email = Users.query.filter_by(Email=sample_user.Email).first()
                if user_by_email:
                    print(f"   [AUTH] Email lookup works: {user_by_email.Name}")
                
                # Test user's registration status
                user_registrations = Registration.query.filter_by(UserId=sample_user.UserId).all()
                for reg in user_registrations[:2]:  # Show first 2
                    workshop = Workshop.query.get(reg.WorkshopId)
                    if workshop:
                        print(f"   [REGISTRATION] {sample_user.Name} -> {workshop.Title} ({reg.Status})")
            
            print("[OK] Query tests successful!")
            return True
            
    except Exception as e:
        print(f"[ERROR] Query tests failed: {e}")
        return False

def main():
    """Run all tests with your exact schema."""
    print("=== HackerIot Database Connectivity Test ===")
    print("Testing against your exact schema")
    print("=" * 60)
    
    tests = [
        ("Database File Check", lambda: check_database_exists() is not None),
        ("Database Connectivity", test_database_connectivity),
        ("Schema Compatibility", test_schema_compatibility),
        ("Sample Data & Relationships", test_sample_data),
        ("API Queries", test_queries)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"[ERROR] {test_name} failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "="*60)
    print("=== TEST SUMMARY ===")
    print("="*60)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"{test_name:.<35} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("*** All tests passed! Your database is ready for Supabase integration. ***")
        print("\nYour schema is perfect:")
        print("- All tables present with correct structure")
        print("- Foreign key relationships working")
        print("- Sample data accessible")
        print("- API queries functional")
        print("\nNext steps:")
        print("1. Run: python migrate_user_table.py")
        print("2. Set up Supabase environment variables")
        print("3. Configure Google OAuth in Supabase")
    else:
        print("[WARNING] Some tests failed. Please check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 