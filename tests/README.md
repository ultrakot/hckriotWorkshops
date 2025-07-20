# HackerIot Server Tests

This folder contains all test scripts for the HackerIot server project. Run these tests to verify your database connectivity, schema compatibility, and system configuration.

## Test Scripts

### 🧪 `test_database.py` - Comprehensive Database Test
**Main comprehensive test for your database and API**

**Usage:** `python tests/test_database.py`

**What it tests:**
- ✅ Database file exists and is accessible
- ✅ All tables are present (Users, Workshop, Registration, Skill, UserSkill, WorkshopSkill)
- ✅ Schema matches your exact specification
- ✅ Foreign key constraints are properly defined
- ✅ Sample data can be read from all tables
- ✅ SQLAlchemy relationships work correctly
- ✅ API queries function properly (capacity calculation, skill filtering, user lookup)

**Expected Output:**
```
🎉 All tests passed! Your database is ready for Supabase integration.
```

### 📍 `test_db_location.py` - Database Location Verification
**Quick test to verify your database location and basic connectivity**

**Usage:** `python tests/test_db_location.py`

**What it tests:**
- ✅ Database folder exists
- ✅ Database file is found and accessible
- ✅ Basic SQLite connection works
- ✅ Tables can be queried
- ✅ Foreign keys are enabled
- ✅ Flask-SQLAlchemy connection works

**Use this when:**
- First setting up the project
- Troubleshooting database path issues
- Quick verification after configuration changes

### 🔧 `test_imports.py` - Import & Dependencies Test
**Tests that all required Python libraries are installed and working**

**Usage:** `python tests/test_imports.py`

**What it tests:**
- ✅ Flask imports correctly
- ✅ SQLAlchemy imports without errors
- ✅ Flask-SQLAlchemy initializes properly
- ✅ Basic model creation works
- ✅ In-memory database creation works

**Use this when:**
- Setting up the project for the first time
- Troubleshooting library version conflicts
- Verifying requirements.txt installation

## Running Tests

### Quick Start Test Sequence
```bash
# 1. Test imports and dependencies first
python tests/test_imports.py

# 2. Verify database location
python tests/test_db_location.py

# 3. Run comprehensive database tests
python tests/test_database.py
```

### Individual Test Usage
```bash
# Test just imports
python tests/test_imports.py

# Test just database location
python tests/test_db_location.py

# Full database test
python tests/test_database.py
```

## Expected Results

### ✅ All Tests Pass
If all tests pass, you should see:
```
🎉 Everything looks good!
Your database is properly configured and accessible.

Next steps:
• Run: python migrate_user_table.py (add Supabase columns)
• Start your Flask app: python app.py
```

### ❌ Tests Fail
Common issues and solutions:

**Database not found:**
- Check your database path in `config.py`
- Verify the database file exists in the specified folder
- Make sure folder path is correct

**Import errors:**
- Run: `pip install -r requirements.txt`
- Check for version conflicts in SQLAlchemy
- Use compatible versions from requirements.txt

**Schema mismatches:**
- Verify your database schema matches the expected structure
- Check table names are correct (case-sensitive)
- Ensure foreign keys are properly defined

## Database Schema Expected

Your database should have these exact tables:
- **Users** (UserId, Name, Email, CreatedDate)
- **Skill** (SkillId, Name)  
- **UserSkill** (UserSkillId, UserId, SkillId, Grade)
- **Workshop** (WorkshopId, Title, Description, SessionDate, StartTime, DurationMin, MaxCapacity)
- **WorkshopSkill** (WorkshopSkillId, WorkshopId, SkillId)
- **Registration** (RegistrationId, WorkshopId, UserId, RegisteredAt, Status)

## Configuration

These tests use your `config.py` settings:
```python
DB_FOLDER = r"C:\Users\RozaVatkin\Documents\Projects\Hackeriot\Site\HackeriotDB"
DB_NAME = "hackeriot.db"
```

Update the path in `config.py` if your database is located elsewhere. 