""
Utility functions and decorators for the main blueprint.
"""
from functools import wraps
from flask import flash, redirect, url_for, abort
from flask_login import current_user

def admin_required(f):
    ""
    Decorator to ensure the user has admin privileges.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Administrator access required.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

def examiner_required(f):
    ""
    Decorator to ensure the user has examiner or admin privileges.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not (current_user.is_examiner or current_user.is_admin):
            flash('Examiner access required.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

def candidate_required(f):
    ""
    Decorator to ensure the user is a candidate.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_candidate:
            flash('Candidate access required.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

def check_assessment_ownership(assessment):
    ""
    Check if the current user owns the assessment or is an admin/examiner.
    
    Args:
        assessment: The assessment object to check ownership of.
        
    Returns:
        bool: True if the user has permission, False otherwise.
    """
    if current_user.is_admin or current_user.is_examiner:
        return True
    return str(assessment.user.id) == str(current_user.id)

def format_duration(seconds):
    ""
    Format a duration in seconds to a human-readable string.
    
    Args:
        seconds (float): Duration in seconds.
        
    Returns:
        str: Formatted duration string (e.g., "2:30").
    """
    if not seconds:
        return "0:00"
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes}:{seconds:02d}"

def allowed_file(filename, allowed_extensions):
    ""
    Check if a filename has an allowed extension.
    
    Args:
        filename (str): The name of the file to check.
        allowed_extensions (set): Set of allowed file extensions.
        
    Returns:
        bool: True if the file has an allowed extension, False otherwise.
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions
