# 🚀 Hotel Booking API - VPS Deployment Guide

Complete step-by-step guide for deploying the Hotel Booking Engine API on VPS hosting.

## 🎯 Quick Deployment Summary

**Total deployment time: ~30-40 minutes**

### For Your Friend - Quick Steps:
1. **Prerequisites** (5 minutes): Ensure VPS has AlmaLinux/RHEL 8+ with 2GB+ RAM, 2+ CPU cores, 20GB+ storage
2. **Quick Deployment** (15-20 minutes): Clone project, configure environment, run automated deployment script
3. **Configuration** (10 minutes): Update `.env` file with production values (domain, database, email)
4. **SSL Setup** (5 minutes): Configure SSL certificates after DNS propagation

### ✅ Deployment Readiness Status

**This project is PRODUCTION READY** with:
- 🐳 **Docker/Podman**: Complete containerization with health checks
- 🗄️ **Database**: PostgreSQL with automated backups
- 🔄 **Redis**: Caching and session management
- 🌐 **Nginx**: Reverse proxy with SSL support and rate limiting
- 🔒 **Security**: Environment variables, CORS, JWT authentication, firewall configuration
- 📊 **Monitoring**: Health checks, logging, and maintenance automation
- ✅ **Tests**: All 26 tests passing successfully
- ✅ **Health Check**: API responding correctly (`{"status": "healthy", "database": "connected", "cache": "connected"}`)

### 🔍 Pre-Deployment Verification Completed

**All required files verified:**
- ✅ `deploy.sh` - Automated deployment script
- ✅ `docker-compose.prod.yml` - Production containers configuration
- ✅ `Dockerfile` - Application container with proper user permissions
- ✅ `.env.template` - Environment configuration template
- ✅ `nginx.conf` - Web server with security headers and rate limiting
- ✅ `requirements.txt` - All dependencies including PostgreSQL driver
- ✅ `hotel_booking/hotel_booking/deployment.py` - Production Django settings
- ✅ Logging directory created and configured
- ✅ Static files configuration ready
- ✅ Health endpoint functional

### 📋 Quick Deployment Checklist for VPS

**Before deployment, ensure you have:**
1. ✅ AlmaLinux/RHEL 8+ VPS with 2GB+ RAM, 2+ CPU cores, 20GB+ storage
2. ✅ Domain name pointed to your VPS IP
3. ✅ SSH access to your VPS
4. ✅ Email provider credentials (Gmail App Password recommended)

**Your deployment will take ~30-40 minutes:**
- 5 minutes: VPS setup and prerequisites
- 15-20 minutes: Clone project and run deployment script
- 10 minutes: Configure environment variables
- 5 minutes: SSL certificate setup

## 📋 Prerequisites

### VPS Requirements
- **Operating System:** AlmaLinux 8+/9+ (Red Hat Enterprise Linux compatible)
- **RAM:** Minimum 2GB (4GB recommended)
- **CPU:** 2+ cores
- **Storage:** 20GB+ SSD
- **Network:** Public IP address

### Local Requirements
- SSH client (Terminal on Mac/Linux, PuTTY on Windows)
- Your VPS credentials (IP address, username, password/SSH key)
- Domain name (optional but recommended)

---

## 🔧 STEP 1: Initial VPS Setup

### Connect to Your VPS

```bash
# Replace YOUR_VPS_IP with your actual VPS IP address
ssh root@YOUR_VPS_IP

# Or if you have a specific username
ssh username@YOUR_VPS_IP

# If using SSH key
ssh -i /path/to/your/key.pem username@YOUR_VPS_IP
```

### AlmaLinux-Specific Setup & System Update

```bash
# Check AlmaLinux version
cat /etc/os-release

# Update package lists and upgrade system
sudo dnf update -y && sudo dnf upgrade -y

# Install essential tools and development packages
sudo dnf install -y git curl wget unzip htop nano vim

# Install Development Tools group for building packages
sudo dnf groupinstall -y "Development Tools"

# Install EPEL repository for additional packages
sudo dnf install -y epel-release

# Enable PowerTools/CRB repository for dependencies
# For AlmaLinux 8:
sudo dnf config-manager --set-enabled powertools
# For AlmaLinux 9:
# sudo dnf config-manager --set-enabled crb

# Update repository cache after adding repos
sudo dnf makecache

# Install Python 3 and development tools (if not already installed)
sudo dnf install -y python3 python3-pip python3-devel

# Reboot if kernel was updated
sudo reboot
```

