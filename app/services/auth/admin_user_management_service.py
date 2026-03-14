"""
Admin User Management Service
Handles admin-only operations for managing students and teachers
including listing, activating, and banning users
"""

import logging
from datetime import datetime

from flask import current_app

from app import db
from app.exceptions import ValidationError, AuthorizationError
from app.models import User, UserAccountStatus, UserRole, Role, StudentProfile, TeacherProfile
from app.services.health.base_service import BaseService
from datetime import datetime

logger = logging.getLogger(__name__)

class AdminUserManagementService(BaseService):
    """Service for admin user management operations"""
    