"""
Utility Functions

This module contains various utility functions used throughout the application.
"""
from datetime import datetime
from flask import current_app

# Import helper functions
from .helpers import (
    is_safe_url,
    get_redirect_target,
    redirect_back,
    generate_confirmation_token,
    confirm_token,
    generate_api_key,
    generate_secure_filename,
    validate_email,
    validate_password,
    json_response,
    error_response,
    success_response,
    paginate_query,
    format_duration,
    human_readable_size,
    log_activity,
    roles_required,
    admin_required,
    examiner_required,
    candidate_required
)

# Import email utilities
from .email import send_email, send_password_reset_email, send_welcome_email

# Import file utilities
from .file_utils import (
    is_allowed_file as allowed_file,
    save_uploaded_file,
    delete_file,
    get_file_extension,
    get_mime_type
)

# Import audio processing utilities
from .audio_processing import (
    process_audio_file,
    extract_audio_features,
    transcribe_audio,
    analyze_pronunciation
)

def format_date(value, format='%Y-%m-%d'):
    """Format a date to the given format.
    
    Args:
        value: The date to format (can be string, datetime, or date)
        format: The format string (default: '%Y-%m-%d')
        
    Returns:
        Formatted date string or None if value is None
    """
    if value is None:
        return None
        
    if isinstance(value, str):
        # Try to parse the string as a datetime
        try:
            value = datetime.strptime(value, '%Y-%m-%d')
        except (ValueError, TypeError):
            return value
    
    return value.strftime(format)

def format_datetime(value, format='%Y-%m-%d %H:%M:%S'):
    """Format a datetime to the given format.
    
    Args:
        value: The datetime to format (can be string or datetime)
        format: The format string (default: '%Y-%m-%d %H:%M:%S')
        
    Returns:
        Formatted datetime string or None if value is None
    """
    if value is None:
        return None
        
    if isinstance(value, str):
        # Try to parse the string as a datetime
        try:
            value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        except (ValueError, TypeError):
            return value
    
    return value.strftime(format)

# Make the format_date and format_datetime available as Jinja2 filters
def init_app(app):
    """Initialize the utils with the Flask app."""
    app.jinja_env.filters['datetime'] = format_datetime
    app.jinja_env.filters['date'] = format_date
