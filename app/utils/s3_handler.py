"""
AWS S3 File Handler
Manages file uploads to AWS S3 storage for production environments
"""

import logging
import io
from flask import current_app
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class S3Handler:
    """Handle file uploads to AWS S3"""

    def __init__(self):
        """Initialize S3 client"""
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=current_app.config.get("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=current_app.config.get("AWS_SECRET_ACCESS_KEY"),
            region_name=current_app.config.get("AWS_S3_REGION", "us-east-1"),
        )
        self.bucket_name = current_app.config.get("AWS_S3_BUCKET")

    @staticmethod
    def is_configured():
        """Check if S3 is properly configured"""
        return (
            current_app.config.get("AWS_ACCESS_KEY_ID")
            and current_app.config.get("AWS_SECRET_ACCESS_KEY")
            and current_app.config.get("AWS_S3_BUCKET")
        )

    def upload_profile_picture(self, file_obj, username, role="student"):
        """
        Upload profile picture to S3.

        S3 key structure: profiles/{role}/{username}/{filename}

        Args:
            file_obj: Flask FileStorage object
            username (str): Username for organization
            role (str): User role (student, teacher, admin, superadmin)

        Returns:
            str: S3 object URL

        Raises:
            Exception: If upload fails
        """
        try:
            # Get file extension
            filename = file_obj.filename
            extension = filename.rsplit(".", 1)[1].lower() if "." in filename else "jpg"

            # Generate S3 key (path)
            s3_key = f"profiles/{role}/{username}/{username}.{extension}"

            # Read file content
            file_content = file_obj.read()
            file_obj.seek(0)  # Reset file pointer for any future reads

            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=io.BytesIO(file_content),
                ContentType=file_obj.content_type or "image/jpeg",
                # Make the file publicly readable
                ACL="public-read",
            )

            # Generate S3 URL
            s3_url = f"https://{self.bucket_name}.s3.{current_app.config.get('AWS_S3_REGION', 'us-east-1')}.amazonaws.com/{s3_key}"

            logger.info(f"Profile picture uploaded to S3: {s3_key}")
            return s3_url

        except ClientError as e:
            logger.error(f"S3 upload error: {str(e)}")
            raise Exception(f"Failed to upload to S3: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during S3 upload: {str(e)}")
            raise

    def upload_course_material(self, file_obj, course_id, filename=None):
        """
        Upload course material to S3.

        S3 key structure: courses/{course_id}/{filename}

        Args:
            file_obj: Flask FileStorage object
            course_id (str): Course ID
            filename (str): Optional custom filename

        Returns:
            str: S3 object URL
        """
        try:
            # Use provided filename or original
            if filename:
                file_name = filename
            else:
                file_name = file_obj.filename

            # Generate S3 key
            s3_key = f"courses/{course_id}/{file_name}"

            # Read and upload file
            file_content = file_obj.read()
            file_obj.seek(0)

            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=io.BytesIO(file_content),
                ContentType=file_obj.content_type or "application/octet-stream",
                ACL="public-read",
            )

            # Generate S3 URL
            s3_url = f"https://{self.bucket_name}.s3.{current_app.config.get('AWS_S3_REGION', 'us-east-1')}.amazonaws.com/{s3_key}"

            logger.info(f"Course material uploaded to S3: {s3_key}")
            return s3_url

        except ClientError as e:
            logger.error(f"S3 upload error: {str(e)}")
            raise Exception(f"Failed to upload to S3: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during S3 upload: {str(e)}")
            raise

    def delete_file(self, s3_key):
        """
        Delete a file from S3.

        Args:
            s3_key (str): S3 object key (path)

        Returns:
            bool: True if deleted, False otherwise
        """
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            logger.info(f"File deleted from S3: {s3_key}")
            return True

        except ClientError as e:
            logger.error(f"S3 delete error: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during S3 delete: {str(e)}")
            return False

    def get_file_url(self, s3_key):
        """
        Generate URL for an S3 object.

        Args:
            s3_key (str): S3 object key (path)

        Returns:
            str: S3 object URL
        """
        if not s3_key:
            return None

        # If it's already a full URL, return as is
        if s3_key.startswith(("http://", "https://")):
            return s3_key

        # Generate S3 URL
        return f"https://{self.bucket_name}.s3.{current_app.config.get('AWS_S3_REGION', 'us-east-1')}.amazonaws.com/{s3_key}"
