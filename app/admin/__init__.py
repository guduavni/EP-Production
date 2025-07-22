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
from .trainees import trainee_bp

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Register blueprints
admin_bp.register_blueprint(trainee_bp, url_prefix='/trainees')

@admin_bp.route('/')
@login_required
def index():
    """Admin dashboard view."""
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('main.index'))
    
    return redirect(url_for('admin.trainee.list_trainees'))

# Export the blueprint as 'bp' for compatibility
bp = admin_bp

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
    from ..models import get_model
    
    # Get models
    User = get_model('User')
    Assessment = get_model('Assessment')
    
    # Get statistics
    stats = {
        'user_count': User.objects.count() if User else 0,
        'exam_count': Assessment.objects.count() if Assessment else 0,
        'active_exams': Assessment.objects(status='in_progress').count() if Assessment else 0,
        'completed_exams': Assessment.objects(status='completed').count() if Assessment else 0,
        'script_count': 0,  # Default value if no scripts
        'avg_score': 0  # Default value if no assessments
    }
    
    # Get script count if Assessment model is available
    if Assessment:
        # Count assessments that have at least one recording
        stats['script_count'] = Assessment.objects(recordings__exists=True, recordings__not__size=0).count()
    
    # Calculate average score if there are completed exams
    if Assessment and stats['completed_exams'] > 0:
        from mongoengine.queryset.visitor import Q
        completed_assessments = Assessment.objects(status='completed')
        total_score = sum(a.overall_score for a in completed_assessments if hasattr(a, 'overall_score') and a.overall_score is not None)
        stats['avg_score'] = (total_score / stats['completed_exams']) * 100  # Convert to percentage
    
    return render_template('admin/dashboard.html', 
                         title='Admin Dashboard',
                         stats=stats)

@admin_bp.route('/users')
def users():
    """User management."""
    from ..models import get_model
    User = get_model('User')
    users = User.objects.all() if User else []
    return render_template('admin/users.html', title='User Management', users=users)

@admin_bp.route('/users/<user_id>')
def user_detail(user_id):
    """User detail view."""
    from ..models import get_model
    User = get_model('User')
    if not User:
        abort(404)
    
    if user_id == 'new':
        user = None
    else:
        user = User.objects.get_or_404(id=user_id)
    
    return render_template('admin/user_detail.html', 
                         title='New User' if user_id == 'new' else f'Edit User: {user.name}', 
                         user=user)

@admin_bp.route('/users/<user_id>/save', methods=['POST'])
def save_user(user_id):
    """Save user details."""
    from ..models import get_model
    from werkzeug.security import generate_password_hash
    
    User = get_model('User')
    if not User:
        abort(500, "User model not found")
    
    try:
        if user_id == 'new':
            # Create new user
            if not request.form.get('password'):
                flash('Password is required for new users', 'error')
                return redirect(url_for('admin.user_detail', user_id='new'))
                
            user = User(
                name=request.form['name'],
                email=request.form['email'],
                role=request.form.get('role', 'candidate'),
                status=request.form.get('status', 'active'),
                password_hash=generate_password_hash(request.form['password'])
            )
            user.save()
            flash('User created successfully!', 'success')
        else:
            # Update existing user
            user = User.objects.get_or_404(id=user_id)
            user.name = request.form['name']
            user.email = request.form['email']
            user.role = request.form.get('role', user.role)
            user.status = request.form.get('status', user.status)
            
            # Update password if provided
            if request.form.get('password'):
                user.password_hash = generate_password_hash(request.form['password'])
            
            user.save()
            flash('User updated successfully!', 'success')
            
    except Exception as e:
        flash(f'Error saving user: {str(e)}', 'error')
        return redirect(url_for('admin.user_detail', user_id=user_id))
    
    return redirect(url_for('admin.users'))

@admin_bp.route('/users/<user_id>/delete', methods=['POST'])
def delete_user(user_id):
    """Delete a user."""
    from ..models import get_model
    
    User = get_model('User')
    if not User:
        abort(500, "User model not found")
    
    try:
        user = User.objects.get_or_404(id=user_id)
        
        # Prevent deleting own account
        if str(user.id) == str(current_user.id):
            flash('You cannot delete your own account', 'error')
            return redirect(url_for('admin.users'))
            
        user.delete()
        flash('User deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting user: {str(e)}', 'error')
    
    return redirect(url_for('admin.users'))

@admin_bp.route('/users/<user_id>/status', methods=['POST'])
def update_user_status(user_id):
    """Update user status (active/inactive)."""
    from ..models import get_model
    from flask import jsonify
    
    User = get_model('User')
    if not User:
        return jsonify({'success': False, 'message': 'User model not found'}), 500
    
    try:
        data = request.get_json()
        new_status = data.get('status')
        
        if new_status not in ['active', 'inactive']:
            return jsonify({'success': False, 'message': 'Invalid status'}), 400
            
        user = User.objects.get_or_404(id=user_id)
        
        # Prevent deactivating own account
        if str(user.id) == str(current_user.id) and new_status == 'inactive':
            return jsonify({'success': False, 'message': 'You cannot deactivate your own account'}), 400
            
        user.status = new_status
        user.save()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/assessments')
def assessments():
    """Assessment management."""
    from ..models import get_model
    Assessment = get_model('Assessment')
    assessments = Assessment.objects.all() if Assessment else []
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
