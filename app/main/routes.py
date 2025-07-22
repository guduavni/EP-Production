"""
Main application routes.

This module contains the main application routes including the home page,
dashboard, and other core functionality.
"""
from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from . import main_bp
from ..models import get_model
User = get_model('User')
Assessment = get_model('Assessment')
from ..utils.decorators import admin_required, examiner_required

@main_bp.route('/')
def index():
    """Home page route."""
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin.index'))
        elif current_user.is_examiner:
            return redirect(url_for('main.dashboard'))
        else:
            return redirect(url_for('main.assessment'))
    return render_template('index.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """User dashboard route."""
    if current_user.is_admin:
        return redirect(url_for('admin.index'))
    
    # Get user's assessments
    if current_user.is_examiner:
        assessments = Assessment.objects(examiner=current_user.id).order_by('-created_at')
    else:
        assessments = Assessment.objects(user=current_user.id).order_by('-created_at')
    
    return render_template('dashboard.html', assessments=assessments)

@main_bp.route('/assessment')
@login_required
def assessment():
    """Assessment interface route."""
    if current_user.is_admin or current_user.is_examiner:
        return redirect(url_for('main.dashboard'))
    
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
