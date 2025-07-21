import os
from flask import Flask, render_template, redirect, url_for, flash
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from flask_mongoengine import MongoEngine
from models import User, Assessment, TestScript, MediaFile, Report, ExamResult
from admin_views import setup_admin
from datetime import datetime
import config

def create_app():
    # Initialize Flask app
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config.Config)
    
    # Initialize extensions
    db = MongoEngine()
    db.init_app(app)
    
    # Initialize login manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'  # Updated to use blueprint name
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.objects(user_id=user_id).first()
    
    # Register blueprints and routes
    from auth import auth_bp
    from main import main_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    
    # Setup admin interface
    setup_admin(app)
    
    # Root route
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            if current_user.role == 'admin':
                return redirect(url_for('admin.index'))
            return redirect(url_for('main.dashboard'))
        return redirect(url_for('auth.login'))
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return render_template('errors/500.html'), 500
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5002)
