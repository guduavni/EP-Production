#!/bin/bash

# Exit on error
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
BACKUP_DIR="/var/backups/ep-simulator"

# Get MongoDB URI from environment or use default
MONGO_URI="${MONGODB_URI:-mongodb://localhost:27017/ep_simulator}"

# Check if mongorestore is available
if ! command -v mongorestore &> /dev/null; then
    echo -e "${YELLOW}mongorestore not found. Please install MongoDB database tools.${NC}"
    exit 1
fi

# List available backups
echo -e "${YELLOW}Available backups:${NC}"
BACKUP_FILES=($(ls -t "${BACKUP_DIR}/"*.gz 2>/dev/null))

if [ ${#BACKUP_FILES[@]} -eq 0 ]; then
    echo -e "${RED}No backup files found in ${BACKUP_DIR}${NC}"
    exit 1
fi

PS3="Select a backup to restore (or 'q' to quit): "
select BACKUP_FILE in "${BACKUP_FILES[@]}" "Quit"; do
    case $BACKUP_FILE in
        "Quit")
            echo -e "${YELLOW}Operation cancelled.${NC}"
            exit 0
            ;;
        *)
            if [ -z "$BACKUP_FILE" ]; then
                echo -e "${RED}Invalid selection. Please try again.${NC}"
                continue
            fi
            
            echo -e "\n${YELLOW}You are about to restore from:${NC} ${BACKUP_FILE}"
            echo -e "${RED}WARNING: This will overwrite the current database!${NC}"
            read -p "Are you sure you want to continue? (y/N): " confirm
            
            if [[ ! $confirm =~ ^[Yy]$ ]]; then
                echo -e "${YELLOW}Restore cancelled.${NC}"
                exit 0
            fi
            
            # Create a backup before restoring
            echo -e "${GREEN}Creating a backup of the current database...${NC}"
            ./backup_db.sh
            
            # Restore the selected backup
            echo -e "\n${GREEN}Restoring database from backup...${NC}"
            mongorestore --uri="${MONGO_URI}" --drop --gzip --archive="${BACKUP_FILE}"
            
            if [ $? -eq 0 ]; then
                echo -e "\n${GREEN}Database restored successfully!${NC}"
            else
                echo -e "\n${RED}Database restore failed!${NC}" >&2
                exit 1
            fi
            
            break
            ;;
    esac
done
