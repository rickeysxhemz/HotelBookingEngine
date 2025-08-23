# 🚀 Hotel Booking API - VPS Deployment Guide

Complete step-by-step guide for deploying the Hotel Booking Engine API on VPS hosting.

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

### AlmaLinux-Specific Setup

```bash
# Check AlmaLinux version
cat /etc/os-release

# Ensure system is up to date
sudo dnf check-update

# Install commonly needed repositories
sudo dnf install -y epel-release
sudo dnf config-manager --set-enabled powertools  # For AlmaLinux 8
# OR for AlmaLinux 9:
# sudo dnf config-manager --set-enabled crb

# Update repository cache
sudo dnf makecache

# Install Podman-Docker compatibility (Alternative to Docker)
# Note: AlmaLinux/RHEL often prefer Podman over Docker
# Uncomment the following lines if you prefer Podman:
# sudo dnf install -y podman podman-docker
# sudo systemctl enable --now podman.socket
# alias docker=podman
# alias docker-compose=podman-compose
```

### Update System

```bash
# Update package lists and upgrade system
sudo dnf update -y && sudo dnf upgrade -y

# Install essential tools
sudo dnf install -y git curl wget unzip htop nano

# Install Development Tools group
sudo dnf groupinstall -y "Development Tools"

# Install Python 3 and pip (if not already installed)
sudo dnf install -y python3 python3-pip

# Install EPEL repository for additional packages
sudo dnf install -y epel-release

# Reboot if kernel was updated
sudo reboot
```

---

## 🐳 STEP 2: Install Docker & Docker Compose

### Option A: Install Docker (Recommended)

```bash
# Download and install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Verify Docker installation
docker --version
```

### Option B: Install Podman (RHEL Native Alternative)

```bash
# Install Podman (Red Hat's container engine)
sudo dnf install -y podman podman-docker podman-compose

# Enable Podman socket for Docker compatibility
sudo systemctl enable --now podman.socket

# Create Docker alias for compatibility
echo 'alias docker=podman' >> ~/.bashrc
echo 'alias docker-compose=podman-compose' >> ~/.bashrc
source ~/.bashrc

# Verify Podman installation
podman --version
podman-compose --version
```

### Install Docker Compose (If using Docker)

```bash
# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# Make it executable
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker-compose --version
```

### Configure Container Permissions

```bash
# For Docker: Add current user to docker group
sudo usermod -aG docker $USER

# For Podman: Enable rootless containers (already default)
# No additional configuration needed for Podman

# Apply group changes (logout and login again)
exit
# SSH back in
ssh root@YOUR_VPS_IP
```

### SELinux Configuration (AlmaLinux/RHEL)

```bash
# Check SELinux status
getenforce

# If SELinux is enabled, configure it for Docker and web services
if [ "$(getenforce)" != "Disabled" ]; then
    # Allow Docker to work with SELinux
    sudo setsebool -P container_manage_cgroup 1
    
    # Allow web services to make network connections
    sudo setsebool -P httpd_can_network_connect 1
    sudo setsebool -P httpd_can_network_relay 1
    
    # Allow containers to use all system resources
    sudo setsebool -P virt_use_nfs 1
    sudo setsebool -P virt_use_samba 1
    
    echo "SELinux configured for Docker and web services"
else
    echo "SELinux is disabled"
fi
```

---

## 📦 STEP 3: Deploy Application Code

### Clone Repository

```bash
# Navigate to application directory
cd /opt

# Clone the project from GitHub
sudo git clone https://github.com/Mujadid2001/HotelBookingEngine.git

# Change ownership to current user
sudo chown -R $USER:$USER HotelBookingEngine

# Navigate to project directory
cd HotelBookingEngine

# Check project structure
ls -la
```

---

## ⚙️ STEP 4: Environment Configuration

### Create Environment File

```bash
# Copy environment template
cp .env.template .env

# Edit the environment file
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
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your_gmail_app_password
DEFAULT_FROM_EMAIL=Hotel Booking System <your-email@gmail.com>

# Security Settings (Enable after SSL setup)
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False

# Redis Configuration
REDIS_URL=redis://redis:6379/0
```

