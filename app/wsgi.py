"""
WSGI config for EP-Simulator project.

This module contains the WSGI application used by the production server.
It exposes the WSGI callable as a module-level variable named ``application``.
"""

import os
from app import create_app

# Create the Flask application using the application factory pattern
application = create_app(os.getenv('FLASK_CONFIG') or 'production')

if __name__ == "__main__":
    # Run the application using the development server
    # In production, use a production WSGI server like Gunicorn or uWSGI
    application.run(host='0.0.0.0', port=5000, debug=application.config['DEBUG'])
