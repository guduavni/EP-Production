from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from functools import wraps
from datetime import datetime

# Local imports
from ..extensions import db, login_manager
from ..models.user import User
from ..utils.email import send_email
from .forms import LoginForm, RegistrationForm, ResetPasswordRequestForm, ResetPasswordForm, EditProfileForm

# Create authentication blueprint
auth_bp = Blueprint('auth', __name__)

# Export the blueprint as 'bp' for compatibility
bp = auth_bp

def generate_confirmation_token(email):
    """Generate a confirmation token for email verification."""
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(email, salt=current_app.config['SECURITY_PASSWORD_SALT'])

def confirm_token(token, expiration=3600):
    """Verify the confirmation token."""
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = serializer.loads(
            token,
            salt=current_app.config['SECURITY_PASSWORD_SALT'],
            max_age=expiration
        )
        return email
    except (SignatureExpired, BadSignature):
        return False

def admin_required(f):
    """Decorator to ensure the user has admin privileges."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You do not have permission to access this page.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def examiner_required(f):
    """Decorator to ensure the user has examiner or admin privileges."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not (current_user.is_examiner or current_user.is_admin):
            flash('Examiner access required.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login."""
    try:
        return User.objects.get(id=user_id)
    except:
        return None

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated and current_user.status == 'active':
        if current_user.role == 'admin':
            return redirect(url_for('admin.index'))
        return redirect(url_for('index'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        remember = form.remember_me.data
        
        user = User.objects(email=email).first()
        
        if not user or not check_password_hash(user.password, password):
            flash('Invalid email or password. Please try again.', 'error')
            return redirect(url_for('auth.login'))
        
        if user.status != 'active':
            flash('Your account is not active. Please contact an administrator.', 'error')
            return redirect(url_for('auth.login'))
            
        login_user(user, remember=remember)
        next_page = request.args.get('next')
        
        if user.role == 'admin':
            return redirect(next_page or url_for('admin.index'))
        return redirect(next_page or url_for('index'))
        
    from datetime import datetime
    return render_template('auth/login.html', 
                        title='Login', 
                        form=form,
                        now=datetime.utcnow())

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    form = RegistrationForm()
    if form.validate_on_submit():
        # Check if user already exists
        user = User.objects(email=form.email.data).first()
        if user:
            flash('Email already registered. Please use a different email.', 'danger')
            return redirect(url_for('auth.register'))
            
        # Create new user
        new_user = User(
            email=form.email.data,
            name=form.name.data,  # Using name field instead of first_name/last_name
            password=generate_password_hash(form.password.data),
            is_active=True  # Set to False if email confirmation is required
        )
        
        # Save the user
        new_user.save()
        
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
        
    from datetime import datetime
    return render_template('auth/register.html', 
                         title='Register', 
                         form=form,
                         now=datetime.utcnow())

@auth_bp.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.objects(email=form.email.data).first()
        if user:
            # Generate reset token
            token = generate_confirmation_token(user.email)
            reset_url = url_for('auth.reset_password', token=token, _external=True)
            
            # Send email with reset link
            send_email(
                'Reset Your Password',
                sender=current_app.config['MAIL_DEFAULT_SENDER'],
                recipients=[user.email],
                text_body=render_template('email/reset_password.txt',
                                       user=user, reset_url=reset_url),
                html_body=render_template('email/reset_password.html',
                                       user=user, reset_url=reset_url)
            )
        
        flash('Check your email for the instructions to reset your password', 'info')
        return redirect(url_for('auth.login'))
    
    from datetime import datetime
    return render_template('auth/reset_password_request.html',
                         title='Reset Password', 
                         form=form,
                         now=datetime.utcnow())

@auth_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    email = confirm_token(token)
    if not email:
        flash('The reset link is invalid or has expired.', 'warning')
        return redirect(url_for('auth.login'))
    
    user = User.objects(email=email).first()
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('auth.login'))
    
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.password = generate_password_hash(form.password.data)
        user.save()
        
        flash('Your password has been reset. You can now log in with your new password.', 'success')
        return redirect(url_for('auth.login'))
    
    from datetime import datetime
    return render_template('auth/reset_password.html', 
                         form=form,
                         now=datetime.utcnow())

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('auth.login'))

def init_auth(app):
    # Initialize login manager
    login_manager.init_app(app)
    
    # Register the auth blueprint
    app.register_blueprint(auth, url_prefix='')
    
    # Create admin user if it doesn't exist
    with app.app_context():
        create_admin_user()
    
    return login_manager
