from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from datetime import datetime
import logging

# Import forms and models
from app.auth.forms import LoginForm
from app.models.user import User

# Create blueprint
auth_bp = Blueprint('auth', __name__)

# Set up logging
logger = logging.getLogger(__name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
@auth_bp.route('/')  # הוספת נתיב שורש שיציג את דף ההתחברות
def login():
    """Handle user login."""
    logger.info("Login attempt")
    
    if current_user.is_authenticated:
        logger.debug("User already authenticated, redirecting to dashboard")
        return redirect(url_for('main.dashboard'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        logger.debug(f"Login form submitted by {form.email.data}")
        user = User.objects(email=form.email.data).first()
        
        if user is None or not user.check_password(form.password.data):
            logger.warning(f"Invalid login attempt for email: {form.email.data}")
            flash('Invalid email or password', 'danger')
            return redirect(url_for('auth.login'))
            
        if not user.is_active:
            logger.warning(f"Login attempt for inactive user: {user.email}")
            flash('Your account is not active. Please contact an administrator.', 'warning')
            return redirect(url_for('auth.login'))
            
        # Log the user in
        login_user(user, remember=form.remember_me.data)
        logger.info(f"User {user.email} logged in successfully")
        
        # Redirect to the next page if it exists
        next_page = request.args.get('next')
        return redirect(next_page or url_for('main.dashboard'))
    
    return render_template('auth/login.html', title='Login', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    from ..forms import ResetPasswordRequestForm
    form = ResetPasswordRequestForm()
    
    if form.validate_on_submit():
        user = User.objects(email=form.email.data).first()
        if user:
            # In a real app, you would send a password reset email here
            # For now, we'll just show a message
            flash('Check your email for the instructions to reset your password', 'info')
            return redirect(url_for('auth.login'))
        else:
            flash('No account found with that email address.', 'warning')
    
    return render_template('auth/reset_password.html', title='Reset Password', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        
        # Check if user already exists
        if User.objects(email=email).first():
            flash('Email address already exists', 'danger')
            return redirect(url_for('auth.register'))
            
        # Create new user
        try:
            new_user = User(
                email=email,
                first_name=first_name,
                last_name=last_name,
                role='candidate'  # Default role
            )
            new_user.password = password  # This will hash the password
            new_user.save()
            
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            current_app.logger.error(f'Error creating user: {str(e)}')
            flash('An error occurred during registration. Please try again.', 'danger')
    
    return render_template('auth/register.html')
