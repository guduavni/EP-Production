"""
Custom Decorators

This module contains custom decorators for route protection and other utilities.
"""
from functools import wraps
from flask import jsonify, request, current_app
from flask_login import current_user
from werkzeug.exceptions import Forbidden

# Role-based access control
def role_required(*roles):
    """
    Decorator to restrict access to users with specific roles.
    
    Args:
        *roles: List of allowed roles
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({
                    'status': 'error',
                    'message': 'Authentication required',
                    'code': 401
                }), 401
                
            if current_user.role not in roles and 'admin' not in roles:
                return jsonify({
                    'status': 'error',
                    'message': 'Insufficient permissions',
                    'code': 403
                }), 403
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    """Decorator to restrict access to admin users only."""
    return role_required('admin')(f)

def examiner_required(f):
    """Decorator to restrict access to examiners and admins."""
    return role_required('admin', 'examiner')(f)

def candidate_required(f):
    """Decorator to restrict access to candidates and above."""
    return role_required('admin', 'examiner', 'candidate')(f)

# Rate limiting
def rate_limit(requests=100, window=15, by="endpoint"):
    """
    Decorator to implement rate limiting.
    
    Args:
        requests: Number of requests allowed per window
        window: Time window in minutes
        by: What to rate limit by ('ip' or 'user' or 'endpoint')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_app.config.get('TESTING'):
                # Use Flask-Limiter if configured, otherwise use a simple in-memory solution
                if hasattr(current_app, 'limiter'):
                    return f(*args, **kwargs)
                
                # Simple in-memory rate limiting (for development)
                from datetime import datetime, timedelta
                from collections import defaultdict
                
                # This is a simple in-memory store - in production, use Redis or similar
                if not hasattr(current_app, 'rate_limit_store'):
                    current_app.rate_limit_store = {
                        'counts': defaultdict(list),
                        'last_cleanup': datetime.utcnow()
                    }
                
                store = current_app.rate_limit_store
                now = datetime.utcnow()
                
                # Clean up old entries periodically
                if (now - store['last_cleanup']).total_seconds() > 60:
                    for key in list(store['counts'].keys()):
                        store['counts'][key] = [t for t in store['counts'][key] 
                                             if (now - t).total_seconds() <= window * 60]
                        if not store['counts'][key]:
                            del store['counts'][key]
                    store['last_cleanup'] = now
                
                # Determine the key to use for rate limiting
                if by == 'ip':
                    key = request.remote_addr
                elif by == 'user' and current_user.is_authenticated:
                    key = f"user_{current_user.id}"
                else:  # by endpoint
                    key = f"{request.endpoint}_{request.remote_addr}"
                
                # Check rate limit
                timestamps = store['counts'].get(key, [])
                timestamps = [t for t in timestamps 
                            if (now - t).total_seconds() <= window * 60]
                
                if len(timestamps) >= requests:
                    return jsonify({
                        'status': 'error',
                        'message': 'Too many requests',
                        'code': 429
                    }), 429
                
                # Update timestamps
                timestamps.append(now)
                store['counts'][key] = timestamps
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# JSON API decorators
def json_required(f):
    """Decorator to ensure the request contains valid JSON."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_json:
            return jsonify({
                'status': 'error',
                'message': 'Content-Type must be application/json',
                'code': 400
            }), 400
        return f(*args, **kwargs)
    return decorated_function

def validate_schema(schema):
    """
    Decorator to validate request data against a schema.
    
    Args:
        schema: A marshmallow Schema class to validate against
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            data = request.get_json()
            errors = schema().validate(data)
            
            if errors:
                return jsonify({
                    'status': 'error',
                    'message': 'Validation error',
                    'errors': errors,
                    'code': 400
                }), 400
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator
