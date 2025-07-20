# CashCow Deployment Guide

This guide covers deploying CashCow in both development and production environments using Docker.

## Quick Start

### Development Deployment

```bash
# Clone the repository
git clone <repository-url>
cd cashcow

# Copy environment template
cp .env.example .env

# Edit .env with your settings
nano .env

# Deploy development environment
make deploy
# Or manually: ./scripts/deploy.sh development
```

The application will be available at:
- Frontend: http://localhost
- API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Grafana: http://localhost:3001
- Prometheus: http://localhost:9090

### Production Deployment

```bash
# Copy and configure production environment
cp .env.example .env
# Update all production values in .env

# Deploy production environment
make deploy-prod
# Or manually: ./scripts/deploy.sh production
```

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     Nginx       │    │   FastAPI App   │    │   PostgreSQL    │
│  (Reverse Proxy)│───▶│    (Python)     │───▶│   (Database)    │
│     Port 80     │    │    Port 8000    │    │    Port 5432    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  React Frontend │    │      Redis      │    │   Monitoring    │
│  (Static Files) │    │     (Cache)     │    │ (Grafana/Prom)  │
│                 │    │    Port 6379    │    │   Ports 3001    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Environment Configuration

### Required Environment Variables

Create a `.env` file from `.env.example` and configure:

#### Security (Required)
```bash
JWT_SECRET_KEY=your-very-secure-jwt-secret-key-change-this
POSTGRES_PASSWORD=your-secure-postgres-password
REDIS_PASSWORD=your-redis-password
GRAFANA_PASSWORD=your-grafana-admin-password
```

#### Database
```bash
# Development (SQLite)
DATABASE_URL=sqlite:///app/data/cashcow.db

# Production (PostgreSQL)
DATABASE_URL=postgresql://cashcow:password@postgres:5432/cashcow
```

#### Application
```bash
DEVELOPMENT_MODE=false
LOG_LEVEL=INFO
WORKERS=4
CORS_ORIGINS=https://your-domain.com
```

### Optional Configuration

#### Email Notifications
```bash
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=notifications@example.com
SMTP_PASSWORD=your-smtp-password
```

#### Cloud Backup (S3)
```bash
BACKUP_S3_BUCKET=cashcow-backups
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_REGION=us-east-1
```

## Docker Services

### Development Environment (`docker-compose.yml`)
- **cashcow**: Main application container
- **nginx**: Reverse proxy and static file serving
- **redis**: Caching and session storage

### Production Environment (`docker-compose.prod.yml`)
- **cashcow**: Main application container (4 workers)
- **postgres**: PostgreSQL database
- **redis**: Redis with authentication
- **nginx**: Production nginx with SSL
- **prometheus**: Metrics collection
- **grafana**: Monitoring dashboards

## SSL/TLS Configuration

### Development
HTTP only (no SSL required)

