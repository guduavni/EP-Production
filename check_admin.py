"""Script to check admin user details."""
import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import Flask app and models
from app import create_app

# Create the Flask application
app = create_app()

# Import models after creating the app to avoid circular imports
with app.app_context():
    from app.models.role import Role
    from app.models.user import User

# Check admin user
def check_admin_user():
    """Check admin user details."""
    with app.app_context():
        # Get admin user
        admin_email = "admin@ep.com"
        admin_user = User.objects(email=admin_email).first()
        
        if not admin_user:
            print(f"Admin user {admin_email} not found")
            return False
        
        print(f"Found admin user: {admin_user.email}")
        print(f"Name: {admin_user.first_name} {admin_user.last_name}")
        print(f"Active: {admin_user.is_active}")
        print(f"Email Verified: {admin_user.email_verified}")
        
        # Check roles
        if hasattr(admin_user, 'roles') and admin_user.roles:
            print("Roles:")
            for role in admin_user.roles:
                print(f"- {role.name}: {role.description}")
        else:
            print("No roles assigned to this user")
            
            # If no roles, try to add admin role
            admin_role = Role.get_by_name('admin')
            if admin_role:
                admin_user.roles = [admin_role]
                admin_user.save()
                print("Added admin role to the user")
            else:
                print("Error: Could not find admin role")
                
        return True

if __name__ == "__main__":
    check_admin_user()
