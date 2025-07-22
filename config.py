import os
import secrets
from datetime import timedelta
from pathlib import Path

try:
    from dotenv import load_dotenv
    # Load environment variables from .env file if it exists
    load_dotenv()
except ImportError:
    print("python-dotenv not installed, using system environment variables")

# Base directory
BASE_DIR = Path(__file__).resolve().parent

# Environment detection
ENV = os.getenv('FLASK_ENV', 'development')
DEBUG = ENV == 'development'
TESTING = ENV == 'testing'

class Config:
    # App settings
    SECRET_KEY = os.getenv('SECRET_KEY', secrets.token_hex(32))
    SECURITY_PASSWORD_SALT = os.getenv('SECURITY_PASSWORD_SALT', secrets.token_hex(16))
    
    # Flask settings
    FLASK_APP = 'app.py'
    FLASK_ENV = ENV
    DEBUG = DEBUG
    TESTING = TESTING
    
    # Session settings
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False') == 'True'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # Security settings
    SECURITY_PASSWORD_SALT = os.environ.get('SECURITY_PASSWORD_SALT', 'dev-salt-please-change-in-production')
    SECURITY_PASSWORD_HASH = 'bcrypt'
    
    # CSRF settings
    WTF_CSRF_ENABLED = False  # Disable CSRF for testing
    
    # Email settings
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True') == 'True'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@ep-simulator.com')
    
    # OpenAI settings
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    
    # File upload settings
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'app', 'static', 'uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp3', 'wav', 'ogg'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload size
    
    # Redis settings (for rate limiting and caching)
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    
    # CORS settings
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')
    
    # Logging configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO' if not DEBUG else 'DEBUG')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_FILE = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'logs', 'app.log')
    
    # File paths
    TEMPLATES_FOLDER = os.path.join(BASE_DIR, 'templates')
    STATIC_FOLDER = os.path.join(BASE_DIR, 'static')
    
    # API settings
    API_PREFIX = '/api/v1'
    
    # Pagination
    ITEMS_PER_PAGE = 20
    
    # JWT settings
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', secrets.token_hex(32))
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # File storage
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max upload size
    
    # Cache settings
    CACHE_TYPE = 'simple' if DEBUG else 'redis'
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes
    
    # Session settings
    SESSION_TYPE = 'mongodb'
    SESSION_MONGODB_DB = 'ep_simulator_dev'  # Default database name for sessions
    SESSION_MONGODB_COLLECT = 'sessions'
    
    @staticmethod
    def init_app(app):
        # Ensure upload and log directories exist
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(os.path.dirname(Config.LOG_FILE), exist_ok=True)
        
        # Configure logging
        import logging
        from logging.handlers import RotatingFileHandler
        
        # File handler
        file_handler = RotatingFileHandler(
            Config.LOG_FILE,
            maxBytes=1024 * 1024 * 10,  # 10MB
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(Config.LOG_FORMAT))
        file_handler.setLevel(logging.getLevelName(Config.LOG_LEVEL))
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(Config.LOG_FORMAT))
        console_handler.setLevel(logging.DEBUG if DEBUG else logging.INFO)
        
        # Configure root logger
        app.logger.setLevel(logging.DEBUG if DEBUG else logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.addHandler(console_handler)
        
        # Disable logging for less important loggers
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('werkzeug').setLevel(logging.ERROR if not DEBUG else logging.INFO)
        logging.getLogger('PIL').setLevel(logging.WARNING)


class DevelopmentConfig(Config):
    DEBUG = True
    MONGODB_SETTINGS = {
        'db': 'ep_simulator_dev',
        'host': 'mongodb://localhost:27017/'
    }


class TestingConfig(Config):
    TESTING = True
    MONGODB_SETTINGS = {
        'db': 'ep_simulator_test',
        'host': 'mongodb://localhost:27017/'
    }
    WTF_CSRF_ENABLED = False
    LOGIN_DISABLED = False


class ProductionConfig(Config):
    DEBUG = False
    MONGODB_SETTINGS = {
        'db': os.getenv('MONGODB_DB', 'ep_simulator'),
        'host': os.getenv('MONGODB_URI', 'mongodb://localhost:27017/'),
        'username': os.getenv('MONGODB_USERNAME', ''),
        'password': os.getenv('MONGODB_PASSWORD', ''),
        'authentication_source': 'admin'
    }
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    SESSION_PROTECTION = 'strong'


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

# Select configuration based on environment
app_config = config[ENV.lower()] if ENV.lower() in config else config['default']
