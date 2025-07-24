"""
Main application routes.

This module contains the main application routes including the home page,
dashboard, and other core functionality.
"""
print("\n\n=== MAIN ROUTES.PY IS BEING IMPORTED ===\n\n")
import logging
from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from . import main_bp
from ..models import get_model

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.info('=' * 50)
logger.info('MAIN ROUTES MODULE IMPORTED')
logger.info(f'Main blueprint name: {main_bp.name}')
logger.info(f'Main blueprint url_prefix: {getattr(main_bp, "url_prefix", "None")}')
logger.info('=' * 50)

User = get_model('User')
Assessment = get_model('Assessment')
from ..utils.decorators import admin_required, examiner_required

# Log when the route is being defined
logger.info('=' * 50)
logger.info('DEFINING MAIN BLUEPRINT ROUTES')
logger.info(f'Main blueprint name: {main_bp.name}')
logger.info(f'Main blueprint url_prefix: {getattr(main_bp, "url_prefix", "None")}')
logger.info(f'Main blueprint template_folder: {main_bp.template_folder}')
logger.info(f'Main blueprint root_path: {main_bp.root_path}')
logger.info(f'Main blueprint has_blueprint_teardown: {hasattr(main_bp, "teardown_app_request")}')
logger.info(f'Main blueprint has_blueprint_before_request: {hasattr(main_bp, "before_request")}')
logger.info(f'Main blueprint has_blueprint_after_request: {hasattr(main_bp, "after_request")}')
logger.info('=' * 50)

@main_bp.route('/')
def index():
    """Home page route that shows appropriate content based on authentication."""
    logger.info('Root URL accessed')
    
    if not current_user.is_authenticated:
        current_app.logger.info('User not authenticated, showing welcome page')
        return render_template('index.html')
        
    current_app.logger.info(f'User {current_user.email} is authenticated')
    if current_user.is_admin:
        current_app.logger.info('Showing admin dashboard')
        return redirect(url_for('admin.index'))
    elif current_user.is_examiner:
        current_app.logger.info('Redirecting examiner to examiner index')
        return redirect(url_for('main.index'))
    else:
        current_app.logger.info('Redirecting regular user to assessment')
        return redirect(url_for('main.assessment'))

# Removed dashboard route as it's no longer needed
# All dashboard functionality has been moved to the index route

@main_bp.route('/assessment')
@login_required
def assessment():
    """Assessment interface route."""
    if current_user.is_admin or current_user.is_examiner:
        return redirect(url_for('main.index'))
    
    # Get active assessment or create a new one
    assessment = Assessment.objects(
        user=current_user.id,
        status__in=['draft', 'in_progress']
    ).order_by('-created_at').first()
    
    if not assessment:
        assessment = Assessment(
            user=current_user.id,
            title=f"Assessment - {current_user.name}",
            status='draft'
        )
        assessment.save()
    
    return render_template('assessment.html', assessment=assessment)

@main_bp.route('/assessment/<assessment_id>')
@login_required
def view_assessment(assessment_id):
    """View assessment details."""
    assessment = Assessment.objects.get_or_404(id=assessment_id)
    
    # Check permissions
    if not (current_user.is_admin or 
            current_user.is_examiner or 
            str(assessment.user.id) == str(current_user.id)):
        flash('You do not have permission to view this assessment.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    return render_template('view_assessment.html', assessment=assessment)

@main_bp.route('/profile')
@login_required
def profile():
    """User profile page."""
    return render_template('profile.html')