### Generate Secure SECRET_KEY

```bash
# Generate a random secret key
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(50))"

# Copy the output and use it in your .env file
```

### Important Configuration Notes

- **SECRET_KEY:** Must be unique and at least 50 characters
- **ALLOWED_HOSTS:** Include your domain and VPS IP
- **DB_PASSWORD:** Use a strong password (letters, numbers, symbols)
- **EMAIL_HOST_PASSWORD:** For Gmail, use App Passwords, not your regular password

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
# Create application user
sudo adduser appuser
sudo usermod -aG sudo appuser
sudo usermod -aG docker appuser

# Switch to app user
su - appuser
cd /opt/HotelBookingEngine
```

---

## 🚀 STEP 6: Deploy Application

### Automated Deployment

```bash
# Make deploy script executable
chmod +x deploy.sh

# Run automated deployment
./deploy.sh
```

### Manual Deployment (If Script Fails)

```bash
# Create logs directory
mkdir -p logs

# Stop any existing containers
docker-compose -f docker-compose.prod.yml down --volumes

# Build and start all services
docker-compose -f docker-compose.prod.yml up -d --build

# Wait for services to initialize
echo "Waiting for services to start..."
sleep 45

# Check container status
docker-compose -f docker-compose.prod.yml ps
```

### Database Setup

```bash
# Run database migrations
docker-compose -f docker-compose.prod.yml exec api python manage.py migrate

# Collect static files
docker-compose -f docker-compose.prod.yml exec api python manage.py collectstatic --noinput

# Create superuser account
docker-compose -f docker-compose.prod.yml exec api python manage.py createsuperuser
```

---

## ✅ STEP 7: Verify Deployment

### Check Services

```bash
# View running containers
docker-compose -f docker-compose.prod.yml ps

# Check API logs
docker-compose -f docker-compose.prod.yml logs api

# Check database logs
docker-compose -f docker-compose.prod.yml logs db

# Check nginx logs
docker-compose -f docker-compose.prod.yml logs nginx
```

### Test API Endpoints

```bash
# Test health endpoint
curl http://YOUR_VPS_IP/api/v1/health/

# Test API documentation
curl http://YOUR_VPS_IP/api/v1/docs/

# Test with domain (after DNS setup)
curl http://yourdomain.com/api/v1/health/
```

Expected health response:
```json
{
    "status": "healthy",
    "database": "connected",
    "cache": "connected",
    "timestamp": 1692700000.0,
    "response_time_ms": 25.4
}
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
docker-compose -f docker-compose.prod.yml stop nginx

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
docker-compose -f docker-compose.prod.yml restart

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
docker-compose -f docker-compose.prod.yml stop nginx
certbot renew --quiet
cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ssl/
cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ssl/
chown -R $USER:$USER ssl/
docker-compose -f docker-compose.prod.yml start nginx
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
docker-compose -f docker-compose.prod.yml exec -T db pg_dump -U hotel_booking_user hotel_booking_prod > $BACKUP_DIR/db_backup_$DATE.sql

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
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --build

# Wait for services
sleep 30

# Run migrations
docker-compose -f docker-compose.prod.yml exec api python manage.py migrate

# Collect static files
docker-compose -f docker-compose.prod.yml exec api python manage.py collectstatic --noinput

echo "✅ Update completed!"
EOF

chmod +x update.sh
```

---

## 🎯 Your API is Now Live!

### Access Points

- **🌐 API Base URL:** `https://yourdomain.com/api/v1/`
- **📚 Interactive Docs:** `https://yourdomain.com/api/v1/docs/`
- **📖 ReDoc Documentation:** `https://yourdomain.com/api/v1/redoc/`
- **⚕️ Health Check:** `https://yourdomain.com/api/v1/health/`
- **👑 Admin Panel:** `https://yourdomain.com/admin/`

### API Endpoints

