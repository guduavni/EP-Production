""
Admin Blueprint

This module contains the admin interface for the EP-Simulator application.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os

# Create admin blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.before_request
@login_required
def require_admin():
    """Ensure user is an admin for all admin routes."""
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('main.index'))

@admin_bp.route('/')
def dashboard():
    """Admin dashboard."""
    return render_template('admin/dashboard.html', title='Admin Dashboard')

@admin_bp.route('/users')
def users():
    """User management."""
    from ..models import User
    users = User.objects.all()
    return render_template('admin/users.html', title='User Management', users=users)

@admin_bp.route('/users/<user_id>')
def user_detail(user_id):
    """User detail view."""
    from ..models import User
    user = User.objects.get_or_404(id=user_id)
    return render_template('admin/user_detail.html', title=f'User: {user.name}', user=user)

@admin_bp.route('/assessments')
def assessments():
    """Assessment management."""
    from ..models import Assessment
    assessments = Assessment.objects.all()
    return render_template('admin/assessments.html', title='Assessment Management', assessments=assessments)

@admin_bp.route('/settings', methods=['GET', 'POST'])
def settings():
    """Application settings."""
    if request.method == 'POST':
        # Handle settings update
        current_app.config.update(
            SITE_NAME=request.form.get('site_name', current_app.config['SITE_NAME']),
            ITEMS_PER_PAGE=int(request.form.get('items_per_page', current_app.config['ITEMS_PER_PAGE'])),
            MAINTENANCE_MODE='maintenance_mode' in request.form
        )
        
        # Handle file uploads
        if 'logo' in request.files:
            file = request.files['logo']
            if file.filename != '':
                filename = secure_filename(file.filename)
                filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], 'logos', filename)
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                file.save(filepath)
                current_app.config['SITE_LOGO'] = f'/static/uploads/logos/{filename}'
        
        flash('Settings updated successfully!', 'success')
        return redirect(url_for('admin.settings'))
    
    return render_template('admin/settings.html', title='Application Settings')

@admin_bp.route('/reports')
def reports():
    """Generate and view reports."""
    from ..models import Assessment, User
    
    # Get statistics
    stats = {
        'total_users': User.objects.count(),
        'total_assessments': Assessment.objects.count(),
        'completed_assessments': Assessment.objects(status='completed').count(),
        'pending_assessments': Assessment.objects(status='pending').count(),
    }
    
    # Get recent activities
    recent_assessments = Assessment.objects.order_by('-created_at').limit(5)
    
    return render_template('admin/reports.html', 
                         title='Reports & Analytics',
                         stats=stats,
                         recent_assessments=recent_assessments)

@admin_bp.route('/api-keys')
def api_keys():
    """Manage API keys."""
    # In a real app, you would have an API key model
    return render_template('admin/api_keys.html', title='API Keys Management')
