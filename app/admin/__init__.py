"""
Admin Blueprint

This module contains the admin interface for the EP-Simulator application.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from ..models import get_model
from ..extensions import db
import json

# Import blueprints
from .exam_trainee import exam_trainee_bp
from .exam_trainee_email import exam_trainee_email_bp
from .users import users_bp

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Register blueprints
admin_bp.register_blueprint(exam_trainee_bp, url_prefix='/trainees')
admin_bp.register_blueprint(exam_trainee_email_bp)
admin_bp.register_blueprint(users_bp)

@admin_bp.route('/')
@login_required
def index():
    """Admin dashboard view."""
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('main.index'))
    
    # Redirect to users list instead of trainees
    return redirect(url_for('admin.users.list_users'))

# Rest of the file remains the same...
