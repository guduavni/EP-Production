from flask_mongoengine import MongoEngine

# Initialize extensions
db = MongoEngine()

def init_app(app):
    """Initialize all extensions with the Flask app"""
    # Initialize database
    db.init_app(app)
    
    # Import models to register them with MongoEngine
    from models import User, Assessment, AudioRecording, Question
    
    # Create indexes
    with app.app_context():
        User.ensure_indexes()
        Assessment.ensure_indexes()
        AudioRecording.ensure_indexes()
        Question.ensure_indexes()
    
    return db