```bash
# Authentication
POST /api/v1/auth/register/
POST /api/v1/auth/login/
POST /api/v1/auth/refresh/
POST /api/v1/auth/logout/

# Hotels
GET /api/v1/hotels/
GET /api/v1/hotels/{id}/

# Rooms
GET /api/v1/hotels/{hotel_id}/rooms/
GET /api/v1/rooms/{id}/

# Bookings
POST /api/v1/bookings/
GET /api/v1/bookings/
GET /api/v1/bookings/{id}/

# Search
GET /api/v1/search/
```

---

## 🛠️ Management Commands

### Daily Operations

```bash
# Check service status
docker-compose -f docker-compose.prod.yml ps

# View real-time logs
docker-compose -f docker-compose.prod.yml logs -f api

# Restart specific service
docker-compose -f docker-compose.prod.yml restart api

# View system resources
htop
df -h
free -h
```

### Backup & Restore

```bash
# Manual database backup
cd /opt/HotelBookingEngine
docker-compose -f docker-compose.prod.yml exec db pg_dump -U hotel_booking_user hotel_booking_prod > backup_$(date +%Y%m%d).sql

# Restore database from backup
docker-compose -f docker-compose.prod.yml exec -T db psql -U hotel_booking_user hotel_booking_prod < backup_file.sql
```

### Update Application

```bash
# Quick update
cd /opt/HotelBookingEngine
./update.sh

# Manual update
git pull origin main
docker-compose -f docker-compose.prod.yml up -d --build
```

---

## 🚨 Troubleshooting

### Common Issues

#### Container Won't Start
```bash
# Check logs for errors
docker-compose -f docker-compose.prod.yml logs

# Rebuild containers
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --build --force-recreate
```

#### Database Connection Error
```bash
# Check database logs
docker-compose -f docker-compose.prod.yml logs db

# Reset database (⚠️ This will delete all data)
docker-compose -f docker-compose.prod.yml down -v
docker-compose -f docker-compose.prod.yml up -d
```

#### Domain Not Working
```bash
# Check DNS
nslookup yourdomain.com
dig yourdomain.com

# Test with IP directly
curl http://YOUR_VPS_IP/api/v1/health/

# Check nginx configuration
docker-compose -f docker-compose.prod.yml logs nginx
```

#### SSL Certificate Issues
```bash
# Check certificate validity
openssl x509 -in ssl/fullchain.pem -text -noout

# Renew certificate manually
sudo certbot renew

# For AlmaLinux/RHEL, if using DNF-installed certbot
sudo systemctl reload nginx  # or restart your web server
```

#### SELinux Issues (AlmaLinux/RHEL)
```bash
# Check SELinux denials
sudo ausearch -m avc -ts recent

# Temporarily disable SELinux for testing (NOT recommended for production)
sudo setenforce 0

# Re-enable SELinux
sudo setenforce 1

# Generate SELinux policy for Docker (if needed)
sudo audit2allow -a -M mydocker
sudo semodule -i mydocker.pp

# Check SELinux context of Docker files
ls -laZ /var/lib/docker/
```

#### Firewall Issues (AlmaLinux/RHEL)
```bash
# Check if firewalld is blocking connections
sudo firewall-cmd --list-all

# Temporarily disable firewall for testing
sudo systemctl stop firewalld

# Re-enable firewall
sudo systemctl start firewalld

# Add custom port or service
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --reload
```

#### Out of Disk Space
```bash
# Check disk usage
df -h

# Clean Docker resources
docker system prune -a

# Clean old backups
find /opt/backups -name "db_backup_*.sql.gz" -type f -mtime +7 -delete
```

---

## 📊 Monitoring & Logs

### Log Locations

```bash
# Application logs
docker-compose -f docker-compose.prod.yml logs api

# Database logs
docker-compose -f docker-compose.prod.yml logs db

# Nginx logs
docker-compose -f docker-compose.prod.yml logs nginx

# System logs (AlmaLinux/RHEL)
sudo journalctl -u docker
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

# Docker stats
docker stats

# Database performance
docker-compose -f docker-compose.prod.yml exec db psql -U hotel_booking_user -d hotel_booking_prod -c "SELECT * FROM pg_stat_activity;"
```

---

## 🔐 Security Best Practices

### Applied Security Measures

- ✅ Firewall configured (UFW)
- ✅ Non-root user for application
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
