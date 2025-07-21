from flask import redirect, url_for, flash
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.mongoengine import ModelView
from flask_admin.form import Select2Widget
from flask_login import current_user, login_required
from wtforms import Form, StringField, SelectField, TextAreaField, IntegerField, validators
from wtforms.validators import DataRequired, Optional, NumberRange
from models import User, Assessment, Question, AudioRecording

class AdminModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == 'admin' and current_user.status == 'active'

    def inaccessible_callback(self, name, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        flash('You do not have permission to access this page.', 'error')
        return redirect(url_for('index'))

class UserView(AdminModelView):
    column_list = ('user_id', 'name', 'email', 'role', 'status', 'created_at')
    column_searchable_list = ('user_id', 'name', 'email')
    column_filters = ('role', 'status')
    column_sortable_list = ('created_at', 'name')
    
    form_columns = ('user_id', 'name', 'email', 'role', 'status')
    form_overrides = {
        'role': SelectField,
        'status': SelectField
    }
    form_args = {
        'role': {
            'choices': [
                ('admin', 'Admin'),
                ('examiner', 'Examiner'),
                ('candidate', 'Candidate')
            ]
        },
        'status': {
            'choices': [
                ('active', 'Active'),
                ('inactive', 'Inactive'),
                ('suspended', 'Suspended')
            ]
        }
    }

class AssessmentView(AdminModelView):
    column_list = ('title', 'user', 'status', 'start_time', 'end_time', 'overall_score')
    column_searchable_list = ('title', 'user')
    column_filters = ('status', 'overall_score')
    column_sortable_list = ('start_time', 'end_time', 'overall_score')
    
    form_columns = ('title', 'user', 'examiner', 'status', 'start_time', 'end_time', 'overall_score')
    form_overrides = {
        'status': SelectField
    }
    form_args = {
        'status': {
            'choices': [
                ('scheduled', 'Scheduled'),
                ('in_progress', 'In Progress'),
                ('completed', 'Completed'),
                ('evaluated', 'Evaluated'),
                ('cancelled', 'Cancelled')
            ]
        }
    }

class QuestionView(AdminModelView):
    column_list = ('text', 'category', 'difficulty')
    column_searchable_list = ('text', 'category')
    column_filters = ('category', 'difficulty')
    
    form_columns = ('text', 'category', 'difficulty')
    form_overrides = {
        'category': SelectField
    }
    form_args = {
        'category': {
            'choices': [
                ('introduction', 'Introduction'),
                ('picture', 'Picture Description'),
                ('scenario', 'Aviation Scenario')
            ]
        },
        'difficulty': {
            'validators': [NumberRange(min=1, max=6)]
        }
    }

class AudioRecordingView(AdminModelView):
    column_list = ('assessment', 'duration', 'created_at')
    column_searchable_list = ('assessment',)
    column_filters = ('created_at',)
    column_sortable_list = ('created_at', 'duration')

class MyAdminIndexView(AdminIndexView):
    @expose('/')
    @login_required
    def index(self):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if current_user.role != 'admin' or current_user.status != 'active':
            flash('You do not have permission to access the admin panel.', 'error')
            return redirect(url_for('index'))
        return super(MyAdminIndexView, self).index()

def init_admin(app):
    admin = Admin(
        app,
        name='EP Simulator Admin',
        template_mode='bootstrap4',
        index_view=MyAdminIndexView(
            name='Dashboard',
            template='admin/index.html',
            url='/admin'
        )
    )
    
    # Add views with categories
    admin.add_view(UserView(User, name='Users', category='User Management'))
    admin.add_view(AssessmentView(Assessment, name='Assessments', category='Assessments'))
    admin.add_view(QuestionView(Question, name='Questions', category='Content'))
    admin.add_view(AudioRecordingView(AudioRecording, name='Recordings', category='Content'))
    
    return admin
