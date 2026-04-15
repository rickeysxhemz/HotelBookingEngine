# SERVER MIGRATION GUIDE - Hotel Booking Engine

## 🔄 Server Migration Process

### Current Situation
- **Current Server:** 209.74.88.53 (marhotels.com.sa) - Expires Tomorrow
- **Status:** Docker Compose deployment with PostgreSQL, Redis, Celery
- **Services:** Web API (port 8000), Database, Cache, Message Queue
- **Reverse Proxy:** Apache 2.4.62 on ports 80/443

---

## 📋 Pre-Migration Checklist (24 Hours Before)

### Data Backup
```bash
# SSH into current server
ssh root@209.74.88.53

# Navigate to project
cd /path/to/HotelBookingEngine

# Create comprehensive backup
./scripts/deploy.sh production backup

# Expected output: Backups in ./backups/ directory
# Files: db_backup_*.sql.gz, media_backup_*.tar.gz, logs_backup_*.tar.gz

# Download backups to your local machine
scp -r root@209.74.88.53:/path/to/HotelBookingEngine/backups ./local_backups/
```

### Verify Backups
```bash
# Check backup sizes and integrity
ls -lh ./local_backups/

# Test database backup integrity (optional but recommended)
gunzip -c db_backup_production_*.sql.gz | head -20
```

### Document Current Configuration
```bash
# Record current environment settings (passwords will be replaced)
cat /path/to/.env | grep -E 'DEBUG|ALLOWED_HOSTS|SECURE_SSL_REDIRECT' > migration_notes.txt

# Record current DNS records
nslookup marhotels.com.sa

# Document current SSL certificate expiry
openssl s_client -connect marhotels.com.sa:443 -brief | grep -i validity
```

---

## 🚀 Migration Execution Steps

### Step 1: Prepare New Server

#### Requirements Check
```bash
# SSH into new server
ssh root@[NEW_SERVER_IP]

# Install Docker & Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version
```

#### Initial Server Setup
```bash
# Update system packages
sudo yum update -y  # AlmaLinux/RHEL
# or
sudo apt update && apt upgrade -y  # Debian/Ubuntu

# Install required utilities
sudo yum install -y git curl wget postgresql-client  # AlmaLinux/RHEL
# or
sudo apt install -y git curl wget postgresql-client  # Debian/Ubuntu

# Create project directory
mkdir -p /home/apps
cd /home/apps
```

### Step 2: Transfer Project to New Server

#### Option A: Using Git (Recommended)
```bash
# Clone the repository
git clone https://github.com/your-org/HotelBookingEngine.git
cd HotelBookingEngine

# Checkout to your working branch (if using branch other than main)
git checkout production
```

#### Option B: Using SCP
```bash
# From current server, create a clean archive
cd /path/to
tar --exclude='.env' --exclude='.git' --exclude='__pycache__' \
    --exclude='*.pyc' --exclude='.DS_Store' \
    -czf /tmp/HotelBookingEngine.tar.gz HotelBookingEngine/

# Transfer to new server
scp /tmp/HotelBookingEngine.tar.gz root@[NEW_SERVER_IP]:/home/apps/

# On new server, extract
cd /home/apps
tar -xzf HotelBookingEngine.tar.gz
cd HotelBookingEngine
```

#### Option C: Using Rsync
```bash
# Faster for large directories
rsync -avz --exclude='.env' --exclude='.git' --exclude='__pycache__' \
    --exclude='*.pyc' --exclude='node_modules' \
    /path/to/HotelBookingEngine/ root@[NEW_SERVER_IP]:/home/apps/HotelBookingEngine/
```

### Step 3: Restore Database Backup

```bash
# On new server, start database service only
cd /home/apps/HotelBookingEngine

# First, create .env file
cp .env.example .env

# Edit .env with production values (same as current server)
nano .env

# Start only PostgreSQL and Redis (to prepare data)
docker-compose up -d db redis

# Wait for database to be ready
sleep 10

# Check database is running
docker-compose logs db | tail -20

# Get the database backup from local backups
scp ./local_backups/db_backup_production_*.sql.gz root@[NEW_SERVER_IP]:/home/apps/HotelBookingEngine/

# On new server, restore from backup
gunzip db_backup_production_*.sql.gz
docker-compose exec -T db psql -U hotelapi_user hotelMaarDB < db_backup_production_*.sql

# Verify data was restored
docker-compose exec -T db psql -U hotelapi_user -d hotelMaarDB \
    -c "SELECT COUNT(*) as table_count FROM information_schema.tables WHERE table_schema='public';"
```

### Step 4: Restore Media Files

```bash
# On new server, restore media files
scp ./local_backups/media_backup_production_*.tar.gz root@[NEW_SERVER_IP]:/home/apps/HotelBookingEngine/

# Extract media
tar -xzf media_backup_production_*.tar.gz

# Verify media restored
ls -la media/ | head -10
```

### Step 5: Start Full Application Stack