### Production
1. Obtain SSL certificates (Let's Encrypt recommended):
```bash
# Using certbot
sudo certbot certonly --webroot -w /var/www/html -d your-domain.com
```

2. Copy certificates to `ssl/` directory:
```bash
mkdir ssl/
cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ssl/
cp /etc/letsencrypt/live/your-domain.com/privkey.pem ssl/
```

3. Update nginx configuration with your domain name.

## Deployment Commands

### Using Make
```bash
make help                    # Show all available commands
make deploy                  # Deploy development
make deploy-prod            # Deploy production
make start                   # Start services
make stop                    # Stop services
make restart                 # Restart services
make logs                    # View logs
make backup                  # Create backup
make restore BACKUP=file     # Restore from backup
```

### Using Scripts Directly
```bash
./scripts/deploy.sh development
./scripts/deploy.sh production
./scripts/backup.sh
./scripts/restore.sh backup_file.tar.gz
```

## Backup and Restore

### Automatic Backups
Configure automatic backups in production:

```bash
# Add to crontab
0 2 * * * /path/to/cashcow/scripts/backup.sh
```

### Manual Backup
```bash
make backup
# Or
./scripts/backup.sh
```

Creates timestamped backup in `backups/` directory containing:
- Entity YAML files
- Configuration files
- Database dump (if PostgreSQL)
- Environment configuration

### Restore from Backup
```bash
make restore BACKUP=backups/cashcow_backup_20241201_020000.tar.gz
# Or
./scripts/restore.sh backups/cashcow_backup_20241201_020000.tar.gz
```

## Monitoring and Logging

### Grafana Dashboards
Access at http://localhost:3001 (development) or https://your-domain.com:3001 (production)

Default login: admin / (password from GRAFANA_PASSWORD)

### Prometheus Metrics
Access at http://localhost:9090 (development) or https://your-domain.com:9090 (production)

### Application Logs
```bash
# View real-time logs
make logs

# View specific service logs
docker-compose logs -f cashcow
docker-compose logs -f nginx
docker-compose logs -f postgres
```

### Log Files
- Application logs: `logs/cashcow.log`
- Nginx logs: `nginx/logs/`
- Database logs: In PostgreSQL container

## Performance Tuning

### FastAPI Workers
Adjust worker count based on CPU cores:
```bash
WORKERS=4  # Recommended: 2 * CPU cores
```

### Database Connection Pool
For high-traffic deployments, configure connection pooling:
```bash
DATABASE_URL=postgresql://user:pass@host:5432/db?pool_size=20&max_overflow=0
```

### Redis Configuration
For production caching:
```bash
# In redis.conf
maxmemory 256mb
maxmemory-policy allkeys-lru
```

## Security Considerations

### Production Checklist
- [ ] Change all default passwords
- [ ] Generate secure JWT secret key
- [ ] Configure firewall rules
- [ ] Set up SSL certificates
- [ ] Enable fail2ban for brute force protection
- [ ] Configure database backups
- [ ] Set up monitoring alerts
- [ ] Review CORS origins
- [ ] Disable debug mode
- [ ] Update system packages

### Firewall Configuration
```bash
# Allow only necessary ports
ufw allow 22    # SSH
ufw allow 80    # HTTP
ufw allow 443   # HTTPS
ufw enable
```

### Database Security
- Use strong passwords
- Enable SSL connections
- Regular security updates
- Backup encryption

## Troubleshooting

### Common Issues

#### Service Won't Start
```bash
# Check logs
docker-compose logs cashcow

# Check health
make health

# Restart services
make restart
```

#### Database Connection Issues
```bash
# Check PostgreSQL status
docker-compose exec postgres pg_isready -U cashcow

# Reset database
make db-reset
```

#### Permission Issues
```bash
# Fix permissions
sudo chown -R $USER:$USER data/ logs/ reports/
chmod 755 data/ logs/ reports/
```

#### SSL Certificate Issues
```bash
# Verify certificate files
ls -la ssl/
openssl x509 -in ssl/fullchain.pem -text -noout
```

### Performance Issues
```bash
# Monitor resource usage
docker stats

# Check slow queries
docker-compose exec postgres psql -U cashcow -d cashcow -c "SELECT * FROM pg_stat_activity;"

# Review metrics
curl http://localhost:8000/api/metrics
```

## Maintenance

### Regular Tasks
- Update Docker images
- Backup verification
- Log rotation
- SSL certificate renewal
- Security patches
- Performance monitoring

### Updates
```bash
# Pull latest code
git pull origin main

# Rebuild and restart
make stop
make build
make start
```

### Health Monitoring
Set up monitoring alerts for:
- Service availability
- Response time
- Error rates
- Disk space
- Memory usage
- Database connections

## Support

For issues and support:
1. Check application logs
2. Review this deployment guide
3. Check GitHub issues
4. Contact support team

---

**Note**: Always test deployments in a staging environment before production deployment.