from flask_script import Manager
from app import create_app
from models import User, Role, db
from werkzeug.security import generate_password_hash

app = create_app()
manager = Manager(app)

@manager.command
def create_admin():
    """Creates the admin user."""
    email = "admin@ep.com"
    password = "admin123"
    
    # Ensure roles exist
    Role.ensure_roles_exist()
    
    # Get admin role
    admin_role = Role.get_by_name('admin')
    if not admin_role:
        print("Error: Could not find admin role")
        return
    
    # Check if user already exists
    admin_user = User.objects(email=email).first()
    if admin_user:
        print(f"User {email} already exists")
        # Ensure the user has the admin role
        if admin_role not in admin_user.roles:
            admin_user.roles.append(admin_role)
            admin_user.save()
            print(f"Added admin role to existing user: {email}")
        return
    
    # Create new admin user
    admin_user = User(
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

@manager.command
def list_users():
    """List all users."""
    users = User.objects()
    print(f"Found {users.count()} users:")
    for user in users:
        role_names = [role.name for role in user.roles] if hasattr(user, 'roles') else []
        print(f"- {user.email} (ID: {user.id}, Roles: {', '.join(role_names) if role_names else 'None'})")
        print(f"  Active: {user.is_active}, Verified: {user.email_verified}")

if __name__ == "__main__":
    manager.run()
