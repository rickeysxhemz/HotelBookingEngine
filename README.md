# Hotel Booking Engine - API Documentation

Production-ready REST API for hotel booking management with HTTPS support, JWT authentication, and complete booking workflow.

---

## 🚀 Quick Start (Development)

### Prerequisites
- Docker & Docker Compose
- No other dependencies needed

### Run Locally (5 minutes)

```bash
# Navigate to project directory
cd HotelBookingEngine

# Start all services (Nginx, Django, PostgreSQL, Redis, Celery)
docker-compose up -d

# Wait for services to initialize (30 seconds)
sleep 30

# Check health
curl http://localhost/api/v1/health/

# View logs
docker-compose logs -f web
```

**Services Running:**
- API: `http://localhost/api/v1/`
- HTTPS: `https://localhost/api/v1/` (self-signed cert for dev)
- Swagger Docs: `http://localhost/api/v1/docs/`
- Admin: `http://localhost/admin/`

**Default Credentials:**
- Username: `admin`
- Password: `Admin@123456`

---

## 📡 API Endpoints Reference

### Base URL
```
Development: http://localhost/api/v1/
Production: https://your-domain.com/api/v1/
```

### Authentication Header
```http
Authorization: Bearer <access_token>
```

---

## 🔐 Authentication Endpoints

### 1. Register User
```http
POST /api/v1/auth/register/
```

**Request:**
```json
{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "SecurePassword123!",
  "first_name": "John",
  "last_name": "Doe",
  "phone_number": "+1234567890"
}
```

**Response (201):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "johndoe",
  "email": "john@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "phone_number": "+1234567890"
}
```

---

### 2. Login
```http
POST /api/v1/auth/login/
```

**Request:**
```json
{
  "username": "johndoe",
  "password": "SecurePassword123!"
}
```

**Response (200):**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNjE2MjM5MDIyfQ...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTYxNjI0MjYyMn0...",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "johndoe",
    "email": "john@example.com"
  }
}
```

**How to use tokens:**
- Store `access` token in localStorage/sessionStorage
- Use `access` token in all requests: `Authorization: Bearer <access>`
- When `access` expires, use `refresh` token to get new one

---

### 3. Logout
```http
POST /api/v1/auth/logout/
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "message": "Successfully logged out"
}
```

---

### 4. Profile
```http
GET /api/v1/auth/profile/
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "johndoe",
  "email": "john@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "phone_number": "+1234567890"
}
```

---

### 5. Update Profile
```http
PUT /api/v1/auth/profile/update/
Authorization: Bearer <access_token>
```

**Request:**
```json
{
  "first_name": "Jonathan",
  "last_name": "Smith",
  "phone_number": "+9876543210"
}
```

**Response (200):** Updated profile object

---

### 6. Change Password
```http
POST /api/v1/auth/password/change/
Authorization: Bearer <access_token>
```

**Request:**
```json
{
  "old_password": "OldPassword123!",
  "new_password": "NewPassword456!"
}
```

**Response (200):**
```json
{
  "message": "Password changed successfully"
}
```

---

## 🏨 Hotel Endpoints

### 1. List All Hotels (Paginated)
```http
GET /api/v1/hotels/?page=1&page_size=10
```

**Query Parameters:**
- `page` - Page number (default: 1)
- `page_size` - Items per page (default: 10)
- `ordering` - Sort by field (e.g., `?ordering=-created_at`)

**Response (200):**
```json
{
  "count": 150,
  "next": "http://localhost/api/v1/hotels/?page=2",
  "previous": null,
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Grand Plaza Hotel",
      "city": "Karachi",
      "country": "Pakistan",
      "rating": 4.5,
      "price_per_night": "15000.00",
      "image": "https://...",
      "description": "Luxury 5-star hotel...",
      "amenities": ["WiFi", "Pool", "Gym"]
    }
  ]
}
```

---

### 2. Search Hotels
```http
GET /api/v1/hotels/search/?city=Karachi&check_in=2024-05-01&check_out=2024-05-05&guests=2
```

**Query Parameters:**
- `city` - Hotel city
- `check_in` - Check-in date (YYYY-MM-DD)
- `check_out` - Check-out date (YYYY-MM-DD)
- `guests` - Number of guests
- `min_price` - Minimum price
- `max_price` - Maximum price

**Response (200):** Hotel list with availability

---

### 3. Get Hotel Details
```http
GET /api/v1/hotels/{hotel_id}/
```

