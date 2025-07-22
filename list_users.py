"""
Script to list all users in the database.
"""
import os
from pymongo import MongoClient

# Database configuration
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
DB_NAME = os.getenv('MONGODB_DB', 'ep_simulator_dev')

def list_users():
    """List all users in the database."""
    try:
        # Connect to MongoDB
        print(f"Connecting to MongoDB at {MONGODB_URI}...")
        client = MongoClient(MONGODB_URI)
        db = client[DB_NAME]
        users = db['users']
        
        # Get all users
        all_users = list(users.find({}, {
            'email': 1,
            'role': 1,
            'is_admin': 1,
            'name': 1,
            '_id': 0
        }))
        
        if not all_users:
            print("No users found in the database.")
        else:
            print("\nUsers in the database:")
            for i, user in enumerate(all_users, 1):
                print(f"\nUser {i}:")
                for key, value in user.items():
                    print(f"  {key}: {value}")
                
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    list_users()
