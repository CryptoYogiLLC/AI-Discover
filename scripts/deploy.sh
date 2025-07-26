#!/bin/bash

# AI-Discover Production Deployment Script
# This script handles the complete deployment process with safety checks and rollback capabilities

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DEPLOYMENT_LOG="$PROJECT_ROOT/logs/deployment_$(date +%Y%m%d_%H%M%S).log"
BACKUP_DIR="$PROJECT_ROOT/backups"
ENV_FILE="$PROJECT_ROOT/.env.production"
DOCKER_COMPOSE_FILE="$PROJECT_ROOT/docker-compose.prod.yml"
MAX_HEALTH_CHECK_ATTEMPTS=30
HEALTH_CHECK_INTERVAL=10

# Ensure log directory exists
mkdir -p "$(dirname "$DEPLOYMENT_LOG")"
mkdir -p "$BACKUP_DIR"

# Logging function
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "[$timestamp] [$level] $message" | tee -a "$DEPLOYMENT_LOG"
}

# Print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $*"
    log "INFO" "$*"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*"
    log "SUCCESS" "$*"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $*"
    log "WARNING" "$*"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $*"
    log "ERROR" "$*"
}

# Check if running as root
check_not_root() {
    if [[ $EUID -eq 0 ]]; then
        print_error "This script should not be run as root!"
        exit 1
    fi
}

