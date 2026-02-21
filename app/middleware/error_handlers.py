"""
Error Handlers
Global error handling for the application
"""

from flask import jsonify
from app.utils.response import error_response
from app.exceptions import LMSException
import logging

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    """
    Register global error handlers for the Flask app
    
    Args:
        app: Flask application instance
    """
    
    @app.errorhandler(LMSException)
    def handle_lms_exception(error):
        """Handle custom LMS exceptions"""
        logger.warning(f'LMS Exception: {error.message}')
        return error_response(error.message, error.status_code)
    
    @app.errorhandler(400)
    def bad_request(error):
        """Handle 400 Bad Request"""
        return error_response('Bad request', 400)
    
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 Not Found"""
        return error_response('Resource not found', 404)
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        """Handle 405 Method Not Allowed"""
        return error_response('Method not allowed', 405)
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 Internal Server Error"""
        logger.error(f'Internal server error: {str(error)}', exc_info=True)
        from app import db
        db.session.rollback()
        return error_response('Internal server error', 500)
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        """Handle unexpected exceptions"""
        logger.error(f'Unexpected error: {str(error)}', exc_info=True)
        from app import db
        db.session.rollback()
        return error_response('Internal server error', 500)