**Response (200):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Grand Plaza Hotel",
  "city": "Karachi",
  "country": "Pakistan",
  "rating": 4.5,
  "description": "Luxury 5-star hotel...",
  "address": "123 Main Street, Karachi",
  "phone": "+92-21-123456",
  "email": "info@grandplaza.com",
  "amenities": ["WiFi", "Pool", "Gym", "Parking"],
  "services": ["Room Service", "Concierge", "Tours"],
  "policies": {
    "check_in_time": "14:00",
    "check_out_time": "12:00",
    "cancellation_policy": "Free cancellation until 48 hours before check-in"
  }
}
```

---

### 4. Get Hotel Rooms
```http
GET /api/v1/hotels/{hotel_id}/rooms/?page=1&page_size=10
```

**Response (200):**
```json
{
  "count": 45,
  "results": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "room_number": "101",
      "type": "Single",
      "capacity": 1,
      "price_per_night": "5000.00",
      "amenities": ["WiFi", "AC", "TV"],
      "available": true,
      "image": "https://..."
    }
  ]
}
```

---

### 5. Get Hotel Availability
```http
GET /api/v1/hotels/{hotel_id}/availability/?check_in=2024-05-01&check_out=2024-05-05
```

**Response (200):**
```json
{
  "hotel_id": "550e8400-e29b-41d4-a716-446655440000",
  "check_in": "2024-05-01",
  "check_out": "2024-05-05",
  "available_rooms": 12,
  "total_rooms": 45,
  "price_range": {
    "min": "5000.00",
    "max": "25000.00"
  }
}
```

---

### 6. Featured Hotels
```http
GET /api/v1/hotels/featured/
```

**Response (200):** List of featured hotels

---

### 7. Hotel Gallery
```http
GET /api/v1/hotels/{hotel_id}/gallery/
```

**Response (200):**
```json
{
  "hotel_id": "550e8400-e29b-41d4-a716-446655440000",
  "images": [
    {
      "id": 1,
      "url": "https://...",
      "caption": "Lobby"
    }
  ]
}
```

---

### 8. Hotel Reviews
```http
GET /api/v1/hotels/{hotel_id}/reviews/?page=1
```

**Response (200):**
```json
{
  "count": 156,
  "results": [
    {
      "id": 1,
      "user": "johndoe",
      "rating": 5,
      "comment": "Great hotel, excellent service!",
      "created_at": "2024-04-15T10:30:00Z"
    }
  ]
}
```

---

## 📅 Booking Endpoints

### 1. Create Booking
```http
POST /api/v1/bookings/create/
Authorization: Bearer <access_token>
```

**Request:**
```json
{
  "hotel_id": "550e8400-e29b-41d4-a716-446655440000",
  "room_id": "660e8400-e29b-41d4-a716-446655440001",
  "check_in": "2024-05-01",
  "check_out": "2024-05-05",
  "guests": 2,
  "guest_name": "John Doe",
  "guest_email": "john@example.com",
  "guest_phone": "+1234567890",
  "special_requests": "Late checkout if available",
  "payment_method": "card"
}
```

**Response (201):**
```json
{
  "id": 1001,
  "confirmation_number": "HBE-2024-001001",
  "status": "pending",
  "hotel": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Grand Plaza Hotel"
  },
  "check_in": "2024-05-01",
  "check_out": "2024-05-05",
  "nights": 4,
  "total_price": "60000.00",
  "currency": "PKR",
  "created_at": "2024-04-20T10:30:00Z"
}
```

---

### 2. Get Booking List
```http
GET /api/v1/bookings/?page=1&status=confirmed
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `status` - pending, confirmed, checked_in, checked_out, cancelled

**Response (200):**
```json
{
  "count": 8,
  "results": [
    {
      "id": 1001,
      "confirmation_number": "HBE-2024-001001",
      "status": "confirmed",
      "hotel": "Grand Plaza Hotel",
      "check_in": "2024-05-01",
      "check_out": "2024-05-05",
      "total_price": "60000.00"
    }
  ]
}
```

---

### 3. Get Booking Details
```http
GET /api/v1/bookings/{booking_id}/
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "id": 1001,
  "confirmation_number": "HBE-2024-001001",
  "status": "confirmed",
  "user": "johndoe",
  "hotel": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Grand Plaza Hotel",
    "city": "Karachi"
  },
  "room": {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "type": "Double",
    "capacity": 2
  },
  "check_in": "2024-05-01",
  "check_out": "2024-05-05",
  "nights": 4,
  "guest_name": "John Doe",
  "guest_email": "john@example.com",
  "total_price": "60000.00",
  "payment_status": "completed",
  "created_at": "2024-04-20T10:30:00Z"
}
```

---

### 4. Update Booking
```http
PUT /api/v1/bookings/{booking_id}/update/
Authorization: Bearer <access_token>
```

