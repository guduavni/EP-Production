#!/usr/bin/env python3
"""
EP-Simulator - ICAO English Proficiency Assessment

This module serves as the main entry point for running the EP-Simulator application.
It initializes the Flask application and starts the development server.
"""
import os
from app import create_app

# Create application instance
app = create_app()

if __name__ == '__main__':
    # Create upload directory if it doesn't exist
    upload_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
    os.makedirs(upload_folder, exist_ok=True)
    
    # Set the upload folder in the app config
    app.config['UPLOAD_FOLDER'] = upload_folder
    
    # Run the application
    app.run(host='0.0.0.0', port=5000, debug=True)
