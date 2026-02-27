"""
File Handler Utility
Manages file uploads with organized directory structure and consistent naming
"""

import os
import logging
from pathlib import Path
from werkzeug.utils import secure_filename
from flask import current_app

logger = logging.getLogger(__name__)


class FileHandler:
    """
    Handles file uploads with organized directory structure.
    
    Directory Structure:
    uploads/
    ├── profiles/
    │   ├── superadmin/
    │   │   └── {username}/
    │   │       ├── {username}_1.jpg
    │   │       └── {username}_2.jpg
    │   ├── admin/
    │   │   └── {username}/...
    │   ├── teacher/
    │   │   └── {username}/...
    │   └── student/
    │       └── {username}/...
    └── courses/
    # ... other categories
    """

    UPLOAD_BASE_DIR = "uploads"
    ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

    @staticmethod
    def get_upload_directory(category="profiles", role="student", username=""):
        """
        Get the full upload directory path for a category.

        Args:
            category (str): Main category (profiles, courses, etc.)
            role (str): User role (superadmin, admin, teacher, student)
            username (str): Username for organization (optional)

        Returns:
            str: Full path to the upload directory
        """
        if username:
            upload_dir = os.path.join(
                current_app.config.get("UPLOAD_FOLDER", "uploads"),
                category,
                role,
                username,
            )
        else:
            upload_dir = os.path.join(
                current_app.config.get("UPLOAD_FOLDER", "uploads"),
                category,
                role,
            )

        # Create directory if it doesn't exist
        Path(upload_dir).mkdir(parents=True, exist_ok=True)
        return upload_dir

    @staticmethod
    def get_file_extension(filename):
        """
        Extract file extension from filename.

        Args:
            filename (str): Original filename

        Returns:
            str: File extension (without dot) in lowercase
        """
        return filename.rsplit(".", 1)[1].lower() if "." in filename else ""

    @staticmethod
    def validate_image_file(file_obj):
        """
        Validate if uploaded file is an allowed image.

        Args:
            file_obj: Flask FileStorage object

        Returns:
            tuple: (is_valid, error_message)

        Raises:
            ValidationError: If validation fails
        """
        if not file_obj:
            return False, "No file provided"

        if file_obj.filename == "":
            return False, "No file selected"

        extension = FileHandler.get_file_extension(file_obj.filename)

        if extension not in FileHandler.ALLOWED_IMAGE_EXTENSIONS:
            allowed = ", ".join(FileHandler.ALLOWED_IMAGE_EXTENSIONS)
            return False, f"Invalid file type. Allowed: {allowed}"

        # Check file size (5MB for images)
        file_obj.seek(0, os.SEEK_END)
        file_size = file_obj.tell()
        file_obj.seek(0)

        max_size = 5 * 1024 * 1024  # 5MB
        if file_size > max_size:
            return False, f"File size exceeds 5MB limit (size: {file_size / 1024 / 1024:.2f}MB)"

        return True, None

    @staticmethod
    def get_next_filename(directory, base_name, extension):
        """
        Generate next filename with counter (e.g., username_1.jpg, username_2.jpg).

        Args:
            directory (str): Directory path
            base_name (str): Base filename without extension
            extension (str): File extension (without dot)

        Returns:
            str: Filename with counter
        """
        counter = 1
        filename = f"{base_name}_{counter}.{extension}"

        # Find the next available counter
        while os.path.exists(os.path.join(directory, filename)):
            counter += 1
            filename = f"{base_name}_{counter}.{extension}"

        return filename

    @staticmethod
    def save_profile_picture(file_obj, username, role="student"):
        """
        Save profile picture with organized naming and directory structure.

        Directory: uploads/profiles/{role}/{username}/
        Filename: {username}_{counter}.{ext}

        Args:
            file_obj: Flask FileStorage object from request.files
            username (str): Username for organization
            role (str): User role (student, teacher, admin, superadmin)

        Returns:
            str: Relative path to saved file (for database storage)

        Raises:
            ValidationError: If file is invalid
        """
        from app.exceptions import ValidationError

        # Validate file
        is_valid, error_msg = FileHandler.validate_image_file(file_obj)
        if not is_valid:
            raise ValidationError(error_msg)

        try:
            # Get upload directory
            upload_dir = FileHandler.get_upload_directory(
                category="profiles", role=role, username=username
            )

            # Secure filename and get extension
            original_filename = secure_filename(file_obj.filename)
            extension = FileHandler.get_file_extension(original_filename)

            # Generate unique filename with counter
            filename = FileHandler.get_next_filename(upload_dir, username, extension)

            # Full file path
            file_path = os.path.join(upload_dir, filename)

            # Save file
            file_obj.save(file_path)

            logger.info(f"Profile picture saved: {filename} for user {username}")

            # Return relative path for database storage
            # Format: profiles/{role}/{username}/{username}_{counter}.{ext}
            relative_path = os.path.relpath(
                file_path, current_app.config.get("UPLOAD_FOLDER", "uploads")
            )

            return relative_path

        except Exception as e:
            logger.error(f"Error saving profile picture: {str(e)}")
            raise ValidationError(f"Failed to save profile picture: {str(e)}")

    @staticmethod
    def save_course_material(file_obj, course_id, filename=None):
        """
        Save course material file.

        Args:
            file_obj: Flask FileStorage object
            course_id (str): Course ID
            filename (str): Optional custom filename

        Returns:
            str: Relative path to saved file
        """
        try:
            upload_dir = FileHandler.get_upload_directory(category="courses", role="materials")
            Path(upload_dir).mkdir(parents=True, exist_ok=True)

            # Use provided filename or secure the original
            if filename:
                filename = secure_filename(filename)
            else:
                filename = secure_filename(file_obj.filename)

            file_path = os.path.join(upload_dir, course_id, filename)
            Path(os.path.dirname(file_path)).mkdir(parents=True, exist_ok=True)

            file_obj.save(file_path)

            relative_path = os.path.relpath(
                file_path, current_app.config.get("UPLOAD_FOLDER", "uploads")
            )

            logger.info(f"Course material saved: {relative_path}")
            return relative_path

        except Exception as e:
            logger.error(f"Error saving course material: {str(e)}")
            raise

    @staticmethod
    def get_file_url(relative_path):
        """
        Convert relative file path to URL.

        Args:
            relative_path (str): Relative path from uploads folder

        Returns:
            str: Full URL to the file
        """
        if not relative_path:
            return None

        # If it's already a full URL, return as is
        if relative_path.startswith(("http://", "https://")):
            return relative_path

        # Convert file path to URL format
        file_url = f"/uploads/{relative_path.replace(os.sep, '/')}"
        return file_url

    @staticmethod
    def delete_file(relative_path):
        """
        Delete a file from uploads.

        Args:
            relative_path (str): Relative path from uploads folder

        Returns:
            bool: True if deleted, False otherwise
        """
        try:
            file_path = os.path.join(
                current_app.config.get("UPLOAD_FOLDER", "uploads"), relative_path
            )

            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"File deleted: {relative_path}")
                return True

            logger.warning(f"File not found for deletion: {relative_path}")
            return False

        except Exception as e:
            logger.error(f"Error deleting file: {str(e)}")
            return False
