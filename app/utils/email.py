"""
Email sending utilities.
"""
from flask import current_app, render_template
from flask_mail import Message
from app.extensions import mail

def send_email(to, subject, template, **kwargs):
    """
    Send an email using the Flask-Mail extension.
    
    Args:
        to (str): Recipient email address
        subject (str): Email subject
        template (str): Template name without extension
        **kwargs: Variables to pass to the template
    """
    msg = Message(
        subject=subject,
        sender=current_app.config['MAIL_DEFAULT_SENDER'],
        recipients=[to]
    )
    
    # Render both HTML and plain text versions
    msg.html = render_template(f'email/{template}.html', **kwargs)
    msg.body = render_template(f'email/{template}.txt', **kwargs)
    
    try:
        mail.send(msg)
        current_app.logger.info(f'Email sent to {to}')
        return True
    except Exception as e:
        current_app.logger.error(f'Failed to send email to {to}: {str(e)}')
        return False

def send_password_reset_email(user):
    """
    Send a password reset email to the user.
    
    Args:
        user (User): User instance
    """
    token = user.get_reset_password_token()
    send_email(
        to=user.email,
        subject='Reset Your Password',
        template='reset_password',
        user=user,
        token=token
    )

def send_email_verification(user):
    """
    Send an email verification email to the user.
    
    Args:
        user (User): User instance
    """
    token = user.generate_confirmation_token()
    confirm_url = f"{current_app.config['BASE_URL']}/auth/confirm/{token}"
    send_email(
        to=user.email,
        subject='Confirm Your Email',
        template='confirm_email',
        user=user,
        confirm_url=confirm_url
    )

def send_welcome_email(user):
    """
    Send a welcome email to a new user.
    
    Args:
        user (User): User instance
    """
    send_email(
        to=user.email,
        subject='Welcome to EP-Simulator',
        template='welcome',
        user=user
    )

def send_assessment_notification(assessment):
    """
    Send a notification about a new assessment.
    
    Args:
        assessment (Assessment): Assessment instance
    """
    if assessment.examiner and assessment.examiner.email:
        send_email(
            to=assessment.examiner.email,
            subject=f'New Assessment Assigned: {assessment.title}',
            template='new_assessment',
            assessment=assessment
        )
