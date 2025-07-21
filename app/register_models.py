"""
Model Registration

This module handles the registration of all models to avoid circular imports.
"""
from flask import current_app
from mongoengine import register_connection
from .models import db
from .models.user import User
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
from .models.base import BaseDocument

# Create a dictionary of all models
MODELS = {
    'User': User,
    'Assessment': Assessment,
    'Question': Question,
    'AudioRecording': AudioRecording,
    'AssessmentAttempt': AssessmentAttempt,
    'CandidateResponse': CandidateResponse,
    'Notification': Notification,
    'BaseDocument': BaseDocument,
    'QuestionType': QuestionType,
    'AssessmentStatus': AssessmentStatus
}

def register_models(app):
    """Register all models with the Flask application."""
    # Make models available on the app
    app.models = MODELS
    
    # Initialize database connection
    with app.app_context():
        from config import config
        config_name = app.config.get('ENV', 'development')
        config_obj = config[config_name]
        
        # Close any existing connections
        db.disconnect()
        
        # Connect to MongoDB
        connection = db.connect(
            db=config_obj.MONGODB_DB,
            host=config_obj.MONGODB_HOST,
            port=config_obj.MONGODB_PORT,
            username=config_obj.MONGODB_USERNAME,
            password=config_obj.MONGODB_PASSWORD,
            authentication_source='admin'
        )
        
        # Ensure indexes for all models
        for name, model in MODELS.items():
            if hasattr(model, 'ensure_indexes'):
                try:
                    model.ensure_indexes()
                    current_app.logger.info(f"Ensured indexes for {name}")
                except Exception as e:
                    current_app.logger.error(f"Error creating indexes for {name}: {str(e)}")
        
        # Verify connection
        try:
            db.connection.admin.command('ping')
            current_app.logger.info("Successfully connected to MongoDB")
        except Exception as e:
            current_app.logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise
    
    return MODELS
