"""Seed Default Superadmin User

Revision ID: rb002_superadmin
Revises: rb001_roles
Create Date: 2026-02-27

This migration creates a default superadmin user for initial system setup.
Credentials:
    Email: superadmin@lms.com
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


# ---------------------------------------------------------------------------
# Superadmin user data
# ---------------------------------------------------------------------------
SUPERADMIN_ID = str(uuid.uuid4())
SUPERADMIN_CREATE_TIME = datetime.utcnow()

SUPERADMIN_USER = {
    "user_id": SUPERADMIN_ID,
    "username": "superadmin_admin",
    "email": "stormprojects47@gmail.com",
    "password_hash": hash_password("SuperAdmin@123"),
    "first_name": "Super",
    "last_name": "Admin",
    "phone": None,
    "profile_picture_url": None,
    "bio": "System Administrator with full access",
    "email_verified": True,
    "phone_verified": False,
    "is_active": True,
    "created_at": SUPERADMIN_CREATE_TIME,
    "updated_at": SUPERADMIN_CREATE_TIME,
    "last_login": None,
    "deleted_at": None,
}

SUPERADMIN_ACCOUNT_STATUS = {
    "user_id": SUPERADMIN_ID,
    "is_active": True,
    "is_banned": False,
    "approval_status": "approved",
    "created_at": SUPERADMIN_CREATE_TIME,
    "updated_at": SUPERADMIN_CREATE_TIME,
}


def upgrade():
    """Upgrade: Insert superadmin user and assign superadmin role"""
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
        column("profile_picture_url", sa.Text),
        column("bio", sa.Text),
        column("email_verified", sa.Boolean),
        column("phone_verified", sa.Boolean),
        column("is_active", sa.Boolean),
        column("created_at", sa.DateTime),
        column("updated_at", sa.DateTime),
        column("last_login", sa.DateTime),
        column("deleted_at", sa.DateTime),
    )

    op.bulk_insert(users_table, [SUPERADMIN_USER])

    # Insert account status
    account_status_table = table(
        "user_account_status",
        column("user_id", sa.String(36)),
        column("is_active", sa.Boolean),
        column("is_banned", sa.Boolean),
        column("approval_status", sa.String(50)),
        column("created_at", sa.DateTime),
        column("updated_at", sa.DateTime),
    )

    op.bulk_insert(account_status_table, [SUPERADMIN_ACCOUNT_STATUS])

    # Assign superadmin role to the user
    # First, get the superadmin role_id
    op.execute(
        f"""
        INSERT INTO user_roles (user_role_id, user_id, role_id, assigned_at, assigned_by)
        SELECT '{str(uuid.uuid4())}', '{SUPERADMIN_ID}', role_id, '{SUPERADMIN_CREATE_TIME}', NULL
        FROM roles WHERE role_name = 'superadmin'
        """
    )


def downgrade():
    """Downgrade: Delete superadmin user and related data"""
    # Delete user roles
    op.execute(f"DELETE FROM user_roles WHERE user_id = '{SUPERADMIN_ID}'")

    # Delete account status
    op.execute(f"DELETE FROM user_account_status WHERE user_id = '{SUPERADMIN_ID}'")

    # Delete user
    op.execute(f"DELETE FROM users WHERE user_id = '{SUPERADMIN_ID}'")
