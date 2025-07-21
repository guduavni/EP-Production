#!/bin/bash

# Exit on error
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
BACKUP_DIR="/var/backups/ep-simulator"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/ep-simulator_${TIMESTAMP}.gz"

# Ensure backup directory exists
mkdir -p "${BACKUP_DIR}"

# Get MongoDB URI from environment or use default
MONGO_URI="${MONGODB_URI:-mongodb://localhost:27017/ep_simulator}"

# Extract database name from URI
DB_NAME=$(echo "${MONGO_URI}" | grep -oP '(?<=/)[^/]+$')

# Check if mongodump is available
if ! command -v mongodump &> /dev/null; then
    echo -e "${YELLOW}mongodump not found. Please install MongoDB database tools.${NC}"
    exit 1
fi

echo -e "${GREEN}Starting database backup...${NC}"
echo -e "Database: ${DB_NAME}"
echo -e "Backup file: ${BACKUP_FILE}"

# Create backup
mongodump --uri="${MONGO_URI}" --archive="${BACKUP_FILE}" --gzip

# Check if backup was successful
if [ $? -eq 0 ]; then
    echo -e "${GREEN}Backup completed successfully!${NC}"
    
    # List all backups, sorted by modification time (newest first)
    echo -e "\n${YELLOW}Available backups (newest first):${NC}"
    ls -lt "${BACKUP_DIR}/"*.gz 2>/dev/null | head -n 10
    
    # Optional: Remove backups older than 30 days
    echo -e "\n${YELLOW}Cleaning up old backups (older than 30 days)...${NC}"
    find "${BACKUP_DIR}" -name "*.gz" -type f -mtime +30 -delete -print
else
    echo -e "${YELLOW}Backup failed!${NC}" >&2
    exit 1
fi
