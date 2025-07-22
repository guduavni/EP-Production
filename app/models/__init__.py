"""
EP-Simulator Database Models

This package contains all the database models for the EP-Simulator application.
"""
# This file is intentionally kept minimal to avoid circular imports
# Model imports are now handled in extensions.py where we can control the import order

def get_model(model_name):
    """Dynamically import and return a model class by name."""
    if model_name == 'Role':
        from .role import Role
        return Role
    elif model_name == 'User':
        from .user import User
        return User
    elif model_name == 'Notification':
        from .notification import Notification
        return Notification
    elif model_name == 'Assessment':
        from .assessment import Assessment
        return Assessment
    elif model_name == 'Question':
        from .assessment import Question
        return Question
    elif model_name == 'AudioRecording':
        from .assessment import AudioRecording
        return AudioRecording
    return None
# Export only the get_model function to avoid circular imports
__all__ = ['get_model']
