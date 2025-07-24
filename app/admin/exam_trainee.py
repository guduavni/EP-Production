"""
Exam Trainees Management

This module handles the management of exam trainees.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from ..models.exam_trainee import ExamTrainee
from ..forms.exam_trainee import ExamTraineeForm
from ..utils.decorators import admin_required
from datetime import datetime
import math
from mongoengine.queryset.visitor import Q

# Create blueprint
exam_trainee_bp = Blueprint('exam_trainee', __name__, url_prefix='/admin/exam-trainees')

@exam_trainee_bp.route('/')
@login_required
@admin_required
def list_trainees():
    """List all exam trainees with search and filters."""
    search = request.args.get('search', '')
    status = request.args.get('status', '')
    
    query = {}
    
    # Apply search filter
    if search:
        search_terms = [
            Q(first_name__icontains=search),
            Q(last_name__icontains=search),
            Q(unique_id__iexact=search.upper())
        ]
        query['__raw__'] = {'$or': [term.to_query(ExamTrainee) for term in search_terms]}
    
    # Apply status filter
    if status in ['registered', 'in_progress', 'completed']:
        query['status'] = status
    
    # Get all matching trainees
    trainees = ExamTrainee.objects(**query).order_by('-registration_date')
    
    return render_template('admin/exam_trainee/list.html',
                         trainees=trainees,
                         search=search,
                         status=status)

@exam_trainee_bp.route('/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_trainee():
    """Add a new exam trainee."""
    form = ExamTraineeForm()
    
    if form.validate_on_submit():
        try:
            trainee = ExamTrainee()
            form.populate_obj(trainee)
            trainee.save()
            flash('הנבחן נוסף בהצלחה', 'success')
            return redirect(url_for('admin.exam_trainee.view_trainee', trainee_id=trainee.unique_id))
        except Exception as e:
            flash(f'אירעה שגיאה בשמירת הנתונים: {str(e)}', 'error')
    
    return render_template('admin/exam_trainee/add.html', form=form)

@exam_trainee_bp.route('/<string:trainee_id>')
@login_required
@admin_required
def view_trainee(trainee_id):
    """View trainee details."""
    trainee = ExamTrainee.objects(unique_id=trainee_id).first()
    if not trainee:
        abort(404)
    return render_template('admin/exam_trainee/view.html', trainee=trainee)

@exam_trainee_bp.route('/delete/<trainee_id>', methods=['POST'])
@login_required
@admin_required
def delete_trainee(trainee_id):
    """Delete a trainee."""
    trainee = ExamTrainee.objects(unique_id=trainee_id).first()
    if not trainee:
        flash('הנבחן לא נמצא', 'error')
        return redirect(url_for('admin.exam_trainee.list_trainees'))
        
    try:
        trainee.delete()
        flash('הנבחן נמחק בהצלחה', 'success')
    except Exception as e:
        flash(f'אירעה שגיאה במחיקת הנבחן: {str(e)}', 'error')
        
    return redirect(url_for('admin.exam_trainee.list_trainees'))

@exam_trainee_bp.route('/edit/<trainee_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_trainee(trainee_id):
    """Edit trainee details."""
    trainee = ExamTrainee.objects(unique_id=trainee_id).first()
    if not trainee:
        flash('הנבחן לא נמצא', 'error')
        return redirect(url_for('admin.exam_trainee.list_trainees'))
        
    form = ExamTraineeForm(obj=trainee)
    
    if form.validate_on_submit():
        try:
            form.populate_obj(trainee)
            trainee.updated_at = datetime.utcnow()
            trainee.save()
            flash('פרטי הנבחן עודכנו בהצלחה', 'success')
            return redirect(url_for('admin.exam_trainee.view_trainee', trainee_id=trainee_id))
        except Exception as e:
            flash(f'אירעה שגיאה בעדכון פרטי הנבחן: {str(e)}', 'error')
    
    return render_template('admin/exam_trainee/edit.html', 
                         form=form, 
                         trainee=trainee)

# Add more routes for exam stages, reports, etc.
