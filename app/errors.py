"""
Error Handlers

This module contains error handlers for the application.
"""
from flask import Blueprint, render_template

# Create errors blueprint
errors_bp = Blueprint('errors', __name__)

# Export the blueprint as 'bp' for compatibility
bp = errors_bp

@errors_bp.app_errorhandler(403)
def forbidden_error(error):
    """Handle 403 Forbidden errors."""
    return render_template('errors/403.html'), 403

@errors_bp.app_errorhandler(404)
def not_found_error(error):
    """Handle 404 Not Found errors."""
    return render_template('errors/404.html'), 404

@errors_bp.app_errorhandler(500)
def internal_error(error):
    """Handle 500 Internal Server errors."""
    return render_template('errors/500.html'), 500
