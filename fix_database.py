from models import User, db
from app import create_app

def fix_duplicate_emails():
    # Create app context
    app = create_app()
    
    with app.app_context():
        # Initialize the database connection
        db.init_app(app)
        
        # Find all users with empty or null emails
        users_with_empty_email = User.objects(email__in=['', None])
        
        print(f"Found {users_with_empty_email.count()} users with empty or null email")
        
        # Update each user to set a unique email based on their user_id
        for user in users_with_empty_email:
            if not user.email or user.email == '':
                new_email = f"user_{user.user_id}@example.com"
                print(f"Updating user {user.user_id} email to {new_email}")
                user.email = new_email
                user.save()
        
        print("Database cleanup complete!")

if __name__ == "__main__":
    fix_duplicate_emails()
