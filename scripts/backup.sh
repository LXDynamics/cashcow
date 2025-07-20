#!/bin/bash
# CashCow Backup Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="cashcow_backup_$TIMESTAMP"

echo -e "${GREEN}💾 Starting CashCow backup${NC}"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Create backup archive
echo -e "${GREEN}📦 Creating backup archive${NC}"
tar -czf "$BACKUP_DIR/$BACKUP_NAME.tar.gz" \
    --exclude='*.log' \
    --exclude='__pycache__' \
    --exclude='node_modules' \
    --exclude='build' \
    --exclude='.git' \
    --exclude='backups' \
    --exclude='data/*.db-wal' \
    --exclude='data/*.db-shm' \
    entities/ \
    config/ \
    scenarios/ \
    data/ \
    .env \
    CLAUDE.md

# Backup database if PostgreSQL
if [ -f ".env" ]; then
    source .env
    if [[ "$DATABASE_URL" == postgresql* ]]; then
        echo -e "${GREEN}🗄️  Backing up PostgreSQL database${NC}"
        docker-compose exec -T postgres pg_dump -U cashcow cashcow | gzip > "$BACKUP_DIR/${BACKUP_NAME}_db.sql.gz"
    fi
fi

# Create manifest file
echo -e "${GREEN}📋 Creating backup manifest${NC}"
cat > "$BACKUP_DIR/${BACKUP_NAME}_manifest.txt" << EOF
CashCow Backup Manifest
======================
Backup Date: $(date)
Backup Name: $BACKUP_NAME
Hostname: $(hostname)
User: $(whoami)
Git Commit: $(git rev-parse HEAD 2>/dev/null || echo "Not a git repository")

Files Included:
$(tar -tzf "$BACKUP_DIR/$BACKUP_NAME.tar.gz" | head -20)
$([ $(tar -tzf "$BACKUP_DIR/$BACKUP_NAME.tar.gz" | wc -l) -gt 20 ] && echo "... and $(( $(tar -tzf "$BACKUP_DIR/$BACKUP_NAME.tar.gz" | wc -l) - 20 )) more files")

Backup Size: $(du -h "$BACKUP_DIR/$BACKUP_NAME.tar.gz" | cut -f1)
EOF

# Clean up old backups (keep last 30)
echo -e "${GREEN}🧹 Cleaning up old backups${NC}"
cd "$BACKUP_DIR"
ls -t cashcow_backup_*.tar.gz | tail -n +31 | xargs -r rm -f
ls -t cashcow_backup_*_db.sql.gz | tail -n +31 | xargs -r rm -f
ls -t cashcow_backup_*_manifest.txt | tail -n +31 | xargs -r rm -f
cd ..

# Upload to S3 if configured
if [ -n "$BACKUP_S3_BUCKET" ] && [ -n "$AWS_ACCESS_KEY_ID" ]; then
    echo -e "${GREEN}☁️  Uploading backup to S3${NC}"
    aws s3 cp "$BACKUP_DIR/$BACKUP_NAME.tar.gz" "s3://$BACKUP_S3_BUCKET/cashcow/" || echo -e "${YELLOW}⚠️  S3 upload failed${NC}"
    if [ -f "$BACKUP_DIR/${BACKUP_NAME}_db.sql.gz" ]; then
        aws s3 cp "$BACKUP_DIR/${BACKUP_NAME}_db.sql.gz" "s3://$BACKUP_S3_BUCKET/cashcow/" || echo -e "${YELLOW}⚠️  S3 DB upload failed${NC}"
    fi
fi

echo -e "${GREEN}✅ Backup completed: $BACKUP_NAME.tar.gz${NC}"
echo -e "Backup location: $BACKUP_DIR/$BACKUP_NAME.tar.gz"
echo -e "Backup size: $(du -h "$BACKUP_DIR/$BACKUP_NAME.tar.gz" | cut -f1)"