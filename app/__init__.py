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
    allowed_origins = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]
    
    # Add production origins if in production
    if app.config.get("ENV") == "production":
        allowed_origins.extend(
            [
                "https://yourdomain.com",
                "https://www.yourdomain.com",
                "https://api.yourdomain.com",
            ]
        )
    
    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": allowed_origins,
                "methods": ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"],
                "expose_headers": ["Content-Range", "X-Content-Range"],
                "supports_credentials": True,
                "max_age": 3600,
            }
        },
        supports_credentials=True,
    )

    # Register blueprints
    from app.routes import admin_routes, auth_routes, course_routes, health_routes, notification_routes
    from app.routes import quiz_routes

    app.register_blueprint(health_routes.bp)
    app.register_blueprint(auth_routes.bp)
    app.register_blueprint(admin_routes.bp)
    app.register_blueprint(notification_routes.bp)
    app.register_blueprint(course_routes.bp)
    app.register_blueprint(quiz_routes.bp)

    @app.route('/uploads/<path:filename>')
    def serve_uploaded_file(filename):
        """Serve uploaded files from the uploads directory"""
        from flask import send_from_directory
        upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads')
        return send_from_directory(upload_folder, filename)

    # Ensure uploads directory exists
    os.makedirs(app.config.get('UPLOAD_FOLDER', 'uploads'), exist_ok=True)
    app.logger.info(f"Uploads folder configured at: {app.config.get('UPLOAD_FOLDER', 'uploads')}")

    # Import all models to register them with SQLAlchemy metadata
    # This ensures db.create_all() can properly handle all model relationships
    from app.models import (  # noqa: F401
        User,
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
        UserAccountStatus,
        UserAchievement,
        UserActivityLog,
        UserPoints,
        UserPreferences,
        UserRole,
        UserStatistics,
        StudentProfile,
        TeacherProfile,
        AccessToken,
        RefreshToken,
    )

    # Setup logging
    setup_logging(app)

    # Initialize database with auto-creation (skip in testing/CI or when the
    # Docker entrypoint has already handled init before gunicorn workers fork).
    skip_init = os.environ.get("SKIP_AUTO_INIT", "false").lower() == "true"

    if not app.testing and not skip_init:
        app.logger.info("Initializing database...")
        db_ready = init_database(app, db)
        if not db_ready:
            app.logger.warning(
                "Database initialization completed with warnings. Check logs above."
            )

        # Auto-seed empty tables with initial data (only when DB is ready)
        if db_ready:
            from app.commands import auto_seed
            auto_seed(app)
        else:
            app.logger.warning(
                "Skipping auto-seed: database tables may not be ready yet."
            )
    elif skip_init:
        app.logger.info(
            "Skipping DB init/seed (SKIP_AUTO_INIT=true) – "
            "already handled by entrypoint before workers started."
        )

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
