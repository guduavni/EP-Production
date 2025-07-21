"""
Helper Functions

This module contains various utility functions used throughout the application.
"""
import os
import re
import json
import uuid
import hashlib
import logging
from datetime import datetime, timedelta
from functools import wraps
from urllib.parse import urlparse, urljoin
from flask import request, redirect, url_for, flash, current_app, jsonify
from flask_login import current_user
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature

# Set up logging
logger = logging.getLogger(__name__)

def is_safe_url(target):
    """Check if a URL is safe for redirection."""
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

def get_redirect_target():
    """Get the redirect target from the request."""
    for target in request.values.get('next'), request.referrer:
        if not target:
            continue
        if is_safe_url(target):
            return target
    return None

def redirect_back(endpoint, **values):
    """Redirect back to the previous page or a default endpoint."""
    target = request.form.get('next')
    if not target or not is_safe_url(target):
        target = url_for(endpoint, **values)
    return redirect(target)

def generate_confirmation_token(email, salt=None):
    """Generate a confirmation token for email verification."""
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(email, salt=salt or current_app.config['SECURITY_PASSWORD_SALT'])

def confirm_token(token, salt=None, expiration=3600):
    """Confirm a token and return the email if valid."""
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = serializer.loads(
            token,
            salt=salt or current_app.config['SECURITY_PASSWORD_SALT'],
            max_age=expiration
        )
        return email
    except (SignatureExpired, BadSignature) as e:
        logger.warning(f"Token validation failed: {e}")
        return None

def generate_api_key():
    """Generate a secure API key."""
    return hashlib.sha256(os.urandom(32)).hexdigest()

def generate_secure_filename(filename):
    """Generate a secure filename for uploads."""
    # Extract the file extension
    ext = os.path.splitext(filename)[1].lower()
    # Generate a random filename with the same extension
    return f"{uuid.uuid4().hex}{ext}"

def validate_email(email):
    """Validate an email address format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength."""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r"[0-9]", password):
        return False, "Password must contain at least one number"
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character"
    return True, ""

def json_response(data=None, status=200, message=None, **kwargs):
    """Generate a standardized JSON response."""
    response = {
        'status': 'success' if 200 <= status < 400 else 'error',
        'message': message,
        'data': data
    }
    # Add any additional fields
    response.update(kwargs)
    return jsonify(response), status

def error_response(message, status=400, **kwargs):
    """Generate an error JSON response."""
    return json_response(None, status, message, **kwargs)

def success_response(data=None, message="Operation successful", **kwargs):
    """Generate a success JSON response."""
    return json_response(data, 200, message, **kwargs)

def paginate_query(query, page=1, per_page=10):
    """Paginate a query."""
    return query.paginate(page=page, per_page=per_page, error_out=False)

def format_duration(seconds):
    """Format duration in seconds to HH:MM:SS."""
    if not isinstance(seconds, (int, float)) or seconds < 0:
        return "00:00:00"
    
    hours, remainder = divmod(int(seconds), 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def human_readable_size(size_bytes):
    """Convert a file size in bytes to a human-readable format."""
    if not isinstance(size_bytes, (int, float)) or size_bytes < 0:
        return "0 B"
    
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    size = float(size_bytes)
    unit = 0
    
    while size >= 1024 and unit < len(units) - 1:
        size /= 1024
        unit += 1
    
    return f"{size:.2f} {units[unit]}"

def log_activity(action, details=None, user_id=None, ip_address=None):
    """Log user activity."""
    if details is None:
        details = {}
    
    log_entry = {
        'timestamp': datetime.utcnow(),
        'action': action,
        'user_id': str(user_id) if user_id else str(current_user.id) if current_user.is_authenticated else None,
        'ip_address': ip_address or request.remote_addr,
        'user_agent': request.user_agent.string if request else None,
        'details': details
    }
    
    logger.info(json.dumps(log_entry, default=str))
    return log_entry

def roles_required(*roles):
    """Decorator to check if user has any of the required roles."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                if request.is_json:
                    return error_response("Authentication required", 401)
                return redirect(url_for('auth.login', next=request.url))
            
            if not any(current_user.has_role(role) for role in roles):
                if request.is_json:
                    return error_response("Insufficient permissions", 403)
                flash("You don't have permission to access this page.", "danger")
                return redirect(url_for('main.index'))
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    """Decorator to require admin role."""
    return roles_required('admin')(f)

def examiner_required(f):
    """Decorator to require examiner role."""
    return roles_required('examiner')(f)

def candidate_required(f):
    """Decorator to require candidate role."""
    return roles_required('candidate')(f)
