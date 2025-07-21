#!/bin/bash

# Exit on error
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to check if a service is running
check_service() {
    local service=$1
    if systemctl is-active --quiet $service; then
        echo -e "${GREEN}✓${NC} $service is running"
    else
        echo -e "${RED}✗${NC} $service is not running"
    fi
}

# Function to check if a port is in use
check_port() {
    local port=$1
    local service=$2
    if ss -tuln | grep -q ":$port "; then
        echo -e "${GREEN}✓${NC} $service is running on port $port"
    else
        echo -e "${RED}✗${NC} $service is not running on port $port"
    fi
}

# Function to check if a command exists
command_exists() {
    if command -v $1 &> /dev/null; then
        echo -e "${GREEN}✓${NC} $1 is installed"
    else
        echo -e "${RED}✗${NC} $1 is not installed"
    fi
}

echo -e "${YELLOW}=== System Status Check ===${NC}"

# Check system resources
echo -e "\n${YELLOW}System Resources:${NC}"
echo "CPU Load: $(uptime | awk -F'load average:' '{print $2}')"
echo "Memory Usage: $(free -h | grep Mem | awk '{print $3 "/" $2}')"
echo "Disk Usage:"
df -h | grep -v "tmpfs" | grep -v "loop"

# Check required services
echo -e "\n${YELLOW}Services:${NC}"
check_service "mongod"
check_service "nginx"
check_service "supervisor"

# Check required ports
echo -e "\n${YELLOW}Ports:${NC}"
check_port 80 "Nginx"
check_port 27017 "MongoDB"
check_port 8000 "Application"

# Check required commands
echo -e "\n${YELLOW}Dependencies:${NC}"
command_exists "python3"
command_exists "pip3"
command_exists "node"
command_exists "npm"
command_exists "yarn"
command_exists "mongodump"
command_exists "mongorestore"

# Check virtual environment
echo -e "\n${YELLOW}Python Environment:${NC}"
if [ -d "venv" ]; then
    echo -e "${GREEN}✓${NC} Virtual environment exists"
    
    # Activate virtual environment and check Python packages
    if source venv/bin/activate; then
        echo -e "${GREEN}✓${NC} Virtual environment activated"
        
        # Check Python version
        echo -n "Python version: "
        python3 --version
        
        # Check installed packages
        echo -e "\n${YELLOW}Installed Python Packages:${NC}"
        pip list | grep -E 'flask|mongoengine|gunicorn|pymongo|python-dotenv|flask-admin|wtforms|email-validator'
        
        deactivate
    else
        echo -e "${RED}✗${NC} Failed to activate virtual environment"
    fi
else
    echo -e "${RED}✗${NC} Virtual environment not found"
fi

# Check application status
echo -e "\n${YELLOW}Application Status:${NC}"
if [ -f ".env" ]; then
    echo -e "${GREEN}✓${NC} .env file exists"
else
    echo -e "${YELLOW}⚠${NC} .env file is missing"
fi

# Check if application is running
if pgrep -f "gunicorn" > /dev/null; then
    echo -e "${GREEN}✓${NC} Application is running"
else
    echo -e "${RED}✗${NC} Application is not running"
fi

# Check database connection
echo -e "\n${YELLOW}Database Connection:${NC}"
if command -v mongo &> /dev/null; then
    if mongo --eval "db.adminCommand('ping')" &> /dev/null; then
        echo -e "${GREEN}✓${NC} Successfully connected to MongoDB"
        
        # Get database stats
        echo -e "\n${YELLOW}Database Stats:${NC}"
        mongo --eval "db = db.getSiblingDB('ep_simulator'); printjson(db.stats())" | grep -E 'db|collections|objects|dataSize|storageSize|indexes|indexSize'
    else
        echo -e "${RED}✗${NC} Failed to connect to MongoDB"
    fi
else
    echo -e "${YELLOW}⚠${NC} MongoDB client not installed"
fi

echo -e "\n${YELLOW}Status check completed!${NC}"
