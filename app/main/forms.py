"""
Forms for the main blueprint.

This module contains all the forms used in the main blueprint.
"""
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, Email

class ContactForm(FlaskForm):
    """Form for the contact page."""
    name = StringField('Name', validators=[DataRequired(), Length(max=100)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    subject = StringField('Subject', validators=[DataRequired(), Length(max=200)])
    message = TextAreaField('Message', validators=[DataRequired(), Length(max=2000)])
    submit = SubmitField('Send Message')

class SearchForm(FlaskForm):
    """Form for the search functionality."""
    query = StringField('Search', validators=[DataRequired(), Length(max=100)])
    submit = SubmitField('Search')

class ProfileForm(FlaskForm):
    """Form for editing user profile."""
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=50)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    phone = StringField('Phone', validators=[Optional(), Length(max=20)])
    company = StringField('Company', validators=[Optional(), Length(max=100)])
    job_title = StringField('Job Title', validators=[Optional(), Length(max=100)])
    bio = TextAreaField('Bio', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Update Profile')

class NotificationSettingsForm(FlaskForm):
    """Form for notification settings."""
    email_notifications = BooleanField('Email Notifications', default=True)
    push_notifications = BooleanField('Push Notifications', default=True)
    assessment_reminders = BooleanField('Assessment Reminders', default=True)
    results_notifications = BooleanField('Results Notifications', default=True)
    submit = SubmitField('Save Settings')
