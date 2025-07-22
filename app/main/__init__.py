"""
Main Blueprint

This module contains the main application routes and error handlers.
"""
import os
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import current_user, login_required
from ..models.user import User
from ..models.assessment import Assessment
from ..models.notification import Notification
from ..utils.decorators import admin_required, examiner_required, candidate_required

# Create main blueprint
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Home page route."""
    try:
        if current_user.is_authenticated:
            if current_user.is_admin:
                return redirect(url_for('admin.dashboard'))
            elif current_user.is_examiner:
                return redirect(url_for('examiner.dashboard'))
            else:
                return redirect(url_for('candidate.dashboard'))
        
        # Try to render the template with full path
        template_path = os.path.join('templates', 'main', 'index.html')
        if not os.path.exists(template_path):
            return f"Template not found at: {template_path}"
            
        return render_template('main/index.html')
    except Exception as e:
        return f"Error: {str(e)}"

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """User dashboard route."""
    if current_user.is_admin:
        return redirect(url_for('admin.dashboard'))
    elif current_user.is_examiner:
        return redirect(url_for('examiner.dashboard'))
    else:
        return redirect(url_for('candidate.dashboard'))

@main_bp.route('/profile')
@login_required
def profile():
    """User profile page."""
    return render_template('main/profile.html', user=current_user)

@main_bp.route('/notifications')
@login_required
def notifications():
    """User notifications page."""
    notifications = Notification.objects(user=current_user).order_by('-created_at')
    return render_template('main/notifications.html', notifications=notifications)

@main_bp.route('/notifications/read_all', methods=['POST'])
@login_required
def mark_all_notifications_read():
    """Mark all notifications as read."""
    Notification.objects(user=current_user, read=False).update(set__read=True)
    return jsonify({'status': 'success'})

@main_bp.route('/search')
def search():
    """Global search functionality."""
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'results': []})
    
    results = {
        'users': [],
        'assessments': []
    }
    
    if current_user.is_authenticated:
        # Search users (admin and examiners can search users)
        if current_user.is_admin or current_user.is_examiner:
            users = User.objects(
                __raw__={
                    '$or': [
                        {'name': {'$regex': query, '$options': 'i'}},
                        {'email': {'$regex': query, '$options': 'i'}}
                    ]
                }
            ).limit(5)
            results['users'] = [{
                'id': str(user.id),
                'name': user.name,
                'email': user.email,
                'role': user.role
            } for user in users]
        
        # Search assessments
        assessments = Assessment.objects(
            __raw__={
                '$or': [
                    {'title': {'$regex': query, '$options': 'i'}},
                    {'description': {'$regex': query, '$options': 'i'}}
                ]
            }
        ).limit(5)
        
        results['assessments'] = [{
            'id': str(assess.id),
            'title': assess.title,
            'status': assess.status,
            'candidate': assess.candidate.name if assess.candidate else 'Unknown'
        } for assess in assessments]
    
    return jsonify(results)

@main_bp.route('/help')
def help():
    """Help and documentation page."""
    return render_template('main/help.html')

@main_bp.route('/terms')
def terms():
    """Terms of service page."""
    return render_template('main/terms.html')

@main_bp.route('/privacy')
def privacy():
    """Privacy policy page."""
    return render_template('main/privacy.html')

# Error handlers
@main_bp.app_errorhandler(403)
def forbidden_error(error):
    """Handle 403 Forbidden errors."""
    if request.path.startswith('/api/'):
        return jsonify({
            'status': 'error',
            'message': 'You do not have permission to access this resource.',
            'code': 403
        }), 403
    return render_template('errors/403.html'), 403

@main_bp.app_errorhandler(404)
def not_found_error(error):
    """Handle 404 Not Found errors."""
    if request.path.startswith('/api/'):
        return jsonify({
            'status': 'error',
            'message': 'The requested resource was not found.',
            'code': 404
        }), 404
    return render_template('errors/404.html'), 404

@main_bp.app_errorhandler(500)
def internal_error(error):
    """Handle 500 Internal Server errors."""
    current_app.logger.error(f'500 Error: {error}')
    if request.path.startswith('/api/'):
        return jsonify({
            'status': 'error',
            'message': 'An internal server error occurred.',
            'code': 500
        }), 500
    return render_template('errors/500.html'), 500

# Export the blueprint as 'bp' for compatibility
bp = main_bp

# Import routes, forms, and utils
from . import routes, forms, utils
