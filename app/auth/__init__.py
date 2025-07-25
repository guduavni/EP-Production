from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import login_user, logout_user, login_required, current_user
# Password hashing is now handled by the User model
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from functools import wraps
from datetime import datetime

# Local imports
from ..extensions import db, login_manager
from ..models.user import User
from ..models.exam_trainee import ExamTrainee
import random
import string
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
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.lower()
        password = form.password.data
        remember = form.remember_me.data
        
        user = User.objects(email=email).first()
        
        if not user or not user.check_password(password):
            flash('Invalid email or password. Please try again.', 'error')
            return redirect(url_for('auth.login'))
        
        if user.status != 'active':
            flash('Your account is not active. Please contact an administrator.', 'error')
            return redirect(url_for('auth.login'))
            
        login_user(user, remember=remember)
        next_page = request.args.get('next')
        
        if user.is_admin:
            return redirect(next_page or url_for('admin.index'))
        return redirect(next_page or url_for('main.index'))
        
    from datetime import datetime
    return render_template('auth/login.html', 
                        title='Login', 
                        form=form,
                        now=datetime.utcnow())

def json_response(success, message, status=200, **kwargs):
    """Helper function to create a JSON response."""
    response = {'success': success, 'message': message, **kwargs}
    return jsonify(response), status, {'Content-Type': 'application/json'}

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    # Check if user is already authenticated
    if current_user.is_authenticated:
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return json_response(False, 'You are already logged in.', 400)
        return redirect(url_for('main.index'))
    
    # Handle POST request
    if request.method == 'POST':
        # Check if we should return JSON (AJAX request or format=json parameter)
        is_ajax = (
            request.is_json or 
            request.headers.get('X-Requested-With') == 'XMLHttpRequest' or
            request.args.get('format') == 'json' or
            request.form.get('format') == 'json'
        )
        
        # Log form data for debugging
        current_app.logger.info(f'Registration form data: {request.form}')
        
        # Create form instance with request form data
        form = RegistrationForm(request.form)
        
        # Check if email already exists
        if User.objects(email=request.form.get('email')).first():
            error_msg = 'כתובת האימייל כבר קיימת במערכת. אנא השתמש בכתובת אימייל אחרת.'
            current_app.logger.warning(f'Registration failed - email already exists: {request.form.get("email")}')
            
            if is_ajax:
                return json_response(
                    False,
                    error_msg,
                    400,
                    field_errors={'email': [error_msg]}
                )
            
            flash(error_msg, 'danger')
            return redirect(url_for('auth.register'))
        
        # Check if name is provided
        if not request.form.get('name'):
            error_msg = 'יש להזין שם מלא.'
            if is_ajax:
                return json_response(
                    False,
                    error_msg,
                    400,
                    field_errors={'name': [error_msg]}
                )
            flash(error_msg, 'danger')
            return redirect(url_for('auth.register'))
        
        # Check password length
        password = request.form.get('password', '')
        if len(password) < 8:
            error_msg = 'הסיסמה חייבת להכיל לפחות 8 תווים.'
            if is_ajax:
                return json_response(
                    False,
                    error_msg,
                    400,
                    field_errors={'password': [error_msg]}
                )
            flash(error_msg, 'danger')
            return redirect(url_for('auth.register'))
            
        # Check if passwords match
        if password != request.form.get('password2'):
            error_msg = 'הסיסמאות אינן תואמות.'
            if is_ajax:
                return json_response(
                    False,
                    error_msg,
                    400,
                    field_errors={'password2': [error_msg]}
                )
            flash(error_msg, 'danger')
            return redirect(url_for('auth.register'))
        
        # Form validation passed, try to create user
        try:
            # Check if user already exists
            existing_user = User.objects(email=form.email.data).first()
            if existing_user:
                error_msg = 'Email already registered. Please use a different email.'
                current_app.logger.warning(f'Registration failed - email already exists: {form.email.data}')
                
                if is_ajax:
                    return json_response(
                        False, 
                        error_msg,
                        400,
                        field_errors={'email': [error_msg]}
                    )
                
                flash(error_msg, 'danger')
                return redirect(url_for('auth.register'))
            
            # Check if ID number already exists
            existing_id_user = User.objects(id_number=form.id_number.data).first()
            if existing_id_user:
                error_msg = 'מספר תעודת זהות זה כבר רשום במערכת.'
                if is_ajax:
                    return json_response(
                        False,
                        error_msg,
                        400,
                        field_errors={'id_number': [error_msg]}
                    )
                flash(error_msg, 'danger')
                return redirect(url_for('auth.register'))
            
            # Create new user with default role and status
            new_user = User(
                email=form.email.data,
                name=form.name.data,
                id_number=form.id_number.data,
                is_active=True,
                role='candidate',  # Default role for new users
                status='active'    # Default status for new users
            )
            new_user.set_password(form.password.data)
            new_user.save()
            
            current_app.logger.info(f'New user registered: {new_user.email} (ID: {new_user.id})')
            
            # Split full name into first and last name
            name_parts = form.name.data.strip().split(' ', 1)
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else ''
            
            # Create corresponding ExamTrainee record
            try:
                # Generate a unique 6-character ID
                unique_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
                
                # Check if unique_id already exists (unlikely but possible)
                while ExamTrainee.objects(unique_id=unique_id).first() is not None:
                    unique_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
                
                # Create the ExamTrainee record
                exam_trainee = ExamTrainee(
                    first_name=first_name,
                    last_name=last_name,
                    email=form.email.data,
                    unique_id=unique_id,
                    status='registered'
                )
                exam_trainee.save()
                
                current_app.logger.info(f'New ExamTrainee created for user {new_user.email} (ID: {exam_trainee.id})')
                
            except Exception as e:
                # If ExamTrainee creation fails, delete the user to maintain consistency
                new_user.delete()
                current_app.logger.error(f'Failed to create ExamTrainee: {str(e)}')
                raise Exception('Failed to create trainee record. Please try again.')
            
            # Get first 6 characters of user ID for display
            user_id_short = str(new_user.id)[:6]
            
            # Return success response with user ID
            if is_ajax:
                return json_response(
                    True, 
                    f'ההרשמה בוצעה בהצלחה!<br><br>מזהה משתמש: <strong>{user_id_short}</strong><br><br>לחץ OK כדי להמשיך לדף ההתחברות.',
                    user_id=user_id_short,
                    show_ok_button=True
                )
            
            flash(f'ההרשמה בוצעה בהצלחה! מזהה משתמש: {user_id_short}', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            error_type = type(e).__name__
            error_details = str(e)
            current_app.logger.error(f'Registration error [{error_type}]: {error_details}', exc_info=True)
            
            # Check for duplicate email error
            if 'duplicate key error' in error_details and 'email' in error_details:
                error_msg = 'כתובת האימייל כבר קיימת במערכת. אנא השתמש בכתובת אימייל אחרת.'
                if is_ajax:
                    return json_response(
                        False,
                        error_msg,
                        400,
                        field_errors={'email': [error_msg]}
                    )
                flash(error_msg, 'danger')
                return redirect(url_for('auth.register'))
                
            # Check for duplicate ID number error
            if 'duplicate key error' in error_details and 'id_number' in error_details:
                error_msg = 'מספר תעודת זהות זה כבר רשום במערכת.'
                if is_ajax:
                    return json_response(
                        False,
                        error_msg,
                        400,
                        field_errors={'id_number': [error_msg]}
                    )
                flash(error_msg, 'danger')
                return redirect(url_for('auth.register'))
                
            # Handle validation errors
            if hasattr(e, 'to_dict'):
                error_msg = 'שגיאת אימות נתונים. אנא בדוק את הפרטים שהזנת.'
                if is_ajax:
                    return json_response(
                        False,
                        error_msg,
                        400,
                        field_errors=e.to_dict()
                    )
                flash(error_msg, 'danger')
                return redirect(url_for('auth.register'))
            
            # Handle other errors
            error_msg = f'אירעה שגיאה בלתי צפויה במהלך ההרשמה. אנא נסה שוב. ({error_type}: {error_details})'
            
            if is_ajax:
                return json_response(
                    False, 
                    error_msg,
                    500,
                    error_type=error_type,
                    error_details=error_details
                )
            
            flash(error_msg, 'danger')
            return redirect(url_for('auth.register'))
    
    # Handle GET request
    return render_template('auth/register.html', 
                         title='Register', 
                         form=RegistrationForm(),
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
        user.set_password(form.password.data)
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
