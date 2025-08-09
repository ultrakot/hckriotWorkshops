from flask import Flask
from flask_cors import CORS
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from config import Config
from models import db
from routes import init_routes


def create_app(config_object=None):
    """
    Application factory that creates and configures the Flask app.
    Accepts a configuration object to allow for different environments (e.g., testing).
    """
    app = Flask(__name__)
    
    # Use default config if none provided, instantiate it to trigger lazy loading
    if config_object is None:
        config_object = Config()
    
    app.config.from_object(config_object)
    
    # Enable CORS with configurable origins and all HTTP methods
    cors_origins = [
        config_object.FRONTEND_URL,
        "http://localhost:5173",   # Development frontend
        "http://localhost:5173"   # HTTPS development
    ]    
    
    # Add additional allowed origins from environment variable (comma-separated list)
    cors_env_origins = os.environ.get('CORS_ORIGINS', '')
    if cors_env_origins:
        additional_origins = [origin.strip() for origin in cors_env_origins.split(',') if origin.strip()]
        cors_origins.extend(additional_origins)
    
    # Remove duplicates while preserving order
    cors_origins = list(dict.fromkeys(cors_origins))
    
    # Configure CORS with all HTTP methods support
    CORS(app, 
         origins=cors_origins, 
         supports_credentials=True,
         methods="*",  # Allow all HTTP methods (GET, POST, PUT, DELETE, PATCH, OPTIONS, HEAD, etc.)
         allow_headers=['Content-Type', 'Authorization', 'X-Requested-With', 'Accept', 'Origin'],
         expose_headers=['Content-Range', 'X-Content-Range'])

    # Initialize database with connection pool settings if configured
    if hasattr(config_object, 'SQLALCHEMY_ENGINE_OPTIONS') and config_object.SQLALCHEMY_ENGINE_OPTIONS:
        db.init_app(app)
        # Apply engine options after initialization
        with app.app_context():
            engine = db.get_engine()
            print(f"Database configured: {config_object.get_db_info()}")
    else:
        db.init_app(app)
        with app.app_context():
            print(f"Database configured: {config_object.get_db_info()}")

    # Initialize routes
    init_routes(app)
    
    return app

# Create app instance for WSGI servers like gunicorn
app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    # Production-ready configuration
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=Config.DEBUG)
