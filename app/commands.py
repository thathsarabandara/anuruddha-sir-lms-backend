"""
Database management CLI commands.
Provides commands to initialize, reset, and manage the database.
"""

import uuid
import logging
import click
from flask import current_app
from getpass import getpass
from datetime import datetime

from app import db
from app.utils.database import DatabaseInitializer, init_database
from app.models.auth import User, UserAccountStatus
from app.models.auth.role import Role
from app.models.auth.user_role import UserRole
from app.utils.auth import PasswordManager
from app.utils.validators import validate_email

logger = logging.getLogger(__name__)


@click.group()
def db_cli():
    """Database management commands."""
    pass


@db_cli.command()
def init():
    """Initialize database - create database and tables."""
    click.echo("🔄 Initializing database...")

    db_uri = current_app.config.get("SQLALCHEMY_DATABASE_URI")
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

    db_uri = current_app.config.get("SQLALCHEMY_DATABASE_URI")
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

    db_uri = current_app.config.get("SQLALCHEMY_DATABASE_URI")
    if not db_uri:
        click.echo("❌ Database URI not configured")
        return

    initializer = DatabaseInitializer(db_uri, current_app.logger)
    if initializer.verify_connection():
        click.echo("✓ Database connection verified")
    else:
        click.echo("❌ Database connection failed")


@db_cli.command()
@click.confirmation_option(
    prompt="Are you sure you want to drop all tables? This cannot be undone."
)
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
@click.option("--sample", is_flag=True, help="Create with sample data")
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

    db_uri = current_app.config.get("SQLALCHEMY_DATABASE_URI")

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


# ===================== Superadmin Management Commands =====================


@click.group()
def admin_cli():
    """Superadmin user management commands."""
    pass


@admin_cli.command("create")
@click.option(
    "-e",
    "--email",
    prompt="Superadmin email",
    default="superadmin@lms.com",
    help="Email address for superadmin user",
)
@click.option(
    "-phone",
    "--phone",
    prompt="Superadmin phone number",
    default=None,
    help="Phone number for superadmin user",
)
@click.option(
    "-u",
    "--username",
    prompt="Superadmin username",
    default="superadmin_admin",
    help="Username for superadmin",
)
@click.option(
    "-f",
    "--first-name",
    prompt="First name",
    default="Super",
    help="First name of superadmin",
)
@click.option(
    "-l",
    "--last-name",
    prompt="Last name",
    default="Admin",
    help="Last name of superadmin",
)
@click.option(
    "-p",
    "--password",
    is_flag=False,
    flag_value=None,
    help="Password (will prompt if not provided)",
)
@click.option(
    "-q",
    "--quiet",
    is_flag=True,
    help="Suppress prompts and use defaults",
)
def create_superadmin(email, username, first_name, last_name, phone, password, quiet):
    """Create a new superadmin user (requires superadmin role to exist)."""
    try:
        # Validate email
        validate_email(email)

        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            click.echo(f"Error: User with email '{email}' already exists", err=True)
            return

        existing_username = User.query.filter_by(username=username).first()
        if existing_username:
            click.echo(f"Error: Username '{username}' already exists", err=True)
            return

        # Get or prompt password
        if not password:
            if not quiet:
                password = getpass("Enter password: ")
                password_confirm = getpass("Confirm password: ")
                if password != password_confirm:
                    click.echo("Error: Passwords do not match", err=True)
                    return
            else:
                click.echo("Error: Password required. Use -p option or remove -q flag", err=True)
                return

        # Validate password strength
        try:
            PasswordManager.validate_password_strength(password)
        except Exception as e:
            click.echo(f"Error: {str(e)}", err=True)
            return

        # Get superadmin role
        superadmin_role = Role.query.filter_by(role_name="superadmin").first()
        if not superadmin_role:
            click.echo(
                "Error: Superadmin role does not exist. Run migrations first.",
                err=True,
            )
            return

        # Create user
        user_id = str(uuid.uuid4())
        user = User(
            user_id=user_id,
            username=username,
            email=email,
            password_hash=PasswordManager.hash_password(password),
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            email_verified=True,
        )

        # Create account status (approved)
        account_status = UserAccountStatus(
            user_id=user_id,
            is_active=True,
            is_banned=False,
        )

        # Assign superadmin role
        user_role = UserRole(user_id=user_id, role_id=superadmin_role.role_id)

        # Save to database
        db.session.add(user)
        db.session.add(account_status)
        db.session.add(user_role)
        db.session.commit()

        click.echo(
            click.style("✓ Superadmin user created successfully!", fg="green", bold=True)
        )
        click.echo(f"  Email: {email}")
        click.echo(f"  Username: {username}")
        click.echo(f"  Full Name: {first_name} {last_name}")
        click.echo(
            click.style(
                "\n⚠️ Important: Change password immediately after first login!",
                fg="yellow",
            )
        )

    except Exception as e:
        click.echo(f"Error creating superadmin: {str(e)}", err=True)
        logger.error(f"Error creating superadmin: {str(e)}", exc_info=True)