# Check system dependencies
check_dependencies() {
    print_info "Checking system dependencies..."
    
    local deps=("docker" "docker-compose" "git" "curl" "jq")
    local missing_deps=()
    
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            missing_deps+=("$dep")
        fi
    done
    
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        print_error "Missing required dependencies: ${missing_deps[*]}"
        print_info "Please install missing dependencies and try again."
        exit 1
    fi
    
    # Check Docker daemon
    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running or you don't have permission to access it."
        exit 1
    fi
    
    # Check Docker Compose version
    local compose_version=$(docker-compose --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
    print_info "Docker Compose version: $compose_version"
    
    print_success "All dependencies satisfied"
}

# Validate environment file
validate_environment() {
    print_info "Validating environment configuration..."
    
    if [[ ! -f "$ENV_FILE" ]]; then
        print_error "Environment file not found: $ENV_FILE"
        print_info "Please copy .env.production.example to .env.production and configure it."
        exit 1
    fi
    
    # Check required environment variables
    local required_vars=(
        "ENVIRONMENT"
        "SECRET_KEY"
        "POSTGRES_USER"
        "POSTGRES_PASSWORD"
        "POSTGRES_DB"
        "REDIS_PASSWORD"
        "OPENAI_API_KEY"
    )
    
    local missing_vars=()
    
    # Source environment file
    set -a
    source "$ENV_FILE"
    set +a
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            missing_vars+=("$var")
        fi
    done
    
    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        print_error "Missing required environment variables: ${missing_vars[*]}"
        exit 1
    fi
    
    # Validate environment is set to production
    if [[ "${ENVIRONMENT}" != "production" ]]; then
        print_error "ENVIRONMENT must be set to 'production' in $ENV_FILE"
        exit 1
    fi
    
    # Check for default/weak values
    if [[ "${SECRET_KEY}" == *"change-in-production"* ]]; then
        print_error "SECRET_KEY contains default value. Please generate a strong secret key."
        exit 1
    fi
    
    print_success "Environment configuration validated"
}

# Build Docker images
build_images() {
    print_info "Building Docker images..."
    
    # Set build arguments
    export BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
    export VCS_REF=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
    export VERSION="${VERSION:-$VCS_REF}"
    
    # Build images
    if ! docker-compose -f "$DOCKER_COMPOSE_FILE" build --no-cache; then
        print_error "Failed to build Docker images"
        exit 1
    fi
    
    print_success "Docker images built successfully"
}

# Create database backup
backup_database() {
    print_info "Creating database backup..."
    
    local backup_file="$BACKUP_DIR/postgres_backup_$(date +%Y%m%d_%H%M%S).sql"
    
    # Check if postgres container is running
    if docker-compose -f "$DOCKER_COMPOSE_FILE" ps postgres | grep -q "Up"; then
        if docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T postgres pg_dump \
            -U "$POSTGRES_USER" \
            -d "$POSTGRES_DB" > "$backup_file"; then
            print_success "Database backed up to: $backup_file"
            
            # Compress backup
            gzip "$backup_file"
            print_info "Backup compressed: ${backup_file}.gz"
            
            # Clean old backups (keep last 7 days)
            find "$BACKUP_DIR" -name "postgres_backup_*.sql.gz" -mtime +7 -delete
        else
            print_warning "Failed to create database backup"
        fi
    else
        print_info "Database container not running, skipping backup"
    fi
}

# Stop running services
stop_services() {
    print_info "Stopping current services..."
    
    if docker-compose -f "$DOCKER_COMPOSE_FILE" ps -q | grep -q .; then
        docker-compose -f "$DOCKER_COMPOSE_FILE" down --remove-orphans
        print_success "Services stopped"
    else
        print_info "No services running"
    fi
}

# Start services
start_services() {
    print_info "Starting services..."
    
    # Start infrastructure services first
    print_info "Starting infrastructure services (PostgreSQL, Redis)..."
    if ! docker-compose -f "$DOCKER_COMPOSE_FILE" up -d postgres redis; then
        print_error "Failed to start infrastructure services"
        exit 1
    fi
    
    # Wait for infrastructure to be healthy
    print_info "Waiting for infrastructure services to be healthy..."
    sleep 10
    
    # Run database migrations
    run_migrations
    
    # Start remaining services
    print_info "Starting application services..."
    if ! docker-compose -f "$DOCKER_COMPOSE_FILE" up -d; then
        print_error "Failed to start application services"
        exit 1
    fi
    
    print_success "All services started"
}

# Run database migrations
run_migrations() {
    print_info "Running database migrations..."
    
    # Wait for database to be ready
    local attempts=0
    while ! docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T postgres pg_isready -U "$POSTGRES_USER" &> /dev/null; do
        ((attempts++))
        if [[ $attempts -gt 30 ]]; then
            print_error "Database failed to become ready"
            exit 1
        fi
        print_info "Waiting for database to be ready... (attempt $attempts/30)"
        sleep 2
    done
    
    # Run Alembic migrations
    if docker-compose -f "$DOCKER_COMPOSE_FILE" run --rm backend alembic upgrade head; then
        print_success "Database migrations completed"
    else
        print_error "Database migrations failed"
        exit 1
    fi
}

# Health check for a service
health_check_service() {
    local service="$1"
    local endpoint="$2"
    local attempts=0
    
    print_info "Checking health of $service..."
    
    while [[ $attempts -lt $MAX_HEALTH_CHECK_ATTEMPTS ]]; do
        if curl -sf "$endpoint" > /dev/null 2>&1; then
            print_success "$service is healthy"
            return 0
        fi
        
        ((attempts++))
        print_info "Waiting for $service to be healthy... (attempt $attempts/$MAX_HEALTH_CHECK_ATTEMPTS)"
        sleep $HEALTH_CHECK_INTERVAL
    done
    
    print_error "$service failed health check"
    return 1
}

# Perform health checks on all services
perform_health_checks() {
    print_info "Performing health checks on all services..."
    
    local all_healthy=true
    
    # Check backend
    if ! health_check_service "Backend API" "http://localhost:8800/health"; then
        all_healthy=false
    fi
    
    # Check frontend
    if ! health_check_service "Frontend" "http://localhost:3300/api/health"; then
        all_healthy=false
    fi
    
    # Check Flower (if enabled)
    if docker-compose -f "$DOCKER_COMPOSE_FILE" ps flower | grep -q "Up"; then
        if ! health_check_service "Flower" "http://localhost:5555/healthcheck"; then
            all_healthy=false
        fi
    fi
    
    # Check database connectivity
    if docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T postgres pg_isready -U "$POSTGRES_USER" &> /dev/null; then
        print_success "PostgreSQL is healthy"
    else
        print_error "PostgreSQL health check failed"
        all_healthy=false
    fi
    
    # Check Redis connectivity
    if docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T redis redis-cli -a "$REDIS_PASSWORD" ping &> /dev/null; then
        print_success "Redis is healthy"
    else
        print_error "Redis health check failed"
        all_healthy=false
    fi
    
    if [[ "$all_healthy" == "true" ]]; then
        print_success "All services are healthy"
        return 0
    else
        print_error "Some services failed health checks"
        return 1
    fi
}

# Rollback deployment
rollback() {
    print_warning "Rolling back deployment..."
    
    # Stop all services
    docker-compose -f "$DOCKER_COMPOSE_FILE" down
    
    # Restore from previous images if tagged
    if [[ -n "${PREVIOUS_VERSION:-}" ]]; then
        print_info "Rolling back to version: $PREVIOUS_VERSION"
        export VERSION="$PREVIOUS_VERSION"
        docker-compose -f "$DOCKER_COMPOSE_FILE" up -d
    else
        print_warning "No previous version specified, services stopped but not rolled back"
    fi
}

# Show deployment status
show_status() {
    print_info "Deployment Status:"
    echo "=================="
    
    docker-compose -f "$DOCKER_COMPOSE_FILE" ps
    
    echo ""
    print_info "Service URLs:"
    echo "- Frontend: http://localhost:3300"
    echo "- Backend API: http://localhost:8800"
    echo "- API Documentation: http://localhost:8800/docs"
    echo "- Flower (Celery monitoring): http://localhost:5555"
    echo "- Grafana (if enabled): http://localhost:3000"
    echo "- Prometheus (if enabled): http://localhost:9090"
}

# Show logs for a service
show_logs() {
    local service="${1:-}"
    
    if [[ -z "$service" ]]; then
        docker-compose -f "$DOCKER_COMPOSE_FILE" logs --tail=100 -f
    else
        docker-compose -f "$DOCKER_COMPOSE_FILE" logs --tail=100 -f "$service"
    fi
}

# Main deployment function
deploy() {
    print_info "Starting AI-Discover deployment..."
    print_info "Deployment log: $DEPLOYMENT_LOG"
    
    # Pre-deployment checks
    check_not_root
    check_dependencies
    validate_environment
    
    # Save current version for potential rollback
    PREVIOUS_VERSION=$(docker-compose -f "$DOCKER_COMPOSE_FILE" ps -q backend | xargs -r docker inspect -f '{{.Config.Image}}' | grep -oE '[^:]+$' || echo "")
    if [[ -n "$PREVIOUS_VERSION" ]]; then
        export PREVIOUS_VERSION
        print_info "Current version: $PREVIOUS_VERSION"
    fi
    
    # Create backup
    backup_database
    
    # Build and deploy
    build_images
    stop_services
    start_services
    
    # Verify deployment
    if perform_health_checks; then
        print_success "Deployment completed successfully!"
        show_status
    else
        print_error "Deployment health checks failed!"
        
        read -p "Do you want to rollback? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rollback
        fi
        
        exit 1
    fi
}

# Parse command line arguments
case "${1:-deploy}" in
    deploy)
        deploy
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs "${2:-}"
        ;;
    rollback)
        rollback
        ;;
    backup)
        backup_database
        ;;
    health)
        perform_health_checks
        ;;
    stop)
        stop_services
        ;;
    start)
        start_services
        ;;
    restart)
        stop_services
        start_services
        ;;
    *)
        echo "Usage: $0 {deploy|status|logs [service]|rollback|backup|health|stop|start|restart}"
        echo ""
        echo "Commands:"
        echo "  deploy    - Full deployment with health checks"
        echo "  status    - Show current deployment status"
        echo "  logs      - Show logs (optionally for specific service)"
        echo "  rollback  - Rollback to previous version"
        echo "  backup    - Create database backup"
        echo "  health    - Run health checks on all services"
        echo "  stop      - Stop all services"
        echo "  start     - Start all services"
        echo "  restart   - Restart all services"
        exit 1
        ;;
esac