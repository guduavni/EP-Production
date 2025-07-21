"""
WSGI config for EP-Simulator project.

This module contains the WSGI application used by the production server.
It exposes the WSGI callable as a module-level variable named ``application``.
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = str(Path(__file__).resolve().parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Set the default configuration
os.environ.setdefault('FLASK_ENV', 'production')
os.environ.setdefault('FLASK_APP', 'wsgi.py')

# Import the application factory
from app import create_app

# Create the Flask application using the application factory pattern
application = create_app()

if __name__ == "__main__":
    # Run the application using the development server
    # In production, use a production WSGI server like Gunicorn or uWSGI
    application.run(host='0.0.0.0', port=5000, debug=application.debug)
