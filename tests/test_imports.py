#!/usr/bin/env python3
"""
Quick test to check if SQLAlchemy import errors are resolved.
"""

import sys
import os

# Add the parent directory to sys.path to import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    print("Testing SQLAlchemy import...")
    from flask_sqlalchemy import SQLAlchemy
    print("[OK] Flask-SQLAlchemy imported successfully")
    
    from sqlalchemy import Column, Integer, String
    print("[OK] SQLAlchemy core imported successfully")
    
    from flask import Flask
    print("[OK] Flask imported successfully")
    
    # Test basic setup
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db = SQLAlchemy(app)
    print("[OK] SQLAlchemy initialized successfully")
    
    # Test model creation
    class TestModel(db.Model):
        id = Column(Integer, primary_key=True)
        name = Column(String(50))
    
    print("[OK] Model creation successful")
    
    with app.app_context():
        db.create_all()
        print("[OK] Database creation successful")
    
    print("\n*** All import tests passed! SQLAlchemy is working correctly. ***")
    
except Exception as e:
    print(f"[ERROR] {e}")
    print(f"   Error type: {type(e).__name__}")
    
    print(f"\nSystem Information:")
    print(f"Python version: {sys.version}")
    
    try:
        import sqlalchemy
        print(f"SQLAlchemy version: {sqlalchemy.__version__}")
    except:
        print("SQLAlchemy not installed")
    
    try:
        import flask_sqlalchemy
        print(f"Flask-SQLAlchemy version: {flask_sqlalchemy.__version__}")
    except:
        print("Flask-SQLAlchemy not installed") 