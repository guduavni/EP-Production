from pymongo import MongoClient
from config import Config
import os

def fix_duplicate_emails():
    # Get MongoDB URI from environment or use default
    mongo_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/ep_simulator')
    db_name = os.getenv('MONGODB_DB', 'ep_simulator')
    
    # Connect to MongoDB
    client = MongoClient(mongo_uri)
    db = client.get_database(db_name)
    
    # Get the users collection
    users = db.users
    
    # Find all users with empty email
    users_with_empty_email = list(users.find({"$or": [{"email": ""}, {"email": None}]}))
    
    print(f"Found {len(users_with_empty_email)} users with empty or null email")
    
    # Update each user to set a unique email based on their _id
    for user in users_with_empty_email:
        new_email = f"user_{user['_id']}@example.com"
        print(f"Updating user {user['_id']} email to {new_email}")
        users.update_one(
            {"_id": user['_id']},
            {"$set": {"email": new_email}}
        )
    
    # Get existing indexes
    existing_indexes = users.index_information()
    
    # Drop the existing email index if it exists
    if 'email_1' in existing_indexes:
        print("Dropping existing email index...")
        users.drop_index("email_1")
    
    # Create a new sparse unique index on email
    print("Creating new sparse unique index on email...")
    users.create_index("email", unique=True, sparse=True)
    
    print("Database cleanup complete!")

if __name__ == "__main__":
    fix_duplicate_emails()
