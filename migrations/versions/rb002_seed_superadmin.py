"""Seed Default Superadmin User

Revision ID: rb002_superadmin
Revises: rb001_roles
Create Date: 2026-02-27

This migration creates a default superadmin user for initial system setup.
Credentials:
    Email: stormprojects47@gmail.com
    Password: SuperAdmin@123
    Username: superadmin_admin

⚠️  IMPORTANT: Change password immediately after first login!
"""

import uuid
from datetime import datetime

import sqlalchemy as sa
from alembic import op
from sqlalchemy.sql import column, table
from werkzeug.security import generate_password_hash

# ---------------------------------------------------------------------------
# Alembic revision metadata
# ---------------------------------------------------------------------------
revision = "rb002_superadmin"
down_revision = "rb001_roles"
branch_labels = None
depends_on = None

# ---------------------------------------------------------------------------
# Helper function to hash password (mimicking app's PasswordManager)
# ---------------------------------------------------------------------------
def hash_password(password):
    """Hash password using werkzeug security."""
    return generate_password_hash(password, method="pbkdf2:sha256", salt_length=16)


def upgrade():
    """Upgrade: Insert superadmin user, account status, and assign superadmin role"""
    # Generate IDs for superadmin
    superadmin_id = str(uuid.uuid4())
    superadmin_create_time = datetime.utcnow()

    # Superadmin user data
    superadmin_user = {
        "user_id": superadmin_id,
        "username": "superadmin_admin",
        "email": "stormprojects47@gmail.com",
        "password_hash": hash_password("SuperAdmin@123"),
        "first_name": "Super",
        "last_name": "Admin",
        "phone": None,
        "profile_picture": None,
        "bio": "System Administrator with full access",
        "email_verified": True,
        "phone_verified": False,
        "created_at": superadmin_create_time,
        "updated_at": superadmin_create_time,
        "last_login": None,
        "deleted_at": None,
    }

    # Superadmin account status data
    superadmin_account_status = {
        "status_id": str(uuid.uuid4()),
        "user_id": superadmin_id,
        "is_active": True,
        "is_banned": False,
        "ban_reason": None,
        "banned_at": None,
        "ban_expires_at": None,
        "failed_login_attempts": 0,
        "last_failed_attempt_at": None,
        "last_notification_sent_at": None,
        "notification_channels": None,
        "updated_at": superadmin_create_time,
    }

    # Insert user
    users_table = table(
        "users",
        column("user_id", sa.String(36)),
        column("username", sa.String(100)),
        column("email", sa.String(255)),
        column("password_hash", sa.String(255)),
        column("first_name", sa.String(100)),
        column("last_name", sa.String(100)),
        column("phone", sa.String(20)),
        column("profile_picture", sa.Text),
        column("bio", sa.Text),
        column("email_verified", sa.Boolean),
        column("phone_verified", sa.Boolean),
        column("created_at", sa.DateTime),
        column("updated_at", sa.DateTime),
        column("last_login", sa.DateTime),
        column("deleted_at", sa.DateTime),
    )

    op.bulk_insert(users_table, [superadmin_user])

    # Insert account status
    account_status_table = table(
        "user_account_status",
        column("status_id", sa.String(36)),
        column("user_id", sa.String(36)),
        column("is_active", sa.Boolean),
        column("is_banned", sa.Boolean),
        column("ban_reason", sa.String(255)),
        column("banned_at", sa.DateTime),
        column("ban_expires_at", sa.DateTime),
        column("failed_login_attempts", sa.Integer),
        column("last_failed_attempt_at", sa.DateTime),
        column("last_notification_sent_at", sa.DateTime),
        column("notification_channels", sa.Text),
        column("updated_at", sa.DateTime),
    )

    op.bulk_insert(account_status_table, [superadmin_account_status])

    # Assign superadmin role to the user
    # First, fetch the superadmin role ID from the roles table
    superadmin_role_result = op.execute(
        "SELECT role_id FROM roles WHERE role_name = 'superadmin'"
    )
    superadmin_role_row = superadmin_role_result.fetchone()

    if superadmin_role_row is None:
        raise Exception(
            "Superadmin role does not exist. Please ensure rb001_roles migration has been run."
        )

    superadmin_role_id = superadmin_role_row[0]

    # Insert user role assignment
    user_roles_table = table(
        "user_roles",
        column("user_role_id", sa.String(36)),
        column("user_id", sa.String(36)),
        column("role_id", sa.String(36)),
        column("assigned_at", sa.DateTime),
        column("assigned_by", sa.String(36)),
    )

    op.bulk_insert(
        user_roles_table,
        [
            {
                "user_role_id": str(uuid.uuid4()),
                "user_id": superadmin_id,
                "role_id": superadmin_role_id,
                "assigned_at": superadmin_create_time,
                "assigned_by": None,
            }
        ],
    )


def downgrade():
    """Downgrade: Delete superadmin user and related data"""
    # Find superadmin user ID first
    superadmin_user_result = op.execute(
        "SELECT user_id FROM users WHERE email = 'stormprojects47@gmail.com'"
    )
    superadmin_user_row = superadmin_user_result.fetchone()

    if superadmin_user_row:
        superadmin_user_id = superadmin_user_row[0]

        # Delete user roles
        op.execute(f"DELETE FROM user_roles WHERE user_id = '{superadmin_user_id}'")

        # Delete account status
        op.execute(f"DELETE FROM user_account_status WHERE user_id = '{superadmin_user_id}'")

        # Delete user
        op.execute(f"DELETE FROM users WHERE user_id = '{superadmin_user_id}'")
