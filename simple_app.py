"""
EP-Simulator - Simple Application

A streamlined version of the EP-Simulator application for testing and development.
"""
import os
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, send_file
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_bootstrap import Bootstrap4
from flask_mongoengine import MongoEngine
from flask_wtf import FlaskForm
from mongoengine import connect, DoesNotExist
from datetime import datetime
import os
from models import User, ExamResult, MediaFile, TestScript
from app.auth.forms import LoginForm, RegistrationForm
from io import BytesIO
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import DataRequired, Email, Length
from werkzeug.security import generate_password_hash, check_password_hash

# Initialize extensions
db = MongoEngine()
login_manager = LoginManager()

# Forms
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Basic configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'dev-key-please-change-in-production'
    
    # Disconnect any existing connections
    from mongoengine import disconnect
    disconnect()
    
    # Configure MongoDB
    app.config['MONGODB_SETTINGS'] = {
        'db': 'ep_simulator',
        'host': 'mongodb://localhost:27017/ep_simulator',
        'alias': 'default',
        'connect': True
    }
    
    # Create static folder if it doesn't exist
    static_folder = os.path.join(app.root_path, 'static')
    if not os.path.exists(static_folder):
        os.makedirs(static_folder)
    
    # Create CSS folder if it doesn't exist
    css_folder = os.path.join(static_folder, 'css')
    if not os.path.exists(css_folder):
        os.makedirs(css_folder)
    
    # Initialize Flask-Admin
    from admin_views import setup_admin
    admin = setup_admin(app)
    
    # Register blueprints if any
    # from .blueprints import some_blueprint
    # app.register_blueprint(some_blueprint)
    
    # Ensure the admin template folder is in the template search path
    admin.template_folder = 'templates'
    
    # Initialize extensions
    try:
        db.init_app(app)
        # Force connection
        with app.app_context():
            from mongoengine.connection import get_db
            get_db('default')
    except Exception as e:
        print(f"Error initializing database: {str(e)}")
        raise
        
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # User loader function
    @login_manager.user_loader
    def load_user(user_id):
        try:
            return User.objects.get(id=user_id)
        except:
            return None
    
    # Routes
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        return render_template('index.html')
    
    @app.route('/dashboard')
    @login_required
    def dashboard():
        # Get statistics
        from models import User, ExamResult, TestScript
        
        stats = {
            'user_count': User.objects.count(),
            'exam_count': ExamResult.objects.count(),
            'script_count': TestScript.objects.count(),
            'avg_score': 0
        }
        
        # Calculate average score if there are exams
        if stats['exam_count'] > 0:
            pipeline = [
                {'$group': {
                    '_id': None,
                    'avg_score': {'$avg': '$final_score'}
                }}
            ]
            result = list(ExamResult.objects.aggregate(*pipeline))
            if result:
                stats['avg_score'] = round(result[0]['avg_score'], 1)
        
        # Get recent exams
        recent_exams = ExamResult.objects.order_by('-exam_date').limit(5)
        
        return render_template(
            'dashboard.html',
            title='Dashboard',
            stats=stats,
            recent_exams=recent_exams
        )

    # API Endpoints for Admin
    @app.route('/api/exam/<exam_id>/transcript')
    @login_required
    def get_exam_transcript(exam_id):
        try:
            exam = ExamResult.objects.get(id=exam_id)
            return jsonify({
                'success': True,
                'transcript': exam.test_transcript or ''
            })
        except DoesNotExist:
            return jsonify({
                'success': False,
                'message': 'Exam not found'
            }), 404
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 500

    @app.route('/api/media/<file_id>/view')
    @login_required
    def view_media(file_id):
        try:
            media = MediaFile.objects.get(file_id=file_id)
            # Assuming file_path is the path to the actual file
            return send_file(media.file_path)
        except DoesNotExist:
            return jsonify({
                'success': False,
                'message': 'Media file not found'
            }), 404
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 500

    @app.route('/api/script/<script_id>')
    @login_required
    def get_script(script_id):
        try:
            script = TestScript.objects.get(script_id=script_id)
            return jsonify({
                'success': True,
                'script': {
                    'id': str(script.id),
                    'script_id': script.script_id,
                    'title': script.title,
                    'content': script.content,
                    'difficulty': script.difficulty,
                    'created_at': script.created_at.isoformat()
                }
            })
        except DoesNotExist:
            return jsonify({
                'success': False,
                'message': 'Script not found'
            }), 404
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 500

    # Auth routes
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        # Ensure database connection is properly handled
        from mongoengine import connect, disconnect
        
        # Disconnect any existing connection
        disconnect('default')
        
        try:
            # Reconnect with the correct settings
            connect('ep_simulator', 
                   host='mongodb://localhost:27017/ep_simulator', 
                   alias='default')
            
            if current_user.is_authenticated:
                print("User is already authenticated, redirecting to dashboard")
                return redirect(url_for('dashboard'))
                
            form = LoginForm()
            if form.validate_on_submit():
                print(f"Login attempt for email: {form.email.data}")
                
                try:
                    # Try to find the user
                    user = User.objects(email=form.email.data).first()
                    
                    if user:
                        print(f"User found: {user.email}")
                        print(f"User status: {user.status}")
                        
                        if user.verify_password(form.password.data):
                            print("Password verification: SUCCESS")
                            if user.status != 'active':
                                print(f"Login failed: User status is {user.status}")
                                flash('Your account is not active. Please contact support.', 'danger')
                            else:
                                login_user(user, remember=form.remember_me.data)
                                next_page = request.args.get('next')
                                print(f"Login successful, redirecting to: {next_page or 'dashboard'}")
                                flash('You have been logged in!', 'success')
                                return redirect(next_page or url_for('dashboard'))
                        else:
                            print("Password verification: FAILED")
                            print("Login failed: Incorrect password")
                            flash('Incorrect password. Please try again.', 'danger')
                    else:
                        print("No user found with this email")
                        flash('No account found with this email address.', 'danger')
                        
                except Exception as e:
                    print(f"Error during login: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    flash('An error occurred during login. Please try again.', 'danger')
            
            return render_template('login.html', title='Login', form=form)
            
        except Exception as e:
            print(f"Database connection error: {str(e)}")
            import traceback
            traceback.print_exc()
            flash('Could not connect to the database. Please try again later.', 'danger')
            return render_template('login.html', title='Login', form=form)
        
        return render_template('login.html', title='Login', form=form)
    
    @app.route('/logout')
    def logout():
        logout_user()
        flash('You have been logged out.', 'info')
        return redirect(url_for('index'))
    
    @app.route('/register')
    def register():
        return 'Registration page - Coming soon! <a href="/">Home</a>'
    
    @app.route('/forgot-password')
    def forgot_password():
        return 'Forgot password page - Coming soon! <a href="/">Home</a>'
    
    @app.route('/profile')
    @login_required
    def profile():
        return f'<h1>Profile Page</h1><p>Email: {current_user.email}</p><a href="/">Home</a> <a href="/logout">Logout</a>'
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return render_template('500.html'), 500
    
    return app
