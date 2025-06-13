#!/bin/bash

# THEODOSI4 - Ubuntu Server Deployment Script
# This script automates the deployment process for Ubuntu servers

set -e  # Exit on any error

echo "=== THEODOSI4 Ubuntu Deployment Script ==="
echo "Starting deployment process..."
echo

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

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root for security reasons"
   print_status "Run it as a regular user with sudo privileges"
   exit 1
fi

# Check if Docker is installed
check_docker() {
    print_status "Checking Docker installation..."
    if ! command -v docker &> /dev/null; then
        print_warning "Docker not found. Installing Docker..."
        sudo apt update
        sudo apt install -y docker.io
        sudo systemctl start docker
        sudo systemctl enable docker
        sudo usermod -aG docker $USER
        print_success "Docker installed successfully"
        print_warning "You may need to logout and login again for Docker group changes to take effect"
    else
        print_success "Docker is already installed"
    fi
}

# Check if Docker Compose is installed
check_docker_compose() {
    print_status "Checking Docker Compose installation..."
    if ! command -v docker-compose &> /dev/null; then
        print_warning "Docker Compose not found. Installing..."
        sudo apt install -y docker-compose
        print_success "Docker Compose installed successfully"
    else
        print_success "Docker Compose is already installed"
    fi
}

# Check if .env file exists
check_env_file() {
    print_status "Checking .env configuration file..."
    if [ ! -f ".env" ]; then
        print_error ".env file not found!"
        print_status "Creating a template .env file..."
        cat > .env << EOF
# Django Settings
DEBUG=False
SECRET_KEY=CHANGE-THIS-TO-A-VERY-LONG-RANDOM-STRING-FOR-PRODUCTION
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com,your-server-ip

# PostgreSQL Database Settings
DB_NAME=theodosi4_prod
DB_USER=theodosi4_user
DB_PASSWORD=CHANGE-THIS-PASSWORD-FOR-PRODUCTION
DB_HOST=db
DB_PORT=5432

# Email Settings (Optional)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
EMAIL_USE_TLS=True
EOF
        print_warning "Template .env file created. Please edit it with your production values:"
        print_status "nano .env"
        print_error "Cannot continue until .env is properly configured"
        exit 1
    else
        print_success ".env file found"
    fi
}

# Stop existing containers
stop_containers() {
    print_status "Stopping any existing containers..."
    if sudo docker-compose ps -q | grep -q .; then
        sudo docker-compose down
        print_success "Existing containers stopped"
    else
        print_status "No running containers found"
    fi
}

# Build and start containers
build_and_start() {
    print_status "Building and starting containers..."
    sudo docker-compose up --build -d
    
    # Wait for containers to be ready
    print_status "Waiting for containers to be ready..."
    sleep 10
    
    # Check if containers are running
    if sudo docker-compose ps | grep -q "Up"; then
        print_success "Containers started successfully"
    else
        print_error "Failed to start containers"
        sudo docker-compose logs
        exit 1
    fi
}

# Run database migrations
run_migrations() {
    print_status "Running database migrations..."
    sudo docker-compose exec -T web python manage.py migrate
    print_success "Database migrations completed"
}

# Collect static files
collect_static() {
    print_status "Collecting static files..."
    sudo docker-compose exec -T web python manage.py collectstatic --noinput
    print_success "Static files collected"
}

# Create superuser (interactive)
create_superuser() {
    print_status "Do you want to create a Django superuser? (y/n)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        print_status "Creating Django superuser..."
        sudo docker-compose exec web python manage.py createsuperuser
        print_success "Superuser created"
    else
        print_status "Skipping superuser creation"
    fi
}

# Test the deployment
test_deployment() {
    print_status "Testing deployment..."
    
    # Wait a bit for services to be fully ready
    sleep 5
    
    # Test main application
    if curl -s http://localhost:8000 > /dev/null; then
        print_success "Main application is responding"
    else
        print_error "Main application is not responding"
        return 1
    fi
    
    # Test admin interface
    if curl -s http://localhost:8000/admin > /dev/null; then
        print_success "Admin interface is responding"
    else
        print_error "Admin interface is not responding"
        return 1
    fi
    
    print_success "Deployment test completed successfully"
}

# Show final status
show_status() {
    echo
    echo "=== Deployment Status ==="
    sudo docker-compose ps
    echo
    print_success "THEODOSI4 has been deployed successfully!"
    echo
    print_status "Access your application at:"
    print_status "  Main site: http://your-server-ip:8000"
    print_status "  Admin: http://your-server-ip:8000/admin"
    echo
    print_status "View logs with:"
    print_status "  sudo docker-compose logs -f web"
    print_status "  sudo docker-compose logs -f db"
    echo
    print_warning "Next steps:"
    print_status "1. Configure firewall: sudo ufw allow 8000"
    print_status "2. Set up Nginx reverse proxy (see README_POSTGRES.md)"
    print_status "3. Configure SSL certificate with Let's Encrypt"
    print_status "4. Set up automated backups"
    echo
}

# Main execution
main() {
    echo "Starting deployment checks..."
    check_docker
    check_docker_compose
    check_env_file
    
    echo
    print_status "Proceeding with deployment..."
    stop_containers
    build_and_start
    run_migrations
    collect_static
    create_superuser
    
    echo
    print_status "Testing deployment..."
    if test_deployment; then
        show_status
    else
        print_error "Deployment test failed. Check logs for details:"
        print_status "sudo docker-compose logs"
        exit 1
    fi
}

# Run main function
main "$@"