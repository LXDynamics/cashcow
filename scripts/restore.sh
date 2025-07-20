#!/bin/bash
# CashCow Restore Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
BACKUP_DIR="./backups"
BACKUP_FILE="$1"

if [ -z "$BACKUP_FILE" ]; then
    echo -e "${RED}❌ Usage: $0 <backup_file>${NC}"
    echo -e "Available backups:"
    ls -la "$BACKUP_DIR"/cashcow_backup_*.tar.gz 2>/dev/null || echo "No backups found"
    exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo -e "${RED}❌ Backup file not found: $BACKUP_FILE${NC}"
    exit 1
fi

echo -e "${GREEN}🔄 Starting CashCow restore from $BACKUP_FILE${NC}"

# Confirm restoration
echo -e "${YELLOW}⚠️  This will overwrite existing data. Continue? (y/N)${NC}"
read -r CONFIRM
if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
    echo -e "${RED}❌ Restore cancelled${NC}"
    exit 1
fi

# Stop services
echo -e "${GREEN}⏹️  Stopping services${NC}"
docker-compose down || true

# Create backup of current state
echo -e "${GREEN}💾 Creating backup of current state${NC}"
CURRENT_BACKUP="current_state_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
tar -czf "$BACKUP_DIR/$CURRENT_BACKUP.tar.gz" \
    --exclude='*.log' \
    --exclude='__pycache__' \
    --exclude='node_modules' \
    --exclude='build' \
    --exclude='.git' \
    --exclude='backups' \
    entities/ config/ scenarios/ data/ 2>/dev/null || true

# Extract backup
echo -e "${GREEN}📦 Extracting backup${NC}"
tar -xzf "$BACKUP_FILE"

# Restore database if PostgreSQL backup exists
DB_BACKUP="${BACKUP_FILE%%.tar.gz}_db.sql.gz"
if [ -f "$DB_BACKUP" ]; then
    echo -e "${GREEN}🗄️  Database backup found. Starting PostgreSQL for restore${NC}"
    docker-compose up -d postgres
    sleep 10
    
    echo -e "${GREEN}🔄 Restoring database${NC}"
    zcat "$DB_BACKUP" | docker-compose exec -T postgres psql -U cashcow -d cashcow
fi

# Start services
echo -e "${GREEN}🚀 Starting services${NC}"
docker-compose up -d

# Wait for services
echo -e "${GREEN}⏳ Waiting for services to be ready${NC}"
sleep 30

# Health check
if docker-compose exec -T cashcow curl -f http://localhost:8000/api/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Restore completed successfully!${NC}"
    echo -e "Current state backup saved as: $BACKUP_DIR/$CURRENT_BACKUP.tar.gz"
else
    echo -e "${RED}❌ Service health check failed after restore${NC}"
    echo -e "You may need to check the logs: docker-compose logs"
    exit 1
fi