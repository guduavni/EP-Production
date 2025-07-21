from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import login_required, current_user
from datetime import datetime, timedelta

# Import db from extensions to avoid circular imports
from extensions import db

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Import models after Blueprint creation to avoid circular imports
from models import User, Assessment, AudioRecording

def admin_required(f):
    """Decorator to ensure the user is an admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/')
@login_required
@admin_required
def admin_dashboard():
    # Get dashboard statistics
    stats = {
        'total_users': User.objects.count(),
        'active_assessments': Assessment.objects(status='in_progress').count(),
        'completed_today': Assessment.objects(
            status='completed',
            end_time__gte=datetime.now() - timedelta(days=1)
        ).count(),
        'avg_score': Assessment.objects.average('overall_score') or 0
    }
    
    # Get recent assessments
    recent_assessments = Assessment.objects.order_by('-start_time').limit(5)
    
    # Calculate score distribution (example data - replace with actual query)
    score_distribution = {
        'level_1_2': Assessment.objects(overall_score__lt=3).count(),
        'level_3': Assessment.objects(overall_score__gte=3, overall_score__lt=4).count(),
        'level_4': Assessment.objects(overall_score__gte=4, overall_score__lt=5).count(),
        'level_5': Assessment.objects(overall_score__gte=5, overall_score__lt=6).count(),
        'level_6': Assessment.objects(overall_score=6).count()
    }
    
    return render_template(
        'admin/dashboard.html',
        stats=stats,
        recent_assessments=recent_assessments,
        score_distribution=score_distribution,
        now=datetime.now()
    )

@admin_bp.route('/users')
@login_required
@admin_required
def admin_users():
    users = User.objects()
    return render_template('admin/users/list.html', users=users)

@admin_bp.route('/users/add', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_add_user():
    if request.method == 'POST':
        try:
            user = User(
                user_id=request.form['user_id'].upper(),
                name=request.form['name'],
                email=request.form['email'],
                role=request.form.get('role', 'candidate'),
                status=request.form.get('status', 'active')
            )
            user.save()
            flash('User added successfully!', 'success')
            return redirect(url_for('admin.admin_users'))
        except Exception as e:
            flash(f'Error adding user: {str(e)}', 'danger')
    
    return render_template('admin/users/add.html')

@admin_bp.route('/users/<user_id>')
@login_required
@admin_required
def admin_view_user(user_id):
    user = User.objects.get_or_404(user_id=user_id)
    assessments = Assessment.objects(user=user).order_by('-start_time')
    return render_template('admin/users/view.html', user=user, assessments=assessments)

@admin_bp.route('/users/<user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_user(user_id):
    user = User.objects.get_or_404(user_id=user_id)
    
    if request.method == 'POST':
        try:
            user.name = request.form['name']
            user.email = request.form['email']
            user.role = request.form['role']
            user.status = request.form['status']
            user.save()
            flash('User updated successfully!', 'success')
            return redirect(url_for('admin.admin_view_user', user_id=user_id))
        except Exception as e:
            flash(f'Error updating user: {str(e)}', 'danger')
    
    return render_template('admin/users/edit.html', user=user)

@admin_bp.route('/assessments')
@login_required
@admin_required
def admin_assessments():
    status = request.args.get('status')
    query = {}
    if status:
        query['status'] = status
    
    assessments = Assessment.objects(**query).order_by('-start_time')
    return render_template('admin/assessments/list.html', assessments=assessments, status_filter=status)

@admin_bp.route('/assessments/<assessment_id>')
@login_required
@admin_required
def admin_view_assessment(assessment_id):
    assessment = Assessment.objects.get_or_404(id=assessment_id)
    return render_template('admin/assessments/view.html', assessment=assessment)

@admin_bp.route('/reports')
@login_required
@admin_required
def admin_reports():
    # Generate report data
    # This is a simplified example - you would typically generate more detailed reports
    report_data = {
        'total_assessments': Assessment.objects.count(),
        'avg_score': Assessment.objects.average('overall_score') or 0,
        'completion_rate': 0,  # Calculate based on your business logic
        'by_month': [],  # Add monthly statistics
        'by_examiner': []  # Add examiner statistics
    }
    
    return render_template('admin/reports/index.html', report_data=report_data)
