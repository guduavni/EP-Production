"""
Model Utilities

This module provides utilities for working with models and avoiding circular imports.
"""
from mongoengine import get_db

def register_models():
    """
    Register all models to avoid circular imports.
    This function should be called after all models are defined.
    """
    # Import models here to avoid circular imports
    from .models.base import BaseDocument
    from .models.user import User
    
    # Import assessment models with string references
    from .models.assessment import (
        Question,
        AudioRecording,
        Assessment,
        AssessmentAttempt,
        CandidateResponse,
        QuestionType,
        AssessmentStatus
    )
    
    from .models.notification import Notification
    from .models import Role
    
    # Create a dictionary of all models
    models = {
        'User': User,
        'Assessment': Assessment,
        'Question': Question,
        'AudioRecording': AudioRecording,
        'AssessmentAttempt': AssessmentAttempt,
        'CandidateResponse': CandidateResponse,
        'Notification': Notification,
        'Role': Role,
        'BaseDocument': BaseDocument,
        'QuestionType': QuestionType,
        'AssessmentStatus': AssessmentStatus
    }
    
    # Register models with MongoEngine
    from mongoengine import register_connection
    
    # Ensure all models are registered
    for name, model in models.items():
        if hasattr(model, '_meta'):
            model._meta['collection'] = model._meta.get('collection', name.lower() + 's')
    
    return models

def ensure_indexes(models):
    """Ensure all indexes are created for the given models."""
    for name, model in models.items():
        if hasattr(model, 'ensure_indexes'):
            try:
                model.ensure_indexes()
                print(f"Ensured indexes for {name}")
            except Exception as e:
                print(f"Error creating indexes for {name}: {str(e)}")

def connect_to_mongodb(app):
    """Connect to MongoDB using the app's configuration."""
    from config import config
    config_name = app.config.get('ENV', 'development')
    config_obj = config[config_name]
    
    # Get the database instance
    from .models import db
    
    # Disconnect any existing connections
    db.disconnect()
    
    # Get MongoDB settings from config
    mongo_settings = getattr(config_obj, 'MONGODB_SETTINGS', {})
    
    # Set default values if not provided
    db_name = mongo_settings.get('db', 'ep_simulator_dev')
    host = mongo_settings.get('host', 'mongodb://localhost:27017/')
    username = mongo_settings.get('username', '')
    password = mongo_settings.get('password', '')
    
    # Connect to MongoDB
    connection = db.connect(
        db=db_name,
        host=host,
        username=username if username else None,
        password=password if password else None,
        authentication_source=mongo_settings.get('authentication_source', 'admin')
    )
    
    return connection
