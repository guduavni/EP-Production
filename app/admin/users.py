"""
User Management

This module handles the management of users in the admin panel.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from ..models.user import User
from ..extensions import db
from datetime import datetime

# Create blueprint
users_bp = Blueprint('users', __name__, url_prefix='/admin/users')

@users_bp.route('/')
@login_required
def list_users():
    """List users with search, filters, and pagination."""
    if not current_user.is_admin:
        flash('אין לך הרשאה לצפות בדף זה', 'danger')
        return redirect(url_for('main.index'))
    
    search = request.args.get('search', '')
    role = request.args.get('role', '')
    page = request.args.get('page', 1, type=int)
    per_page = 6  # Show 6 users per page
    
    query = {}
    
    # Apply search filter
    if search:
        # Create a regex pattern for case-insensitive search
        from bson.regex import Regex
        search_regex = Regex(f'.*{search}.*', 'i')
        
        # Search in name, email, or ID number
        query['$or'] = [
            {'name': search_regex},
            {'email': search_regex},
            {'id_number': search_regex}
        ]
    
    from mongoengine.queryset.visitor import Q
    
    # Start with an empty query that matches all documents
    final_query = Q()
    
    # Apply search filter if provided
    if search:
        search_terms = search.split()
        search_conditions = Q()
        
        for term in search_terms:
            if term:
                search_conditions &= (Q(name__icontains=term) |
                                   Q(email__icontains=term) |
                                   Q(id_number__icontains=term))
        
        if search_conditions:
            final_query &= search_conditions
    
    # Apply role filter if provided
    if role in ['admin', 'examiner', 'candidate']:
        final_query &= Q(role=role)
    
    # Convert to query dict if needed
    if final_query != Q():
        query = final_query
    
    # Get total count with current filters
    if isinstance(query, dict):
        total = User.objects(**query).count()
        users_query = User.objects(**query)
    else:
        total = User.objects(query).count()
        users_query = User.objects(query)
    
    # Calculate pagination and get paginated results
    skip = (page - 1) * per_page
    users = users_query.order_by('-created_at').skip(skip).limit(per_page)
    
    # Create pagination object for template
    pagination = {
        'page': page,
        'per_page': per_page,
        'total': total,
        'pages': (total + per_page - 1) // per_page if per_page > 0 else 1,
        'has_prev': page > 1,
        'has_next': skip + per_page < total,
        'prev_num': page - 1 if page > 1 else None,
        'next_num': page + 1 if skip + per_page < total else None,
        'first': skip + 1 if total > 0 else 0,
        'last': min(skip + per_page, total) if total > 0 else 0
    }
    
    return render_template('admin/users/list.html',
                         users=users,
                         pagination=pagination,
                         search=search,
                         role=role,
                         current_time=datetime.utcnow())

@users_bp.route('/<string:user_id>/toggle-status', methods=['POST'])
@login_required
def toggle_user_status(user_id):
    """Toggle user active status."""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'אין לך הרשאה לבצע פעולה זו'}), 403
    
    try:
        user = User.objects.get(id=user_id)
        if user == current_user:
            return jsonify({'success': False, 'message': 'לא ניתן לשנות את הסטטוס של עצמך'}), 400
            
        user.is_active = not user.is_active
        user.save()
        
        return jsonify({
            'success': True, 
            'message': 'סטטוס המשתמש עודכן בהצלחה',
            'is_active': user.is_active
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'שגיאה: {str(e)}'}), 400

@users_bp.route('/<string:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    """Delete a user."""
    if not current_user.is_admin:
        flash('אין לך הרשאה לבצע פעולה זו', 'danger')
        return redirect(url_for('admin.users.list_users'))
    
    try:
        user = User.objects.get(id=user_id)
        if user == current_user:
            flash('לא ניתן למחוק את המשתמש הנוכחי', 'danger')
        else:
            user.delete()
            flash('המשתמש נמחק בהצלחה', 'success')
    except Exception as e:
        flash(f'אירעה שגיאה במחיקת המשתמש: {str(e)}', 'danger')
    
    return redirect(url_for('admin.users.list_users'))
