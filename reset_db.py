#!/usr/bin/env python3
"""
Database reset script for EP-Simulator

This script will drop all collections and recreate them with test data.
Use with caution in production environments!
"""
import sys
from mongoengine import connect
from models import User, TestScript, ExamResult, MediaFile, Assessment, Report

# Import test data creation functions
from init_db import create_test_users, create_test_scripts, create_test_exam_results

def confirm_reset():
    """Ask for confirmation before resetting the database"""
    if '--force' not in sys.argv:
        print("WARNING: This will delete all data in the database!")
        response = input("Are you sure you want to continue? (yes/no): ")
        if response.lower() not in ('y', 'yes'):
            print("Operation cancelled.")
            sys.exit(0)

def drop_collections():
    """Drop all collections"""
    collections = [User, TestScript, ExamResult, MediaFile, Assessment, Report]
    for model in collections:
        print(f"Dropping collection: {model._get_collection_name()}")
        model.drop_collection()

def main():
    # Ask for confirmation
    confirm_reset()
    
    # Connect to the database
    from simple_app import create_app
    app = create_app()
    
    with app.app_context():
        # Drop all collections
        print("\nDropping existing collections...")
        drop_collections()
        
        # Create test data
        print("\nCreating test users...")
        users = create_test_users()
        
        print("\nCreating test scripts...")
        scripts = create_test_scripts()
        
        print("\nCreating test exam results...")
        exams = create_test_exam_results(users, scripts)
        
        print("\nDatabase reset complete!")
        print(f"Created {len(users)} users, {len(scripts)} scripts, and {len(exams)} exam results.")

if __name__ == '__main__':
    print("EP-Simulator Database Reset Tool")
    print("-------------------------------")
    print("Add '--force' flag to skip confirmation prompt.\n")
    main()
