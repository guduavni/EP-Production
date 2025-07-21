from flask import redirect, url_for, flash, request
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.mongoengine import ModelView
from flask_login import current_user, login_required, logout_user
from functools import wraps
from models import User, TestScript, Assessment, MediaFile, Report, ExamResult

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Access denied: Admin privileges required', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

class AdminModelView(ModelView):
    """Base admin view with common settings"""
    
    # Enable RTL support
    extra_css = [
        'https://cdn.rtlcss.com/bootstrap/4.5.3/css/bootstrap.min.css',
        'https://cdnjs.cloudflare.com/ajax/libs/bootstrap-rtl/3.4.0/css/bootstrap-rtl.min.css',
        '/static/css/admin-rtl.css'  # Custom RTL overrides
    ]
    
    # Add Font Awesome
    extra_js = [
        'https://kit.fontawesome.com/a076d05399.js'
    ]
    
    # Set page size for lists
    page_size = 20
    
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == 'admin'
    
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login', next=request.url))
    
    def get_list_columns(self):
        # Override to set RTL direction for list view
        columns = super().get_list_columns()
        for column in columns:
            if hasattr(column, 'cell_formatter'):
                column.cell_formatter = self._rtl_cell_formatter(column.cell_formatter)
        return columns
    
    def _rtl_cell_formatter(self, formatter):
        # Add RTL support to cell formatters
        if formatter:
            def wrapped_formatter(view, context, model, name):
                result = formatter(view, context, model, name)
                if result and isinstance(result, str) and not result.startswith('<'):
                    return f'<div style="text-align: right; direction: rtl;">{result}</div>'
                return result or ''
            return wrapped_formatter
        return lambda v,c,m,n: ''
    
    def create_model(self, form):
        # Add created_by field automatically
        try:
            if hasattr(form, '_fields') and 'created_by' in form._fields:
                form.created_by.data = current_user
            return super().create_model(form)
        except Exception as ex:
            flash(f'Error creating record: {str(ex)}', 'error')
            return False
    
    def update_model(self, form, model):
        # Add updated_by field automatically
        try:
            if hasattr(model, 'updated_at'):
                model.updated_at = datetime.utcnow()
            if hasattr(model, 'updated_by'):
                model.updated_by = current_user
            return super().update_model(form, model)
        except Exception as ex:
            flash(f'Error updating record: {str(ex)}', 'error')
            return False

class UserAdminView(AdminModelView):
    column_list = ('user_id', 'first_name', 'last_name', 'email', 'role', 'status', 'created_at')
    column_searchable_list = ('user_id', 'first_name', 'last_name', 'email')
    column_filters = ('role', 'status', 'created_at')
    form_excluded_columns = ('created_at', 'last_login')
    
    def on_model_change(self, form, model, is_created):
        if is_created:
            # Additional logic when creating a new user
            pass

class TestScriptAdminView(AdminModelView):
    column_list = ('script_id', 'title', 'difficulty', 'is_active', 'created_at')
    column_searchable_list = ('script_id', 'title', 'description')
    column_filters = ('difficulty', 'is_active', 'created_at')
    form_excluded_columns = ('created_at',)

class AssessmentAdminView(AdminModelView):
    column_list = ('id', 'candidate', 'examiner', 'status', 'start_time', 'overall_score')
    column_filters = ('status', 'start_time', 'overall_score')
    form_excluded_columns = ('recordings',)
    
    def on_model_change(self, form, model, is_created):
        if model.pronunciation and model.structure and model.vocabulary and model.fluency and model.comprehension:
            model.overall_score = model.calculate_overall()

class MediaFileAdminView(AdminModelView):
    column_list = ('file_id', 'filename', 'file_type', 'uploaded_by', 'uploaded_at', 'is_active')
    column_filters = ('file_type', 'is_active', 'uploaded_at')
    form_excluded_columns = ('uploaded_at',)

class ReportAdminView(AdminModelView):
    column_list = ('report_id', 'title', 'report_type', 'generated_by', 'generated_at')
    column_filters = ('report_type', 'generated_at')
    form_excluded_columns = ('generated_at',)

class ExamResultAdminView(AdminModelView):
    column_list = ('exam_id', 'first_name', 'last_name', 'user_id', 'exam_date', 'final_score')
    column_searchable_list = ('exam_id', 'first_name', 'last_name', 'user_id')
    column_filters = ('exam_date', 'final_score')
    form_excluded_columns = ('created_at', 'updated_at')
    
    def _format_transcript(view, context, model, name):
        if model.test_transcript:
            return f'<a href="#" onclick="showTranscript(\'{model.id}\')" class="btn btn-sm btn-info">צפה בתמליל</a>'
        return ''
    
    def _format_image(view, context, model, name):
        if model.test_image:
            return f'<a href="#" onclick="showImage(\'{model.test_image.file_id}\')" class="btn btn-sm btn-success">צפה בתמונה</a>'
        return ''
    
    def _format_script(view, context, model, name):
        if model.test_script:
            return f'<a href="#" onclick="showScript(\'{model.test_script.script_id}\')" class="btn btn-sm btn-primary">צפה בתסריט</a>'
        return ''
    
    column_formatters = {
        'test_transcript': _format_transcript,
        'test_image': _format_image,
        'test_script': _format_script
    }
    
    column_labels = {
        'exam_id': 'מספר מבחן',
        'first_name': 'שם פרטי',
        'last_name': 'שם משפחה',
        'user_id': 'ת.ז. מערכת',
        'join_date': 'תאריך קליטה',
        'exam_date': 'תאריך מבחן',
        'final_score': 'ציון סופי',
        'test_transcript': 'תמליל מבחן',
        'test_image': 'תמונה',
        'test_script': 'תסריט'
    }

class AdminDashboard(AdminIndexView):
    """Custom admin dashboard view with statistics and recent exams"""
    
    def is_visible(self):
        # This view should not appear in the menu
        return False
    
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == 'admin'
    
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login', next=request.url))
    
    @expose('/')
    def index(self):
        """Render the admin dashboard with statistics and recent exams"""
        # Get statistics
        stats = {
            'user_count': User.objects.count(),
            'exam_count': ExamResult.objects.count(),
            'script_count': TestScript.objects.count(),
            'avg_score': 0
        }
        return self.render('admin/dashboard.html', stats=stats)

def setup_admin(app):
    admin = Admin(
        app, 
        name='EP-Simulator Admin', 
        template_mode='bootstrap4', 
        index_view=AdminDashboard(),
        base_template='admin_base.html'
    )
    
    # Add admin views with Hebrew names and proper categories
    admin.add_view(UserAdminView(
        User, 
        name='משתמשים', 
        category='ניהול',
        endpoint='user'
    ))
    
    admin.add_view(TestScriptAdminView(
        TestScript, 
        name='תסריטי מבחן', 
        category='תוכן',
        endpoint='testscript'
    ))
    
    admin.add_view(AssessmentAdminView(
        Assessment, 
        name='הערכות', 
        category='ניהול',
        endpoint='assessment'
    ))
    
    admin.add_view(MediaFileAdminView(
        MediaFile, 
        name='קבצי מדיה', 
        category='תוכן',
        endpoint='mediafile'
    ))
    
    admin.add_view(ReportAdminView(
        Report, 
        name='דוחות', 
        category='ניהול',
        endpoint='report'
    ))
    
    admin.add_view(ExamResultAdminView(
        ExamResult, 
        name='תוצאות מבחנים', 
        category='ניהול',
        endpoint='examresult'
    ))
    
    return admin