@admin_cli.command("reset-password")
@click.option(
    "-e",
    "--email",
    prompt="Superadmin email",
    help="Email of superadmin account",
)
@click.option(
    "-p",
    "--password",
    is_flag=False,
    flag_value=None,
    help="New password (will prompt if not provided)",
)
def reset_superadmin_password(email, password):
    """Reset superadmin password."""
    try:
        # Find user
        user = User.query.filter_by(email=email).first()
        if not user:
            click.echo(f"Error: User with email '{email}' not found", err=True)
            return

        # Check if user is superadmin
        user_superadmin_role = (
            UserRole.query.join(Role)
            .filter(UserRole.user_id == user.user_id, Role.role_name == "superadmin")
            .first()
        )

        if not user_superadmin_role:
            click.echo(
                f"Error: User '{email}' is not a superadmin",
                err=True,
            )
            return

        # Get new password
        if not password:
            password = getpass("Enter new password: ")
            password_confirm = getpass("Confirm password: ")
            if password != password_confirm:
                click.echo("Error: Passwords do not match", err=True)
                return

        # Validate password strength
        try:
            PasswordManager.validate_password_strength(password)
        except Exception as e:
            click.echo(f"Error: {str(e)}", err=True)
            return

        # Update password
        user.password_hash = PasswordManager.hash_password(password)
        user.updated_at = datetime.utcnow()
        db.session.commit()

        click.echo(
            click.style(
                f"✓ Password reset successfully for {email}!",
                fg="green",
                bold=True,
            )
        )

    except Exception as e:
        click.echo(f"Error resetting password: {str(e)}", err=True)
        logger.error(f"Error resetting password: {str(e)}", exc_info=True)


@admin_cli.command("list")
def list_superadmins():
    """List all superadmin users."""
    try:
        superadmins = (
            User.query.join(UserRole)
            .join(Role)
            .filter(Role.role_name == "superadmin")
            .all()
        )

        if not superadmins:
            click.echo("No superadmin users found.")
            return

        click.echo(click.style("=== Superadmin Users ===", fg="blue", bold=True))
        click.echo()

        for user in superadmins:
            click.echo(f"Username: {user.username}")
            click.echo(f"Email:    {user.email}")
            click.echo(f"Name:     {user.first_name} {user.last_name}")
            click.echo(f"Active:   {user.is_active}")
            click.echo(f"Created:  {user.created_at}")
            click.echo(f"Last Login: {user.last_login or 'Never'}")
            click.echo("-" * 40)

    except Exception as e:
        click.echo(f"Error listing superadmins: {str(e)}", err=True)
        logger.error(f"Error listing superadmins: {str(e)}", exc_info=True)


@admin_cli.command("delete")
@click.option(
    "-e",
    "--email",
    prompt="Superadmin email to delete",
    help="Email of superadmin to delete",
)
@click.option(
    "-y",
    "--yes",
    is_flag=True,
    help="Skip confirmation prompt",
)
def delete_superadmin(email, yes):
    """Delete a superadmin user (with confirmation)."""
    try:
        user = User.query.filter_by(email=email).first()
        if not user:
            click.echo(f"Error: User with email '{email}' not found", err=True)
            return

        # Check if user is superadmin
        user_superadmin_role = (
            UserRole.query.join(Role)
            .filter(UserRole.user_id == user.user_id, Role.role_name == "superadmin")
            .first()
        )

        if not user_superadmin_role:
            click.echo(
                f"Error: User '{email}' is not a superadmin",
                err=True,
            )
            return

        # Confirm deletion
        if not yes:
            click.echo(f"About to delete superadmin: {user.email}")
            click.echo(f"Name: {user.first_name} {user.last_name}")
            if not click.confirm("Are you sure?"):
                click.echo("Cancelled.")
                return

        # Delete user (cascade will handle related records)
        db.session.delete(user)
        db.session.commit()

        click.echo(
            click.style(
                f"✓ Superadmin '{email}' deleted successfully!",
                fg="green",
                bold=True,
            )
        )

    except Exception as e:
        click.echo(f"Error deleting superadmin: {str(e)}", err=True)
        logger.error(f"Error deleting superadmin: {str(e)}", exc_info=True)


def register_db_commands(app):
    """Register database CLI commands with Flask app."""
    app.cli.add_command(db_cli)
    app.cli.add_command(admin_cli, name="admin")