**Request:**
```json
{
  "check_out": "2024-05-06",
  "special_requests": "Updated request"
}
```

**Response (200):** Updated booking object

---

### 5. Confirm Booking
```http
POST /api/v1/bookings/{booking_id}/confirm/
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "id": 1001,
  "status": "confirmed",
  "message": "Booking confirmed successfully"
}
```

---

### 6. Cancel Booking
```http
POST /api/v1/bookings/{booking_id}/cancel/
Authorization: Bearer <access_token>
```

**Request:**
```json
{
  "reason": "Change of plans"
}
```

**Response (200):**
```json
{
  "id": 1001,
  "status": "cancelled",
  "refund_amount": "55000.00",
  "message": "Booking cancelled, refund processed"
}
```

---

### 7. Booking Audit History
```http
GET /api/v1/bookings/{booking_id}/audit-history/
Authorization: Bearer <access_token>
```

**Response (200):**
```json
[
  {
    "timestamp": "2024-04-20T10:30:00Z",
    "action": "created",
    "changed_by": "johndoe",
    "details": "Booking created"
  },
  {
    "timestamp": "2024-04-20T11:30:00Z",
    "action": "confirmed",
    "changed_by": "johndoe",
    "details": "Payment completed"
  }
]
```

---

## 🎁 Offers Endpoints

### 1. Get All Offers
```http
GET /api/v1/offers/?page=1
```

**Response (200):**
```json
{
  "count": 25,
  "results": [
    {
      "id": "770e8400-e29b-41d4-a716-446655440002",
      "title": "Summer Special 30% Off",
      "description": "Book now and get 30% discount...",
      "discount_percentage": 30,
      "valid_from": "2024-05-01",
      "valid_until": "2024-06-30",
      "category": "seasonal",
      "featured": true
    }
  ]
}
```

---

### 2. Featured Offers
```http
GET /api/v1/offers/featured/
```

**Response (200):** List of featured special offers

---

### 3. Search Offers
```http
GET /api/v1/offers/search/?category=seasonal&min_discount=20
```

**Response (200):** Filtered offers

---

### 4. Get Offer Details
```http
GET /api/v1/offers/{offer_slug}/
```

**Response (200):**
```json
{
  "id": "770e8400-e29b-41d4-a716-446655440002",
  "title": "Summer Special 30% Off",
  "description": "Book now and get 30% discount...",
  "discount_percentage": 30,
  "max_discount_amount": "50000.00",
  "valid_from": "2024-05-01",
  "valid_until": "2024-06-30",
  "terms_and_conditions": "...",
  "highlights": ["Free breakfast", "Late checkout"],
  "images": ["https://..."]
}
```

---

### 5. Get Offer Categories
```http
GET /api/v1/offers/categories/
```

**Response (200):**
```json
[
  {
    "id": 1,
    "name": "Seasonal",
    "slug": "seasonal"
  },
  {
    "id": 2,
    "name": "Corporate",
    "slug": "corporate"
  }
]
```

---

## 💚 Health Check Endpoint

```http
GET /api/v1/health/
```

**Response (200):**
```json
{
  "status": "healthy",
  "timestamp": 1713607800.123,
  "database": "connected",
  "cache": "connected",
  "response_time_ms": 45.23
}
```

---

## 📱 Frontend Integration Guide

### Setup

1. **Store Auth Token:**
```javascript
// After login
localStorage.setItem('access_token', response.access);
localStorage.setItem('refresh_token', response.refresh);
```

2. **Create API Client:**
```javascript
const apiClient = {
  baseURL: 'http://localhost/api/v1', // Change to production URL
  
  async request(endpoint, options = {}) {
    const token = localStorage.getItem('access_token');
    const headers = {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` })
    };
    
    const response = await fetch(`${this.baseURL}${endpoint}`, {
      ...options,
      headers
    });
    
    if (response.status === 401) {
      // Token expired, refresh or redirect to login
      window.location.href = '/login';
    }
    
    return response.json();
  },
  
  get(endpoint) {
    return this.request(endpoint);
  },
  
  post(endpoint, data) {
    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(data)
    });
  },
  
  put(endpoint, data) {
    return this.request(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data)
    });
  }
};
```

3. **Use in Components:**
```javascript
// Get hotels
const hotels = await apiClient.get('/hotels/?page=1');

// Search hotels
const results = await apiClient.get(
  '/hotels/search/?city=Karachi&check_in=2024-05-01&check_out=2024-05-05&guests=2'
);

