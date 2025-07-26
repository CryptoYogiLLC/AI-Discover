# AI-Discover Security Hardening Checklist

## Overview

This document provides a comprehensive security hardening checklist for production deployment of AI-Discover. Follow these guidelines to ensure your deployment meets security best practices.

## Pre-Deployment Security

### 1. Secrets Management

- [ ] **Generate Strong Secrets**
  ```bash
  # Generate SECRET_KEY
  openssl rand -hex 32
  
  # Generate database passwords
  openssl rand -base64 32
  
  # Generate Redis password
  openssl rand -base64 32
  ```

- [ ] **Never Use Default Passwords**
  - Change all default passwords in `.env.production`
  - Ensure no passwords contain dictionary words
  - Use minimum 16 characters with mixed case, numbers, and symbols

- [ ] **Secure Storage**
  ```bash
  # Encrypt .env.production file
  gpg --symmetric --cipher-algo AES256 .env.production
  
  # Store encrypted backup
  aws s3 cp .env.production.gpg s3://secure-bucket/backups/
  ```

- [ ] **Use Secrets Management System**
  - HashiCorp Vault integration
  - AWS Secrets Manager
  - Azure Key Vault
  - Kubernetes Secrets

### 2. SSL/TLS Configuration

- [ ] **Valid SSL Certificates**
  ```bash
  # Verify certificate
  openssl x509 -in nginx/ssl/cert.pem -text -noout
  
  # Check expiration
  openssl x509 -in nginx/ssl/cert.pem -noout -dates
  ```

- [ ] **Strong TLS Configuration**
  ```nginx
  # In nginx.conf
  ssl_protocols TLSv1.2 TLSv1.3;
  ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES128-GCM-SHA256;
  ssl_prefer_server_ciphers on;
  ssl_session_cache shared:SSL:10m;
  ```

- [ ] **Enable HSTS**
  ```nginx
  add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
  ```

### 3. Network Security

- [ ] **Firewall Configuration**
  ```bash
  # UFW setup
  sudo ufw default deny incoming
  sudo ufw default allow outgoing
  sudo ufw allow 22/tcp    # SSH
  sudo ufw allow 80/tcp    # HTTP (redirects to HTTPS)
  sudo ufw allow 443/tcp   # HTTPS
  sudo ufw enable
  ```

- [ ] **SSH Hardening**
  ```bash
  # Edit /etc/ssh/sshd_config
  PermitRootLogin no
  PasswordAuthentication no
  PubkeyAuthentication yes
  AllowUsers your-username
  ```

- [ ] **Fail2Ban Configuration**
  ```bash
  # Install fail2ban
  sudo apt-get install fail2ban
  
  # Configure for SSH and nginx
  sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local
  sudo systemctl enable fail2ban
  ```

## Application Security

### 4. API Security

- [ ] **Rate Limiting**
  ```nginx
  # In nginx.conf
  limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
  limit_req_zone $binary_remote_addr zone=auth_limit:10m rate=5r/m;
  ```

- [ ] **CORS Configuration**
  ```python
  # Only allow specific origins
  BACKEND_CORS_ORIGINS = ["https://your-domain.com"]
  ```

- [ ] **API Key Security**
  - Rotate API keys regularly
  - Use different keys for different environments
  - Monitor API key usage

### 5. Database Security

- [ ] **Connection Security**
  ```bash
  # Force SSL connections
  docker-compose -f docker-compose.prod.yml exec postgres \
    psql -U $POSTGRES_USER -d $POSTGRES_DB -c \
    "ALTER SYSTEM SET ssl = on;"
  ```

- [ ] **User Privileges**
  ```sql
  -- Create application user with limited privileges
  CREATE USER app_user WITH PASSWORD 'strong_password';
  GRANT CONNECT ON DATABASE ai_discover_production TO app_user;
  GRANT USAGE ON SCHEMA public TO app_user;
  GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;
  
  -- Revoke unnecessary privileges
  REVOKE CREATE ON SCHEMA public FROM PUBLIC;
  ```

- [ ] **Backup Encryption**
  ```bash
  # Encrypt backups
  pg_dump $DATABASE_URL | gpg --symmetric --cipher-algo AES256 > backup.sql.gpg
  ```

### 6. Container Security

- [ ] **Non-Root Users**
  ```dockerfile
  # In Dockerfile
  RUN useradd -m -u 1000 appuser
  USER appuser
  ```

- [ ] **Read-Only Filesystems**
  ```yaml
  # In docker-compose.prod.yml
  services:
    backend:
      read_only: true
      tmpfs:
        - /tmp
  ```

- [ ] **Security Scanning**
  ```bash
  # Scan images for vulnerabilities
  trivy image ai-discover/backend:latest
  trivy image ai-discover/frontend:latest
  ```

## Runtime Security

### 7. Monitoring and Logging

- [ ] **Centralized Logging**
  ```yaml
  # In docker-compose.prod.yml
  logging:
    driver: "json-file"
    options:
      max-size: "10m"
      max-file: "3"
  ```

- [ ] **Security Monitoring**
  - Enable audit logging
  - Monitor failed authentication attempts
  - Alert on suspicious patterns

