"""
Model Registry

This module handles the registration of all models to avoid circular imports.
"""
from mongoengine import Document

# This will hold all registered models
_registry = {}

def register_model(cls):
    """Register a model class with the registry."""
    if cls is not None and hasattr(cls, '__name__'):
        _registry[cls.__name__] = cls
    return cls

def get_model(name):
    """Get a registered model class by name."""
    return _registry.get(name)

def get_all_models():
    """Get all registered models."""
    return _registry

def clear_registry():
    """Clear the model registry (for testing)."""
    _registry.clear()

# Import models in the correct order to avoid circular imports
# Import base document first
from .base import BaseDocument

# Then import Role (no dependencies)
from .role import Role

# Then import User (depends on Role)
from .user import User

# Then import Notification (depends on User)
from .notification import Notification

# Finally import Assessment models (depend on User)
from .assessment import Assessment, Question as AssessmentQuestion, AudioRecording as AssessmentAudioRecording

# Register all models
register_model(BaseDocument)
register_model(Role)
register_model(User)
register_model(Notification)
register_model(Assessment)
register_model(AssessmentQuestion)
register_model(AssessmentAudioRecording)
register_model('User', User)
