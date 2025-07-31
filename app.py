from flask import Flask

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

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(debug=Config.DEBUG)