```bash
# Stop any running services
docker-compose stop

# Build and start all services
docker-compose up -d

# Wait for services to initialize
sleep 15

# Verify all services are running
docker-compose ps

# Expected output: All services should show "Up"
```

### Step 6: Run Migrations & Initialization

```bash
# Apply any pending migrations (should be none if restore worked)
docker-compose exec web python manage.py migrate

# Collect static files
docker-compose exec web python manage.py collectstatic --noinput

# Run health check
./scripts/health-check.sh

# Expected: All checks should pass
```

### Step 7: Configure Web Server (Apache)

```bash
# On new server, install Apache if not present
sudo yum install -y httpd mod_ssl  # AlmaLinux/RHEL
# or
sudo apt install -y apache2 ssl-cert  # Debian/Ubuntu

# Enable required modules
sudo a2enmod proxy
sudo a2enmod proxy_http
sudo a2enmod rewrite
sudo a2enmod headers
sudo a2enmod ssl

# Copy configuration
sudo cp config/apache-hotel-booking.conf /etc/httpd/conf.d/
# or
sudo cp config/apache-hotel-booking.conf /etc/apache2/sites-available/hotel-booking.conf
sudo a2ensite hotel-booking

# Test configuration
sudo apachectl configtest
# Expected: "Syntax OK"

# Restart Apache
sudo systemctl restart httpd
# or
sudo systemctl restart apache2
```

### Step 8: SSL Certificate Migration

#### Option A: Copy Existing Certificate
```bash
# On current server
sudo ls -la /etc/letsencrypt/live/marhotels.com.sa/

# Copy certificate files to new server
scp -r /etc/letsencrypt/live/marhotels.com.sa/ \
    root@[NEW_SERVER_IP]:/etc/letsencrypt/live/

scp -r /etc/letsencrypt/archive/marhotels.com.sa/ \
    root@[NEW_SERVER_IP]:/etc/letsencrypt/archive/

# Set proper permissions on new server
sudo chown -R root:root /etc/letsencrypt/live/
sudo chmod -R 755 /etc/letsencrypt/live/
```

#### Option B: Generate New Certificate (If transferred cert fails)
```bash
# On new server, generate new Let's Encrypt certificate
sudo certbot certonly --apache -d marhotels.com.sa -d www.marhotels.com.sa

# Verify certificate
sudo openssl x509 -in /etc/letsencrypt/live/marhotels.com.sa/fullchain.pem -text -noout | grep -i validity
```

### Step 9: Pre-DNS-Switch Testing

```bash
# Edit local hosts file to test new server before DNS switch
# On your local machine:

# Linux/Mac: Edit /etc/hosts
# Windows: Edit C:\Windows\System32\drivers\etc\hosts

# Add: [NEW_SERVER_IP] marhotels.com.sa

# Test the new server
curl -I https://marhotels.com.sa/api/v1/health/
# Expected: HTTP 200 OK

curl -I https://marhotels.com.sa/admin/
# Expected: HTTP 302 or 200

# Test API endpoint
curl https://marhotels.com.sa/api/v1/docs/ | head -20

# Remove from hosts file after testing
# Delete the added line
```

---

## 🔀 DNS Switchover

### Update DNS Records

Contact your DNS provider (GoDaddy, Namecheap, etc.) or use your DNS panel:

```
Update these DNS A records:
- marhotels.com.sa        -> [NEW_SERVER_IP]
- www.marhotels.com.sa    -> [NEW_SERVER_IP]

(Optional) Update mail records if hosting email:
- MX records
- SPF records
- DKIM records
```

### Wait for DNS Propagation

```bash
# Monitor DNS propagation (can take 5 minutes to 48 hours)
# Use online tools or command:

# Every 30 seconds, check DNS resolution
watch -n 30 'nslookup marhotels.com.sa'

# Or use dig
dig marhotels.com.sa

# Expected: Should resolve to [NEW_SERVER_IP]

# Once propagated, verify the site is fully functional:
curl -I https://marhotels.com.sa/api/v1/health/
curl https://marhotels.com.sa/api/v1/docs/ | grep -i "swagger"
```

---

## ✅ Post-Migration Verification

### Immediate Checks (First Hour)

```bash
# On new server, check all services
docker-compose ps

# Monitor logs for errors
docker-compose logs -f web

# Run comprehensive health check
./scripts/health-check.sh

# Test API endpoints
curl -I https://marhotels.com.sa/api/v1/health/
curl -I https://marhotels.com.sa/api/v1/docs/
curl -I https://marhotels.com.sa/admin/
```

### Functional Tests (First 24 Hours)

```bash
# Test user login
curl -X POST https://marhotels.com.sa/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"your_password"}'

# Test booking creation (requires valid token)
# Test payment processing
# Test email notifications
```

### Performance Baseline

```bash
# Check response times
time curl https://marhotels.com.sa/api/v1/health/

# Check server resource usage
docker-compose stats

# Check database performance
docker-compose exec db psql -U hotelapi_user -d hotelMaarDB \
  -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 5;"
```

### Monitor for 7 Days Post-Migration

