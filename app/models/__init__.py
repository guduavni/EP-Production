"""
EP-Simulator Database Models

This package contains all the database models for the EP-Simulator application.
"""
import os
from mongoengine import connect, disconnect_all, Document, StringField, DateTimeField, ListField
from flask import current_app
from flask_mongoengine import MongoEngine
from flask_login import UserMixin
from datetime import datetime

# Initialize the database
db = MongoEngine()

# Import models after db is initialized
def import_models():
    """Import all models to ensure they are registered with MongoEngine."""
    # Import models in the correct order to avoid circular imports
    from .base import BaseDocument
    from .role import Role
    from .user import User
    from .question import Question
    from .assessment import Assessment
    from .audio_recording import AudioRecording
    from .notification import Notification
    
    # Return a dict of all models for easy access
    models = {
        'BaseDocument': BaseDocument,
        'Role': Role,
        'User': User,
        'Question': Question,
        'Assessment': Assessment,
        'AudioRecording': AudioRecording,
        'Notification': Notification,
    }
    
    # Set document_type for LazyReferenceFields
    from mongoengine.base.common import _document_registry
    for name, model in models.items():
        if hasattr(model, '_meta') and hasattr(model._meta, 'collection'):
            _document_registry[model._meta['collection']] = model
    
    return models

# Define Role model here to avoid circular imports
class Role(Document, UserMixin):
    """
    Role model for role-based access control (RBAC).
    """
    name = StringField(required=True, unique=True)
    description = StringField()
    permissions = ListField(StringField())
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
    
    meta = {
        'collection': 'roles',
        'indexes': [
            'name',
            'permissions'
        ]
    }
    
    def __str__(self):
        return self.name

def init_db(app):
    """Initialize the database with the Flask app and register all models."""
    global db
    from flask_mongoengine import MongoEngine
    
    # Initialize the database
    db = MongoEngine(app)
    
    # Import models here to avoid circular imports
    from .base import BaseDocument
    from .user import User
    
    # Set the db instance for all models
    BaseDocument.meta['db_alias'] = 'default'
    
    # Import other models
    from .assessment import (
        Question, AudioRecording, Assessment,
        AssessmentAttempt, CandidateResponse,
        QuestionType, AssessmentStatus
    )
    from .notification import Notification
    
    # Create a dictionary of all models for easy access
    models = {
        'User': User,
        'Role': Role,
        'Assessment': Assessment,
        'Question': Question,
        'AudioRecording': AudioRecording,
        'AssessmentAttempt': AssessmentAttempt,
        'CandidateResponse': CandidateResponse,
        'Notification': Notification,
        'QuestionType': QuestionType,
        'AssessmentStatus': AssessmentStatus
    }
    
    # Ensure indexes
    for model in models.values():
        if hasattr(model, 'ensure_indexes'):
            try:
                model.ensure_indexes()
            except Exception as e:
                app.logger.error(f"Error creating indexes for {model.__name__}: {str(e)}")
    
    # Create indexes and initialize data
    with app.app_context():
        try:
            # Create default roles if they don't exist
            default_roles = [
                {
                    'name': 'admin',
                    'description': 'Administrator with full access',
                    'permissions': ['admin']
                },
                {
                    'name': 'examiner',
                    'description': 'Examiner who can conduct assessments',
                    'permissions': ['conduct_assessments', 'view_reports']
                },
                {
                    'name': 'candidate',
                    'description': 'Candidate taking assessments',
                    'permissions': ['take_assessments']
                }
            ]
            
            for role_data in default_roles:
                if not Role.objects(name=role_data['name']).first():
                    Role(**role_data).save()
            
            # Create a default admin user if none exists
            if not User.objects(email='admin@example.com').first():
                from werkzeug.security import generate_password_hash
                admin_role = Role.objects(name='admin').first()
                if admin_role:
                    user = User(
                        email='admin@example.com',
                        password_hash=generate_password_hash('admin'),
                        first_name='Admin',
                        last_name='User',
                        name='Admin User',
                        is_active=True,
                        roles=[admin_role],
                        email_verified=True
                    )
                    user.save()
            
            app.logger.info("Database initialization completed successfully")
            
        except Exception as e:
            app.logger.error(f"Error initializing database: {str(e)}")
            if app.debug:
                raise
    
    return db

# Import User model
from .user import User

# Export all models for easier imports
__all__ = [
    'db',
    'Role',
    'User',
    'BaseDocument'
]

def init_db(app=None):
    """Initialize the database connection.
    
    Args:
        app: The Flask application instance (optional)
    """
    if app is not None:
        # Disconnect any existing connections
        disconnect_all()
        
        # Configure MongoDB settings
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
        
        # Initialize the database with the app
        db.init_app(app)
        
        # Create indexes and initialize data
        with app.app_context():
            try:
                # Import all models to ensure they are registered
                models = import_models()
                
                # Create indexes for all models
                for model in models.values():
                    if hasattr(model, 'ensure_indexes'):
                        model.ensure_indexes()
                
                # Create default roles if they don't exist
                admin_role = Role.objects(name='admin').first()
                if not admin_role:
                    admin_role = Role(
                        name='admin',
                        description='Administrator with full access',
                        permissions=['admin']
                    )
                    admin_role.save()
                
                # Create a default admin user if none exists
                if not models['User'].objects(email='admin@example.com').first():
                    from werkzeug.security import generate_password_hash
                    admin_role = Role.objects(name='admin').first()
                    if admin_role:
                        user = models['User'](
                            email='admin@example.com',
                            password=generate_password_hash('admin'),
                            first_name='Admin',
                            last_name='User',
                            is_active=True,
                            roles=[admin_role]
                        ).save()
                        
                current_app.logger.info("Database initialization completed successfully")
                
            except Exception as e:
                current_app.logger.error(f"Error initializing database: {str(e)}")
                if app.debug:
                    raise

    return db
