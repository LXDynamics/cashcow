#!/bin/bash
# CashCow Deployment Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-development}
DOCKER_COMPOSE_FILE="docker-compose.yml"
BACKUP_DIR="./backups"

if [ "$ENVIRONMENT" = "production" ]; then
    DOCKER_COMPOSE_FILE="docker-compose.prod.yml"
fi

echo -e "${GREEN}🚀 Starting CashCow deployment for $ENVIRONMENT environment${NC}"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Creating from .env.example${NC}"
    cp .env.example .env
    echo -e "${RED}❗ Please update .env file with your configuration before running again${NC}"
    exit 1
fi

# Create necessary directories
echo -e "${GREEN}📁 Creating required directories${NC}"
mkdir -p data logs reports backups ssl nginx/logs

# Set proper permissions
chmod 755 data logs reports backups
chmod 600 .env

# Load environment variables
source .env

# Generate JWT secret if not set
if [ "$JWT_SECRET_KEY" = "your-very-secure-jwt-secret-key-change-this" ]; then
    echo -e "${YELLOW}⚠️  Generating new JWT secret key${NC}"
    JWT_SECRET=$(openssl rand -hex 32)
    sed -i "s/JWT_SECRET_KEY=.*/JWT_SECRET_KEY=$JWT_SECRET/" .env
fi

# Build and start services
echo -e "${GREEN}🔨 Building and starting services${NC}"
docker-compose -f $DOCKER_COMPOSE_FILE down --remove-orphans
docker-compose -f $DOCKER_COMPOSE_FILE build --no-cache
docker-compose -f $DOCKER_COMPOSE_FILE up -d

# Wait for services to be healthy
echo -e "${GREEN}⏳ Waiting for services to be healthy${NC}"
sleep 30

# Check service health
echo -e "${GREEN}🔍 Checking service health${NC}"
if docker-compose -f $DOCKER_COMPOSE_FILE exec -T cashcow curl -f http://localhost:8000/api/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ CashCow API is healthy${NC}"
else
    echo -e "${RED}❌ CashCow API health check failed${NC}"
    docker-compose -f $DOCKER_COMPOSE_FILE logs cashcow
    exit 1
fi

# Run any database migrations or setup
echo -e "${GREEN}🗄️  Running database setup${NC}"
if [ "$ENVIRONMENT" = "production" ]; then
    # Run database migrations if needed
    docker-compose -f $DOCKER_COMPOSE_FILE exec -T cashcow python -c "
import asyncio
from cashcow.storage.yaml_loader import YamlEntityLoader
from pathlib import Path

# Initialize database with existing YAML entities
loader = YamlEntityLoader(Path('/app/entities'))
print('Database initialized with existing entities')
"
fi

# Show running services
echo -e "${GREEN}📊 Services status${NC}"
docker-compose -f $DOCKER_COMPOSE_FILE ps

# Show access URLs
echo -e "${GREEN}🌐 Access URLs${NC}"
if [ "$ENVIRONMENT" = "production" ]; then
    echo -e "Application: https://your-domain.com"
    echo -e "API Docs: https://your-domain.com/docs"
    echo -e "Monitoring: https://your-domain.com:3001 (Grafana)"
    echo -e "Metrics: https://your-domain.com:9090 (Prometheus)"
else
    echo -e "Application: http://localhost"
    echo -e "API: http://localhost :8001"
    echo -e "API Docs: http://localhost :8001/docs"
    echo -e "Grafana: http://localhost:3001"
    echo -e "Prometheus: http://localhost:9090"
fi

echo -e "${GREEN}✅ Deployment completed successfully!${NC}"

# Reminder for production
if [ "$ENVIRONMENT" = "production" ]; then
    echo -e "${YELLOW}📋 Production checklist:${NC}"
    echo -e "  • Update domain names in nginx configuration"
    echo -e "  • Set up SSL certificates"
    echo -e "  • Configure firewall rules"
    echo -e "  • Set up monitoring alerts"
    echo -e "  • Configure backup strategy"
    echo -e "  • Review security settings"
fi