"""
Models Initializer

This module initializes all models to ensure they are registered with MongoEngine.
This helps avoid circular imports by centralizing model imports.
"""
from ..models import registry

def register_models():
    """
    Import and register all models with the models registry.
    Returns a dictionary of all models for backward compatibility.
    """
    # Import models here to trigger their registration
    from .role import Role
    from .user import User
    from .notification import Notification
    from .assessment import Assessment, Question, AudioRecording
    from .base import BaseDocument
    
    # Get all registered models from the registry
    models = registry.get_all_models()
    
    # Return models dictionary for backward compatibility
    return models

# Get all models
models = register_models()

# Make models available as module-level variables
for name, model in models.items():
    globals()[name] = model

# Export all models
__all__ = list(models.keys())
