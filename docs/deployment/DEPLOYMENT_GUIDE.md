# AI-Discover Production Deployment Guide

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Initial Deployment](#initial-deployment)
4. [Deployment Commands](#deployment-commands)
5. [Monitoring and Health Checks](#monitoring-and-health-checks)
6. [Backup and Restore](#backup-and-restore)
7. [Troubleshooting](#troubleshooting)
8. [Security Checklist](#security-checklist)
9. [Scaling and Performance](#scaling-and-performance)
10. [Disaster Recovery](#disaster-recovery)

## Prerequisites

### System Requirements

- **Operating System**: Ubuntu 20.04+ or CentOS 8+
- **CPU**: Minimum 4 cores, recommended 8+ cores
- **RAM**: Minimum 8GB, recommended 16GB+
- **Storage**: Minimum 50GB available space, SSD recommended
- **Network**: Stable internet connection with ports 80, 443 open

### Software Dependencies

1. **Docker Engine** (20.10+)

   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   sudo usermod -aG docker $USER
   ```

2. **Docker Compose** (2.0+)

   ```bash
   sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose
   ```

3. **Git**

   ```bash
   sudo apt-get update && sudo apt-get install -y git
   ```

4. **Additional Tools**

   ```bash
   sudo apt-get install -y curl jq htop iotop
   ```

## Environment Setup

### 1. Clone Repository

```bash
git clone https://github.com/your-org/ai-discover.git
cd ai-discover
```

### 2. Configure Environment Variables

```bash
# Copy production environment template
cp .env.production.example .env.production

# Edit with your values
nano .env.production
```

#### Required Environment Variables

| Variable              | Description                                              | Example                       |
| --------------------- | -------------------------------------------------------- | ----------------------------- |
| `SECRET_KEY`          | Django secret key (generate with `openssl rand -hex 32`) | `a1b2c3d4...`                 |
| `POSTGRES_USER`       | PostgreSQL username                                      | `ai_discover_prod`            |
| `POSTGRES_PASSWORD`   | PostgreSQL password (strong)                             | `StrongP@ssw0rd!`             |
| `POSTGRES_DB`         | Database name                                            | `ai_discover_production`      |
| `REDIS_PASSWORD`      | Redis password (strong)                                  | `R3d1sP@ssw0rd!`              |
| `OPENAI_API_KEY`      | OpenAI API key                                           | `sk-...`                      |
| `CORS_ORIGINS`        | Allowed CORS origins                                     | `https://your-domain.com`     |
| `NEXT_PUBLIC_API_URL` | API URL for frontend                                     | `https://api.your-domain.com` |

### 3. SSL Certificates

For production, you need valid SSL certificates:

```bash
# Create SSL directory
mkdir -p nginx/ssl

# Option 1: Let's Encrypt (recommended)
sudo apt-get install certbot
sudo certbot certonly --standalone -d your-domain.com -d api.your-domain.com

# Copy certificates
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem nginx/ssl/key.pem

# Option 2: Self-signed (for testing only)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/key.pem \
  -out nginx/ssl/cert.pem
```

## Initial Deployment

### 1. Pre-deployment Checks

Run the deployment script in check mode:

```bash
./scripts/deploy.sh check
```

This validates:

- All required environment variables are set
- Docker and Docker Compose are installed
- Sufficient disk space is available
- Network connectivity

### 2. Build and Deploy

```bash
# Full deployment with all checks
./scripts/deploy.sh deploy

# Or step by step:
./scripts/deploy.sh build    # Build images
./scripts/deploy.sh migrate  # Run database migrations
./scripts/deploy.sh start    # Start services
./scripts/deploy.sh health   # Verify health
```

### 3. Verify Deployment

```bash
# Check service status
./scripts/deploy.sh status

# View logs
./scripts/deploy.sh logs

# Access services:
# - Frontend: https://your-domain.com
# - API: https://api.your-domain.com
# - API Docs: https://api.your-domain.com/docs
# - Flower: http://your-domain.com:5555 (if enabled)
# - Grafana: http://your-domain.com:3000 (if enabled)
```

## Deployment Commands

### deploy.sh Usage

```bash
./scripts/deploy.sh [command] [options]

Commands:
  deploy    - Full deployment with health checks
  status    - Show current deployment status
  logs      - Show logs (optionally for specific service)
  rollback  - Rollback to previous version
  backup    - Create database backup
  health    - Run health checks on all services
  stop      - Stop all services
  start     - Start all services
  restart   - Restart all services

Examples:
  ./scripts/deploy.sh deploy              # Full deployment
  ./scripts/deploy.sh logs backend        # View backend logs
  ./scripts/deploy.sh rollback            # Rollback deployment
```

### Docker Compose Commands

```bash
# Using production compose file
docker-compose -f docker-compose.prod.yml [command]

# Common commands:
docker-compose -f docker-compose.prod.yml ps              # List services
docker-compose -f docker-compose.prod.yml logs -f backend # Follow logs
docker-compose -f docker-compose.prod.yml exec backend bash # Shell access
docker-compose -f docker-compose.prod.yml restart celery  # Restart service
```

## Monitoring and Health Checks

### Health Check Endpoints

1. **Backend Health**: `https://api.your-domain.com/health`

   ```json
   {
     "status": "healthy",
     "version": "1.0.0",
     "environment": "production",
     "checks": {
       "database": { "status": "healthy" },
       "redis": { "status": "healthy" },
       "openai": { "status": "configured" }
     }
   }
   ```

2. **Frontend Health**: `https://your-domain.com/api/health`

   ```json
   {
     "status": "healthy",
     "timestamp": "2024-01-26T10:00:00Z",
     "checks": {
       "frontend": { "status": "healthy" },
       "backend": { "status": "healthy" }
     }
   }
   ```

### Monitoring Stack

#### Accessing Monitoring Tools

1. **Prometheus**: <http://localhost:9090>

   - Metrics collection and alerting
   - Query examples:

     ```promql
     # API request rate
     sum(rate(http_requests_total{job="backend"}[5m]))

     # Database connections
     pg_stat_database_numbackends{datname="ai_discover_production"}

     # Redis memory usage
     redis_memory_used_bytes / redis_memory_max_bytes
     ```

2. **Grafana**: <http://localhost:3000>

   - Default login: admin / `GRAFANA_ADMIN_PASSWORD`
   - Pre-configured dashboards:
     - AI-Discover Overview
     - System Metrics
     - Container Metrics

3. **Flower** (Celery monitoring): <http://localhost:5555>
   - Default login: admin / `FLOWER_BASIC_AUTH`
   - Monitor task queues and workers

### Alert Configuration

Alerts are configured in `monitoring/alerts/`:

- `application.yml`: Application-specific alerts
- `system.yml`: System resource alerts

To add custom alerts:

```yaml
- alert: CustomAlert
  expr: your_prometheus_query > threshold
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "Alert summary"
    description: "Detailed description"
```

## Backup and Restore

### Automated Backups

The deployment includes automated daily backups:

```bash
# Manual backup
./scripts/deploy.sh backup

# Backup location: ./backups/postgres_backup_YYYYMMDD_HHMMSS.sql.gz
```

### Backup Configuration

Add to crontab for automated backups:

```bash
# Daily backup at 2 AM
0 2 * * * /path/to/ai-discover/scripts/deploy.sh backup
```

### Restore Procedure

1. **Stop services**:

   ```bash
   ./scripts/deploy.sh stop
   ```

2. **Restore database**:

   ```bash
   # Decompress backup
   gunzip backups/postgres_backup_20240126_020000.sql.gz

   # Restore
   docker-compose -f docker-compose.prod.yml run --rm postgres \
     psql -U $POSTGRES_USER -d $POSTGRES_DB < backups/postgres_backup_20240126_020000.sql
   ```

3. **Start services**:

   ```bash
   ./scripts/deploy.sh start
   ```

### Backup to S3 (Optional)

```bash
# Install AWS CLI
sudo apt-get install awscli

# Configure
aws configure

# Backup script with S3 upload
cat > scripts/backup-to-s3.sh << 'EOF'
#!/bin/bash
BACKUP_FILE=$(./scripts/deploy.sh backup | grep "backed up to" | awk '{print $NF}')
aws s3 cp $BACKUP_FILE s3://your-backup-bucket/ai-discover/
find ./backups -name "*.sql.gz" -mtime +7 -delete
EOF

chmod +x scripts/backup-to-s3.sh
```

## Troubleshooting

### Common Issues

#### 1. Service Won't Start

```bash
# Check logs
./scripts/deploy.sh logs [service-name]

# Common causes:
# - Port already in use
sudo lsof -i :8800  # Check backend port
sudo lsof -i :3300  # Check frontend port

# - Database connection issues
docker-compose -f docker-compose.prod.yml exec postgres pg_isready

# - Environment variables missing
./scripts/deploy.sh check
```

#### 2. Database Migration Failures

```bash
# Run migrations manually
docker-compose -f docker-compose.prod.yml run --rm backend \
  alembic upgrade head

# Rollback if needed
docker-compose -f docker-compose.prod.yml run --rm backend \
  alembic downgrade -1
```

#### 3. High Memory Usage

```bash
# Check memory usage
docker stats

# Limit container memory in docker-compose.prod.yml
deploy:
  resources:
    limits:
      memory: 2G
```

#### 4. Celery Task Failures

```bash
# Check Celery logs
./scripts/deploy.sh logs celery

# Restart workers
docker-compose -f docker-compose.prod.yml restart celery celery-beat

# Purge task queue
docker-compose -f docker-compose.prod.yml exec redis \
  redis-cli -a $REDIS_PASSWORD FLUSHDB
```

### Debug Mode

Enable debug logging:

```bash
# Set in .env.production
LOG_LEVEL=DEBUG

# Restart services
./scripts/deploy.sh restart
```

### Container Shell Access

```bash
# Backend shell
docker-compose -f docker-compose.prod.yml exec backend bash

# Database shell
docker-compose -f docker-compose.prod.yml exec postgres psql -U $POSTGRES_USER -d $POSTGRES_DB

# Redis CLI
docker-compose -f docker-compose.prod.yml exec redis redis-cli -a $REDIS_PASSWORD
```

## Security Checklist

### Pre-deployment Security

- [ ] Change all default passwords
- [ ] Generate strong SECRET_KEY: `openssl rand -hex 32`
- [ ] Configure firewall rules
- [ ] Enable fail2ban for SSH
- [ ] Disable root SSH access
- [ ] Set up SSL certificates
- [ ] Review environment variables for sensitive data

### Network Security

```bash
# UFW firewall setup
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# Fail2ban for brute force protection
sudo apt-get install fail2ban
sudo systemctl enable fail2ban
```

### Application Security

1. **API Rate Limiting**: Configured in nginx.conf
2. **CORS**: Set `CORS_ORIGINS` to your domain only
3. **Security Headers**: Automatically added by nginx
4. **Database Security**:

   ```sql
   -- Revoke unnecessary privileges
   REVOKE ALL ON SCHEMA public FROM PUBLIC;
   GRANT USAGE ON SCHEMA public TO ai_discover_prod;
   ```

### Monitoring Security

```bash
# Secure Grafana
# Change default admin password immediately after first login

# Secure Flower
# Use strong FLOWER_BASIC_AUTH credentials

# Restrict metrics endpoint access in nginx
```

### Regular Security Tasks

- [ ] Weekly: Review logs for suspicious activity
- [ ] Monthly: Update Docker images
- [ ] Monthly: Rotate API keys
- [ ] Quarterly: Security audit
- [ ] Quarterly: Penetration testing

## Scaling and Performance

### Horizontal Scaling

1. **Backend Scaling**:

   ```yaml
   # In docker-compose.prod.yml
   backend:
     deploy:
       replicas: 3
   ```

2. **Celery Worker Scaling**:

   ```bash
   # Increase worker concurrency
   CELERY_WORKER_CONCURRENCY=8

   # Or add more worker containers
   docker-compose -f docker-compose.prod.yml up -d --scale celery=3
   ```

### Performance Tuning

1. **PostgreSQL Optimization**:

   ```sql
   -- Analyze tables
   ANALYZE;

   -- Create indexes for common queries
   CREATE INDEX idx_applications_user_id ON applications(user_id);
   CREATE INDEX idx_discovery_tasks_status ON discovery_tasks(status);
   ```

2. **Redis Optimization**:

   ```bash
   # In redis command
   maxmemory-policy allkeys-lru
   maxmemory 2gb
   ```

3. **Frontend Optimization**:
   - Enable CDN for static assets
   - Configure browser caching
   - Enable HTTP/2 in nginx

### Load Testing

```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Test API endpoint
ab -n 1000 -c 10 https://api.your-domain.com/health

# Install k6 for advanced testing
sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 379CE192D401AB61
echo "deb https://dl.k6.io/deb stable main" | sudo tee -a /etc/apt/sources.list
sudo apt-get update
sudo apt-get install k6
```

## Disaster Recovery

### Backup Strategy

1. **Database**: Daily automated backups, 30-day retention
2. **Application Data**: Version controlled in Git
3. **User Uploads**: Backup to S3 with versioning
4. **Configuration**: Encrypted backups of .env files

### Recovery Time Objectives

- **RTO** (Recovery Time Objective): 4 hours
- **RPO** (Recovery Point Objective): 24 hours

### Disaster Recovery Plan

1. **Infrastructure Failure**:

   ```bash
   # Switch to DR site
   ./scripts/dr-failover.sh

   # Update DNS
   # Restore from latest backup
   ```

2. **Data Corruption**:

   ```bash
   # Stop services
   ./scripts/deploy.sh stop

   # Restore from known good backup
   ./scripts/restore-backup.sh 2024-01-25

   # Verify data integrity
   ./scripts/verify-data.sh
   ```

3. **Security Breach**:

   ```bash
   # Immediate actions
   ./scripts/deploy.sh stop

   # Rotate all credentials
   ./scripts/rotate-credentials.sh

   # Audit logs
   ./scripts/security-audit.sh
   ```

### Testing Disaster Recovery

Monthly DR tests:

```bash
# Test backup restoration
./scripts/test-dr.sh

# Test failover procedures
./scripts/test-failover.sh

# Document results
```

## Maintenance

### Regular Maintenance Tasks

1. **Daily**:

   - Monitor health endpoints
   - Check error logs
   - Verify backups

2. **Weekly**:

   - Review performance metrics
   - Clean up old logs
   - Update monitoring dashboards

3. **Monthly**:

   - Security updates
   - Performance optimization
   - Capacity planning

4. **Quarterly**:
   - Major version updates
   - Security audit
   - DR testing

### Update Procedure

```bash
# Pull latest changes
git pull origin main

# Build new images
./scripts/deploy.sh build

# Deploy with zero downtime
./scripts/deploy.sh deploy

# Verify deployment
./scripts/deploy.sh health
```

## Support

For production support:

- **Documentation**: /docs
- **Monitoring**: Grafana dashboards
- **Logs**: Centralized in /logs
- **Alerts**: Configured in Prometheus

Remember to always test changes in a staging environment before applying to production!
