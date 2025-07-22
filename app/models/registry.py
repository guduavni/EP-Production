"""
Models Registry

This module provides a central registry for all models to avoid circular imports.
"""
from mongoengine.base import get_document

class ModelsRegistry:
    _instance = None
    _models = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelsRegistry, cls).__new__(cls)
        return cls._instance
    
    def register(self, name, model):
        """Register a model class with the given name."""
        self._models[name] = model
        return model
    
    def get_model(self, name):
        """Get a model class by name."""
        # First try to get from local registry
        if name in self._models:
            return self._models[name]
        
        # Then try to get from MongoEngine's registry
        try:
            return get_document(name)
        except Exception:
            # If not found, try to import the model
            try:
                # Import models dynamically to avoid circular imports
                if name == 'Role':
                    from .role import Role
                    self._models[name] = Role
                    return Role
                elif name == 'User':
                    from .user import User
                    self._models[name] = User
                    return User
                elif name == 'Notification':
                    from .notification import Notification
                    self._models[name] = Notification
                    return Notification
                elif name == 'Assessment':
                    from .assessment import Assessment
                    self._models[name] = Assessment
                    return Assessment
                elif name == 'Question':
                    from .assessment import Question
                    self._models[name] = Question
                    return Question
                elif name == 'AudioRecording':
                    from .assessment import AudioRecording
                    self._models[name] = AudioRecording
                    return AudioRecording
            except ImportError as e:
                raise ValueError(f"Model {name} not found: {str(e)}") from e
    
    def get_all_models(self):
        """Get all registered models."""
        return self._models.copy()

# Create a singleton instance
registry = ModelsRegistry()

def register_model(name):
    """Decorator to register a model class."""
    def decorator(cls):
        registry.register(name, cls)
        return cls
    return decorator

def get_model(name):
    """Get a model class by name."""
    return registry.get_model(name)

def get_all_models():
    """Get all registered models."""
    return registry.get_all_models()
