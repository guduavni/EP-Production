"""Script to create an admin user."""
import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import Flask app and models
from app import create_app
from app.extensions import db

# Create the Flask application
app = create_app()

# Import models after creating the app to avoid circular imports
with app.app_context():
    from app.models.role import Role
    from app.models.user import User

def create_admin_user():
    """Create an admin user if it doesn't exist."""
    with app.app_context():
        # Ensure roles exist
        Role.ensure_roles_exist()
        
        # Get admin role
        admin_role = Role.get_by_name('admin')
        if not admin_role:
            print("Error: Could not find admin role")
            return False
        
        # Admin user details
        email = "admin@ep.com"
        password = "admin123"
        
        # Check if user already exists
        admin_user = User.objects(email=email).first()
        if admin_user:
            print(f"User {email} already exists")
            # Delete the existing user to start fresh
            print("Deleting existing admin user...")
            admin_user.delete()
            print("Existing admin user deleted")
            
        # Create new admin user
        try:
            admin_user = User(
                user_id=email,  # Using email as user_id since it's required and unique
                email=email,
                first_name="Admin",
                last_name="User",
                name="Admin User",
                is_active=True,
                email_verified=True
            )
            
            # Set password
            admin_user.set_password(password)
            
            # Add admin role
            admin_user.roles = [admin_role]
            
            # Save the user
            admin_user.save()
            
            print(f"Created admin user: {email}")
            print(f"Password: {password}")
            return True
            
        except Exception as e:
            print(f"Error creating admin user: {e}")
            return False
        
        # Create new admin user
        try:
            admin_user = User(
                user_id=email,  # Using email as user_id since it's required and unique
                email=email,
                first_name="Admin",
                last_name="User",
                name="Admin User",
                is_active=True,
                email_verified=True
            )
            
            # Set password
            admin_user.set_password(password)
            
            # Add admin role
            admin_user.roles = [admin_role]
            
            # Save the user
            admin_user.save()
            
            print(f"Created admin user: {email}")
            print(f"Password: {password}")
            return True
            
        except Exception as e:
            print(f"Error creating admin user: {e}")
            return False

if __name__ == "__main__":
    create_admin_user()
