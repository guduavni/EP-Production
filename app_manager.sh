#!/bin/bash

# Exit on error
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="ep-simulator"
APP_USER=$(whoami)
APP_DIR=$(pwd)
VENV_DIR="${APP_DIR}/venv"
GUNICORN_CONF="${APP_DIR}/gunicorn_conf.py"
LOG_DIR="/var/log/${APP_NAME}"
PID_DIR="/var/run/${APP_NAME}"

# Ensure running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${YELLOW}Please run as root or with sudo${NC}"
    exit 1
fi

# Create necessary directories
mkdir -p "${LOG_DIR}"
mkdir -p "${PID_DIR}"
chown -R ${APP_USER}:${APP_USER} "${LOG_DIR}"
chown -R ${APP_USER}:${APP_USER} "${PID_DIR}"

# Function to start the application
start() {
    echo -e "${GREEN}Starting ${APP_NAME}...${NC}"
    
    # Check if already running
    if [ -f "${PID_DIR}/gunicorn.pid" ]; then
        PID=$(cat "${PID_DIR}/gunicorn.pid")
        if ps -p $PID > /dev/null; then
            echo -e "${YELLOW}${APP_NAME} is already running (PID: ${PID})${NC}"
            return 1
        fi
    fi
    
    # Activate virtual environment and start Gunicorn
    cd "${APP_DIR}"
    source "${VENV_DIR}/bin/activate"
    
    nohup "${VENV_DIR}/bin/gunicorn" --config "${GUNICORN_CONF}" "run_simple:app" > "${LOG_DIR}/app.log" 2>&1 & 
    echo $! > "${PID_DIR}/gunicorn.pid"
    
    echo -e "${GREEN}${APP_NAME} started successfully${NC}"
}

# Function to stop the application
stop() {
    echo -e "${YELLOW}Stopping ${APP_NAME}...${NC}"
    
    if [ ! -f "${PID_DIR}/gunicorn.pid" ]; then
        echo -e "${YELLOW}${APP_NAME} is not running${NC}"
        return 1
    fi
    
    PID=$(cat "${PID_DIR}/gunicorn.pid")
    
    if ps -p $PID > /dev/null; then
        kill -TERM $PID
        sleep 2
        
        if ps -p $PID > /dev/null; then
            echo -e "${YELLOW}Graceful shutdown failed, forcing...${NC}"
            kill -9 $PID
        fi
        
        rm -f "${PID_DIR}/gunicorn.pid"
        echo -e "${GREEN}${APP_NAME} stopped successfully${NC}"
    else
        echo -e "${YELLOW}${APP_NAME} was not running${NC}"
        rm -f "${PID_DIR}/gunicorn.pid"
    fi
}

# Function to restart the application
restart() {
    stop
    sleep 2
    start
}

# Function to check application status
status() {
    if [ -f "${PID_DIR}/gunicorn.pid" ]; then
        PID=$(cat "${PID_DIR}/gunicorn.pid")
        if ps -p $PID > /dev/null; then
            echo -e "${GREEN}${APP_NAME} is running (PID: ${PID})${NC}"
            return 0
        else
            echo -e "${YELLOW}${APP_NAME} PID file exists but process is not running${NC}"
            return 1
        fi
    else
        echo -e "${YELLOW}${APP_NAME} is not running${NC}"
        return 1
    fi
}

# Function to view application logs
logs() {
    echo -e "${YELLOW}=== Application Logs (last 50 lines) ===${NC}"
    tail -n 50 "${LOG_DIR}/app.log"
}

# Function to show help
show_help() {
    echo "Usage: $0 {start|stop|restart|status|logs|help}"
    echo ""
    echo "Options:"
    echo "  start     Start the application"
    echo "  stop      Stop the application"
    echo "  restart   Restart the application"
    echo "  status    Check application status"
    echo "  logs      View application logs"
    echo "  help      Show this help message"
    echo ""
    exit 1
}

# Main script logic
case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    status)
        status
        ;;
    logs)
        logs
        ;;
    *)
        show_help
        ;;
esac

exit 0
