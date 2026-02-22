"""
Database initialization and management utilities.
Handles automatic database and table creation on application startup.
"""

import os
import logging
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import OperationalError
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class DatabaseInitializer:
    """
    Handles database initialization, creation, and schema setup.
    """

    def __init__(self, db_uri, app_logger=None):
        """
        Initialize the database manager.
        
        Args:
            db_uri: Database connection URI
            app_logger: Optional Flask app logger
        """
        self.db_uri = db_uri
        self.logger = app_logger or logger

    def parse_database_url(self):
        """
        Parse database URL to extract connection details.
        
        Returns:
            dict: Parsed database details
        """
        parsed = urlparse(self.db_uri)
        return {
            'driver': parsed.scheme.split('+')[0],  # mysql, postgresql, sqlite, etc.
            'user': parsed.username,
            'password': parsed.password,
            'host': parsed.hostname,
            'port': parsed.port,
            'database': parsed.path.lstrip('/'),
            'dialect': parsed.scheme
        }

    def create_database_if_not_exists(self):
        """
        Create the database if it doesn't already exist.
        Currently supports MySQL and PostgreSQL.
        """
        parsed = self.parse_database_url()
        driver = parsed['driver'].lower()

        if driver == 'sqlite':
            # SQLite creates database automatically
            self.logger.info("Using SQLite - database will be created automatically")
            return True

        if driver in ['mysql', 'postgresql']:
            try:
                # Create connection to server without specifying database
                if driver == 'mysql':
                    engine_uri = f"mysql+pymysql://{parsed['user']}:{parsed['password']}@{parsed['host']}:{parsed['port'] or 3306}"
                elif driver == 'postgresql':
                    engine_uri = f"postgresql://{parsed['user']}:{parsed['password']}@{parsed['host']}:{parsed['port'] or 5432}/postgres"

                engine = create_engine(engine_uri)
                
                with engine.connect() as connection:
                    # Check if database exists
                    db_name = parsed['database']
                    
                    if driver == 'mysql':
                        result = connection.execute(
                            text(f"SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = '{db_name}'")
                        )
                        exists = result.fetchone() is not None
                        
                        if not exists:
                            self.logger.info(f"Creating MySQL database: {db_name}")
                            connection.execute(text(f"CREATE DATABASE {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
                            connection.commit()
                            self.logger.info(f"✓ Database '{db_name}' created successfully")
                        else:
                            self.logger.info(f"✓ Database '{db_name}' already exists")
                    
                    elif driver == 'postgresql':
                        result = connection.execute(
                            text(f"SELECT datname FROM pg_database WHERE datname = '{db_name}'")
                        )
                        exists = result.fetchone() is not None
                        
                        if not exists:
                            self.logger.info(f"Creating PostgreSQL database: {db_name}")
                            connection.execute(text(f"CREATE DATABASE {db_name}"))
                            connection.commit()
                            self.logger.info(f"✓ Database '{db_name}' created successfully")
                        else:
                            self.logger.info(f"✓ Database '{db_name}' already exists")
                
                engine.dispose()
                return True
                
            except OperationalError as e:
                self.logger.error(f"✗ Failed to create database: {str(e)}")
                return False
            except Exception as e:
                self.logger.error(f"✗ Unexpected error during database creation: {str(e)}")
                return False

        self.logger.warning(f"Database driver '{driver}' not supported for auto-creation")
        return False

    def verify_connection(self):
        """
        Verify database connection is working.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            engine = create_engine(self.db_uri, pool_pre_ping=True)
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            engine.dispose()
            self.logger.info("✓ Database connection verified")
            return True
        except Exception as e:
            self.logger.error(f"✗ Database connection failed: {str(e)}")
            return False

    def initialize_database(self, db, app=None):
        """
        Complete database initialization process:
        1. Create database if not exists
        2. Verify connection
        3. Create all tables from models
        
        Args:
            db: SQLAlchemy database instance
            app: Flask application instance (optional)
            
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            self.logger.info("Starting database initialization...")
            
            # Step 1: Create database if not exists
            self.logger.info("Step 1: Creating database if not exists...")
            if not self.create_database_if_not_exists():
                self.logger.warning("Database creation failed, attempting to continue...")
            
            # Step 2: Verify connection
            self.logger.info("Step 2: Verifying database connection...")
            if not self.verify_connection():
                self.logger.error("Database connection verification failed")
                return False
            
            # Step 3: Create all tables
            if app:
                self.logger.info("Step 3: Creating database tables from models...")
                with app.app_context():
                    db.create_all()
                    self.logger.info("✓ Database tables created/verified")
            
            self.logger.info("✓ Database initialization completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"✗ Database initialization failed: {str(e)}")
            return False


def init_database(app, db):
    """
    Initialize database on application startup.
    
    Args:
        app: Flask application instance
        db: SQLAlchemy database instance
        
    Returns:
        bool: True if initialization successful
    """
    db_uri = app.config.get('SQLALCHEMY_DATABASE_URI')
    
    if not db_uri:
        app.logger.error("SQLALCHEMY_DATABASE_URI not configured")
        if not app.testing:
            raise ValueError("Database URI not configured")
        return False
    
    # Skip for SQLite in-memory databases (testing)
    if 'sqlite:///:memory:' in db_uri:
        with app.app_context():
            db.create_all()
        return True
    
    initializer = DatabaseInitializer(db_uri, app.logger)
    return initializer.initialize_database(db, app)