- [ ] **Log Rotation**
  ```bash
  # Configure logrotate
  cat > /etc/logrotate.d/ai-discover << EOF
  /var/log/ai-discover/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 www-data adm
  }
  EOF
  ```

### 8. Access Control

- [ ] **Multi-Factor Authentication**
  - Enable MFA for all admin accounts
  - Use TOTP or hardware tokens

- [ ] **Role-Based Access Control**
  ```python
  # Implement RBAC in application
  ROLES = {
    'admin': ['all'],
    'user': ['read', 'write'],
    'viewer': ['read']
  }
  ```

- [ ] **Session Security**
  ```python
  # Secure session configuration
  SESSION_COOKIE_SECURE = True
  SESSION_COOKIE_HTTPONLY = True
  SESSION_COOKIE_SAMESITE = 'Strict'
  ```

### 9. Data Protection

- [ ] **Encryption at Rest**
  ```bash
  # Encrypt database volume
  cryptsetup luksFormat /dev/sdb1
  cryptsetup open /dev/sdb1 encrypted_db
  ```

- [ ] **Encryption in Transit**
  - All internal communication over TLS
  - Redis with password authentication
  - PostgreSQL with SSL required

- [ ] **Data Sanitization**
  - Sanitize all user inputs
  - Use parameterized queries
  - Implement output encoding

## Compliance and Auditing

### 10. Compliance Requirements

- [ ] **GDPR Compliance**
  - Data retention policies
  - Right to erasure implementation
  - Privacy policy endpoint

- [ ] **SOC2 Requirements**
  - Access logging
  - Change management
  - Incident response plan

- [ ] **Security Headers**
  ```nginx
  # Security headers in nginx
  add_header X-Frame-Options "SAMEORIGIN" always;
  add_header X-Content-Type-Options "nosniff" always;
  add_header X-XSS-Protection "1; mode=block" always;
  add_header Referrer-Policy "strict-origin-when-cross-origin" always;
  add_header Content-Security-Policy "default-src 'self'" always;
  ```

### 11. Regular Security Tasks

- [ ] **Daily Tasks**
  - Review authentication logs
  - Check for failed login attempts
  - Monitor resource usage

- [ ] **Weekly Tasks**
  - Review security alerts
  - Check for system updates
  - Audit user access

- [ ] **Monthly Tasks**
  - Security patches
  - Certificate renewal check
  - Vulnerability scanning

- [ ] **Quarterly Tasks**
  - Security audit
  - Penetration testing
  - Policy review

## Security Testing

### 12. Vulnerability Testing

- [ ] **Dependency Scanning**
  ```bash
  # Python dependencies
  pip-audit
  bandit -r backend/
  
  # JavaScript dependencies
  cd frontend && npm audit
  ```

- [ ] **Container Scanning**
  ```bash
  # Scan all images
  for image in $(docker-compose -f docker-compose.prod.yml config | grep 'image:' | awk '{print $2}'); do
    trivy image $image
  done
  ```

- [ ] **Secret Scanning**
  ```bash
  # Scan for secrets
  gitleaks detect --source . --verbose
  ```

### 13. Penetration Testing

- [ ] **API Security Testing**
  ```bash
  # OWASP ZAP
  docker run -t owasp/zap2docker-stable zap-api-scan.py \
    -t https://api.your-domain.com/openapi.json \
    -f openapi
  ```

- [ ] **Web Application Testing**
  - SQL injection testing
  - XSS testing
  - CSRF testing
  - Authentication bypass testing

## Incident Response

### 14. Incident Response Plan

- [ ] **Detection**
  - Monitoring alerts configured
  - Log analysis automated
  - Anomaly detection enabled

- [ ] **Response Procedures**
  ```bash
  # Emergency shutdown
  ./scripts/emergency-shutdown.sh
  
  # Rotate credentials
  ./scripts/rotate-all-credentials.sh
  
  # Preserve evidence
  ./scripts/collect-forensics.sh
  ```

- [ ] **Recovery**
  - Backup restoration tested
  - Rollback procedures documented
  - Communication plan in place

## Security Automation

### 15. Automated Security

- [ ] **CI/CD Security**
  ```yaml
  # In .github/workflows/security.yml
  - name: Security Scan
    run: |
      pip-audit
      bandit -r backend/
      trivy fs .
  ```

- [ ] **Automated Patching**
  ```bash
  # Unattended upgrades
  sudo apt-get install unattended-upgrades
  sudo dpkg-reconfigure unattended-upgrades
  ```

- [ ] **Security Monitoring**
  ```yaml
  # Prometheus alerts
  - alert: SuspiciousActivity
    expr: rate(nginx_http_requests_total{status=~"4.."}[5m]) > 100
    annotations:
      summary: "High rate of 4xx errors detected"
  ```

## Final Checklist

Before going to production, ensure:

- [ ] All default passwords changed
- [ ] SSL certificates valid and strong
- [ ] Firewall rules configured
- [ ] Security headers enabled
- [ ] Monitoring and alerting active
- [ ] Backup and recovery tested
- [ ] Incident response plan documented
- [ ] Security scanning automated
- [ ] Access controls implemented
- [ ] Compliance requirements met

Remember: Security is an ongoing process. Regular reviews and updates are essential to maintain a secure deployment.