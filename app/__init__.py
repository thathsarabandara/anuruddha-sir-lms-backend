"""
Flask LMS Backend Application
Initializes and configures the Flask application and extensions.
"""

from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging.handlers import RotatingFileHandler
import os
from app.utils.database import init_database

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()

def create_app(config_name='development'):
    """
    Application factory pattern for creating Flask app instances.
    
    Args:
        config_name: Configuration environment (development, testing, production)
    
    Returns:
        Flask application instance
    """
    app = Flask(__name__)
    
    # Load configuration
    if config_name == 'production':
        from app.config import ProductionConfig
        app.config.from_object(ProductionConfig)
    elif config_name == 'testing':
        from app.config import TestingConfig
        app.config.from_object(TestingConfig)
    else:
        from app.config import DevelopmentConfig
        app.config.from_object(DevelopmentConfig)
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Enable CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": ["*"],
            "methods": ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # Register blueprints
    from app.routes import health_routes
    app.register_blueprint(health_routes.bp)
    
    from app.models import user, course  # Import models to register with SQLAlchemy

    # Setup logging
    setup_logging(app)
    
    # Initialize database with auto-creation
    app.logger.info("Initializing database...")
    if not init_database(app, db):
        app.logger.warning("Database initialization completed with warnings. Check logs above.")
    
    # Register error handlers
    from app.middleware.error_handlers import register_error_handlers
    register_error_handlers(app)
    
    return app

def setup_logging(app):
    """Configure logging for the application."""
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        file_handler = RotatingFileHandler('logs/lms_backend.log', 
                                         maxBytes=10240000, 
                                         backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('LMS Backend startup')