---

## 🐳 STEP 2: Install Podman & Podman Compose

### Install Podman (Native Container Engine for RHEL/AlmaLinux)

```bash
# Install Podman and related tools (native to RHEL/AlmaLinux)
sudo dnf install -y podman podman-docker podman-compose

# Install additional container tools
sudo dnf install -y buildah skopeo

# Enable and start Podman socket for better performance
sudo systemctl --user enable podman.socket
sudo systemctl --user start podman.socket

# Enable user lingering to allow containers to run without login
sudo loginctl enable-linger $(whoami)

# Verify Podman installation
podman --version
podman-compose --version
```

### Configure Podman for Rootless Operation

```bash
# Podman runs rootless by default - verify setup
podman info | grep -i rootless

# Initialize Podman for current user
podman system migrate

# Test Podman installation
podman run hello-world

# Configure Podman registries (IMPORTANT - fixes image pull issues)
mkdir -p ~/.config/containers
cat > ~/.config/containers/registries.conf << EOF
[registries.search]
registries = ["docker.io"]

[registries.insecure]
registries = []

[registries.block]
registries = []

[[registry]]
location = "docker.io"
insecure = false
blocked = false
EOF

echo "✅ Podman configured to use Docker Hub registry"
```

**Note:** This configuration ensures Podman pulls images from Docker Hub instead of Red Hat's registry, which prevents authentication and "repo not found" errors.

### SELinux Configuration (AlmaLinux/RHEL Security)

```bash
# Check SELinux status
sudo getenforce

# Configure SELinux for containers and web services (if enabled)
if [ "$(getenforce)" != "Disabled" ]; then
    # Allow containers to manage cgroups
    sudo setsebool -P container_manage_cgroup 1
    
    # Allow web services to make network connections
    sudo setsebool -P httpd_can_network_connect 1
    sudo setsebool -P httpd_can_network_relay 1
    
    # Allow containers to use system resources
    sudo setsebool -P virt_use_nfs 1
    sudo setsebool -P virt_use_samba 1
    
    # Allow containers to bind to privileged ports
    sudo setsebool -P container_use_cgroup_namespace 1
    
    echo "✅ SELinux configured for Podman and web services"
else
    echo "⚠️  SELinux is disabled"
fi

# Optional: Install SELinux troubleshooting tools
sudo dnf install -y setroubleshoot-server policycoreutils-python-utils
```

---

## 📦 STEP 3: Deploy Application Code

### Clone Repository and Set Permissions

```bash
# Navigate to applications directory
cd /opt

# Clone the project from GitHub
sudo git clone https://github.com/Mujadid2001/HotelBookingEngine.git

# Change ownership to current user (important for Podman rootless)
sudo chown -R $USER:$USER HotelBookingEngine

# Navigate to project directory
cd HotelBookingEngine

# Check project structure
ls -la

# Verify all required files are present
echo "✅ Checking required files..."
required_files=("deploy.sh" "docker-compose.prod.yml" "Dockerfile" ".env.template" "nginx.conf")
for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file found"
    else
        echo "❌ $file missing"
        exit 1
    fi
done
```

---

## ⚙️ STEP 4: Environment Configuration

### Understanding Settings Files

This project uses **two different settings files**:

- **`settings.py`** - For development (SQLite, local testing)
- **`deployment.py`** - For production (PostgreSQL, containers, environment variables)

The Docker container automatically uses `deployment.py` for production deployment.

### Create Environment File

```bash
# Copy environment template
cp .env.template .env

# Edit the environment file with your production values
nano .env
```

### Configure Environment Variables

Replace the content with your production values:

```bash
# Django Configuration
SECRET_KEY=your-super-secure-secret-key-at-least-50-characters-long-with-random-numbers-and-symbols
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,YOUR_VPS_IP

# Database Configuration (PostgreSQL)
DB_NAME=hotel_booking_prod
DB_USER=hotel_booking_user
DB_PASSWORD=your_very_secure_database_password_123!
DB_HOST=db
DB_PORT=5432

# Email Configuration (Gmail Example)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your_gmail_app_password
DEFAULT_FROM_EMAIL=Hotel Booking System <your-email@gmail.com>
SERVER_EMAIL=Hotel Booking System <your-email@gmail.com>

# Security Settings (Enable after SSL setup)
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False

# Redis Configuration
REDIS_URL=redis://redis:6379/0
```

