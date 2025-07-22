#!/usr/bin/env python3
"""
Run the EP-Simulator application directly.
"""
import os
import argparse
from app import create_app

def parse_arguments():
    parser = argparse.ArgumentParser(description='Run the EP-Simulator application')
    parser.add_argument('--port', type=int, default=5000, help='Port to run the server on')
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_arguments()
    
    # Create the application
    app = create_app()
    
    # Create necessary directories
    os.makedirs('uploads', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    # Run the application
    app.run(host='0.0.0.0', port=args.port, debug=True)
