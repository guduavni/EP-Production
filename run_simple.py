#!/usr/bin/env python3
"""
Simple runner for the EP-Simulator application
"""
from simple_app import create_app
import os

# Create the application instance
app = create_app()

if __name__ == '__main__':
    # Ensure the static folder exists
    static_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    if not os.path.exists(static_folder):
        os.makedirs(static_folder)
    
    # Ensure the CSS folder exists
    css_folder = os.path.join(static_folder, 'css')
    if not os.path.exists(css_folder):
        os.makedirs(css_folder)
    
    # Run the application
    app.run(debug=True, port=5003, host='0.0.0.0')
    # Removed duplicate app.run line to prevent syntax error