```bash
# Set up continuous monitoring
watch -n 300 'docker-compose ps; echo "---"; free -h; df -h /; docker-compose stats --no-stream'

# Monitor error logs daily
docker-compose logs web | grep ERROR > daily_errors.log

# Backup new server immediately after successful migration
./scripts/deploy.sh production backup
```

---

## 🚨 Rollback Plan (If Issues Occur)

### Immediate Rollback (Within 1 Hour)

```bash
# Change DNS back to old server
# Update DNS A records to point back to 209.74.88.53

# Verify traffic is returning to old server
nslookup marhotels.com.sa

# On old server, ensure services still running
docker-compose ps
docker-compose logs web | tail -50
```

### Full Rollback (If Database Corruption)

```bash
# On old server, restore from backup (if needed)
./scripts/deploy.sh production backup

# Restore from previous backup
gunzip db_backup_production_[timestamp].sql.gz
docker-compose exec -T db psql -U hotelapi_user -d hotelMaarDB < db_backup_production_[timestamp].sql

# Restart services
docker-compose restart

# Run health checks
./scripts/health-check.sh
```

---

## 📊 Migration Monitoring Script

Create `scripts/migration-monitor.sh`:

```bash
#!/bin/bash

# Monitor migration progress
while true; do
    clear
    echo "=== Migration Monitoring Dashboard ==="
    echo "Timestamp: $(date)"
    echo ""
    
    echo "=== Current Server (209.74.88.53) ==="
    curl -s --connect-timeout 2 -I https://209.74.88.53/api/v1/health/ | head -1
    
    echo ""
    echo "=== New Server ([NEW_SERVER_IP]) ==="
    curl -s --connect-timeout 2 -I https://[NEW_SERVER_IP]/api/v1/health/ | head -1
    
    echo ""
    echo "=== DNS Resolution ==="
    nslookup marhotels.com.sa | grep "Address:" | tail -1
    
    echo ""
    echo "Press Ctrl+C to exit. Auto-refreshing every 30 seconds..."
    sleep 30
done
```

---

## 📞 Troubleshooting During Migration

### Issue: Old Server Not Working After DNS Update
```bash
# Solution: Temporarily change host file to test both servers
echo "[OLD_IP] old-server.test" >> /etc/hosts
echo "[NEW_IP] marhotels.com.sa" >> /etc/hosts

# Test explicitly
curl -I https://old-server.test/api/v1/health/
curl -I https://marhotels.com.sa/api/v1/health/
```

### Issue: Database Restore Failed
```bash
# Check database logs
docker-compose logs db

# Verify database is running
docker-compose exec -T db psql -U hotelapi_user -d hotelMaarDB -c "\l"

# Try restoring again with verbose output
docker-compose exec -T db psql -U hotelapi_user -d hotelMaarDB < backup.sql -v

# If corrupted, drop and recreate
docker-compose exec -T db dropdb -U hotelapi_user hotelMaarDB
docker-compose exec -T db createdb -U hotelapi_user hotelMaarDB
# Then restore again
```

### Issue: SSL Certificate Not Working
```bash
# Check certificate paths in Apache config
grep SSLCertificate /etc/httpd/conf.d/hotel-booking.conf

# Verify cert files exist
ls -la /etc/letsencrypt/live/marhotels.com.sa/

# Check certificate validity
openssl x509 -in /etc/letsencrypt/live/marhotels.com.sa/fullchain.pem -noout -dates

# Test SSL connection
openssl s_client -connect marhotels.com.sa:443 -brief
```

### Issue: Static Files Not Loading
```bash
# Collect static files again
docker-compose exec web python manage.py collectstatic --noinput

# Check volume mount in docker-compose
docker inspect hotel_booking_engine_web | grep Mounts

# Check if Apache is configured to proxy static files
grep -A5 "static" /etc/httpd/conf.d/hotel-booking.conf
```

---

## 🔒 Post-Migration Security Checklist

- [ ] Update SSH keys on new server
- [ ] Change database password if needed
- [ ] Review and update firewall rules
- [ ] Enable automated backups
- [ ] Set up SSL auto-renewal certificate
- [ ] Review log files for anomalies
- [ ] Update monitoring and alerting systems
- [ ] Document new server IP and access procedures
- [ ] Decommission old server (after 1-week monitoring period)

---

## 📝 Decommission Old Server (After 7 Days)

```bash
# SSH into old server
ssh root@209.74.88.53

# Final backup (just in case)
./scripts/deploy.sh production backup
scp -r backups/ root@[your-backup-server]:/backups/old-server/

# Stop services
docker-compose stop
docker-compose down

# Clean up (optional)
docker system prune -a

# Verify no data remains
ls -la /app/

# Notify hosting provider to deallocate server
# Update records to reflect decommission date
```

---

**Total Migration Time Estimate:**
- Preparation: 1-2 hours
- Execution: 30-60 minutes
- Verification: 30-60 minutes
- DNS Propagation: 5 minutes to 48 hours
- **Total: 2-4 hours (plus DNS propagation)**

**Recommended:** Schedule migration during off-peak hours.
