# How To Run - Hotel Booking Engine API

## 🚀 Quick Start Guide

This document provides step-by-step instructions to run the Hotel Booking Engine API locally and deploy it to production.

---

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Local Development Setup](#local-development-setup)
- [Running the API](#running-the-api)
- [Testing the API](#testing-the-api)
- [Admin Access](#admin-access)
- [Production Deployment](#production-deployment)
- [Troubleshooting](#troubleshooting)
- [Additional Resources](#additional-resources)

---

## Prerequisites

### System Requirements
- **Python**: 3.8 or higher (recommended: 3.12+)
- **Operating System**: Windows, macOS, or Linux
- **Memory**: Minimum 2GB RAM
- **Storage**: At least 500MB free space

### Required Software
- Python 3.8+ installed and accessible via command line
- Git (optional, for version control)
- Code editor (VS Code, PyCharm, etc.)

### Check Your Python Installation
```bash
python --version
# or
python3 --version
```

---

## Local Development Setup

### Step 1: Navigate to Project Directory
```bash
cd "c:\Users\PMLS\Downloads\My Learning\Hotel booking Engine\HotelBookingEngine"
```

### Step 2: Create Virtual Environment (Recommended)
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
cd hotel_booking
pip install -r requirements.txt
```

### Step 4: Database Setup
```bash
# Apply database migrations
python manage.py migrate

# Set up initial hotel data (Hotel Maar with rooms and services)
python manage.py setup_initial_data

# Create admin superuser (optional)
python manage.py createsuperuser
```

---

## Running the API

### Start the Development Server
```bash
# Navigate to project directory
cd hotel_booking

# Start the Django development server
python manage.py runserver
```

### Server Information
- **API Base URL**: `http://127.0.0.1:8000/api/`
- **Admin Panel**: `http://127.0.0.1:8000/admin/`
- **API Documentation**: `http://127.0.0.1:8000/api/schema/swagger-ui/`
- **API Browser**: `http://127.0.0.1:8000/api/`

### Verify Server is Running
Open your browser and visit: `http://127.0.0.1:8000/api/core/hotels/`

You should see a JSON response with Hotel Maar information.

---

## Testing the API

### Option 1: Automated Test Suite (Recommended)
```bash
# Run comprehensive API test suite
python complete_api_test.py --check-server
```

**Expected Output:**
```
🏨 HOTEL BOOKING ENGINE - COMPLETE API TEST SUITE
================================================================================
Total Tests: 15
Passed: 15
Failed: 0
Errors: 0
Success Rate: 100.0%
🎉 EXCELLENT! Hotel Booking Engine API is working great!
```

### Option 2: Manual Testing with curl
```bash
# Test hotels endpoint
curl -X GET "http://127.0.0.1:8000/api/core/hotels/" -H "Content-Type: application/json"

# Test user registration
curl -X POST "http://127.0.0.1:8000/api/accounts/register/" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "first_name": "Test",
    "last_name": "User",
    "phone_number": "+1234567890",
    "password": "TestPass123!",
    "password_confirm": "TestPass123!"
  }'
```

### Option 3: Browser-based Testing
1. Visit `http://127.0.0.1:8000/api/` for interactive API browser
2. Visit `http://127.0.0.1:8000/api/schema/swagger-ui/` for Swagger UI

---

## Admin Access

### Pre-configured Admin User
- **URL**: `http://127.0.0.1:8000/admin/`
- **Email**: `admin@hotelmaar.com`
- **Password**: `AdminPass123!`

### Admin Panel Features
- **User Management**: View and manage user accounts
- **Hotel Management**: Configure rooms, pricing, and services
- **Booking Management**: View and manage all bookings
- **System Monitoring**: Database records and statistics

---

## Production Deployment

### Option 1: Basic VPS Deployment

#### Step 1: Server Setup
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install Python and required packages
sudo apt install python3 python3-pip python3-venv nginx postgresql postgresql-contrib -y

# Install Gunicorn for production server
pip3 install gunicorn
```

#### Step 2: Database Configuration
```bash
# Create PostgreSQL database
sudo -u postgres psql
CREATE DATABASE hotel_booking_db;
CREATE USER hotel_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE hotel_booking_db TO hotel_user;
\q
```

#### Step 3: Environment Configuration
Create `.env` file:
```bash
DEBUG=False
SECRET_KEY=your-super-secret-key-here
DATABASE_URL=postgresql://hotel_user:your_secure_password@localhost:5432/hotel_booking_db
ALLOWED_HOSTS=your-domain.com,www.your-domain.com,your-server-ip
CORS_ALLOWED_ORIGINS=https://your-frontend-domain.com
```

#### Step 4: Application Setup
```bash
# Clone/upload your code
git clone your-repository-url
cd hotel-booking-engine

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install gunicorn psycopg2-binary

# Run migrations
python manage.py migrate
python manage.py setup_initial_data
python manage.py collectstatic

# Create superuser
python manage.py createsuperuser
```

#### Step 5: Gunicorn Configuration
Create `gunicorn.conf.py`:
```python
bind = "127.0.0.1:8000"
workers = 3
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 30
keepalive = 2
```

#### Step 6: Systemd Service
Create `/etc/systemd/system/hotel-booking.service`:
```ini
[Unit]
Description=Hotel Booking Engine
After=network.target

[Service]
User=your-user
Group=your-group
WorkingDirectory=/path/to/your/project
Environment="PATH=/path/to/your/project/venv/bin"
ExecStart=/path/to/your/project/venv/bin/gunicorn --config gunicorn.conf.py hotel_booking.wsgi:application
Restart=always

[Install]
WantedBy=multi-user.target
```

#### Step 7: Nginx Configuration
Create `/etc/nginx/sites-available/hotel-booking`:
```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    location /static/ {
        alias /path/to/your/project/staticfiles/;
    }

    location /media/ {
        alias /path/to/your/project/media/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### Step 8: SSL Certificate (Let's Encrypt)
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Get SSL certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

#### Step 9: Start Services
```bash
# Enable and start services
sudo systemctl enable hotel-booking
sudo systemctl start hotel-booking
sudo systemctl enable nginx
sudo systemctl restart nginx

# Check status
sudo systemctl status hotel-booking
sudo systemctl status nginx
```

### Option 2: Docker Deployment

#### Create Dockerfile
```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "hotel_booking.wsgi:application"]
```

#### Create docker-compose.yml
```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DEBUG=False
      - SECRET_KEY=your-secret-key
      - DATABASE_URL=postgresql://hotel_user:password@db:5432/hotel_booking_db
    depends_on:
      - db
    volumes:
      - static_volume:/app/staticfiles
      - media_volume:/app/media

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=hotel_booking_db
      - POSTGRES_USER=hotel_user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    depends_on:
      - web

volumes:
  postgres_data:
  static_volume:
  media_volume:
```

#### Deploy with Docker
```bash
# Build and start containers
docker-compose up -d

# Run migrations
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py setup_initial_data
docker-compose exec web python manage.py collectstatic --noinput
```

### Option 3: Cloud Platform Deployment

#### Heroku Deployment
1. Install Heroku CLI
2. Create `Procfile`:
   ```
   web: gunicorn hotel_booking.wsgi:application --log-file -
   release: python manage.py migrate && python manage.py setup_initial_data
   ```
3. Configure environment variables in Heroku dashboard
4. Deploy:
   ```bash
   heroku create your-app-name
   git push heroku main
   ```

#### AWS/Google Cloud/Azure
- Use platform-specific guides for Django deployment
- Configure load balancers, auto-scaling, and managed databases
- Set up CDN for static files
- Configure monitoring and logging

---

## Troubleshooting

### Common Issues and Solutions

#### 1. Server Won't Start
**Problem**: `ModuleNotFoundError` or import errors
**Solution**:
```bash
# Ensure virtual environment is activated
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

#### 2. Database Errors
**Problem**: `django.db.utils.OperationalError`
**Solution**:
```bash
# Reset database
python manage.py migrate
python manage.py setup_initial_data
```

#### 3. Permission Denied
**Problem**: `PermissionError` on Windows
**Solution**:
- Run terminal as Administrator
- Check file permissions
- Ensure Python is in PATH

#### 4. Port Already in Use
**Problem**: `Error: That port is already in use`
**Solution**:
```bash
# Use different port
python manage.py runserver 8001

# Or kill process using port 8000
# Windows:
netstat -ano | findstr :8000
taskkill /PID <process_id> /F

# Linux/Mac:
lsof -ti:8000 | xargs kill -9
```

#### 5. API Tests Failing
**Problem**: Test suite shows failures
**Solution**:
```bash
# Ensure server is running first
python manage.py runserver

# In another terminal, run tests
python complete_api_test.py --check-server
```

### Getting Help

#### Check Logs
```bash
# Django development server logs
python manage.py runserver --verbosity=2

# Production logs
sudo journalctl -u hotel-booking -f
sudo tail -f /var/log/nginx/error.log
```

#### Validate Configuration
```bash
# Check Django configuration
python manage.py check

# Check database connection
python manage.py dbshell

# Check static files
python manage.py collectstatic --dry-run
```

---

## Additional Resources

### API Documentation
- **Complete API Docs**: `API_DOCUMENTATION.md`
- **Project Summary**: `COMPLETION_SUMMARY.md`
- **Interactive API Browser**: `http://127.0.0.1:8000/api/`
- **Swagger UI**: `http://127.0.0.1:8000/api/schema/swagger-ui/`

### Useful Commands
```bash
# Create superuser
python manage.py createsuperuser

# Clear database and start fresh
python manage.py flush
python manage.py migrate
python manage.py setup_initial_data

# Generate new secret key
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Check installed packages
pip list

# Export current environment
pip freeze > requirements.txt
```

### Project Structure
```
HotelBookingEngine/
├── hotel_booking/              # Main Django project
│   ├── accounts/              # User authentication
│   ├── core/                  # Hotel management
│   ├── bookings/              # Booking system
│   ├── manage.py              # Django management
│   ├── requirements.txt       # Dependencies
│   ├── complete_api_test.py   # Test suite
│   └── db.sqlite3            # Database file
├── API_DOCUMENTATION.md       # Complete API docs
├── HowTo_RUN.md              # This file
└── COMPLETION_SUMMARY.md     # Project summary
```

### Environment Variables Reference
```bash
# Development
DEBUG=True
SECRET_KEY=your-dev-secret-key
DATABASE_URL=sqlite:///db.sqlite3

# Production
DEBUG=False
SECRET_KEY=your-production-secret-key
DATABASE_URL=postgresql://user:pass@host:5432/dbname
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
CORS_ALLOWED_ORIGINS=https://your-frontend.com
EMAIL_HOST=smtp.your-provider.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@domain.com
EMAIL_HOST_PASSWORD=your-email-password
```

---

## 🎉 Success!

If you've followed this guide successfully, you should now have:

✅ **Hotel Booking Engine API** running locally  
✅ **Admin panel** accessible for management  
✅ **Complete test suite** passing with 100% success  
✅ **Production deployment** (if deployed)  
✅ **API documentation** available for reference  

### Quick Verification Checklist
- [ ] Server starts without errors: `python manage.py runserver`
- [ ] API responds: Visit `http://127.0.0.1:8000/api/core/hotels/`
- [ ] Tests pass: `python complete_api_test.py --check-server`
- [ ] Admin accessible: `http://127.0.0.1:8000/admin/`
- [ ] Documentation loads: `http://127.0.0.1:8000/api/schema/swagger-ui/`

### Need Help?
- 📖 Read the complete `API_DOCUMENTATION.md`
- 🧪 Run the test suite to verify functionality
- 🔍 Check the troubleshooting section above
- 📧 Contact support (if available)

**Happy Coding! 🚀**

---

**Last Updated**: July 26, 2025  
**Version**: 1.0  
**Compatibility**: Python 3.8+, Django 5.2+
