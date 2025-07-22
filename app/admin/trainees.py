"""
Trainee Management Module

This module handles all trainee management functionality for the admin interface.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from bson.objectid import ObjectId
import os
from datetime import datetime

# Create blueprint
trainee_bp = Blueprint('trainee', __name__, url_prefix='/admin/trainees')

@trainee_bp.before_request
@login_required
def require_admin():
    """Ensure user is an admin for all trainee routes."""
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('main.index'))

@trainee_bp.route('/')
def list_trainees():
    """List all trainees."""
    from ..models import get_model
    Trainee = get_model('Trainee')
    User = get_model('User')
    
    # Get filter parameters
    status = request.args.get('status', 'all')
    program = request.args.get('program', 'all')
    search = request.args.get('search', '').strip()
    
    # Build query
    query = {}
    if status != 'all':
        query['status'] = status
    if program != 'all':
        query['training_program'] = program
    
    # Get trainees with user information
    if Trainee:
        trainees = Trainee.objects(**query).order_by('-created_at')
        
        # Apply search filter if provided
        if search:
            # Get user IDs matching search
            users = User.objects(name__icontains=search)
            user_ids = [str(user.id) for user in users]
            trainees = trainees.filter(user__in=user_ids)
        
        # Get unique programs for filter
        programs = sorted(list(set(t.training_program for t in Trainee.objects.distinct('training_program') if t.training_program)))
    else:
        trainees = []
        programs = []
    
    return render_template('admin/trainees/list.html',
                         trainees=trainees,
                         status=status,
                         program=program,
                         search=search,
                         programs=programs)

@trainee_bp.route('/add', methods=['GET', 'POST'])
def add_trainee():
    """Add a new trainee."""
    from ..models import get_model
    User = get_model('User')
    
    if request.method == 'POST':
        try:
            # Get form data
            user_id = request.form.get('user_id')
            id_number = request.form.get('id_number')
            date_of_birth = datetime.strptime(request.form.get('date_of_birth'), '%Y-%m-%d')
            phone = request.form.get('phone')
            address = request.form.get('address')
            city = request.form.get('city')
            training_program = request.form.get('training_program')
            start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d')
            end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d') if request.form.get('end_date') else None
            status = request.form.get('status', 'active')
            emergency_contact_name = request.form.get('emergency_contact_name')
            emergency_contact_phone = request.form.get('emergency_contact_phone')
            emergency_contact_relation = request.form.get('emergency_contact_relation')
            
            # Create trainee
            Trainee = get_model('Trainee')
            trainee = Trainee(
                user=User.objects.get(id=user_id),
                id_number=id_number,
                date_of_birth=date_of_birth,
                phone=phone,
                address=address,
                city=city,
                training_program=training_program,
                start_date=start_date,
                end_date=end_date,
                status=status,
                emergency_contact_name=emergency_contact_name,
                emergency_contact_phone=emergency_contact_phone,
                emergency_contact_relation=emergency_contact_relation
            )
            
            # Handle file uploads
            if 'documents' in request.files:
                documents = []
                for file in request.files.getlist('documents'):
                    if file and file.filename != '':
                        filename = secure_filename(file.filename)
                        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], 'documents', filename)
                        os.makedirs(os.path.dirname(filepath), exist_ok=True)
                        file.save(filepath)
                        documents.append(f'documents/{filename}')
                trainee.documents = documents
            
            trainee.save()
            flash('Trainee added successfully!', 'success')
            return redirect(url_for('admin.trainee.view_trainee', trainee_id=str(trainee.id)))
            
        except Exception as e:
            flash(f'Error adding trainee: {str(e)}', 'danger')
    
    # Get users who are not already trainees
    existing_trainees = [str(t.user.id) for t in get_model('Trainee').objects.only('user')]
    users = User.objects(id__nin=existing_trainees)
    
    return render_template('admin/trainees/add.html', users=users)

@trainee_bp.route('/<trainee_id>')
def view_trainee(trainee_id):
    """View trainee details."""
    from ..models import get_model
    Trainee = get_model('Trainee')
    
    trainee = Trainee.objects.get_or_404(id=trainee_id)
    return render_template('admin/trainees/view.html', trainee=trainee)

@trainee_bp.route('/<trainee_id>/edit', methods=['GET', 'POST'])
def edit_trainee(trainee_id):
    """Edit trainee details."""
    from ..models import get_model
    Trainee = get_model('Trainee')
    
    trainee = Trainee.objects.get_or_404(id=trainee_id)
    
    if request.method == 'POST':
        try:
            # Update trainee data
            trainee.id_number = request.form.get('id_number', trainee.id_number)
            if request.form.get('date_of_birth'):
                trainee.date_of_birth = datetime.strptime(request.form.get('date_of_birth'), '%Y-%m-%d')
            trainee.phone = request.form.get('phone', trainee.phone)
            trainee.address = request.form.get('address', trainee.address)
            trainee.city = request.form.get('city', trainee.city)
            trainee.training_program = request.form.get('training_program', trainee.training_program)
            if request.form.get('start_date'):
                trainee.start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d')
            if request.form.get('end_date'):
                trainee.end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d')
            trainee.status = request.form.get('status', trainee.status)
            trainee.emergency_contact_name = request.form.get('emergency_contact_name', trainee.emergency_contact_name)
            trainee.emergency_contact_phone = request.form.get('emergency_contact_phone', trainee.emergency_contact_phone)
            trainee.emergency_contact_relation = request.form.get('emergency_contact_relation', trainee.emergency_contact_relation)
            
            # Handle file uploads
            if 'documents' in request.files:
                documents = list(trainee.documents or [])
                for file in request.files.getlist('documents'):
                    if file and file.filename != '':
                        filename = secure_filename(file.filename)
                        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], 'documents', filename)
                        os.makedirs(os.path.dirname(filepath), exist_ok=True)
                        file.save(filepath)
                        documents.append(f'documents/{filename}')
                trainee.documents = documents
            
            trainee.save()
            flash('Trainee updated successfully!', 'success')
            return redirect(url_for('admin.trainee.view_trainee', trainee_id=str(trainee.id)))
            
        except Exception as e:
            flash(f'Error updating trainee: {str(e)}', 'danger')
    
    return render_template('admin/trainees/edit.html', trainee=trainee)

@trainee_bp.route('/<trainee_id>/delete', methods=['POST'])
def delete_trainee(trainee_id):
    """Delete a trainee."""
    from ..models import get_model
    Trainee = get_model('Trainee')
    
    try:
        trainee = Trainee.objects.get_or_404(id=trainee_id)
        
        # Delete associated documents
        for doc in trainee.documents or []:
            try:
                os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], doc))
            except OSError:
                pass
        
        trainee.delete()
        flash('Trainee deleted successfully!', 'success')
        return redirect(url_for('admin.trainee.list_trainees'))
    except Exception as e:
        flash(f'Error deleting trainee: {str(e)}', 'danger')
        return redirect(url_for('admin.trainee.view_trainee', trainee_id=trainee_id))

@trainee_bp.route('/<trainee_id>/documents/delete', methods=['POST'])
def delete_document(trainee_id):
    """Delete a document from a trainee's record."""
    from ..models import get_model
    Trainee = get_model('Trainee')
    
    try:
        document_path = request.form.get('document_path')
        if not document_path:
            return jsonify({'success': False, 'message': 'No document path provided'}), 400
        
        trainee = Trainee.objects.get_or_404(id=trainee_id)
        
        # Remove document from trainee's documents
        if trainee.documents and document_path in trainee.documents:
            trainee.documents.remove(document_path)
            trainee.save()
            
            # Delete the actual file
            try:
                os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], document_path))
            except OSError:
                pass
            
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'message': 'Document not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@trainee_bp.route('/<trainee_id>/status', methods=['POST'])
def update_status(trainee_id):
    """Update trainee status."""
    from ..models import get_model
    Trainee = get_model('Trainee')
    
    try:
        status = request.form.get('status')
        if not status:
            return jsonify({'success': False, 'message': 'No status provided'}), 400
        
        trainee = Trainee.objects.get_or_404(id=trainee_id)
        trainee.status = status
        trainee.save()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
