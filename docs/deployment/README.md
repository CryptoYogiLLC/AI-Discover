# AI-Discover Deployment Documentation

This directory contains comprehensive documentation for deploying and maintaining the AI-Discover application in production environments.

## Documentation Structure

### 📘 [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)

Complete guide for production deployment including:

- System requirements and prerequisites
- Step-by-step deployment instructions
- Configuration management
- Monitoring setup
- Backup and restore procedures
- Scaling guidelines
- Disaster recovery planning

### 🔧 [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)

Comprehensive troubleshooting guide covering:

- Common issues and solutions
- Diagnostic commands
- Performance troubleshooting
- Emergency procedures
- Log analysis
- Recovery procedures

### 🔒 [SECURITY_HARDENING.md](./SECURITY_HARDENING.md)

Security hardening checklist including:

- Pre-deployment security measures
- Network security configuration
- Application security best practices
- Container security
- Compliance requirements
- Regular security tasks
- Incident response procedures

### 📋 [QUICK_REFERENCE.md](./QUICK_REFERENCE.md)

Quick reference for operators containing:

- Essential commands
- Service URLs and endpoints
- Common tasks
- Performance monitoring
- Emergency procedures
- Key metrics to watch

## Getting Started

1. **First-time deployment**: Start with [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)
2. **Security setup**: Follow [SECURITY_HARDENING.md](./SECURITY_HARDENING.md)
3. **Daily operations**: Keep [QUICK_REFERENCE.md](./QUICK_REFERENCE.md) handy
4. **When issues arise**: Consult [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)

## Key Scripts

The deployment process is managed through scripts in the `/scripts` directory:

- **`deploy.sh`**: Main deployment script with rollback capabilities
- **`setup-monitoring.sh`**: Sets up the monitoring stack
- **`backup.sh`**: Automated backup script (called by deploy.sh)
- **`load-test.sh`**: Simple load testing utility

## Production Configuration Files

- **`docker-compose.prod.yml`**: Production Docker Compose configuration
- **`.env.production.example`**: Template for production environment variables
- **`nginx/nginx.conf`**: Production-ready Nginx configuration
- **`monitoring/`**: Prometheus and Grafana configurations

## Port Configuration

The application uses non-standard ports to avoid conflicts:

| Service    | Internal Port | External Port |
| ---------- | ------------- | ------------- |
| Frontend   | 3000          | 3300          |
| Backend    | 8000          | 8800          |
| PostgreSQL | 5432          | 5442          |
| Redis      | 6379          | 6479          |
| Flower     | 5555          | 5555          |

## Support and Maintenance

For production support:

1. Check health endpoints first
2. Review logs for errors
3. Monitor Grafana dashboards
4. Follow troubleshooting guide
5. Execute emergency procedures if needed

## Important Notes

- Always test deployments in staging first
- Maintain separate environment files for each environment
- Regular backups are automated but should be verified
- Security updates should be applied monthly
- Monitor resource usage and scale proactively

For additional support or questions, refer to the main project documentation or contact the development team.
