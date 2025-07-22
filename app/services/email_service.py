from flask_mail import Message
from flask import current_app, render_template
from flask_mail import Mail
from threading import Thread

# Initialize Mail extension
mail = Mail()

def send_async_email(app, msg):
    """Send email asynchronously"""
    with app.app_context():
        try:
            mail.send(msg)
            current_app.logger.info(f"Email sent to {msg.recipients}")
        except Exception as e:
            current_app.logger.error(f"Failed to send email: {str(e)}")

def send_email(subject, recipients, template=None, **template_kwargs):
    """Send an email using a template if provided"""
    app = current_app._get_current_object()
    
    # Create message
    msg = Message(
        subject=subject,
        recipients=recipients if isinstance(recipients, list) else [recipients],
        sender=app.config.get('MAIL_DEFAULT_SENDER')
    )
    
    # If template is provided, render it
    if template:
        msg.html = render_template(f'emails/{template}.html', **template_kwargs)
    
    # Send email in background
    if not app.testing:  # Don't send emails during tests
        Thread(target=send_async_email, args=(app, msg)).start()
    
    return msg

def send_welcome_email(user):
    """Send welcome email to new user"""
    return send_email(
        subject="ברוכים הבאים למערכת ההדרכה",
        recipients=[user.email],
        template='welcome',
        user=user
    )

def send_password_reset_email(user, token):
    """Send password reset email"""
    reset_url = f"{current_app.config.get('FRONTEND_URL', '')}/reset-password/{token}"
    return send_email(
        subject="איפוס סיסמה",
        recipients=[user.email],
        template='reset_password',
        user=user,
        reset_url=reset_url
    )

def send_trainee_registered_email(trainee):
    """Send email when a new trainee is registered"""
    return send_email(
        subject="נרשם חניך חדש למערכת",
        recipients=[trainee.email],
        template='trainee_registered',
        trainee=trainee
    )
