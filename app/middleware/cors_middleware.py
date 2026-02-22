"""
CORS Middleware
Handles Cross-Origin Resource Sharing (CORS) configuration and requests
"""

from functools import wraps
from flask import request, jsonify
from flask_cors import CORS

def configure_cors(app, origins=None):
    """
    Configure CORS for Flask application
    
    Args:
        app: Flask application instance
        origins: List of allowed origins (default: localhost and local IPs)
    """
    if origins is None:
        origins = [
            'http://localhost:3000',
            'http://localhost:8000',
            'http://127.0.0.1:3000',
            'http://127.0.0.1:8000',
            'https://localhost:3000',
            'https://localhost:8000',
        ]
        
        # In production, add actual domain
        if app.config.get('ENV') == 'production':
            origins.extend([
                'https://yourdomain.com',
                'https://www.yourdomain.com',
                'https://api.yourdomain.com',
            ])
    
    CORS(
        app,
        resources={r"/api/*": {
            "origins": origins,
            "methods": ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"],
            "expose_headers": ["Content-Range", "X-Content-Range"],
            "supports_credentials": True,
            "max_age": 3600
        }},
        expose_headers=['Content-Type'],
        allow_headers=['Content-Type'],
        send_wildcard=False,
        automatic_options=True,
        vary_header=True
    )

def setup_cors_error_handler(app):
    """
    Setup error handlers for CORS issues
    
    Args:
        app: Flask application instance
    """
    @app.errorhandler(400)
    def handle_bad_request(e):
        return jsonify({
            'status': 'error',
            'message': 'Bad request',
            'code': 'BAD_REQUEST'
        }), 400
    
    @app.before_request
    def handle_preflight():
        """Handle CORS preflight requests"""
        if request.method == "OPTIONS":
            response = {
                'status': 'success',
                'message': 'CORS preflight request accepted'
            }
            return response, 200

def require_origin(allowed_origins=None):
    """
    Decorator to verify request origin
    
    Usage:
        @app.route('/api/v1/webhook', methods=['POST'])
        @require_origin(['https://trusted-service.com'])
        def webhook():
            ...
    
    Args:
        allowed_origins: List of allowed origins
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            origin = request.headers.get('Origin')
            
            if allowed_origins is None:
                # If no specific origins required, allow
                return f(*args, **kwargs)
            
            if origin not in allowed_origins:
                return jsonify({
                    'status': 'error',
                    'message': 'Origin not allowed',
                    'code': 'FORBIDDEN_ORIGIN'
                }), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def add_security_headers(f):
    """
    Decorator to add security headers to response
    
    Usage:
        @app.route('/api/v1/users')
        @add_security_headers
        def get_users():
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        result = f(*args, **kwargs)
        
        # Get response object
        if isinstance(result, tuple):
            response = result[0] if hasattr(result[0], 'headers') else None
        else:
            response = result
        
        if response and hasattr(response, 'headers'):
            # Add security headers
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
            response.headers['Content-Security-Policy'] = "default-src 'self'"
        
        return result
    
    return decorated_function
