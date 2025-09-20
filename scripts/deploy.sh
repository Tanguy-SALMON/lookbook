#!/bin/bash

# Lookbook-MPC Deployment Script
# This script helps deploy the lookbook-MPC system using Docker Compose

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check Docker and Docker Compose
check_prerequisites() {
    print_status "Checking prerequisites..."

    if ! command_exists docker; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi

    if ! command_exists docker-compose; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi

    print_success "Prerequisites check passed."
}

# Function to create necessary directories
setup_directories() {
    print_status "Setting up directories..."

    mkdir -p logs
    mkdir -p ssl
    mkdir -p data

    print_success "Directories created."
}

# Function to check environment variables
check_environment() {
    print_status "Checking environment variables..."

    if [ ! -f .env ]; then
        print_warning ".env file not found. Creating from template..."
        cp .env.example .env
        print_warning "Please edit .env file with your configuration before running."
        return 1
    fi

    # Check required environment variables
    required_vars=("OLLAMA_HOST" "OLLAMA_VISION_MODEL" "OLLAMA_TEXT_MODEL" "S3_BASE_URL")
    missing_vars=()

    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_vars+=("$var")
        fi
    done

    if [ ${#missing_vars[@]} -ne 0 ]; then
        print_error "Missing required environment variables: ${missing_vars[*]}"
        return 1
    fi

    print_success "Environment variables check passed."
}

# Function to pull Docker images
pull_images() {
    print_status "Pulling Docker images..."

    docker-compose pull

    print_success "Docker images pulled."
}

# Function to build Docker images
build_images() {
    print_status "Building Docker images..."

    docker-compose build --no-cache

    print_success "Docker images built."
}

# Function to initialize database
init_database() {
    print_status "Initializing database..."

    docker-compose --profile init up db-init

    print_success "Database initialized."
}

# Function to start services
start_services() {
    print_status "Starting services..."

    docker-compose up -d

    print_success "Services started."
}

# Function to stop services
stop_services() {
    print_status "Stopping services..."

    docker-compose down

    print_success "Services stopped."
}

# Function to view logs
view_logs() {
    print_status "Viewing logs..."

    if [ -n "$1" ]; then
        docker-compose logs -f "$1"
    else
        docker-compose logs -f
    fi
}

# Function to check service health
check_health() {
    print_status "Checking service health..."

    # Check API health
    if curl -f http://localhost:8000/health >/dev/null 2>&1; then
        print_success "API service is healthy"
    else
        print_error "API service is not healthy"
    fi

    # Check Ollama health
    if curl -f http://localhost:11434/api/tags >/dev/null 2>&1; then
        print_success "Ollama service is healthy"
    else
        print_error "Ollama service is not healthy"
    fi

    # Check vision service health
    if curl -f http://localhost:8001/health >/dev/null 2>&1; then
        print_success "Vision service is healthy"
    else
        print_error "Vision service is not healthy"
    fi
}

# Function to show status
show_status() {
    print_status "Service status..."

    docker-compose ps
}

# Function to clean up
cleanup() {
    print_status "Cleaning up..."

    docker-compose down -v --remove-orphans
    docker system prune -f

    print_success "Cleanup completed."
}

# Function to show help
show_help() {
    echo "Lookbook-MPC Deployment Script"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  setup         - Check prerequisites and setup directories"
    echo "  check-env     - Check environment variables"
    echo "  pull          - Pull Docker images"
    echo "  build         - Build Docker images"
    echo "  init-db       - Initialize database"
    echo "  start         - Start all services"
    echo "  stop          - Stop all services"
    echo "  restart       - Restart all services"
    echo "  logs [service] - View logs (optional: specify service)"
    echo "  health        - Check service health"
    echo "  status        - Show service status"
    echo "  cleanup       - Clean up containers and images"
    echo "  help          - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 setup"
    echo "  $0 start"
    echo "  $0 logs api"
    echo "  $0 health"
}

# Main script logic
main() {
    case "${1:-help}" in
        setup)
            check_prerequisites
            setup_directories
            check_environment
            ;;
        check-env)
            check_environment
            ;;
        pull)
            check_prerequisites
            pull_images
            ;;
        build)
            check_prerequisites
            build_images
            ;;
        init-db)
            check_prerequisites
            init_database
            ;;
        start)
            check_prerequisites
            check_environment
            start_services
            check_health
            ;;
        stop)
            stop_services
            ;;
        restart)
            stop_services
            sleep 5
            start_services
            check_health
            ;;
        logs)
            view_logs "$2"
            ;;
        health)
            check_health
            ;;
        status)
            show_status
            ;;
        cleanup)
            cleanup
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "Unknown command: $1"
            show_help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"