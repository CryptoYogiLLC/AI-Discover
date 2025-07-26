# AI-Discover Quick Reference

## Essential Commands

### Deployment
```bash
./scripts/deploy.sh deploy    # Full deployment
./scripts/deploy.sh status    # Check status
./scripts/deploy.sh health    # Health check
./scripts/deploy.sh logs      # View all logs
./scripts/deploy.sh rollback  # Rollback deployment
```

### Service Management
```bash
# Start/stop services
./scripts/deploy.sh start
./scripts/deploy.sh stop
./scripts/deploy.sh restart

# Individual service control
docker-compose -f docker-compose.prod.yml restart backend
docker-compose -f docker-compose.prod.yml stop celery
docker-compose -f docker-compose.prod.yml start redis
```

### Monitoring
```bash
# Check logs
./scripts/deploy.sh logs backend    # Backend logs
./scripts/deploy.sh logs frontend   # Frontend logs
./scripts/deploy.sh logs celery     # Celery logs

# Real-time logs
docker-compose -f docker-compose.prod.yml logs -f backend

# Resource usage
docker stats
```

## Service URLs

| Service | URL | Credentials |
|---------|-----|-------------|
| Frontend | https://your-domain.com | N/A |
| Backend API | https://api.your-domain.com | JWT Auth |
| API Docs | https://api.your-domain.com/docs | N/A |
| Flower | http://localhost:5555 | Set in FLOWER_BASIC_AUTH |
| Grafana | http://localhost:3000 | admin / GRAFANA_ADMIN_PASSWORD |
| Prometheus | http://localhost:9090 | N/A |

## Health Check Endpoints

```bash
# Backend health
curl https://api.your-domain.com/health

# Frontend health
curl https://your-domain.com/api/health

# Database check
docker-compose -f docker-compose.prod.yml exec postgres pg_isready

# Redis check
docker-compose -f docker-compose.prod.yml exec redis redis-cli -a $REDIS_PASSWORD ping
```

## Common Tasks

### Database Operations
```bash
# Connect to database
docker-compose -f docker-compose.prod.yml exec postgres \
  psql -U $POSTGRES_USER -d $POSTGRES_DB

# Create backup
./scripts/deploy.sh backup

# Run migrations
docker-compose -f docker-compose.prod.yml exec backend \
  alembic upgrade head
```

### Cache Management
```bash
# Clear Redis cache
docker-compose -f docker-compose.prod.yml exec redis \
  redis-cli -a $REDIS_PASSWORD FLUSHALL

# Check Redis memory
docker-compose -f docker-compose.prod.yml exec redis \
  redis-cli -a $REDIS_PASSWORD INFO memory
```

### Celery Management
```bash
# Check worker status
docker-compose -f docker-compose.prod.yml exec celery \
  celery -A app.core.celery inspect stats

# List active tasks
docker-compose -f docker-compose.prod.yml exec celery \
  celery -A app.core.celery inspect active

# Purge queue
docker-compose -f docker-compose.prod.yml exec celery \
  celery -A app.core.celery purge
```

## Troubleshooting

### Quick Diagnostics
```bash
# System health
./scripts/deploy.sh health

# Service status
docker-compose -f docker-compose.prod.yml ps

# Recent errors
docker-compose -f docker-compose.prod.yml logs | grep -i error | tail -20

# Container shell access
docker-compose -f docker-compose.prod.yml exec backend bash
```

### Common Fixes
```bash
# Restart unhealthy service
docker-compose -f docker-compose.prod.yml restart [service]

# Rebuild service
docker-compose -f docker-compose.prod.yml build --no-cache [service]
docker-compose -f docker-compose.prod.yml up -d [service]

# Clear disk space
docker system prune -a --volumes
```

## Emergency Procedures

### Complete Shutdown
```bash
./scripts/deploy.sh stop
```

### Emergency Rollback
```bash
./scripts/deploy.sh rollback
```

### Data Recovery
```bash
# List backups
ls -la backups/

# Restore from backup
gunzip backups/postgres_backup_YYYYMMDD_HHMMSS.sql.gz
docker-compose -f docker-compose.prod.yml exec -T postgres \
  psql -U $POSTGRES_USER -d $POSTGRES_DB < backups/postgres_backup_YYYYMMDD_HHMMSS.sql
```

## Performance Monitoring

### Key Metrics to Watch

1. **API Response Time**
   - Target: < 200ms p50, < 1s p95
   - Alert: > 2s p95

2. **Database Connections**
   - Target: < 80% of max_connections
   - Alert: > 90% utilized

3. **Redis Memory**
   - Target: < 80% of maxmemory
   - Alert: > 90% utilized

4. **Celery Queue Size**
   - Target: < 100 tasks
   - Alert: > 1000 tasks

5. **CPU Usage**
   - Target: < 70% average
   - Alert: > 85% sustained

6. **Memory Usage**
   - Target: < 80% utilized
   - Alert: > 90% utilized

### Quick Performance Check
```bash
# API response time
curl -w "@curl-format.txt" -o /dev/null -s https://api.your-domain.com/health

# Database performance
docker-compose -f docker-compose.prod.yml exec postgres \
  psql -U $POSTGRES_USER -d $POSTGRES_DB -c \
  "SELECT query, mean_exec_time FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 5;"

# Redis performance
docker-compose -f docker-compose.prod.yml exec redis \
  redis-cli -a $REDIS_PASSWORD --latency
```

## Log Locations

| Component | Log Location | View Command |
|-----------|--------------|--------------|
| Backend | Docker logs | `./scripts/deploy.sh logs backend` |
| Frontend | Docker logs | `./scripts/deploy.sh logs frontend` |
| PostgreSQL | Docker logs | `./scripts/deploy.sh logs postgres` |
| Redis | Docker logs | `./scripts/deploy.sh logs redis` |
| Celery | Docker logs | `./scripts/deploy.sh logs celery` |
| Nginx | Docker logs | `./scripts/deploy.sh logs nginx` |
| Deployment | `logs/deployment_*.log` | `tail -f logs/deployment_*.log` |

## Environment Variables

Key variables to check:
```bash
# View current configuration
grep -E "ENVIRONMENT|DEBUG|DATABASE_URL|REDIS_URL|SECRET_KEY" .env.production

# Validate all required variables
./scripts/deploy.sh check
```

## Support Contacts

- **Documentation**: `/docs/deployment/`
- **Monitoring**: Grafana dashboards
- **Logs**: `/logs/`
- **Backups**: `/backups/`

---

Remember: Always check health endpoints first when troubleshooting!