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
    
    # Enable CORS for production frontend integration
    # Only allow specific origins for security
    cors_origins = [
        config_object.FRONTEND_URL,
        "http://localhost:3000",   # Development frontend
        "https://localhost:3000"   # HTTPS development
    ]    
    
    # Add additional allowed origins from environment variable
    additional_origins = os.environ.get('CORS_ORIGINS', '').split(',')
    cors_origins.extend([origin.strip() for origin in additional_origins if origin.strip()])
    
    CORS(app, origins=cors_origins, supports_credentials=True)

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