// Create booking
const booking = await apiClient.post('/bookings/create/', {
  hotel_id: 'hotel-uuid',
  room_id: 'room-uuid',
  check_in: '2024-05-01',
  check_out: '2024-05-05',
  guests: 2,
  guest_name: 'John Doe',
  guest_email: 'john@example.com',
  guest_phone: '+1234567890'
});
```

---

## 🚀 Server Deployment (Production)

### Prerequisites
- Linux server (Ubuntu 20.04+ recommended)
- Docker & Docker Compose
- Domain name with SSL certificate (Let's Encrypt recommended)

### Step 1: Prepare Server

```bash
# SSH into server
ssh user@your-server-ip

# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### Step 2: Clone & Setup Project

```bash
# Clone repository
git clone <your-repo-url> /opt/hotel-booking-api
cd /opt/hotel-booking-api

# Create production .env
cp .env .env.production
nano .env.production  # Edit values below
```

### Step 3: Update .env.production

```env
# DEPLOYMENT MODE
ENVIRONMENT=production
DEBUG=False

# APPLICATION SECURITY (CHANGE THESE!)
SECRET_KEY=<generate-new-secure-key>
ALLOWED_HOSTS=your-domain.com,api.your-domain.com,www.your-domain.com

# DOMAIN & SSL
DOMAIN_NAME=api.your-domain.com
USE_HTTPS=True

# DATABASE (CHANGE PASSWORD!)
DB_PASSWORD=<strong-random-password>

# SSL/TLS SECURITY
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True

# EMAIL (Configure SMTP)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=<your-app-password>

# CORS (Allow your frontend domain)
CORS_ALLOWED_ORIGINS=https://your-domain.com,https://www.your-domain.com

# Django Superuser
DJANGO_SUPERUSER_PASSWORD=<strong-admin-password>
```

### Step 4: Generate SSL Certificate

```bash
# Using Let's Encrypt (Recommended for production)
sudo apt install certbot -y

# Generate certificate
sudo certbot certonly --standalone -d your-domain.com -d api.your-domain.com

# Copy to project
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ./certs/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem ./certs/privkey.pem
sudo chown $USER:$USER ./certs/*
```

### Step 5: Start Services

```bash
# Load production env
export $(cat .env.production | xargs)

# Build and start
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f web
```

### Step 6: Configure Firewall

```bash
# UFW (Ubuntu)
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable
```

### Step 7: Auto-Renew SSL Certificate

```bash
# Create renewal script
sudo crontab -e

# Add this line (renews daily at 2 AM)
0 2 * * * certbot renew --quiet && cp /etc/letsencrypt/live/your-domain.com/fullchain.pem /opt/hotel-booking-api/certs/cert.pem && cp /etc/letsencrypt/live/your-domain.com/privkey.pem /opt/hotel-booking-api/certs/privkey.pem && docker-compose -f /opt/hotel-booking-api/docker-compose.yml restart nginx
```

### Step 8: Monitor & Maintain

```bash
# Check logs in real-time
docker-compose logs -f

# Backup database
docker-compose exec db pg_dump -U hotelapi_user hotelMaarDB > backup.sql

# Restart services
docker-compose restart

# View resource usage
docker stats
```

---

## 🐛 Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| **Connection refused** | Wait 30 seconds for services to start, check logs: `docker-compose logs web` |
| **Port 80/443 already in use** | Change ports in docker-compose.yml or kill process: `lsof -i :80` |
| **Database connection error** | Check DB credentials in .env, ensure DB service is healthy: `docker-compose ps` |
| **CORS error on frontend** | Update `CORS_ALLOWED_ORIGINS` in .env to include your frontend URL |
| **SSL certificate error** | Use self-signed cert for dev (working by default), use Let's Encrypt for production |

---

## 📞 Support

For issues and questions:
1. Check logs: `docker-compose logs -f`
2. Visit API Swagger docs: `http://localhost/api/v1/docs/`
3. Check .env configuration
4. Ensure all services are running: `docker-compose ps`

---

Client Request Flow:
┌──────────────┐
│   Client     │
│  HTTP/HTTPS  │
└──────┬───────┘
       │
       ↓
┌──────────────────────────────────────┐
│      NGINX (Port 80/443)             │
│  - SSL/TLS Termination               │
│  - Reverse Proxy                     │
│  - Serve Static Files                │
└──────┬───────────────────────────────┘
       │ (internal docker network)
       │ proxy_pass http://web:8000
       ↓
┌──────────────────────────────────────┐
│  Django/Gunicorn (Port 8000)         │
│  - Run application                   │
│  - Handle requests                   │
│  - Queue Celery tasks                │
└──────┬────────────┬──────────┬───────┘
       │            │          │
  ┌────↓──┐   ┌─────↓─┐   ┌──↓──────┐
  │  DB   │   │ Redis │   │ Celery  │
  └───────┘   └───────┘   └─────────┘