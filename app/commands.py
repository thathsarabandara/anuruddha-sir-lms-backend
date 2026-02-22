"""
Database management CLI commands.
Provides commands to initialize, reset, and manage the database.
"""

import click
from flask import current_app
from app import db
from app.utils.database import DatabaseInitializer, init_database


@click.group()
def db_cli():
    """Database management commands."""
    pass


@db_cli.command()
def init():
    """Initialize database - create database and tables."""
    click.echo("🔄 Initializing database...")
    
    db_uri = current_app.config.get('SQLALCHEMY_DATABASE_URI')
    if not db_uri:
        click.echo("❌ Database URI not configured")
        return
    
    if init_database(current_app, db):
        click.echo("✓ Database initialization completed successfully")
    else:
        click.echo("❌ Database initialization failed")


@db_cli.command()
def create():
    """Create database only (without tables)."""
    click.echo("🔄 Creating database...")
    
    db_uri = current_app.config.get('SQLALCHEMY_DATABASE_URI')
    if not db_uri:
        click.echo("❌ Database URI not configured")
        return
    
    initializer = DatabaseInitializer(db_uri, current_app.logger)
    if initializer.create_database_if_not_exists():
        click.echo("✓ Database created successfully")
    else:
        click.echo("❌ Failed to create database")


@db_cli.command()
def migrate_create():
    """Create all tables from models."""
    click.echo("🔄 Creating database tables...")
    
    with current_app.app_context():
        try:
            db.create_all()
            click.echo("✓ Database tables created successfully")
        except Exception as e:
            click.echo(f"❌ Failed to create tables: {str(e)}")


@db_cli.command()
def verify():
    """Verify database connection."""
    click.echo("🔄 Verifying database connection...")
    
    db_uri = current_app.config.get('SQLALCHEMY_DATABASE_URI')
    if not db_uri:
        click.echo("❌ Database URI not configured")
        return
    
    initializer = DatabaseInitializer(db_uri, current_app.logger)
    if initializer.verify_connection():
        click.echo("✓ Database connection verified")
    else:
        click.echo("❌ Database connection failed")


@db_cli.command()
@click.confirmation_option(prompt='Are you sure you want to drop all tables? This cannot be undone.')
def drop():
    """Drop all tables from the database."""
    click.echo("🔄 Dropping all tables...")
    
    with current_app.app_context():
        try:
            db.drop_all()
            click.echo("✓ All tables dropped successfully")
        except Exception as e:
            click.echo(f"❌ Failed to drop tables: {str(e)}")


@db_cli.command()
@click.option('--sample', is_flag=True, help='Create with sample data')
def reset(sample):
    """Reset database - drop and recreate all tables."""
    click.echo("🔄 Resetting database...")
    
    with current_app.app_context():
        try:
            click.echo("  Dropping all tables...")
            db.drop_all()
            
            click.echo("  Creating new tables...")
            db.create_all()
            
            if sample:
                click.echo("  (Sample data seeding not yet implemented)")
            
            click.echo("✓ Database reset successfully")
        except Exception as e:
            click.echo(f"❌ Failed to reset database: {str(e)}")


@db_cli.command()
def status():
    """Show database status and connection information."""
    click.echo("\n📊 Database Status\n" + "=" * 50)
    
    db_uri = current_app.config.get('SQLALCHEMY_DATABASE_URI')
    
    try:
        initializer = DatabaseInitializer(db_uri, current_app.logger)
        parsed = initializer.parse_database_url()
        
        click.echo(f"Driver:    {parsed['driver']}")
        click.echo(f"Host:      {parsed['host']}")
        click.echo(f"Port:      {parsed['port']}")
        click.echo(f"Database:  {parsed['database']}")
        click.echo(f"User:      {parsed['user']}")
        
        click.echo("\nConnection Status:")
        if initializer.verify_connection():
            click.echo("✓ Connected")
        else:
            click.echo("✗ Unable to connect")
    
    except Exception as e:
        click.echo(f"Error parsing database URI: {str(e)}")
    
    click.echo("=" * 50 + "\n")


def register_db_commands(app):
    """Register database CLI commands with Flask app."""
    app.cli.add_command(db_cli)
