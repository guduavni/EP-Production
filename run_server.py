#!/usr/bin/env python3
"""
Run the EP-Simulator application directly.
"""
import os
from app_old import create_app

# Create the application
app = create_app()

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('uploads', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    # Run the application
    app.run(host='0.0.0.0', port=5000, debug=True)
