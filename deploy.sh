#!/bin/bash
# Production deployment script for Hotel Booking API (Podman - AlmaLinux/RHEL)
# Version 2.0 - With fixes for registry and DNS conflicts.

set -e

echo "🚀 Starting Hotel Booking API deployment with Podman..."
echo "This script will configure Podman, build services, and start the application."

# --- Helper Functions ---
function check_command() {
    if ! command -v $1 &> /dev/null; then
        echo "❌ Error: Command '$1' not found!"
        echo "Please install it first. For podman-compose, run:"
        echo "  sudo dnf install -y podman podman-docker podman-compose"
        exit 1
    fi
}

function validate_env_var() {
    if ! grep -q "^$1=" .env || grep -q "^$1=$" .env; then
        echo "❌ Error: Required variable '$1' is not set in the .env file."
        exit 1
    fi
}

# --- Pre-flight Checks ---
echo "✅ Step 1: Running pre-flight checks..."

check_command podman-compose
check_command git

if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found!"
    echo "Please copy .env.template to .env and configure it with your production values."
    exit 1
fi

echo "🔍 Validating environment variables..."
validate_env_var "SECRET_KEY"
validate_env_var "DB_PASSWORD"
validate_env_var "EMAIL_HOST_PASSWORD"
echo "✅ Environment variables are valid."

# --- Podman Configuration ---
echo "✅ Step 2: Configuring Podman for production..."
echo "🔧 Resetting Podman configuration to prevent conflicts..."
# Forcefully remove old configs to prevent format mixing errors
# This is to fix "mixing sysregistry v1/v2 is not supported"
rm -f ~/.config/containers/registries.conf
rm -f ~/.config/containers/containers.conf

# Configure Podman registries to prioritize Docker Hub
echo "🔧 Creating new Podman registry configuration..."
mkdir -p ~/.config/containers
cat > ~/.config/containers/registries.conf << EOF
# This configuration forces Podman to use Docker Hub as the default registry.
[registries.search]
registries = ["docker.io"]

# This section is for v2 format compatibility.
[[registry]]
location = "docker.io"
insecure = false
blocked = false
EOF

# Configure Podman networking to avoid DNS conflicts
echo "🔧 Creating new Podman networking configuration..."
cat > ~/.config/containers/containers.conf << EOF
# This configuration prevents Podman's DNS from conflicting with system services
# by using a random port instead of the default port 53.
# This is to fix "Address already in use (os error 98)" for aardvark-dns.
[network]
dns_bind_port = 0
EOF

echo "✅ Podman configuration has been reset and configured for this project."

# --- Application Deployment ---
echo "✅ Step 3: Deploying the application..."

# Pull latest code
if [ -d ".git" ]; then
    echo "📦 Pulling latest code from git..."
    git pull origin main
fi

# Create logs directory
mkdir -p logs

# Stop any existing containers and clean up networks
echo "🧹 Cleaning up existing containers and networks..."
podman-compose -f docker-compose.prod.yml down --volumes --remove-orphans 2>/dev/null || true
podman network prune -f 2>/dev/null || true

# Pre-pull required images from Docker Hub
echo "📥 Pre-pulling required Docker images to ensure availability..."
podman pull docker.io/postgres:15-alpine
podman pull docker.io/redis:7-alpine
podman pull docker.io/nginx:alpine

# Build and start containers
echo "🐳 Building and starting all services..."
podman-compose -f docker-compose.prod.yml up -d --build --force-recreate

# Wait for services to be ready
echo "⏳ Waiting for services to initialize (this may take a minute)..."
sleep 45

# --- Post-Deployment Setup & Verification ---
echo "✅ Step 4: Finalizing setup and verifying deployment..."

# Check if database is ready
echo "🔗 Checking database connection..."
if ! podman-compose -f docker-compose.prod.yml exec -T db pg_isready -U ${DB_USER:-hotel_booking_user}; then
    echo "❌ CRITICAL: Database is not ready. Deployment failed."
    echo "🔍 Check database logs for errors:"
    podman-compose -f docker-compose.prod.yml logs db
    exit 1
fi
echo "✅ Database connection successful."

# Run database migrations
echo "🔧 Running database migrations..."
podman-compose -f docker-compose.prod.yml exec -T api python manage.py migrate

# Collect static files
echo "📁 Collecting static files for Nginx..."
podman-compose -f docker-compose.prod.yml exec -T api python manage.py collectstatic --noinput

# Check for superuser
echo "👤 Checking for existing superuser..."
has_superuser=$(podman-compose -f docker-compose.prod.yml exec -T api python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); print(User.objects.filter(is_superuser=True).exists())")

if [ "$has_superuser" = "False" ]; then
    read -p "❓ No superuser found. Do you want to create one now? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        podman-compose -f docker-compose.prod.yml exec api python manage.py createsuperuser
    fi
fi

# Run Django deployment checks
echo "🔍 Running Django deployment checks..."
if ! podman-compose -f docker-compose.prod.yml exec -T api python manage.py check --deploy; then
    echo "⚠️  Deployment checks reported some issues. Please review the warnings above."
fi

# --- Final Health Check ---
echo "✅ Step 5: Performing final health check..."
sleep 5
if curl -f -s http://localhost/api/v1/health/; then
    echo "🎉 SUCCESS! Deployment completed successfully with Podman!"
    echo "----------------------------------------------------------"
    echo "📊 Service Status:"
    podman-compose -f docker-compose.prod.yml ps
    echo "----------------------------------------------------------"
    echo "📋 Access Information:"
    echo "   - 🌐 API Base URL: http://<your_vps_ip>/api/v1/"
    echo "   - 📚 API Docs:   http://<your_vps_ip>/api/v1/docs/"
    echo "   - 👑 Admin Panel:  http://<your_vps_ip>/admin/"
    echo "   - ❤️  Health Check: http://<your_vps_ip>/api/v1/health/"
    echo "----------------------------------------------------------"
    echo "💡 Next Steps:"
    echo "   1. Point your domain to your VPS IP address."
    echo "   2. Configure SSL certificates for HTTPS (see deployment.md)."
    echo "   3. Set up automated backups and monitoring."
else
    echo "❌ CRITICAL: Final health check failed. The application may not be running correctly."
    echo "🔍 Gathering diagnostic information..."
    echo "--- API Logs (last 20 lines) ---"
    podman-compose -f docker-compose.prod.yml logs --tail=20 api
    echo "--- Nginx Logs (last 20 lines) ---"
    podman-compose -f docker-compose.prod.yml logs --tail=20 nginx
    echo "--- Database Logs (last 10 lines) ---"
    podman-compose -f docker-compose.prod.yml logs --tail=10 db
    echo "-------------------------------------"
    echo "🔥 Please review the logs above to diagnose the issue."
    exit 1
fi
