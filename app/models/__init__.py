"""
EP-Simulator Database Models

This package contains all the database models for the EP-Simulator application.
"""

# Import the registry first
from .registry import registry

# Re-export the public API functions
get_model = registry.get_model
register_model = registry.register
get_all_models = registry.get_all_models

# Import base document first to ensure it's available for other models
from .base import BaseDocument

# Define model names as strings to avoid circular imports
MODEL_NAMES = [
    'Role',
    'Notification',
    'Question',
    'AudioRecording',
    'Assessment',
    'User'
]

def _import_base_models():
    """Import base models first."""
    from .base import BaseDocument
    return {'BaseDocument': BaseDocument}

def _import_models():
    """Import all models in the correct order to avoid circular imports."""
    models = {}
    
    try:
        # 1. Import base document first
        from .base import BaseDocument
        models['BaseDocument'] = BaseDocument
        
        # 2. Import Role model (no dependencies)
        from .role import Role
        models['Role'] = Role
        
        # 3. Import Assessment and related models (no dependencies on User)
        from .assessment import Question, AudioRecording, Assessment
        models.update({
            'Question': Question,
            'AudioRecording': AudioRecording,
            'Assessment': Assessment,
        })
        
        # 4. Import User model (depends on Role and Assessment)
        from .user import User
        models['User'] = User
        
        # 5. Import Notification model (depends on User)
        from .notification import Notification
        models['Notification'] = Notification
        
    except Exception as e:
        print(f"Error importing models: {e}")
        import traceback
        traceback.print_exc()
        raise
    
    return models

def register_models():
    """Register all models with the registry."""
    try:
        # First, import all models to ensure they're defined
        models = _import_models()
        
        # Then register them in the correct order to handle dependencies
        model_order = [
            'Role',
            'Question',
            'AudioRecording',
            'Assessment',
            'User',
            'Notification'
        ]
        
        registered_models = {}
        for name in model_order:
            if name in models:
                registry.register(name, models[name])
                registered_models[name] = models[name]
                print(f"Registered model: {name}")
        
        return registered_models
    except Exception as e:
        print(f"Error registering models: {e}")
        import traceback
        traceback.print_exc()
        raise

# Register all models
models = register_models()

# Export the public API
__all__ = [
    'BaseDocument',
    'get_model',
    'register_model',
    'get_all_models',
    *MODEL_NAMES
]
