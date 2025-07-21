import os
import string
import random
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify
from werkzeug.utils import secure_filename

# File upload helpers
def allowed_file(filename, allowed_extensions=None):
    """Check if the file has an allowed extension"""
    if allowed_extensions is None:
        allowed_extensions = {'wav', 'mp3', 'ogg', 'm4a'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def save_uploaded_file(file, upload_folder, allowed_extensions=None):
    """Save an uploaded file to the specified folder"""
    if file.filename == '':
        return None, 'No selected file'
        
    if file and allowed_file(file.filename, allowed_extensions):
        filename = secure_filename(file.filename)
        # Add timestamp to avoid filename collisions
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        file_path = os.path.join(upload_folder, filename)
        
        # Ensure upload directory exists
        os.makedirs(upload_folder, exist_ok=True)
        
        file.save(file_path)
        return file_path, None
    return None, 'File type not allowed'

# Authentication helpers
def generate_random_password(length=12):
    """Generate a random password"""
    chars = string.ascii_letters + string.digits + '!@#$%^&*()'
    return ''.join(random.choice(chars) for _ in range(length))

def generate_user_id(prefix='USR'):
    """Generate a unique user ID"""
    timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
    random_str = ''.join(random.choices(string.digits, k=4))
    return f"{prefix}{timestamp}{random_str}"

# Date and time helpers
def format_date(value, format='%Y-%m-%d'):
    """Format a date to the given format"""
    if value is None:
        return ''
    if isinstance(value, str):
        value = datetime.strptime(value, '%Y-%m-%d')
    return value.strftime(format)

def parse_date(date_str, format='%Y-%m-%d'):
    """Parse a date string to a datetime object"""
    try:
        return datetime.strptime(date_str, format)
    except (ValueError, TypeError):
        return None

# API response helpers
def json_response(data=None, message='', status=200, **kwargs):
    """Create a standardized JSON response"""
    response = {
        'success': 200 <= status < 300,
        'message': message,
        'data': data
    }
    response.update(kwargs)
    return jsonify(response), status

def error_response(message, status=400, **kwargs):
    """Create an error response"""
    return json_response(None, message, status, **kwargs)

# Role-based access control
def roles_required(*roles):
    """Decorator to check if user has required role"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return json_response(message='Authentication required', status=401)
            if current_user.role not in roles:
                return json_response(message='Insufficient permissions', status=403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# File operations
def ensure_directory_exists(directory):
    """Ensure that a directory exists, create it if it doesn't"""
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
    return directory

# Validation helpers
def validate_email(email):
    """Basic email validation"""
    if not email or '@' not in email or '.' not in email:
        return False
    return True

def validate_phone(phone):
    """Basic phone number validation"""
    if not phone:
        return False
    # Simple check for digits and common separators
    cleaned = ''.join(c for c in phone if c.isdigit() or c in '+-.() ')
    return len(cleaned) >= 10

# Logging helpers
def setup_logging(app):
    """Configure application logging"""
    import logging
    from logging.handlers import RotatingFileHandler
    
    log_level = getattr(logging, app.config.get('LOG_LEVEL', 'INFO').upper())
    log_file = app.config.get('LOG_FILE', 'app.log')
    max_bytes = app.config.get('LOG_MAX_BYTES', 1024 * 1024 * 10)  # 10MB
    backup_count = app.config.get('LOG_BACKUP_COUNT', 5)
    
    # Ensure log directory exists
    log_dir = os.path.dirname(log_file)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
    
    # File handler
    file_handler = RotatingFileHandler(
        log_file, 
        maxBytes=max_bytes, 
        backupCount=backup_count
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(log_level)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    
    # Configure root logger
    app.logger.setLevel(logging.DEBUG)
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    
    # Disable logging for other loggers
    logging.getLogger('werkzeug').setLevel(logging.ERROR)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('PIL').setLevel(logging.WARNING)
