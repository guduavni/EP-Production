from werkzeug.security import generate_password_hash
from models import User

def create_test_user():
    # Check if user already exists
    if User.objects(email='test@example.com').first():
        print("Test user already exists!")
        return
    
    # Create test user with hashed password
    user = User(
        first_name='Test',
        last_name='User',
        email='test@example.com',
        status='active',
        role='admin'  # Make this an admin user for full access
    )
    user.password = 'password123'  # This will hash the password
    user.save()
    print("Test user created successfully!")
    print("Email: test@example.com")
    print("Password: password123")

if __name__ == "__main__":
    # Import and create the Flask app
    from simple_app import create_app
    app = create_app()
    
    # Initialize MongoDB connection
    from mongoengine import connect, disconnect
    from pymongo import MongoClient
    
    # Drop the existing users collection to avoid index conflicts
    client = MongoClient('mongodb://localhost:27017/')
    db = client['ep_simulator']
    if 'users' in db.list_collection_names():
        db.drop_collection('users')
    
    # Connect with mongoengine
    disconnect()  # Disconnect any existing connections
    connect('ep_simulator', host='mongodb://localhost:27017/ep_simulator', alias='default')
    
    with app.app_context():
        create_test_user()
