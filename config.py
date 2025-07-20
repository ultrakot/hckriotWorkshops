import os

class Config:
    # User's specific database location
    DB_FOLDER = r"C:\Users\RozaVatkin\Documents\Projects\Hackeriot\Site\HackeriotDB"
    DB_NAME = "hackeriot.db"
    
    # Construct the full database path
    DATABASE_PATH = os.path.join(DB_FOLDER, DB_NAME)
    
    # SQLite URL format for absolute paths (use forward slashes even on Windows)
    DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{DATABASE_PATH.replace(os.sep, '/')}")
    
    SUPABASE_URL = os.environ.get("SUPABASE_URL")
    SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = True 