from flask import Flask
from flask_mongoengine import MongoEngine
from flask_login import LoginManager
from .config import Config

# Initialize extensions
db = MongoEngine()
login_manager = LoginManager()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    # Register blueprints
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.admin import bp as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')

    # Create database indexes
    with app.app_context():
        from app.models import User
        User.ensure_indexes()

    return app
