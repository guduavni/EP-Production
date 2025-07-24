"""
Exam Trainee Forms

This module contains forms for managing exam trainees.
"""
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, Optional, Email
from datetime import datetime

class ExamTraineeForm(FlaskForm):
    """Form for adding/editing exam trainees."""
    
    # Personal Information
    id_number = StringField('תעודת זהות', validators=[
        DataRequired(message='שדה חובה'),
        Length(min=6, max=6, message='יש להזין בדיוק 6 ספרות')
    ])
    
    first_name = StringField('שם פרטי', validators=[
        DataRequired(message='שדה חובה'),
        Length(max=100, message='עד 100 תווים')
    ])
    
    last_name = StringField('שם משפחה', validators=[
        DataRequired(message='שדה חובה'),
        Length(max=100, message='עד 100 תווים')
    ])
    
    email = StringField('אימייל', validators=[
        DataRequired(message='שדה חובה'),
        Length(max=255, message='עד 255 תווים'),
        Email(message='יש להזין כתובת אימייל תקינה')
    ])
    
    # Exam Details
    status = SelectField('סטטוס', choices=[
        ('registered', 'רשום'),
        ('in_progress', 'בתהליך מבחן'),
        ('completed', 'המבחן הושלם')
    ], validators=[DataRequired()])
    
    # Buttons
    submit = SubmitField('שמור')
    cancel = SubmitField('ביטול')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setup_form()
    
    def setup_form(self):
        """Configure form fields and labels."""
        # Set up any additional field configurations here
        pass
