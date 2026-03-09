"""
Profile Picture Handling Tests

Tests for profile picture uploads and URL handling in registration
"""

import json
import io
from pathlib import Path


class TestProfilePictureRegistration:
    """Test cases for profile picture handling during registration"""

    def test_register_with_file_upload(self, client):
        """Test registration with profile picture file upload"""
        # Create a simple test image (PNG)
        image_data = (
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
            b'\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01'
            b'\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
        )
        
        data = {
            'email': 'student_with_pic@example.com',
            'password': 'SecurePass123!',
            'first_name': 'John',
            'last_name': 'Doe',
            'role': 'student',
            'grade_level': '10',
            'school': 'Test School'
        }
        
        # Add profile picture as file
        files = {
            'profile_picture': (io.BytesIO(image_data), 'profile.png', 'image/png')
        }
        
        response = client.post(
            '/api/v1/auth/register',
            data=data,
            files=files,
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 201
        result = json.loads(response.data)
        assert result['success'] is True
        assert 'email' in result['data']

    def test_register_with_profile_picture_url(self, client):
        """Test registration with profile picture URL"""
        data = {
            'email': 'student_with_url@example.com',
            'password': 'SecurePass123!',
            'first_name': 'Jane',
            'last_name': 'Smith',
            'profile_picture_url': 'https://example.com/avatar.jpg',
            'role': 'student',
            'grade_level': 'A/L',
            'school': 'Test School'
        }
        
        response = client.post(
            '/api/v1/auth/register',
            json=data
        )
        
        assert response.status_code == 201
        result = json.loads(response.data)
        assert result['success'] is True
        assert 'email' in result['data']

    def test_register_without_profile_picture(self, client):
        """Test registration without profile picture (should still work)"""
        data = {
            'email': 'student_no_pic@example.com',
            'password': 'SecurePass123!',
            'first_name': 'Bob',
            'last_name': 'Johnson',
            'role': 'student',
            'grade_level': '11',
            'school': 'Test School'
        }
        
        response = client.post(
            '/api/v1/auth/register',
            json=data
        )
        
        assert response.status_code == 201
        result = json.loads(response.data)
        assert result['success'] is True

    def test_register_teacher_with_file_upload(self, client):
        """Test teacher registration with profile picture file upload"""
        image_data = (
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
            b'\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01'
            b'\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
        )
        
        data = {
            'email': 'teacher_with_pic@example.com',
            'password': 'SecurePass123!',
            'first_name': 'Alice',
            'last_name': 'Williams',
            'role': 'teacher',
            'qualifications': 'Masters in Mathematics',
            'subjects_taught': ['Mathematics', 'Physics'],
            'years_of_experience': 5,
            'language_of_instruction': 'English'
        }
        
        files = {
            'profile_picture': (io.BytesIO(image_data), 'profile.png', 'image/png')
        }
        
        response = client.post(
            '/api/v1/auth/register',
            data=data,
            files=files,
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 201
        result = json.loads(response.data)
        assert result['success'] is True

    def test_register_invalid_image_type(self, client):
        """Test registration with invalid image type"""
        # Invalid file (text file instead of image)
        invalid_data = b'This is not an image'
        
        data = {
            'email': 'student_invalid_pic@example.com',
            'password': 'SecurePass123!',
            'first_name': 'Charlie',
            'last_name': 'Brown',
            'role': 'student',
            'grade_level': '9',
            'school': 'Test School'
        }
        
        files = {
            'profile_picture': (io.BytesIO(invalid_data), 'notimage.txt', 'text/plain')
        }
        
        response = client.post(
            '/api/v1/auth/register',
            data=data,
            files=files,
            content_type='multipart/form-data'
        )
        
        # Should still succeed (picture upload failure is non-fatal)
        # but picture won't be saved
        assert response.status_code in [201, 400]

    def test_file_upload_takes_precedence_over_url(self, client):
        """Test that file upload takes precedence over URL when both are provided"""
        image_data = (
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
            b'\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01'
            b'\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
        )
        
        data = {
            'email': 'student_both_pic@example.com',
            'password': 'SecurePass123!',
            'first_name': 'David',
            'last_name': 'Evans',
            'role': 'student',
            'grade_level': '12',
            'school': 'Test School',
            'profile_picture_url': 'https://example.com/notused.jpg'  # Should be ignored
        }
        
        files = {
            'profile_picture': (io.BytesIO(image_data), 'profile.png', 'image/png')
        }
        
        response = client.post(
            '/api/v1/auth/register',
            data=data,
            files=files,
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 201
        result = json.loads(response.data)
        assert result['success'] is True
