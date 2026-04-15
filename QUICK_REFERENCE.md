# QUICK REFERENCE - DEPLOYMENT CHECKLIST

## ⚡ 5-Minute Deployment Checklist

### Pre-Deployment (Before touching server)
- [ ] Backup current system: `./scripts/deploy.sh production backup`
- [ ] Download backups locally: `scp -r backups/ local_backups/`
- [ ] Review .env changes
- [ ] Test new code locally if possible
- [ ] Notify stakeholders of maintenance window

### Deployment
```bash
# 1. SSH to server
ssh root@[SERVER_IP]

# 2. Navigate to project
cd /path/to/HotelBookingEngine

# 3. Copy and update .env
cp .env.example .env
nano .env  # Update production values

# 4. Deploy
./scripts/deploy.sh production deploy

# 5. Verify
./scripts/health-check.sh
```

### Post-Deployment
- [ ] Check logs: `docker-compose logs -f web`
- [ ] Test endpoints: `curl -I https://marhotels.com.sa/api/v1/health/`
- [ ] Verify SSL certificate: Works
- [ ] Test admin login: `https://marhotels.com.sa/admin/`
- [ ] Monitor for 1 hour: `watch -n 30 'docker-compose stats'`

---

## 🔧 Environment Variables - Quick Reference

### Minimal Production Setup
```env
# Core
DEBUG=False
SECRET_KEY=[generate-new]
ALLOWED_HOSTS=marhotels.com.sa,www.marhotels.com.sa

# Database
DB_NAME=hotelMaarDB
DB_USER=hotelapi_user
DB_PASSWORD=[secure-password]
DB_HOST=db

# Security
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True

# Admin User (created on first run)
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_PASSWORD=[strong-password]
```

### Generate Required Values
```bash
# SECRET_KEY
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# DB_PASSWORD
openssl rand -base64 32
```

---

## 🚀 Deployment Scenarios

### Scenario 1: First Deployment on New Server
```bash
# 1. Ensure Docker + Compose installed
docker --version && docker-compose --version

# 2. Clone project
git clone [repo-url] && cd HotelBookingEngine

# 3. Create configuration
cp .env.example .env
# Edit .env with production values

# 4. Deploy
./scripts/deploy.sh production deploy

# 5. Configure Apache
sudo cp config/apache-hotel-booking.conf /etc/httpd/conf.d/
sudo systemctl restart httpd
```

### Scenario 2: Update Application (New Code Version)
```bash
# 1. Pull latest code
git fetch origin main
git checkout main
git pull

# 2. Deploy with automatic migration
./scripts/deploy.sh production deploy

# 3. If deployment fails, rollback
docker-compose restart
```

### Scenario 3: Database Migration Only
```bash
# 1. Backup first
./scripts/deploy.sh production backup

# 2. Run migration
./scripts/deploy.sh production migrate

# 3. Verify
docker-compose exec web python manage.py migrate --list
```

### Scenario 4: Server Hardware Change (IP/Domain Changes)
```bash
# On current server:
./scripts/deploy.sh production backup
scp -r backups/ root@[new-server]:/tmp/

# On new server:
# Follow SERVER_MIGRATION.md steps
```

---

## 🆘 Troubleshooting Quick Fixes

### Application won't start
```bash
docker-compose ps  # Check status
docker-compose logs web  # View errors
docker-compose up -d  # Try restart
```

### Port 8000 already in use
```bash
lsof -i :8000  # Find process
kill -9 [PID]  # Kill it
docker-compose restart web
```

### Database connection error
```bash
docker-compose ps db  # Check DB status
docker-compose logs db  # Check DB logs
docker-compose exec db psql -U hotelapi_user -c "SELECT 1;"
```

### Static files missing
```bash
docker-compose exec web python manage.py collectstatic --noinput
docker-compose restart web
```

### Celery worker not working
```bash
docker-compose logs celery_worker
docker-compose exec redis redis-cli ping  # Check Redis
docker-compose restart celery_worker
```

---

## 📊 Health Check Commands

```bash
# Quick health check
./scripts/health-check.sh

# Manual checks
curl -I http://127.0.0.1:8000/api/v1/health/
docker-compose ps
docker-compose stats

# Database check
docker-compose exec db psql -U hotelapi_user -d hotelMaarDB -c "SELECT COUNT(*) FROM auth_user;"

# Redis check
docker-compose exec redis redis-cli ping

# Celery check
docker-compose exec celery_worker celery -A hotel_booking inspect active
```

---

## 📈 Common Management Tasks

### View logs
```bash
docker-compose logs -f web  # Live web logs
docker-compose logs -f db   # Database logs
docker-compose logs -f redis # Cache logs
```

### Restart service
```bash
docker-compose restart web
docker-compose restart db
docker-compose restart [service-name]
```

### Execute manage.py command
```bash
docker-compose exec web python manage.py [command]

# Examples:
docker-compose exec web python manage.py createsuperuser
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py shell
```

### Backup database
```bash
docker-compose exec db pg_dump -U hotelapi_user hotelMaarDB > backup.sql
gzip backup.sql
```

### Restore database
```bash
gunzip backup.sql.gz
docker-compose exec -T db psql -U hotelapi_user hotelMaarDB < backup.sql
```

---

## ⏰ Monitoring & Alerts

### Setup continuous monitoring
```bash
# Watch all services
watch -n 30 'docker-compose ps; echo "---"; docker-compose stats --no-stream'

# Monitor specific service
watch -n 10 'docker-compose logs --tail=10 web'
```

### Monitor resources
```bash
# CPU/Memory usage
docker-compose stats

# Disk space
df -h /

# System memory
free -h

# Database size
docker-compose exec db psql -U hotelapi_user -d hotelMaarDB -c "SELECT pg_size_pretty(pg_database_size('hotelMaarDB'));"
```

---

## 🔐 Security Checklists

### Before going production
- [ ] SECRET_KEY is unique and strong
- [ ] DEBUG=False
- [ ] ALLOWED_HOSTS updated with correct domains
- [ ] SECURE_SSL_REDIRECT=True
- [ ] SESSION_COOKIE_SECURE=True
- [ ] SSL certificate installed and valid
- [ ] Database password is strong
- [ ] Superuser password changed from default
- [ ] Email credentials configured correctly
- [ ] Firewall rules configured
- [ ] Backups tested and verified
- [ ] Monitoring/alerts configured
- [ ] Log rotation configured

### Regular security tasks
```bash
# Monthly: Backup database
./scripts/deploy.sh production backup

# Weekly: Check logs for errors
docker-compose logs web | grep ERROR

# Monthly: Update dependencies
docker-compose build --no-cache

# Quarterly: Renew SSL certificate
sudo certbot renew --force-renewal
```

---

## 📞 Emergency Contacts

**Database Issue:** Check docker-compose logs db
**API Down:** Check docker-compose logs web
**Static Files Missing:** Run collectstatic
**Performance Slow:** Check docker-compose stats + database slow queries
**Out of Disk:** Clean old backups and logs

**Quick Emergency Fix:**
```bash
docker-compose stop
docker-compose up -d
./scripts/health-check.sh
```

---

## 📝 Documentation References

- Full Deployment Guide: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- Server Migration: [SERVER_MIGRATION.md](SERVER_MIGRATION.md)
- Environment Variables: [.env.example](.env.example)
- Docker Compose: [docker-compose.yml](docker-compose.yml)
- Health Check: [scripts/health-check.sh](scripts/health-check.sh)
- Deploy Script: [scripts/deploy.sh](scripts/deploy.sh)

---

**Last Updated:** April 15, 2026
**Version:** 1.0.0
