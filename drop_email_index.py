"""
Script to drop the conflicting email index from the users collection.
"""
from app import create_app
from app.extensions import db

def drop_conflicting_index():
    """Drop the conflicting email index from the users collection."""
    try:
        # Get the database connection
        connection = db.connection
        db_name = db.get_db().name
        
        # Get the users collection
        db_client = connection[db_name]
        users = db_client['users']
        
        # List all indexes
        indexes = users.index_information()
        print("Current indexes:")
        for name, index in indexes.items():
            print(f"- {name}: {index}")
        
        # Drop the _cls_1_email_1 index if it exists
        if '_cls_1_email_1' in indexes:
            print("\nDropping index: _cls_1_email_1")
            users.drop_index('_cls_1_email_1')
            print("Index dropped successfully.")
        else:
            print("\nNo _cls_1_email_1 index found.")
            
        # List indexes again to confirm
        print("\nUpdated indexes:")
        for name, index in users.index_information().items():
            print(f"- {name}: {index}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        drop_conflicting_index()
