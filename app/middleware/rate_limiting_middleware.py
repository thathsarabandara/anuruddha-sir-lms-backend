"""
Rate Limiting Middleware
Implements rate limiting for sensitive operations (payments, login attempts, etc.)
"""

from functools import wraps
from flask import request, jsonify, current_app
from datetime import datetime, timedelta
from collections import defaultdict
import threading

class RateLimiter:
    """
    Simple in-memory rate limiter
    In production, use Redis for distributed rate limiting
    """
    
    def __init__(self):
        self.requests = defaultdict(list)
        self.lock = threading.Lock()
    
    def is_rate_limited(self, identifier, max_requests=10, window_seconds=60):
        """
        Check if identifier has exceeded rate limit
        
        Args:
            identifier: Unique identifier (e.g., IP, user_id)
            max_requests: Maximum requests allowed
            window_seconds: Time window in seconds
            
        Returns:
            bool: True if rate limited, False otherwise
        """
        with self.lock:
            now = datetime.utcnow()
            window_start = now - timedelta(seconds=window_seconds)
            
            # Clean old requests
            self.requests[identifier] = [
                req_time for req_time in self.requests[identifier]
                if req_time > window_start
            ]
            
            # Check limit
            if len(self.requests[identifier]) >= max_requests:
                return True
            
            # Record this request
            self.requests[identifier].append(now)
            return False
    
    def get_reset_time(self, identifier, window_seconds=60):
        """Get when rate limit resets for identifier"""
        with self.lock:
            if identifier in self.requests and self.requests[identifier]:
                oldest = self.requests[identifier][0]
                reset = oldest + timedelta(seconds=window_seconds)
                return reset
            return None

# Global rate limiter instance
rate_limiter = RateLimiter()

def limit_rate(max_requests=10, window_seconds=60, key_func=None):
    """
    Decorator to rate limit requests
    
    Usage:
        @app.route('/api/v1/payments/process', methods=['POST'])
        @limit_rate(max_requests=5, window_seconds=60, key_func=lambda: request.user_id)
        def process_payment():
            ...
    
    Args:
        max_requests: Maximum requests in window
        window_seconds: Time window in seconds
        key_func: Function to generate rate limit key (default: IP address)
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Generate rate limit key
                if key_func:
                    identifier = key_func()
                else:
                    # Use IP address by default
                    identifier = request.remote_addr
                
                # Check rate limit
                if rate_limiter.is_rate_limited(identifier, max_requests, window_seconds):
                    reset_time = rate_limiter.get_reset_time(identifier, window_seconds)
                    return jsonify({
                        'status': 'error',
                        'message': 'Rate limit exceeded',
                        'code': 'RATE_LIMITED',
                        'retry_after': window_seconds
                    }), 429
                
                return f(*args, **kwargs)
                
            except Exception as e:
                # Log error but don't block request
                print(f'Rate limiting error: {str(e)}')
                return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def limit_payment_attempts():
    """
    Rate limiter for payment operations
    5 attempts per minute per user
    """
    return limit_rate(
        max_requests=5,
        window_seconds=60,
        key_func=lambda: getattr(request, 'user_id', request.remote_addr)
    )

def limit_login_attempts():
    """
    Rate limiter for login attempts
    5 attempts per minute per IP
    """
    return limit_rate(
        max_requests=5,
        window_seconds=60,
        key_func=lambda: request.remote_addr
    )
