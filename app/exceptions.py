"""
Custom Exceptions
Standardized exception classes for the application
"""


class LMSException(Exception):
    """Base exception class for LMS application"""

    def __init__(self, message, status_code=400):
        """
        Initialize LMS exception

        Args:
            message (str): Error message
            status_code (int): HTTP status code
        """
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class ValidationError(LMSException):
    """Raised when input validation fails"""

    def __init__(self, message):
        super().__init__(message, status_code=400)


class AuthenticationError(LMSException):
    """Raised when authentication fails"""

    def __init__(self, message="Unauthorized"):
        super().__init__(message, status_code=401)


class AuthorizationError(LMSException):
    """Raised when user lacks required permissions"""

    def __init__(self, message="Forbidden"):
        super().__init__(message, status_code=403)


class ResourceNotFoundError(LMSException):
    """Raised when requested resource is not found"""

    def __init__(self, resource_type, resource_id):
        message = f"{resource_type} with id {resource_id} not found"
        super().__init__(message, status_code=404)


class ConflictError(LMSException):
    """Raised when resource already exists or state conflict"""

    def __init__(self, message):
        super().__init__(message, status_code=409)


class DatabaseError(LMSException):
    """Raised when database operation fails"""

    def __init__(self, message="Database error occurred"):
        super().__init__(message, status_code=500)


class ExternalServiceError(LMSException):
    """Raised when external service call fails (email, payment, etc.)"""

    def __init__(self, service_name, message):
        msg = f"{service_name} error: {message}"
        super().__init__(msg, status_code=500)
