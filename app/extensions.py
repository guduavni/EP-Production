"""
Extensions Module

This module initializes all the Flask extensions used by the application.
"""
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

# Initialize extensions
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
babel.locale_selector_func = lambda: 'en'  # Default to English

def init_extensions(app):
    """
    Initialize all Flask extensions with the given app.
    
    Args:
        app: The Flask application instance
    """
    try:
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
        cors.init_app(app)
        app.logger.info("Initialized Flask-CORS")
        
        # Initialize Flask-Principal
        principal.init_app(app)
        app.logger.info("Initialized Flask-Principal")
        
        # Initialize Flask-Babel
        babel.init_app(app)
        app.logger.info("Initialized Flask-Babel")
        
        # Configure Babel
        @babel.localeselector
        def get_locale():
            # Get the language from the user's session or default to 'en'
            from flask import session, request
            # Try to get language from URL parameter
            lang = request.args.get('lang')
            if lang:
                session['language'] = lang
                return lang
            # Try to get language from session
            return session.get('language', 'en')
        
        # Initialize Flask-Assets
        assets_env.init_app(app)
        configure_assets(assets_env)
        app.logger.info("Initialized Flask-Assets")
        
    except Exception as e:
        app.logger.error(f"Failed to initialize extensions: {str(e)}")
        raise
    
    # Configure CORS
    cors.init_app(app, resources={
        r"/api/*": {
            "origins": app.config.get('CORS_ORIGINS', '*'),
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # Configure assets
    configure_assets(assets)

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
