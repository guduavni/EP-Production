"""
Script to drop the conflicting email index directly using pymongo.
"""
import os
from pymongo import MongoClient

# Database configuration
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
DB_NAME = os.getenv('MONGODB_DB', 'ep_simulator_dev')

def drop_email_index():
    """Drop the conflicting email index directly."""
    try:
        # Connect to MongoDB
        print(f"Connecting to MongoDB at {MONGODB_URI}...")
        client = MongoClient(MONGODB_URI)
        db = client[DB_NAME]
        users = db['users']
        
        # List all indexes
        print("\nCurrent indexes:")
        for index in users.list_indexes():
            print(f"- {index}")
        
        # Drop the _cls_1_email_1 index if it exists
        if '_cls_1_email_1' in users.index_information():
            print("\nDropping index: _cls_1_email_1")
            users.drop_index('_cls_1_email_1')
            print("Index dropped successfully.")
        else:
            print("\nNo _cls_1_email_1 index found.")
            
        # List indexes again to confirm
        print("\nUpdated indexes:")
        for index in users.list_indexes():
            print(f"- {index}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    drop_email_index()
