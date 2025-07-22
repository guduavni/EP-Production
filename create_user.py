import sys
from app import create_app
from models import User
from werkzeug.security import generate_password_hash

def create_user(email, password, first_name="Admin", last_name="User", role="admin"):
    app = create_app()
    with app.app_context():
        # Check if user exists
        if User.objects(email=email).first():
            print(f"User {email} already exists")
            return False
        
        # Create new user
        user = User(
            email=email,
            first_name=first_name,
            last_name=last_name,
            role=role
        )
        
        # Set password directly
        user.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
        user.save()
        
        # Verify the password was set correctly
        print("\n=== User Created Successfully ===")
        print(f"Email: {user.email}")
        print(f"Role: {user.role}")
        print(f"Password set: {'Yes' if user.verify_password(password) else 'No'}")
        print("==============================\n")
        
        return True

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python create_user.py <email> <password>")
        sys.exit(1)
    
    email = sys.argv[1]
    password = sys.argv[2]
    
    create_user(email, password)
