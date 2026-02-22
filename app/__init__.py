"""
Flask LMS Backend Application
Initializes and configures the Flask application and extensions.
"""

import logging
import os
from logging.handlers import RotatingFileHandler

from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from app.utils.database import init_database

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()


def create_app(config_name="development"):
    """
    Application factory pattern for creating Flask app instances.

    Args:
        config_name: Configuration environment (development, testing, production)

    Returns:
        Flask application instance
    """
    app = Flask(__name__)

    # Load configuration
    if config_name == "production":
        from app.config import ProductionConfig

        app.config.from_object(ProductionConfig)
    elif config_name == "testing":
        from app.config import TestingConfig

        app.config.from_object(TestingConfig)
    else:
        from app.config import DevelopmentConfig

        app.config.from_object(DevelopmentConfig)

    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)

    # Enable CORS
    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": ["*"],
                "methods": ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization"],
            }
        },
    )

    # Register blueprints
    from app.routes import health_routes

    app.register_blueprint(health_routes.bp)

    # Import all models to register them with SQLAlchemy metadata
    # This ensures db.create_all() can properly handle all model relationships
    from app.models import (  # noqa: F401
        Achievement,
        AttemptAnswer,
        Certificate,
        CertificateSharingLog,
        CertificateTemplate,
        CertificateVerificationLog,
        Challenge,
        Coupon,
        Course,
        CourseActivityLog,
        CourseCategory,
        CourseEnrollment,
        CourseEnrollmentKey,
        CourseLesson,
        CourseReview,
        CourseSection,
        CourseStatusAudit,
        EmailVerificationToken,
        Invoice,
        LeaderboardSnapshot,
        LessonContent,
        LessonContentProgress,
        LoginFailure,
        LoginHistory,
        ManualGrade,
        Notification,
        NotificationBatch,
        NotificationDeliveryLog,
        NotificationPreferences,
        NotificationTemplate,
        NotificationTypePreferences,
        OTPRequest,
        PasswordResetToken,
        Permission,
        PointTransaction,
        Question,
        QuestionOption,
        Quiz,
        QuizAttempt,
        Refund,
        Review,
        ReviewFlag,
        ReviewResponse,
        ReviewVote,
        Role,
        RolePermission,
        Streak,
        Transaction,
        User,
        UserAccountStatus,
        UserAchievement,
        UserActivityLog,
        UserPoints,
        UserPreferences,
        UserProfile,
        UserRole,
        UserStatistics,
        UserSuspensionLog,
    )

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
        if not os.path.exists("logs"):
            os.mkdir("logs")

        file_handler = RotatingFileHandler(
            "logs/lms_backend.log", maxBytes=10240000, backupCount=10
        )
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]")
        )
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info("LMS Backend startup")
