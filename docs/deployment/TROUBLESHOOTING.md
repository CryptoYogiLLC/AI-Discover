# AI-Discover Troubleshooting Guide

## Quick Diagnostics

Run this command first for a complete system check:
```bash
./scripts/deploy.sh health
```

## Common Issues and Solutions

### 1. Services Won't Start

#### Symptom: Container keeps restarting
```bash
# Check container status
docker-compose -f docker-compose.prod.yml ps

# View recent logs
docker-compose -f docker-compose.prod.yml logs --tail=50 [service_name]
```

#### Common Causes and Solutions:

**Port Already in Use**
```bash
# Check what's using the port
sudo lsof -i :8800  # Backend
sudo lsof -i :3300  # Frontend
sudo lsof -i :5442  # PostgreSQL
sudo lsof -i :6479  # Redis

# Kill the process or change the port in docker-compose.prod.yml
```

**Database Connection Failed**
```bash
# Test database connection
docker-compose -f docker-compose.prod.yml exec postgres pg_isready

# Check PostgreSQL logs
docker-compose -f docker-compose.prod.yml logs postgres

# Verify environment variables
grep DATABASE_URL .env.production
```

**Missing Environment Variables**
```bash
# Validate all required variables
./scripts/deploy.sh check

# Common missing variables:
# - OPENAI_API_KEY
# - SECRET_KEY
# - REDIS_PASSWORD
```

### 2. Backend API Issues

#### 500 Internal Server Error

**Check Application Logs**
```bash
# Backend logs
docker-compose -f docker-compose.prod.yml logs -f backend

# Look for Python tracebacks
docker-compose -f docker-compose.prod.yml logs backend | grep -A 10 "Traceback"
```

**Database Migration Issues**
```bash
# Check migration status
docker-compose -f docker-compose.prod.yml exec backend alembic current

# Run migrations manually
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head

# If migrations fail, check for locks
docker-compose -f docker-compose.prod.yml exec postgres \
  psql -U $POSTGRES_USER -d $POSTGRES_DB -c \
  "SELECT * FROM pg_stat_activity WHERE state = 'active';"
```

#### API Performance Issues

**Slow Response Times**
```bash
# Check resource usage
docker stats

# Monitor API metrics
curl http://localhost:8800/metrics | grep http_request_duration

# Check database slow queries
docker-compose -f docker-compose.prod.yml exec postgres \
  psql -U $POSTGRES_USER -d $POSTGRES_DB -c \
  "SELECT query, mean_exec_time, calls 
   FROM pg_stat_statements 
   ORDER BY mean_exec_time DESC 
   LIMIT 10;"
```

**High Memory Usage**
```bash
# Check Python memory usage
docker-compose -f docker-compose.prod.yml exec backend \
  python -c "import psutil; print(psutil.Process().memory_info())"

# Restart with memory limits
docker-compose -f docker-compose.prod.yml up -d --force-recreate backend
```

### 3. Frontend Issues

#### Build Failures

**Next.js Build Errors**
```bash
# Check build logs
docker-compose -f docker-compose.prod.yml logs frontend

# Common issues:
# - Missing NEXT_PUBLIC_API_URL
# - TypeScript errors
# - Module resolution failures

# Rebuild frontend
docker-compose -f docker-compose.prod.yml build --no-cache frontend
```

#### Blank Page or 404 Errors

**Check Static Files**
```bash
# Verify build output
docker-compose -f docker-compose.prod.yml exec frontend ls -la .next/

# Check Next.js server
docker-compose -f docker-compose.prod.yml exec frontend \
  curl -I http://localhost:3000
```

**API Connection Issues**
```bash
# Test API connectivity from frontend
docker-compose -f docker-compose.prod.yml exec frontend \
  curl http://backend:8000/health

# Check CORS settings
grep CORS_ORIGINS .env.production
```

### 4. Database Issues

#### Connection Pool Exhausted

**Symptoms**: "too many connections" errors

**Solution**:
```bash
# Check current connections
docker-compose -f docker-compose.prod.yml exec postgres \
  psql -U $POSTGRES_USER -d $POSTGRES_DB -c \
  "SELECT count(*) FROM pg_stat_activity;"

# Increase max connections
docker-compose -f docker-compose.prod.yml exec postgres \
  psql -U $POSTGRES_USER -d $POSTGRES_DB -c \
  "ALTER SYSTEM SET max_connections = 200;"

# Restart PostgreSQL
docker-compose -f docker-compose.prod.yml restart postgres
```

#### Disk Space Issues

**Check Disk Usage**
```bash
# Overall disk usage
df -h

# Docker volumes
docker system df

# Database size
docker-compose -f docker-compose.prod.yml exec postgres \
  psql -U $POSTGRES_USER -d $POSTGRES_DB -c \
  "SELECT pg_database_size('$POSTGRES_DB');"
```

**Clean Up**
```bash
# Remove old backups
find ./backups -name "*.sql.gz" -mtime +30 -delete

# Clean Docker resources
docker system prune -a --volumes

# Vacuum database
docker-compose -f docker-compose.prod.yml exec postgres \
  psql -U $POSTGRES_USER -d $POSTGRES_DB -c "VACUUM FULL;"
```

### 5. Redis Issues

#### Memory Issues

**Check Memory Usage**
```bash
# Redis memory info
docker-compose -f docker-compose.prod.yml exec redis \
  redis-cli -a $REDIS_PASSWORD INFO memory

# Check eviction policy
docker-compose -f docker-compose.prod.yml exec redis \
  redis-cli -a $REDIS_PASSWORD CONFIG GET maxmemory-policy
```

