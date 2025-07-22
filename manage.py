from flask_script import Manager
from app import create_app
from models import User, db
from werkzeug.security import generate_password_hash

app = create_app()
manager = Manager(app)

@manager.command
def create_admin():
    """Creates the admin user."""
    email = "admin@ep.com"
    password = "admin123"
    
    if User.objects(email=email).first():
        print(f"User {email} already exists")
        return
    
    # Create admin user
    admin = User(
        email=email,
        first_name="Admin",
        last_name="User",
        role="admin"
    )
    
    # Set password directly using the same method as in User model
    admin.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
    admin.save()
    
    print(f"Created admin user: {email}")
    print(f"Password: {password}")

@manager.command
def list_users():
    """List all users."""
    users = User.objects()
    print(f"Found {users.count()} users:")
    for user in users:
        print(f"- {user.email} (ID: {user.id}, Role: {user.role})")
        print(f"  Password hash: {user.password_hash}")

if __name__ == "__main__":
    manager.run()
