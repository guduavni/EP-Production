"""
EP-Simulator Application Factory

This module contains the application factory function that creates and configures
the Flask application instance.
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, current_app, session
from flask_security import Security
from bson import ObjectId
from config import Config

# Import extensions
from .extensions import (
    db,
    login_manager, 
    mail, 
    cache, 
    limiter, 
    cors, 
    principal, 
    babel, 
    assets_env,
    init_extensions,
    configure_assets,
    csrf
)

# Import email service
from .services import email_service

# Import models will be done in create_app to ensure proper context

# Import blueprints
from .main import bp as main_bp
from .auth import bp as auth_bp
from .admin import bp as admin_bp

# Import test routes (only in development)
if os.environ.get('FLASK_ENV') == 'development':
    from .tests.test_email import test_bp

# Initialize Flask-Security with None for now, will be set in create_app
user_datastore = None
security = Security()

def create_app(config_name=None):
    """Create and configure the Flask application."""
    # Create the Flask application with explicit template folder
    template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
    app = Flask(__name__, template_folder=template_dir)
    
    # Configure CSRF protection
    app.config['WTF_CSRF_ENABLED'] = True
    app.config['WTF_CSRF_SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-for-testing')
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-for-testing')
    
    # Load configuration
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    # Load the appropriate configuration
    if config_name == 'testing':
        app.config.from_object('config.TestingConfig')
    elif config_name == 'production':
        app.config.from_object('config.ProductionConfig')
    else:
        app.config.from_object('config.DevelopmentConfig')
    
    # Load environment variables from .env file if it exists
    if os.path.exists('.env'):
        from dotenv import load_dotenv
        load_dotenv()
    
    # Override configuration with environment variables
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', app.config.get('SECRET_KEY', 'dev-key-123'))
    app.config['MONGODB_URI'] = os.environ.get('MONGODB_URI', app.config.get('MONGODB_URI', 'mongodb://localhost/ep_simulator'))
    
    # Import extensions
    from .extensions import db, login_manager, babel, assets_env, init_extensions
    
    # Set up login manager
    @login_manager.user_loader
    def load_user(user_id):
        User = get_model('User')
        return User.objects(id=user_id).first()
    
    # Initialize all extensions first
    init_extensions(app)
    
    # Configure assets
    configure_assets(assets_env)
    
    # Ensure CSRF token is available in all templates
    @app.context_processor
    def inject_csrf_token():
        from flask_wtf.csrf import generate_csrf
        return dict(csrf_token=generate_csrf)
    
    # Import models after extensions are initialized
    from .models import registry, get_model
    
    # Initialize the database
    with app.app_context():
        # Get models from registry
        User = get_model('User')
        Role = get_model('Role')
        Notification = get_model('Notification')
        Assessment = get_model('Assessment')
        
        # Create indexes
        try:
            User.ensure_indexes()
            Role.ensure_indexes()
            Notification.ensure_indexes()
            Assessment.ensure_indexes()
            app.logger.info("Successfully created all indexes")
        except Exception as e:
            app.logger.error(f"Error creating indexes: {e}")
            # Don't raise here, as some indexes might already exist
            
        # Ensure default roles exist
        try:
            Role.ensure_roles_exist()
        except Exception as e:
            app.logger.error(f"Error creating default roles: {e}")
            # Don't raise here, as some roles might already exist
            
        try:
            # Ensure admin role exists
            admin_role = Role.objects(name='admin').first()
            if not admin_role:
                admin_role = Role(
                    name='admin',
                    description='Administrator with full access',
                    permissions=['admin']
                )
                admin_role.save()
                app.logger.info('Created admin role')
            
            # Check if admin user exists by email
            admin_email = 'admin@example.com'
            admin_user = User.objects(email=admin_email).first()
            
            if not admin_user:
                # Create new admin user if it doesn't exist
                admin_user = User(
                    email=admin_email,
                    name='Admin',
                    roles=[admin_role],
                    is_active=True,
                    user_id=str(ObjectId())  # Generate a unique user_id
                )
                admin_user.set_password('admin123')
                admin_user.save()
                app.logger.info('Created default admin user')
            else:
                # Update existing admin user to ensure it has the admin role
                if admin_role not in admin_user.roles:
                    admin_user.roles.append(admin_role)
                    admin_user.save()
                    app.logger.info('Updated admin user with admin role')
                    
        except Exception as e:
            app.logger.error(f'Error initializing database: {str(e)}')
            if app.debug:
                raise
    
    # Register blueprints
    def register_blueprints(app):
        app.register_blueprint(main_bp)
        app.register_blueprint(auth_bp, url_prefix='/auth')
        app.register_blueprint(admin_bp, url_prefix='/admin')
        
        # Register test routes (only in development)
        if os.environ.get('FLASK_ENV') == 'development':
            app.register_blueprint(test_bp, url_prefix='/test')
    
    register_blueprints(app)
    
    # Register error handlers
    def register_error_handlers(app):
        from .errors import bp as errors_bp
        app.register_blueprint(errors_bp)
    
    register_error_handlers(app)
    
    # Initialize utils with the app
    from .utils import init_app as init_utils
    init_utils(app)
    
    # Configure logging
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/ep_simulator.log',
                                         maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s '
            '[in %(pathname)s:%(lineno)d]'))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('EP-Simulator startup')
    
    return app
