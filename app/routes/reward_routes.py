"""
Reward Routes
All reward management endpoints:
"""

import logging
from flask import Blueprint, request

from app.exceptions import ValidationError
from app.middleware.auth_middleware import require_auth, require_role
from app.services.auth import AdminUserManagementService
from app.utils.decorators import handle_exceptions, validate_json
from app.utils.response import error_response, success_response

bp = Blueprint("rewards", __name__, url_prefix="/api/v1/rewards")
logger = logging.getLogger(__name__)