### Generate Secure SECRET_KEY

```bash
# Generate a random secret key (using Python)
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(50))"

# Alternative: Generate using OpenSSL
openssl rand -base64 50 | tr -d '\n' && echo

# Copy the output and use it in your .env file
```

### 📧 How to Obtain Gmail App Password for Email Configuration

For the `EMAIL_HOST_PASSWORD` in your `.env` file, you'll need to generate a Gmail App Password (not your regular Gmail password). Follow these steps:

#### Step 1: Enable 2-Factor Authentication
1. Go to your [Google Account settings](https://myaccount.google.com/)
2. Navigate to **Security** in the left sidebar
3. Under **Signing in to Google**, click **2-Step Verification**
4. Follow the setup process to enable 2FA (required for App Passwords)

#### Step 2: Generate App Password
1. After enabling 2FA, go back to **Security** settings
2. Under **Signing in to Google**, click **App passwords**
3. You may need to sign in again for verification
4. In the **Select app** dropdown, choose **Mail**
5. In the **Select device** dropdown, choose **Other (Custom name)**
6. Enter a name like "Hotel Booking API" or "VPS Server"
7. Click **Generate**
8. Google will display a 16-character password (example: `abcd efgh ijkl mnop`)
9. **Copy this password immediately** - you won't be able to see it again
10. Use this 16-character password as your `EMAIL_HOST_PASSWORD` in the `.env` file

#### Step 3: Configure .env File
```bash
# Use the 16-character App Password (remove spaces)
EMAIL_HOST_PASSWORD=abcdefghijklmnop
```

#### Alternative Email Providers

**If you don't want to use Gmail:**
- **Outlook/Hotmail**: Use `smtp.office365.com` port `587`
- **Yahoo**: Use `smtp.mail.yahoo.com` port `587` 
- **Custom SMTP**: Contact your email provider for SMTP settings

**For other providers, you may need:**
- SMTP server address
- Port number (usually 587 for TLS or 465 for SSL)
- Username (usually your email address)
- Password or App-specific password

#### Important Security Notes
- **Never use your regular Gmail password** - always use App Passwords
- **Keep your App Password secure** - treat it like a regular password
- **If compromised**: Delete the App Password from Google Account settings and generate a new one
- **Multiple apps**: Generate separate App Passwords for different applications

### Important Configuration Notes

- **SECRET_KEY:** Must be unique, at least 50 characters, and kept secret
- **ALLOWED_HOSTS:** Include your domain, www subdomain, and VPS IP address
- **DB_PASSWORD:** Use a strong password with letters, numbers, and symbols
- **EMAIL_HOST_PASSWORD:** For Gmail, use App Passwords (16-character code from Google Account settings)
- **DEBUG:** Must be False for production
- **SSL Settings:** Start with False, enable after SSL certificates are configured

### Example Production .env Configuration

```bash
# Example configuration - DO NOT use these exact values
SECRET_KEY=AbCdEf123456789_Your_Very_Long_Random_Secret_Key_Here_987654321
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,123.45.67.89

DB_NAME=hotel_booking_prod
DB_USER=hotel_booking_user
DB_PASSWORD=SuperSecure_DB_Pass123!
DB_HOST=db
DB_PORT=5432

EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=booking@yourdomain.com
EMAIL_HOST_PASSWORD=your_app_password_here
DEFAULT_FROM_EMAIL=Hotel Booking System <booking@yourdomain.com>
SERVER_EMAIL=Hotel Booking System <booking@yourdomain.com>

# Start with False, enable after SSL setup
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False
```

---

## 🔒 STEP 5: Configure Server Security

### Setup Firewall

```bash
# Enable and start firewalld
sudo systemctl enable firewalld
sudo systemctl start firewalld

# Allow SSH (CRITICAL - Don't lock yourself out!)
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-port=22/tcp

# Allow HTTP and HTTPS
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --permanent --add-port=80/tcp
sudo firewall-cmd --permanent --add-port=443/tcp

# Optional: Allow direct API access
sudo firewall-cmd --permanent --add-port=8000/tcp

# Reload firewall rules
sudo firewall-cmd --reload

# Check firewall status
sudo firewall-cmd --list-all
```

### Create Non-Root User (Recommended)

```bash
# Create application user (Podman runs rootless - no docker group needed)
sudo adduser appuser
sudo usermod -aG sudo appuser

# Switch to app user
su - appuser
cd /opt/HotelBookingEngine
```

---

## 🚀 STEP 6: Deploy Application

### Automated Deployment (Recommended)

```bash
# Ensure you're in the project directory
cd /opt/HotelBookingEngine

# Make deploy script executable
chmod +x deploy.sh

# Run automated deployment
./deploy.sh
```

**The deploy.sh script will automatically:**
- ✅ Validate environment variables
- ✅ Build and start all containers with Podman
- ✅ Run database migrations
- ✅ Collect static files
- ✅ Check for superuser and prompt to create one
- ✅ Run Django deployment checks
- ✅ Test API health endpoint
- ✅ Display service status and access URLs

### Manual Deployment (If Automated Script Fails)

```bash
# Create logs directory
mkdir -p logs

# Stop any existing containers
podman-compose -f docker-compose.prod.yml down --volumes

# Build and start all services
podman-compose -f docker-compose.prod.yml up -d --build

# Wait for services to initialize (important!)
echo "⏳ Waiting for services to start..."
sleep 45

# Check container status
podman-compose -f docker-compose.prod.yml ps

# Check service logs if any containers failed
podman-compose -f docker-compose.prod.yml logs
```

### Database Setup

```bash
# Run database migrations
podman-compose -f docker-compose.prod.yml exec api python manage.py migrate

# Collect static files for nginx
podman-compose -f docker-compose.prod.yml exec api python manage.py collectstatic --noinput

# Create superuser account (for admin access)
podman-compose -f docker-compose.prod.yml exec api python manage.py createsuperuser

# Test Django deployment configuration
podman-compose -f docker-compose.prod.yml exec api python manage.py check --deploy
```

---

## ✅ STEP 7: Verify Deployment

### Check All Services

```bash
# View running containers and their status
podman-compose -f docker-compose.prod.yml ps

# Check individual service logs
echo "📋 Checking API logs..."
podman-compose -f docker-compose.prod.yml logs --tail=20 api

echo "📋 Checking Database logs..."
podman-compose -f docker-compose.prod.yml logs --tail=10 db

echo "📋 Checking Nginx logs..."
podman-compose -f docker-compose.prod.yml logs --tail=10 nginx

echo "📋 Checking Redis logs..."
podman-compose -f docker-compose.prod.yml logs --tail=10 redis
```

### Test API Endpoints

```bash
# Test health endpoint (most important)
curl -v http://YOUR_VPS_IP/api/v1/health/

# Test API root
curl http://YOUR_VPS_IP/api/v1/

# Test API documentation
curl -I http://YOUR_VPS_IP/api/v1/docs/

# Test admin interface
curl -I http://YOUR_VPS_IP/admin/

# Test with domain (after DNS setup)
curl http://yourdomain.com/api/v1/health/
```

**Expected health response:**
```json
{
    "status": "healthy",
    "database": "connected", 
    "cache": "connected",
    "timestamp": 1692700000.0,
    "response_time_ms": 25.4
}
```

### Troubleshoot Common Issues

```bash
# If API health check fails, check these:

# 1. Container status
podman-compose -f docker-compose.prod.yml ps

# 2. API container logs
podman-compose -f docker-compose.prod.yml logs api

# 3. Database connection
podman-compose -f docker-compose.prod.yml exec db pg_isready -U hotel_booking_user

# 4. Port accessibility
sudo netstat -tulpn | grep :80
sudo netstat -tulpn | grep :8000

# 5. Firewall status
sudo firewall-cmd --list-all

# 6. SELinux denials (if enabled)
sudo ausearch -m avc -ts recent
```

---

## 🌐 STEP 8: Domain Configuration

### DNS Setup

In your domain registrar's control panel, add these DNS records:

```
Type: A
Name: @
Value: YOUR_VPS_IP
TTL: 300

Type: A
Name: www
Value: YOUR_VPS_IP
TTL: 300

Type: A
Name: api
Value: YOUR_VPS_IP
TTL: 300
```

### Wait for DNS Propagation

```bash
# Check DNS propagation (wait 15-30 minutes)
nslookup yourdomain.com
dig yourdomain.com

# Test domain access
curl http://yourdomain.com/api/v1/health/
```

---

## 🔐 STEP 9: SSL Certificate Setup

### Install Certbot

```bash
# Install Certbot via DNF (AlmaLinux/RHEL)
sudo dnf install -y certbot

# Alternative: Install via Snap if available
# sudo dnf install -y snapd
# sudo systemctl enable --now snapd.socket
# sudo snap install --classic certbot
# sudo ln -s /snap/bin/certbot /usr/bin/certbot
```

### Obtain SSL Certificate

```bash
# Stop nginx temporarily
podman-compose -f docker-compose.prod.yml stop nginx

# Get SSL certificate for your domain
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# Follow the prompts and provide your email
```

### Configure SSL in Application

```bash
# Create SSL directory in project
mkdir -p ssl

# Copy certificates to project directory
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ssl/
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ssl/

# Fix ownership
sudo chown -R $USER:$USER ssl/
```

### Enable SSL in Environment

```bash
# Edit environment file
nano .env

# Update these settings:
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

### Restart Services

```bash
# Restart all services to apply SSL
podman-compose -f docker-compose.prod.yml restart

# Test HTTPS
curl https://yourdomain.com/api/v1/health/
```

---

## 🔄 STEP 10: Automation & Maintenance

### Auto-SSL Renewal

```bash
# Create SSL renewal script
sudo tee /opt/ssl-renew.sh > /dev/null <<'EOF'
#!/bin/bash
cd /opt/HotelBookingEngine
podman-compose -f docker-compose.prod.yml stop nginx
certbot renew --quiet
cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ssl/
cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ssl/
chown -R $USER:$USER ssl/
podman-compose -f docker-compose.prod.yml start nginx
EOF

# Make executable
sudo chmod +x /opt/ssl-renew.sh

# Add to crontab for monthly renewal
(crontab -l 2>/dev/null; echo "0 3 1 * * /opt/ssl-renew.sh") | crontab -
```

### Database Backup Automation

```bash
# Create backup script
sudo tee /opt/backup-db.sh > /dev/null <<'EOF'
#!/bin/bash
BACKUP_DIR="/opt/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

cd /opt/HotelBookingEngine
podman-compose -f docker-compose.prod.yml exec -T db pg_dump -U hotel_booking_user hotel_booking_prod > $BACKUP_DIR/db_backup_$DATE.sql

# Compress backup
gzip $BACKUP_DIR/db_backup_$DATE.sql

# Keep only last 7 days of backups
find $BACKUP_DIR -name "db_backup_*.sql.gz" -type f -mtime +7 -delete

echo "Database backup completed: db_backup_$DATE.sql.gz"
EOF

# Make executable
sudo chmod +x /opt/backup-db.sh

# Add to crontab for daily backups at 2 AM
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/backup-db.sh") | crontab -
```

### Application Update Script

```bash
# Create update script
tee /opt/HotelBookingEngine/update.sh > /dev/null <<'EOF'
#!/bin/bash
echo "🔄 Updating Hotel Booking API..."

cd /opt/HotelBookingEngine

# Pull latest code
git pull origin main

# Rebuild and restart services
podman-compose -f docker-compose.prod.yml down
podman-compose -f docker-compose.prod.yml up -d --build

# Wait for services
sleep 30

# Run migrations
podman-compose -f docker-compose.prod.yml exec api python manage.py migrate

# Collect static files
podman-compose -f docker-compose.prod.yml exec api python manage.py collectstatic --noinput

echo "✅ Update completed!"
EOF

chmod +x update.sh
```

---

## 🎯 Your API is Now Live!

### 🌐 Service Access Points

After successful deployment, your API will be available at:

- **� API Root:** `http://YOUR_VPS_IP/api/v1/` or `https://yourdomain.com/api/v1/`
- **📚 Interactive Docs (Swagger):** `http://YOUR_VPS_IP/api/v1/docs/`
- **📖 ReDoc Documentation:** `http://YOUR_VPS_IP/api/v1/redoc/`
- **⚕️ Health Check:** `http://YOUR_VPS_IP/api/v1/health/`
- **👑 Admin Panel:** `http://YOUR_VPS_IP/admin/`

### 🧪 Complete API Testing Suite

Test all critical endpoints to ensure everything works:

```bash
# 1. Health Check (Critical)
curl -X GET http://YOUR_VPS_IP/api/v1/health/
# Should return: {"status": "healthy", "database": "connected", ...}

# 2. API Root
curl -X GET http://YOUR_VPS_IP/api/v1/
# Should return: {"message": "Hotel Booking API", "version": "v1.0", ...}

# 3. Hotels List (Public endpoint)
curl -X GET http://YOUR_VPS_IP/api/v1/hotels/
# Should return: {"count": 0, "next": null, "previous": null, "results": []}

# 4. API Documentation
curl -I http://YOUR_VPS_IP/api/v1/docs/
# Should return: HTTP/1.1 200 OK

# 5. Admin Interface
curl -I http://YOUR_VPS_IP/admin/
# Should return: HTTP/1.1 200 OK

# 6. Test User Registration (POST endpoint)
curl -X POST http://YOUR_VPS_IP/api/v1/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "securepass123",
    "first_name": "Test",
    "last_name": "User"
  }'
# Should return user data or validation errors
```

### 📋 API Endpoint Reference

```bash
# Authentication Endpoints
POST /api/v1/auth/register/           # User registration
POST /api/v1/auth/login/              # User login
POST /api/v1/auth/logout/             # User logout
POST /api/v1/auth/refresh/            # Refresh JWT token
GET  /api/v1/auth/profile/            # User profile

# Hotel Management
GET  /api/v1/hotels/                  # List all hotels
GET  /api/v1/hotels/{id}/             # Hotel details
GET  /api/v1/hotels/{id}/rooms/       # Hotel rooms
GET  /api/v1/hotels/search/           # Search hotels

# Room Management
GET  /api/v1/rooms/{id}/              # Room details
GET  /api/v1/rooms/{id}/availability/ # Room availability

# Booking Management  
POST /api/v1/bookings/                # Create booking
GET  /api/v1/bookings/                # List user bookings
GET  /api/v1/bookings/{id}/           # Booking details
PUT  /api/v1/bookings/{id}/           # Update booking
DELETE /api/v1/bookings/{id}/         # Cancel booking

# System Endpoints
GET  /api/v1/health/                  # Health check
GET  /api/v1/docs/                    # API documentation
GET  /api/v1/redoc/                   # Alternative docs
```

---

## 🛠️ Management Commands

### Daily Operations

```bash
# Check service status
podman-compose -f docker-compose.prod.yml ps

# View real-time logs
podman-compose -f docker-compose.prod.yml logs -f api

# Restart specific service
podman-compose -f docker-compose.prod.yml restart api

# View system resources
htop
df -h
free -h
```

### Backup & Restore

```bash
# Manual database backup
cd /opt/HotelBookingEngine
podman-compose -f docker-compose.prod.yml exec db pg_dump -U hotel_booking_user hotel_booking_prod > backup_$(date +%Y%m%d).sql

# Restore database from backup
podman-compose -f docker-compose.prod.yml exec -T db psql -U hotel_booking_user hotel_booking_prod < backup_file.sql
```

### Update Application

```bash
# Update application
cd /opt/HotelBookingEngine
git pull origin main
podman-compose -f docker-compose.prod.yml up -d --build
```

---

## 🚨 Troubleshooting Guide

### 🔧 Common Issues and Solutions

#### 1. Registry/Image Pull Errors (Podman)
**Error:** `Error: initializing source docker://registry.access.redhat.com/postgres:15-alpine: reading manifest 15-alpine in registry.access.redhat.com/postgres: name unknown: Repo not found`

**Solution:**
```bash
# Configure Podman to use Docker Hub registry
mkdir -p ~/.config/containers
cat > ~/.config/containers/registries.conf << EOF
[registries.search]
registries = ["docker.io"]

[registries.insecure]
registries = []

[registries.block]
registries = []

[[registry]]
location = "docker.io"
insecure = false
blocked = false
EOF

# Pre-pull images from Docker Hub
podman pull docker.io/postgres:15-alpine
podman pull docker.io/redis:7-alpine
podman pull docker.io/nginx:alpine

# Restart deployment
./deploy.sh
```

**Quick Fix Script:** A `fix-registry.sh` script is included in the project that automates this fix:
```bash
# Run the quick fix script
chmod +x fix-registry.sh
./fix-registry.sh

# Then run deployment
./deploy.sh
```

**Why this happens:** Podman on AlmaLinux/RHEL sometimes defaults to Red Hat's registry instead of Docker Hub, causing authentication and "repo not found" errors.

#### 2. DNS Port Conflict (Aardvark-DNS Error)
**Error:** `aardvark-dns failed to start: Error from child process... failed to bind udp listener on 10.89.0.1:53: Address already in use`

**Solution:**
```bash
# Configure Podman to avoid DNS port conflicts
mkdir -p ~/.config/containers
cat > ~/.config/containers/containers.conf << EOF
[network]
dns_bind_port = 0

[engine]
network_cmd_options = ["enable_ipv6=false"]
EOF

# Clean up existing networks
podman network prune -f
podman-compose -f docker-compose.prod.yml down --volumes

# Restart deployment
./deploy.sh
```

**Alternative Solution - Disable systemd-resolved:**
```bash
# If the above doesn't work, disable systemd-resolved temporarily
sudo systemctl stop systemd-resolved
sudo systemctl disable systemd-resolved

# Use alternative DNS
echo "nameserver 8.8.8.8" | sudo tee /etc/resolv.conf

# Run deployment
./deploy.sh

# Re-enable systemd-resolved after deployment
sudo systemctl enable systemd-resolved
sudo systemctl start systemd-resolved
```

**Why this happens:** Podman's DNS service (aardvark-dns) conflicts with system DNS services like systemd-resolved that are already using port 53.

#### 3. Container Won't Start
```bash
# Check container logs for errors
podman-compose -f docker-compose.prod.yml logs

# Check specific service logs
podman-compose -f docker-compose.prod.yml logs api
podman-compose -f docker-compose.prod.yml logs db
podman-compose -f docker-compose.prod.yml logs nginx

# Rebuild containers from scratch
podman-compose -f docker-compose.prod.yml down --volumes
podman-compose -f docker-compose.prod.yml build --no-cache
podman-compose -f docker-compose.prod.yml up -d
```

#### 4. Database Connection Error
```bash
# Check database container status
podman-compose -f docker-compose.prod.yml ps

# Test database connection
podman-compose -f docker-compose.prod.yml exec db pg_isready -U hotel_booking_user

# Check database logs
podman-compose -f docker-compose.prod.yml logs db

# Reset database (⚠️ This will delete all data)
podman-compose -f docker-compose.prod.yml down -v
podman-compose -f docker-compose.prod.yml up -d
```

#### 5. API Health Check Fails
```bash
# 1. Check if API container is running
podman-compose -f docker-compose.prod.yml ps

# 2. Check API logs for errors
podman-compose -f docker-compose.prod.yml logs api

# 3. Test internal API connection
podman-compose -f docker-compose.prod.yml exec api curl http://localhost:8000/api/v1/health/

# 4. Check Django configuration
podman-compose -f docker-compose.prod.yml exec api python manage.py check

# 5. Restart API service
podman-compose -f docker-compose.prod.yml restart api
```

#### 4. Domain Not Working
```bash
# Check DNS propagation
nslookup yourdomain.com
dig yourdomain.com

# Test with IP directly first
curl http://YOUR_VPS_IP/api/v1/health/

# Check nginx configuration
podman-compose -f docker-compose.prod.yml logs nginx

# Test nginx config syntax
podman-compose -f docker-compose.prod.yml exec nginx nginx -t
```

#### 5. SSL Certificate Issues
```bash
# Check certificate validity
openssl x509 -in ssl/fullchain.pem -text -noout

# Renew certificate manually
sudo certbot renew

# Check certificate files exist
ls -la ssl/

# Restart nginx after certificate update
podman-compose -f docker-compose.prod.yml restart nginx
```

#### 6. SELinux Issues (AlmaLinux/RHEL)
```bash
# Check for SELinux denials
sudo ausearch -m avc -ts recent

# Temporarily disable SELinux for testing (NOT for production)
sudo setenforce 0

# Re-enable SELinux
sudo setenforce 1

# Generate custom SELinux policy if needed
sudo grep podman /var/log/audit/audit.log | audit2allow -M mypodman
sudo semodule -i mypodman.pp

# Check SELinux context of files
ls -laZ /opt/HotelBookingEngine/
```

#### 7. Firewall Issues
```bash
# Check current firewall rules
sudo firewall-cmd --list-all

# Temporarily disable firewall for testing
sudo systemctl stop firewalld

# Re-enable firewall
sudo systemctl start firewalld

# Add custom port
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --reload

# Check if ports are listening
sudo netstat -tulpn | grep -E ':80|:443|:8000'
```

#### 8. Out of Disk Space
```bash
# Check disk usage
df -h

# Clean Podman resources
podman system prune -a --volumes

# Clean old container images
podman image prune -a

# Clean old backups
find /opt/backups -name "db_backup_*.sql.gz" -type f -mtime +7 -delete

# Check largest directories
du -h --max-depth=1 /opt/ | sort -hr
```

#### 9. Permission Issues
```bash
# Fix ownership of project files
sudo chown -R $USER:$USER /opt/HotelBookingEngine

# Fix permissions for logs directory
mkdir -p logs
chmod 755 logs

# Check file permissions
ls -la /opt/HotelBookingEngine/

# Fix execute permissions on scripts
chmod +x deploy.sh
```

#### 10. Memory/Performance Issues
```bash
# Check system resources
free -h
htop

# Check container resource usage
podman stats

# Restart services to clear memory
podman-compose -f docker-compose.prod.yml restart

# Check system logs for OOM (Out of Memory) errors
sudo journalctl -f | grep -i "killed process"
```

---

## 📊 Monitoring & Logs

### Log Locations

```bash
# Application logs
podman-compose -f docker-compose.prod.yml logs api

# Database logs
podman-compose -f docker-compose.prod.yml logs db

# Nginx logs
podman-compose -f docker-compose.prod.yml logs nginx

# System logs (AlmaLinux/RHEL)
sudo journalctl -u podman
sudo journalctl -u firewalld

# SELinux logs (if enabled)
sudo ausearch -m avc -ts recent

# Server logs
sudo journalctl -f
tail -f /var/log/messages
```

### Performance Monitoring

```bash
# System resources
htop
iostat
netstat -tulpn

# Podman stats
podman stats

# Database performance
podman-compose -f docker-compose.prod.yml exec db psql -U hotel_booking_user -d hotel_booking_prod -c "SELECT * FROM pg_stat_activity;"
```

---

## 🔐 Security Best Practices

### Applied Security Measures

- ✅ Firewall configured (Firewalld)
- ✅ Rootless containers with Podman
- ✅ SSL/TLS encryption
- ✅ Secure database passwords
- ✅ Environment variables for secrets
- ✅ Rate limiting (nginx)
- ✅ CORS properly configured
- ✅ JWT token security

### Additional Recommendations

```bash
# Disable root login (optional)
sudo nano /etc/ssh/sshd_config
# Set: PermitRootLogin no
sudo systemctl restart sshd

# Enable automatic security updates (AlmaLinux/RHEL)
sudo dnf install -y dnf-automatic
sudo systemctl enable --now dnf-automatic.timer

# Monitor failed login attempts
sudo dnf install -y fail2ban
sudo systemctl enable --now fail2ban

# Configure SELinux (if enabled)
sudo setsebool -P httpd_can_network_connect 1
sudo setsebool -P httpd_can_network_relay 1
```

---

## 📞 Support & Maintenance

### Getting Help

1. Check the troubleshooting section above
2. Review application logs for errors
3. Check GitHub repository issues
4. Contact system administrator

### Regular Maintenance Tasks

- **Daily:** Monitor application logs and performance
- **Weekly:** Check backup integrity, review security logs
- **Monthly:** Update system packages (`sudo dnf update`), renew SSL certificates
- **Quarterly:** Review security settings, update application, check SELinux policies

---

**🎉 Congratulations! Your Hotel Booking API is now successfully deployed and running in production!**

For additional support or questions, refer to the project documentation or contact the development team.