**Clear Cache**
```bash
# Flush all data (WARNING: This clears everything)
docker-compose -f docker-compose.prod.yml exec redis \
  redis-cli -a $REDIS_PASSWORD FLUSHALL

# Clear specific database
docker-compose -f docker-compose.prod.yml exec redis \
  redis-cli -a $REDIS_PASSWORD -n 0 FLUSHDB
```

### 6. Celery Issues

#### Workers Not Processing Tasks

**Check Worker Status**
```bash
# View Celery logs
docker-compose -f docker-compose.prod.yml logs celery

# Check worker status via Flower
curl http://localhost:5555/api/workers

# Inspect active tasks
docker-compose -f docker-compose.prod.yml exec celery \
  celery -A app.core.celery inspect active
```

**Queue Buildup**
```bash
# Check queue lengths
docker-compose -f docker-compose.prod.yml exec redis \
  redis-cli -a $REDIS_PASSWORD LLEN celery

# Purge queue (WARNING: Loses all pending tasks)
docker-compose -f docker-compose.prod.yml exec celery \
  celery -A app.core.celery purge
```

#### Task Failures

**Debug Failed Tasks**
```bash
# Check for exceptions
docker-compose -f docker-compose.prod.yml logs celery | grep -i error

# Retry failed tasks
docker-compose -f docker-compose.prod.yml exec backend python << EOF
from app.core.celery import celery_app
# Get failed task IDs from logs
task_id = "your-task-id-here"
celery_app.AsyncResult(task_id).retry()
EOF
```

### 7. Nginx/Proxy Issues

#### SSL Certificate Problems

**Certificate Expired**
```bash
# Check certificate expiry
openssl x509 -in nginx/ssl/cert.pem -noout -dates

# Renew with Let's Encrypt
sudo certbot renew
```

#### 502 Bad Gateway

**Check Upstream Services**
```bash
# Test backend directly
curl http://localhost:8800/health

# Test frontend directly
curl http://localhost:3300/api/health

# Check nginx logs
docker-compose -f docker-compose.prod.yml logs nginx
```

### 8. Performance Issues

#### High CPU Usage

**Identify CPU-Heavy Processes**
```bash
# Container CPU usage
docker stats --no-stream

# Python profiling
docker-compose -f docker-compose.prod.yml exec backend \
  py-spy top --pid 1 --duration 30
```

#### Memory Leaks

**Monitor Memory Growth**
```bash
# Track memory over time
while true; do
  docker stats --no-stream | grep backend
  sleep 60
done

# Force garbage collection
docker-compose -f docker-compose.prod.yml exec backend python << EOF
import gc
gc.collect()
print(f"Collected {gc.collect()} objects")
EOF
```

### 9. Monitoring Issues

#### Prometheus Not Scraping Metrics

**Check Targets**
```bash
# Access Prometheus UI
curl http://localhost:9090/targets

# Test metric endpoints
curl http://localhost:8800/metrics
```

#### Grafana Dashboard Empty

**Check Data Sources**
```bash
# Test Prometheus query
curl -G http://localhost:9090/api/v1/query \
  --data-urlencode 'query=up{job="backend"}'

# Restart Grafana
docker-compose -f docker-compose.prod.yml restart grafana
```

## Emergency Procedures

### Complete System Recovery

```bash
# 1. Stop all services
./scripts/deploy.sh stop

# 2. Clean up Docker resources
docker system prune -a

# 3. Restore from backup
./scripts/restore-from-backup.sh

# 4. Rebuild and restart
./scripts/deploy.sh deploy
```

### Roll Back Deployment

```bash
# Automatic rollback to previous version
./scripts/deploy.sh rollback

# Manual rollback to specific version
git checkout v1.2.3
./scripts/deploy.sh deploy
```

### Data Recovery

```bash
# List available backups
ls -la backups/

# Restore specific backup
gunzip backups/postgres_backup_20240126_020000.sql.gz
docker-compose -f docker-compose.prod.yml exec -T postgres \
  psql -U $POSTGRES_USER -d $POSTGRES_DB < backups/postgres_backup_20240126_020000.sql
```

## Diagnostic Commands Reference

### System Health
```bash
# Overall health check
./scripts/deploy.sh health

# Service status
docker-compose -f docker-compose.prod.yml ps

# Resource usage
docker stats
htop
iotop
```

### Logs
```bash
# All logs
docker-compose -f docker-compose.prod.yml logs

# Specific service
docker-compose -f docker-compose.prod.yml logs -f backend

# Last N lines
docker-compose -f docker-compose.prod.yml logs --tail=100 backend

# Grep for errors
docker-compose -f docker-compose.prod.yml logs | grep -i error
```

### Network
```bash
# Test connectivity
docker-compose -f docker-compose.prod.yml exec backend ping postgres
docker-compose -f docker-compose.prod.yml exec frontend curl http://backend:8000/health

# Check ports
netstat -tulpn | grep LISTEN
```

### Database
```bash
# Connect to database
docker-compose -f docker-compose.prod.yml exec postgres \
  psql -U $POSTGRES_USER -d $POSTGRES_DB

# Common queries
\dt                          # List tables
\d+ table_name              # Describe table
SELECT version();           # PostgreSQL version
SELECT current_database();  # Current database
\l                         # List databases
\du                        # List users
```

## Getting Help

1. **Check Logs First**: Most issues can be diagnosed from logs
2. **Health Endpoint**: Always check `/health` endpoints
3. **Monitoring**: Review Grafana dashboards for trends
4. **Documentation**: Refer to deployment guide for configuration

If you're still stuck:
- Review this troubleshooting guide
- Check application logs for stack traces
- Verify all environment variables are set correctly
- Ensure all services are running and healthy
- Test connectivity between services