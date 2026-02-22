"""
Audit Logging Middleware
Logs all user actions and API calls for compliance and security
"""

from functools import wraps
from flask import request, g
from datetime import datetime
from sqlalchemy import text
from app import db
import json
import traceback

class AuditLog:
    """Model for audit logs - add to models if needed"""
    
    def __init__(self, user_id, action, resource_type, resource_id, 
                 method, endpoint, status_code, ip_address, user_agent, details=None):
        self.user_id = user_id
        self.action = action
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.method = method
        self.endpoint = endpoint
        self.status_code = status_code
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.details = details or {}
        self.created_at = datetime.utcnow()

def audit_action(action, resource_type=None):
    """
    Decorator to log user actions
    
    Usage:
        @app.route('/api/v1/courses/<course_id>', methods=['PUT'])
        @audit_action('UPDATE', 'course')
        def update_course(course_id):
            ...
    
    Args:
        action: Action type (CREATE, READ, UPDATE, DELETE, etc.)
        resource_type: Type of resource being modified
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            start_time = datetime.utcnow()
            status_code = 200
            error_message = None
            
            try:
                response = f(*args, **kwargs)
                
                # Extract status code from response
                if isinstance(response, tuple):
                    status_code = response[1] if len(response) > 1 else 200
                
                return response
                
            except Exception as e:
                status_code = 500
                error_message = str(e)
                raise
                
            finally:
                try:
                    # Log the audit entry
                    user_id = getattr(request, 'user_id', None)
                    ip_address = request.remote_addr
                    user_agent = request.headers.get('User-Agent', 'Unknown')
                    
                    # Extract resource ID from route if available
                    resource_id = None
                    for key, value in kwargs.items():
                        if 'id' in key.lower():
                            resource_id = value
                            break
                    
                    audit_entry = {
                        'timestamp': start_time.isoformat(),
                        'user_id': user_id,
                        'action': action,
                        'resource_type': resource_type,
                        'resource_id': resource_id,
                        'method': request.method,
                        'endpoint': request.path,
                        'status_code': status_code,
                        'ip_address': ip_address,
                        'duration_ms': (datetime.utcnow() - start_time).total_seconds() * 1000,
                        'error': error_message
                    }
                    
                    # Try to log to database
                    log_to_database(audit_entry)
                    
                except Exception as e:
                    # Log any audit logging errors but don't break request
                    print(f'Audit logging error: {str(e)}')
        
        return decorated_function
    return decorator

def log_to_database(audit_entry):
    """
    Log audit entry to database
    This should be implemented with an AuditLog model
    """
    try:
        # When AuditLog model is created, implement:
        # audit_log = AuditLog(**audit_entry)
        # db.session.add(audit_log)
        # db.session.commit()
        
        # For now, just store in memory or print
        print(f'[AUDIT] {json.dumps(audit_entry)}')
        
    except Exception as e:
        print(f'Failed to log to database: {str(e)}')

def log_authentication(f):
    """Decorator to log authentication events"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = datetime.utcnow()
        
        try:
            result = f(*args, **kwargs)
            status_code = result[1] if isinstance(result, tuple) else 200
            
            log_entry = {
                'timestamp': start_time.isoformat(),
                'event': 'LOGIN_ATTEMPT',
                'ip_address': request.remote_addr,
                'status': 'success' if status_code == 200 else 'failed',
                'status_code': status_code
            }
            
            print(f'[AUTH_LOG] {json.dumps(log_entry)}')
            return result
            
        except Exception as e:
            log_entry = {
                'timestamp': start_time.isoformat(),
                'event': 'LOGIN_ATTEMPT',
                'ip_address': request.remote_addr,
                'status': 'failed',
                'error': str(e)
            }
            
            print(f'[AUTH_LOG] {json.dumps(log_entry)}')
            raise
    
    return decorated_function
