"""
Unit tests for models
"""

from app.models import (
    User,
    Role,
    Permission,
    Course,
    CourseEnrollment,
    Quiz,
    Question,
    Notification,
    Review,
)


class TestModelImports:
    """Test that models can be imported"""

    def test_user_model_import(self):
        """Test User model is importable"""
        assert User is not None

    def test_role_model_import(self):
        """Test Role model is importable"""
        assert Role is not None

    def test_course_model_import(self):
        """Test Course model is importable"""
        assert Course is not None

    def test_quiz_model_import(self):
        """Test Quiz model is importable"""
        assert Quiz is not None

    def test_question_model_import(self):
        """Test Question model is importable"""
        assert Question is not None

    def test_notification_model_import(self):
        """Test Notification model is importable"""
        assert Notification is not None

    def test_review_model_import(self):
        """Test Review model is importable"""
        assert Review is not None

    def test_permission_model_import(self):
        """Test Permission model is importable"""
        assert Permission is not None

    def test_course_enrollment_model_import(self):
        """Test CourseEnrollment model is importable"""
        assert CourseEnrollment is not None


class TestModelAttributes:
    """Test model attributes are accessible"""

    def test_user_has_username_attribute(self):
        """Test User model has username attribute"""
        assert hasattr(User, "username")

    def test_course_has_title_attribute(self):
        """Test Course model has title attribute"""
        assert hasattr(Course, "title")

    def test_quiz_has_title_attribute(self):
        """Test Quiz model has title attribute"""
        assert hasattr(Quiz, "title")

    def test_notification_has_title_attribute(self):
        """Test Notification model has title attribute"""
        assert hasattr(Notification, "title")

    def test_review_has_rating_attribute(self):
        """Test Review model has rating attribute"""
        assert hasattr(Review, "rating")
