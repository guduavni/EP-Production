import os
from pathlib import Path

def setup_env():
    env_file = Path('.env')
    
    if env_file.exists():
        print(".env file already exists. Please edit it manually if needed.")
        return
    
    # Default configuration
    config = """# Flask Configuration
FLASK_APP=app.py
FLASK_ENV=development
FLASK_SECRET_KEY=dev-secret-key-change-in-production

# Database Configuration
MONGODB_URI=mongodb://localhost:27017/ep_simulator
MONGODB_DB=ep_simulator
MONGODB_USERNAME=
MONGODB_PASSWORD=

# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key-here

# File Uploads
UPLOAD_FOLDER=./static/uploads
MAX_CONTENT_LENGTH=16777216  # 16MB max file size
"""
    # Write the config to .env file
    with open(env_file, 'w') as f:
        f.write(config)
    
    print("Created .env file. Please update it with your configuration.")
    print("Make sure to set your OpenAI API key and database credentials.")

if __name__ == "__main__":
    setup_env()
