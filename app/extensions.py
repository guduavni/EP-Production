"""
Extensions Module

This module initializes all the Flask extensions used by the application.
"""
import os
from flask import current_app
from flask_login import LoginManager
from flask_mail import Mail
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
from flask_principal import Principal, Permission, RoleNeed
from flask_babel import Babel
from flask_assets import Environment, Bundle
from flask_mongoengine import MongoEngine

# Initialize extensions without any configuration
db = MongoEngine()
login_manager = LoginManager()
mail = Mail()
cache = Cache()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
    strategy="fixed-window"  # or "moving-window"
)
cors = CORS()
principal = Principal(use_sessions=False)
babel = Babel()
assets_env = Environment()

# Configure Babel
def get_locale():
    # Default to English
    from flask import session, request
    # Try to get language from URL parameter
    lang = request.args.get('lang')
    if lang:
        session['language'] = lang
        return lang
    # Try to get language from session
    return session.get('language', 'en')

babel.localeselector = get_locale

# Define permissions
admin_permission = Permission(RoleNeed('admin'))
user_permission = Permission(RoleNeed('user'))
examiner_permission = Permission(RoleNeed('examiner'))
candidate_permission = Permission(RoleNeed('candidate'))

# Configure LoginManager
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'
login_manager.session_protection = 'strong'

# Configure Babel
def get_locale():
    # Default to English
    from flask import session, request
    # Try to get language from URL parameter
    lang = request.args.get('lang')
    if lang:
        session['language'] = lang
        return lang
    # Try to get language from session
    return session.get('language', 'en')

babel.localeselector = get_locale

def init_extensions(app):
    """
    Initialize all Flask extensions with the given app.
    
    Args:
        app: The Flask application instance
    """
    try:
        # Configure MongoDB settings if not already configured
        if 'MONGODB_SETTINGS' not in app.config:
            mongodb_uri = os.environ.get('MONGODB_URI', 'mongodb://localhost/ep_simulator')
            
            app.config['MONGODB_SETTINGS'] = {
                'host': mongodb_uri,
                'connect': False,  # Lazy connection
                'connectTimeoutMS': 30000,  # 30 seconds
                'socketTimeoutMS': None,  # No timeout
                'serverSelectionTimeoutMS': 30000,  # 30 seconds
                'retryWrites': True,
                'w': 'majority'
            }
        
        # Initialize Flask-MongoEngine first
        db.init_app(app)
        app.logger.info("Initialized Flask-MongoEngine")
        
        # Initialize models after initializing the database
        with app.app_context():
            # First, import all models without initializing them
            import importlib
            import pkgutil
            import inspect
            from mongoengine import Document
            
            # Get all modules in the models package
            from . import models
            
            # Dictionary to store all model classes
            model_classes = {}
            
            # Import all modules in the models package
            for _, module_name, _ in pkgutil.iter_modules(models.__path__):
                if module_name == '__init__' or module_name.startswith('_'):
                    continue
                    
                try:
                    module = importlib.import_module(f'app.models.{module_name}')
                    
                    # Find all Document classes in the module
                    for name, obj in inspect.getmembers(module):
                        if (inspect.isclass(obj) and 
                            issubclass(obj, Document) and 
                            obj.__module__ == f'app.models.{module_name}'):
                            model_classes[name] = obj
                            
                except Exception as e:
                    app.logger.error(f"Error importing module {module_name}: {str(e)}")
            
            # Now import models in the correct order
            # 1. Import Role first (no dependencies)
            from .models.role import Role
            
            # 2. Import User (depends on Role)
            from .models.user import User
            
            # 3. Import Notification (depends on User)
            from .models.notification import Notification
            
            # 4. Import Assessment models (depend on User)
            from .models.assessment import Assessment, Question, AudioRecording
            
            # Force registration of all models
            models = [Role, User, Notification, Assessment, Question, AudioRecording]
            
            # Ensure all models are registered with MongoEngine
            for model in models:
                if hasattr(model, '_meta') and model._meta.get('collection'):
                    model._meta['collection'] = model._meta['collection'].lower()
            
            # Initialize any required model indexes
            for model in models:
                if hasattr(model, 'ensure_indexes'):
                    try:
                        model.ensure_indexes()
                    except Exception as e:
                        app.logger.error(f"Error creating indexes for {model.__name__}: {str(e)}")
            
            # Set up roles
            from .models.role import setup_roles
            try:
                setup_roles()
            except Exception as e:
                app.logger.error(f"Error setting up roles: {str(e)}")
            
            app.logger.info("Successfully initialized all models")
        
        # Initialize Flask-Login
        login_manager.init_app(app)
        app.logger.info("Initialized Flask-Login")
        
        # Initialize Flask-Mail
        mail.init_app(app)
        app.logger.info("Initialized Flask-Mail")
        
        # Initialize Flask-Caching
        cache.init_app(app)
        app.logger.info("Initialized Flask-Caching")
        
        # Initialize Flask-Limiter
        limiter.init_app(app)
        app.logger.info("Initialized Flask-Limiter")
        
        # Initialize Flask-CORS
        cors.init_app(app, resources={
            r"/api/*": {
                "origins": app.config.get('CORS_ORIGINS', '*'),
                "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization"]
            }
        })
        app.logger.info("Initialized Flask-CORS")
        
        # Initialize Flask-Principal
        principal.init_app(app)
        app.logger.info("Initialized Flask-Principal")
        
        # Initialize Flask-Babel
        babel.init_app(app)
        app.logger.info("Initialized Flask-Babel")
        
        # Initialize Flask-Assets
        assets_env.init_app(app)
        configure_assets(assets_env)
        app.logger.info("Initialized Flask-Assets")
        
        return True
        
    except Exception as e:
        app.logger.error(f"Error initializing extensions: {str(e)}", exc_info=True)
        raise
    
    # Assets are already configured above

def configure_assets(assets_env):
    """Configure web assets."""
    # JavaScript bundles
    js_libs = Bundle(
        'js/vendor/jquery-3.6.0.min.js',
        'js/vendor/bootstrap.bundle.min.js',
        'js/vendor/popper.min.js',
        'js/vendor/select2.min.js',
        'js/vendor/chart.min.js',
        output='gen/packed.js',
        filters='jsmin'
    )
    
    # CSS bundles
    css_libs = Bundle(
        'css/vendor/bootstrap.min.css',
        'css/vendor/select2.min.css',
        'css/vendor/select2-bootstrap4.min.css',
        'css/main.css',
        output='gen/packed.css',
        filters='cssmin'
    )
    
    # Register assets
    assets_env.register('js_all', js_libs)
    assets_env.register('css_all', css_libs)
