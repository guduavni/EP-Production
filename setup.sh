#!/bin/bash

# Exit on error
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${YELLOW}Please run as root or with sudo${NC}"
    exit 1
fi

# Update package lists
echo -e "${GREEN}Updating package lists...${NC}"
apt-get update

# Install system dependencies
echo -e "${GREEN}Installing system dependencies...${NC}"
apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    build-essential \
    libssl-dev \
    libffi-dev \
    mongodb \
    nginx \
    supervisor

# Install Node.js and npm
curl -fsSL https://deb.nodesource.com/setup_16.x | bash -
apt-get install -y nodejs

# Install Yarn
npm install -g yarn

# Create necessary directories
echo -e "${GREEN}Creating necessary directories...${NC}"
mkdir -p /var/log/ep-simulator
mkdir -p /var/run/ep-simulator
mkdir -p /etc/ep-simulator

# Set permissions
chown -R $SUDO_USER:$SUDO_USER /var/log/ep-simulator
chown -R $SUDO_USER:$SUDO_USER /var/run/ep-simulator
chown -R $SUDO_USER:$SUDO_USER /etc/ep-simulator

# Create virtual environment
echo -e "${GREEN}Creating Python virtual environment...${NC}
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo -e "${GREEN}Installing Python dependencies...${NC}
pip install --upgrade pip
pip install -r requirements.txt

# Install frontend dependencies
echo -e "${GREEN}Installing frontend dependencies...${NC}
cd static
npm install
yarn build
cd ..

# Copy configuration files
echo -e "${GREEN}Setting up configuration...${NC}
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo -e "${YELLOW}Please edit the .env file with your configuration${NC}"
fi

# Initialize database
echo -e "${GREEN}Initializing database...${NC}
python init_db.py

# Set up Nginx
if [ -f "/etc/nginx/sites-enabled/default" ]; then
    rm /etc/nginx/sites-enabled/default
fi

if [ ! -f "/etc/nginx/sites-available/ep-simulator" ]; then
    cat > /etc/nginx/sites-available/ep-simulator << 'EOL'
server {
    listen 80;
    server_name _;

    location / {
        include proxy_params;
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /static {
        alias /path/to/EP-Simulator/static;
        expires 30d;
    }

    location /uploads {
        alias /path/to/EP-Simulator/uploads;
        expires 30d;
    }
}
EOL

    ln -s /etc/nginx/sites-available/ep-simulator /etc/nginx/sites-enabled/
    nginx -t
    systemctl restart nginx
fi

# Set up Supervisor
if [ ! -f "/etc/supervisor/conf.d/ep-simulator.conf" ]; then
    cat > /etc/supervisor/conf.d/ep-simulator.conf << 'EOL'
[program:ep-simulator]
command=/path/to/EP-Simulator/venv/bin/gunicorn --bind 127.0.0.1:8000 --workers 4 --timeout 120 run_simple:app
directory=/path/to/EP-Simulator
user=%(ENV_USER)s
autostart=true
autorestart=true
stderr_logfile=/var/log/ep-simulator/error.log
stdout_logfile=/var/log/ep-simulator/out.log
EOL

    supervisorctl reread
    supervisorctl update
    supervisorctl start ep-simulator
fi

echo -e "${GREEN}Setup completed successfully!${NC}"
echo -e "${YELLOW}Please make sure to:"
echo "1. Update the .env file with your configuration"
echo "2. Update the Nginx and Supervisor configuration files with the correct paths"
echo "3. Restart Nginx and Supervisor services"
echo -e "4. Access the application at http://your-server-ip/${NC}"

# Create and activate virtual environment
echo "Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Install Node.js dependencies (if any)
if [ -f "package.json" ]; then
    echo "Installing Node.js dependencies..."
    npm install
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from example..."
    cp .env.example .env
    echo "Please edit the .env file with your configuration"
fi

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p logs
mkdir -p static/uploads

# Initialize database
echo "Initializing database..."
sudo systemctl start mongodb

# Create admin user
echo "Creating admin user..."
read -p "Admin email: " admin_email
read -s -p "Admin password: " admin_password
echo
read -p "Admin first name: " first_name
read -p "Admin last name: " last_name

python init_db.py "$admin_email" "$admin_password" "$first_name" "$last_name"

echo "Setup complete!"
echo "To start the application, run:"
echo "  source venv/bin/activate"
echo "  python run.py"
