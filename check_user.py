from mongoengine import connect, disconnect
from models import User

# Disconnect any existing connections
disconnect()

# Connect to MongoDB directly
connect('ep_simulator', host='mongodb://localhost:27017/ep_simulator', alias='default')

# Check if user exists
user = User.objects(email='test@example.com').first()
if user:
    print("User found in database:")
    print(f"Email: {user.email}")
    print(f"Name: {user.first_name} {user.last_name}")
    print(f"Role: {user.role}")
    print(f"Status: {user.status}")
    
    # Verify the password
    if user.verify_password('password123'):
        print("Password verification: SUCCESS")
    else:
        print("Password verification: FAILED")
else:
    print("User test@example.com not found in the database.")
