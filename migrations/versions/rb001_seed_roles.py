"""Seed Initial Roles

Revision ID: rb001_roles
Revises:
Create Date: 2026-02-27

This migration seeds the initial system roles:
- superadmin: Full system access, can manage everything
- admin: Administrative access, manages users and content
- teacher: Can create and manage courses, assignments, quizzes
- student: Can enroll in courses, take quizzes, submit assignments
"""

import uuid
from datetime import datetime

import sqlalchemy as sa
from alembic import op
from sqlalchemy.sql import column, table

# ---------------------------------------------------------------------------
# Alembic revision metadata
# ---------------------------------------------------------------------------
revision = "rb001_roles"
down_revision = None
branch_labels = ("roles",)
depends_on = None

# ---------------------------------------------------------------------------
# Role definitions
# ---------------------------------------------------------------------------
ROLES = [
    {
        "role_id": str(uuid.uuid4()),
        "role_name": "superadmin",
        "description": "Full system access - can manage all aspects of the platform",
        "created_at": datetime.utcnow(),
    },
    {
        "role_id": str(uuid.uuid4()),
        "role_name": "admin",
        "description": "Administrative access - manages users, courses, and platform settings",
        "created_at": datetime.utcnow(),
    },
    {
        "role_id": str(uuid.uuid4()),
        "role_name": "teacher",
        "description": "Can create and manage courses, assignments, quizzes, and student progress",
        "created_at": datetime.utcnow(),
    },
    {
        "role_id": str(uuid.uuid4()),
        "role_name": "student",
        "description": "Can enroll in courses, take quizzes, submit assignments, and view progress",
        "created_at": datetime.utcnow(),
    },
]


def upgrade():
    """Upgrade: Insert roles"""
    roles_table = table(
        "roles",
        column("role_id", sa.String(36)),
        column("role_name", sa.String(50)),
        column("description", sa.Text),
        column("created_at", sa.DateTime),
    )

    op.bulk_insert(roles_table, ROLES)


def downgrade():
    """Downgrade: Delete roles"""
    op.execute(
        "DELETE FROM roles WHERE role_name IN ('superadmin', 'admin', 'teacher', 'student')"
    )
