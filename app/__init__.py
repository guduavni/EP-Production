"""
EP-Simulator Application Factory

This module contains the application factory function that creates and configures
the Flask application instance.
"""

import os
import logging
import click
from datetime import datetime
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template, request, current_app
from flask_security import Security
from config import config
from flask_mongoengine import MongoEngine

# Initialize extensions
db = MongoEngine()

# Import other extensions
from .extensions import (
    login_manager, 
    mail, 
    cache, 
    limiter, 
    cors, 
    principal, 
    babel, 
    assets_env,
    init_extensions,
    configure_assets
)

# Initialize Flask-Security with None for now, will be set in create_app
user_datastore = None
security = Security()

# Import assets
from .assets import css, js


def create_app(config_name=None):
    """
    Create and configure the Flask application.
    
    Args:
        config_name: Name of the configuration to use (development, testing, production, etc.)
        
    Returns:
        Flask: The configured Flask application instance
    """
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    # Import config here to avoid circular imports
    from config import config
    
    # Create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    
    # Load configuration
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # Set up logging
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.makedirs('logs')
        file_handler = RotatingFileHandler('logs/ep-simulator.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
    
    app.logger.info('Initializing EP-Simulator application...')
    
    try:
        # Initialize database and models first
        app.logger.info('Initializing database and models...')
        from .models import init_db
        db = init_db(app)
        
        # Import and initialize extensions
        app.logger.info('Initializing extensions...')
        from .extensions import (
            login_manager, 
            mail, 
            cache, 
            limiter, 
            cors, 
            principal, 
            babel, 
            assets_env, 
            main_css, 
            main_js
        )
        
        # Initialize extensions
        login_manager.init_app(app)
        mail.init_app(app)
        cache.init_app(app)
        limiter.init_app(app)
        cors.init_app(app)
        principal.init_app(app)
        babel.init_app(app)
        
        # Configure assets
        assets_env.init_app(app)
        assets_env.register('main_css', main_css)
        assets_env.register('main_js', main_js)
        
        # Register blueprints
        app.logger.info('Registering blueprints...')
        from .main import main as main_blueprint
        from .auth import auth as auth_blueprint
        from .admin import admin as admin_blueprint
        from .api import api as api_blueprint
        
        app.register_blueprint(main_blueprint)
        app.register_blueprint(auth_blueprint, url_prefix='/auth')
        app.register_blueprint(admin_blueprint, url_prefix='/admin')
        app.register_blueprint(api_blueprint, url_prefix='/api/v1')
        
        # Create upload folder if it doesn't exist
        create_upload_dirs(app)
        
        # Register error handlers
        register_error_handlers(app)
        
        # Register context processors
        register_context_processors(app)
        
        # Register shell context
        register_shell_context(app)
        
        # Register CLI commands
        register_commands(app)
        
        app.logger.info('EP-Simulator application initialized successfully')
        
    except Exception as e:
        app.logger.error(f'Failed to initialize application: {str(e)}')
        if app.debug:
            raise
    
    return app

def register_error_handlers(app):
    """Register error handlers."""
    @app.errorhandler(400)
    def bad_request_error(error):
        return render_template('errors/400.html'), 400

    @app.errorhandler(401)
    def unauthorized_error(error):
        return render_template('errors/401.html'), 401

    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(405)
    def method_not_allowed_error(error):
        return render_template('errors/405.html'), 405

    @app.errorhandler(409)
    def conflict_error(error):
        return render_template('errors/409.html'), 409

    @app.errorhandler(410)
    def gone_error(error):
        return render_template('errors/410.html'), 410

    @app.errorhandler(413)
    def request_entity_too_large_error(error):
        return render_template('errors/413.html'), 413

    @app.errorhandler(429)
    def too_many_requests_error(error):
        return render_template('errors/429.html'), 429

    @app.errorhandler(500)
    def internal_server_error(error):
        return render_template('errors/500.html'), 500

    @app.errorhandler(503)
    def service_unavailable_error(error):
        return render_template('errors/503.html'), 503

    @app.errorhandler(504)
    def gateway_timeout_error(error):
        return render_template('errors/504.html'), 504

def create_upload_dirs(app):
    """Create necessary upload directories."""
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'audio'), exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'avatars'), exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'logos'), exist_ok=True)

def register_context_processors(app):
    """Register template context processors."""
    @app.context_processor
    def inject_now():
        """Inject current datetime into all templates."""
        from datetime import datetime
        return {'now': datetime.utcnow()}
        
    @app.context_processor
    def inject_config():
        """Inject selected config values into all templates."""
        return {
            'site_name': current_app.config.get('SITE_NAME', 'EP-Simulator'),
            'site_description': current_app.config.get('SITE_DESCRIPTION', ''),
            'debug': current_app.debug
        }

def register_shell_context(app):
    """Register shell context items."""
    @app.shell_context_processor
    def make_shell_context():
        from .models.user import User
        from .models.role import Role
        from .models.assessment import Assessment, Question, AudioRecording
        from .models.notification import Notification
        from .extensions import db
        
        return {
            'db': db,
            'User': User,
            'Role': Role,
            'Assessment': Assessment,
            'AudioRecording': AudioRecording,
            'Question': Question,
            'Notification': Notification
        }

def register_commands(app):
    """Register Click commands."""
    import click
    from .models.user import User
    from .models.assessment import Assessment, Question, AudioRecording
    from .models.notification import Notification
    
    @app.cli.command('create-admin')
    @click.argument('email')
    @click.argument('password')
    def create_admin(email, password):
        """Create an admin user."""
        from werkzeug.security import generate_password_hash
        
        if User.objects(email=email).first():
            click.echo(f'User {email} already exists.')
            return
            
        admin = User(
            email=email,
            name='Admin',
            role='admin',
            is_active=True,
            email_verified=True,
            password_hash=generate_password_hash(password)
        )
        admin.save()
        click.echo(f'Admin user {email} created successfully.')
    
    @app.cli.command('init-db')
    def init_db():
        """Initialize the database."""
        # Create indexes
        User.ensure_indexes()
        Assessment.ensure_indexes()
        Question.ensure_indexes()
        AudioRecording.ensure_indexes()
        Notification.ensure_indexes()
        click.echo('Database initialized.')
    return app
