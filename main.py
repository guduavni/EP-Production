from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from models import Assessment, TestScript, MediaFile, Report
from datetime import datetime
import os
from werkzeug.utils import secure_filename

main_bp = Blueprint('main', __name__)

# Test route to verify the application is working
@main_bp.route('/test')
def test():
    return "The application is running!"

@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('index.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    # Get user-specific data for dashboard
    if current_user.role == 'candidate':
        assessments = Assessment.objects(candidate=current_user).order_by('-start_time')
        return render_template('dashboard/candidate.html', assessments=assessments)
    elif current_user.role == 'examiner':
        pending_assessments = Assessment.objects(examiner=current_user, status='in_progress')
        return render_template('dashboard/examiner.html', pending_assessments=pending_assessments)
    else:
        return redirect(url_for('admin.index'))

@main_bp.route('/assessment/<assessment_id>')
@login_required
def view_assessment(assessment_id):
    assessment = Assessment.objects.get_or_404(id=assessment_id)
    # Check if user has permission to view this assessment
    if current_user.role == 'candidate' and str(assessment.candidate.id) != str(current_user.id):
        flash('You do not have permission to view this assessment', 'danger')
        return redirect(url_for('main.dashboard'))
    return render_template('assessment/view.html', assessment=assessment)

@main_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        # Update profile logic here
        current_user.first_name = request.form.get('first_name', current_user.first_name)
        current_user.last_name = request.form.get('last_name', current_user.last_name)
        current_user.email = request.form.get('email', current_user.email)
        current_user.phone = request.form.get('phone', current_user.phone)
        
        # Handle password change if provided
        if request.form.get('new_password'):
            if check_password_hash(current_user.password_hash, request.form.get('current_password')):
                current_user.password_hash = generate_password_hash(request.form.get('new_password'))
            else:
                flash('Current password is incorrect', 'danger')
                return redirect(url_for('main.profile'))
        
        current_user.save()
        flash('Profile updated successfully', 'success')
        return redirect(url_for('main.profile'))
    
    return render_template('profile.html')
