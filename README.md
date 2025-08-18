# Hotel Booking Engine

A comprehensive Django REST API for hotel booking management with search, booking flow, payment processing, and email notifications.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Django 5.2.5
- PostgreSQL (recommended) or SQLite (development)

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd hotel_booking_engine

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup database
cd hotel_booking
python manage.py migrate

# Create superuser (optional)
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

### Environment Settings
- **Development**: `settings.py` (default)
- **Production**: `deployment.py` (set `DJANGO_SETTINGS_MODULE=hotel_booking.deployment`)

## 📖 API Documentation

### Base URL
```
http://localhost:8000/api/v1/
```

### Interactive Documentation
- **Swagger UI**: `http://localhost:8000/api/v1/docs/`
- **ReDoc**: `http://localhost:8000/api/v1/redoc/`
- **OpenAPI Schema**: `http://localhost:8000/api/v1/schema/`

## 🔐 Authentication

The API uses JWT (JSON Web Token) authentication. Include the token in the Authorization header:

```http
Authorization: Bearer <your-jwt-token>
```

### Authentication Endpoints

#### Register
```http
POST /api/v1/auth/register/
```
**Request:**
```json
{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "securepassword123",
  "first_name": "John",
  "last_name": "Doe",
  "phone_number": "+1234567890"
}
```

#### Login
```http
POST /api/v1/auth/login/
```
**Request:**
```json
{
  "username": "johndoe",
  "password": "securepassword123"
}
```
**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": "uuid",
    "username": "johndoe",
    "email": "john@example.com"
  }
}
```

#### Token Refresh
```http
POST /api/v1/auth/token/refresh/
```
**Request:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### Logout
```http
POST /api/v1/auth/logout/
```
Headers: `Authorization: Bearer <token>`

## 🏨 Hotel Management API

### Hotel Discovery

#### List All Hotels
```http
GET /api/v1/hotels/
```
**Query Parameters:**
- `page` (optional): Page number for pagination
- `page_size` (optional): Number of items per page (default: 20)

**Response:**
```json
{
  "count": 45,
  "next": "http://localhost:8000/api/v1/hotels/?page=2",
  "previous": null,
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Grand Hotel",
      "description": "Luxury hotel in downtown",
      "full_address": "123 Main St, New York, NY 10001",
      "city": "New York",
      "state": "NY",
      "country": "United States",
      "star_rating": 5,
      "phone_number": "+1234567890",
      "email": "info@grandhotel.com",
      "website": "https://grandhotel.com",
      "room_types": ["Standard", "Deluxe", "Suite"],
      "amenities_count": 15,
      "room_stats": {
        "total_rooms": 150,
        "available_rooms": 45
      }
    }
  ]
}
```

#### Hotel Search
```http
GET /api/v1/hotels/search/
```
**Query Parameters:**
- `location` (optional): City name to search in
- `check_in` (optional): Check-in date (YYYY-MM-DD)
- `check_out` (optional): Check-out date (YYYY-MM-DD)
- `guests` (optional): Number of guests
- `min_price` (optional): Minimum price per night
- `max_price` (optional): Maximum price per night
- `star_rating` (optional): Hotel star rating (1-5)

**Example:**
```http
GET /api/v1/hotels/search/?location=New York&check_in=2024-03-15&check_out=2024-03-17&guests=2
```

#### Hotel Details
```http
GET /api/v1/hotels/{hotel_id}/
```
**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Grand Hotel",
  "description": "Luxury hotel with stunning city views...",
  "full_address": "123 Main St, New York, NY 10001",
  "phone_number": "+1234567890",
  "email": "info@grandhotel.com",
  "website": "https://grandhotel.com",
  "star_rating": 5,
  "check_in_time": "15:00:00",
  "check_out_time": "11:00:00",
  "cancellation_policy": "Free cancellation 24 hours before check-in",
  "pet_policy": "Pets allowed with additional fee",
  "smoking_policy": "Non-smoking property",
  "amenities": [
    {
      "id": "uuid",
      "name": "Free WiFi",
      "category": "Internet",
      "description": "High-speed internet throughout the property"
    }
  ],
  "room_types": [
    {
      "id": "uuid",
      "name": "Deluxe Room",
      "description": "Spacious room with city view",
      "capacity": 2,
      "size_sqm": 35,
      "base_price": "150.00"
    }
  ]
}
```

### Hotel Information Endpoints

#### Hotel Gallery
```http
GET /api/v1/hotels/{hotel_id}/gallery/
```

#### Hotel Reviews
```http
GET /api/v1/hotels/{hotel_id}/reviews/
```

#### Hotel Amenities
```http
GET /api/v1/hotels/{hotel_id}/amenities/
```

#### Hotel Room Types
```http
GET /api/v1/hotels/{hotel_id}/room-types/
```

#### Hotel Availability
```http
GET /api/v1/hotels/{hotel_id}/availability/
```
**Query Parameters:**
- `check_in`: Check-in date (YYYY-MM-DD)
- `check_out`: Check-out date (YYYY-MM-DD)
- `guests`: Number of guests

## 🛏️ Room Management

#### Hotel Rooms
```http
GET /api/v1/hotels/{hotel_id}/rooms/
```

#### Room Details
```http
GET /api/v1/hotels/{hotel_id}/rooms/{room_id}/
```

#### Room Availability
```http
GET /api/v1/hotels/{hotel_id}/rooms/{room_id}/availability/
```

## 📅 Booking Management API

### Booking Flow

#### Complete Booking Flow
```http
POST /api/v1/bookings/complete-booking/
```
**Description:** Handles the complete booking process from room search to confirmation email.

**Request:**
```json
{
  "search_criteria": {
    "hotel_id": "550e8400-e29b-41d4-a716-446655440000",
    "location": "New York",
    "check_in": "2024-03-15",
    "check_out": "2024-03-17",
    "guests": 2
  },
  "booking_details": {
    "room_id": "550e8400-e29b-41d4-a716-446655440001",
    "primary_guest_name": "John Doe",
    "primary_guest_email": "john@example.com",
    "primary_guest_phone": "+1234567890",
    "special_requests": "Early check-in if possible",
    "extras": [
      {
        "extra_id": "550e8400-e29b-41d4-a716-446655440002",
        "quantity": 1
      }
    ]
  },
  "payment_info": {
    "payment_method": "card",
    "save_payment_method": false
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Booking completed successfully",
  "booking": {
    "id": "550e8400-e29b-41d4-a716-446655440003",
    "booking_reference": "BK001234",
    "status": "confirmed",
    "payment_status": "paid",
    "check_in": "2024-03-15",
    "check_out": "2024-03-17",
    "guests": 2,
    "total_price": "450.00",
    "room": {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "room_number": "101",
      "room_type": {
        "name": "Deluxe Room",
        "description": "Spacious room with city view"
      }
    },
    "hotel": {
      "name": "Grand Hotel",
      "address": "123 Main St, New York"
    }
  },
  "payment": {
    "status": "success",
    "transaction_id": "txn_1234567890"
  },
  "email_notification": {
    "sent": true,
    "recipient": "john@example.com"
  }
}
```

#### Room Search Only
```http
GET /api/v1/bookings/search-rooms/
```
**Description:** Search for available rooms without creating a booking.

**Query Parameters:**
- `hotel_id` (optional): Specific hotel UUID
- `location` (optional): City name to search in
- `check_in`: Check-in date (YYYY-MM-DD)
- `check_out`: Check-out date (YYYY-MM-DD)
- `guests`: Number of guests (default: 1)

**Example:**
```http
GET /api/v1/bookings/search-rooms/?check_in=2024-03-15&check_out=2024-03-17&guests=2&location=New York
```

**Response:**
```json
{
  "search_criteria": {
    "check_in": "2024-03-15",
    "check_out": "2024-03-17",
    "guests": 2,
    "location": "New York"
  },
  "available_rooms": [
    {
      "room_id": "550e8400-e29b-41d4-a716-446655440001",
      "room_number": "101",
      "room_type": {
        "id": "550e8400-e29b-41d4-a716-446655440004",
        "name": "Deluxe Room",
        "description": "Spacious room with city view",
        "capacity": 3,
        "amenities": ["WiFi", "TV", "Air Conditioning"]
      },
      "hotel": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "Grand Hotel",
        "address": "123 Main St, New York",
        "city": "New York",
        "rating": 4.5
      },
      "pricing": {
        "room_price": "300.00",
        "extras_price": "0.00",
        "tax_amount": "30.00",
        "total_price": "330.00",
        "nights": 2,
        "price_per_night": "150.00"
      }
    }
  ],
  "total_found": 1
}
```

### Booking Management

#### List User Bookings
```http
GET /api/v1/bookings/
```
Headers: `Authorization: Bearer <token>`

#### Create Booking
```http
POST /api/v1/bookings/create/
```

#### Get Booking Quote
```http
POST /api/v1/bookings/quote/
```

#### Booking Details
```http
GET /api/v1/bookings/{booking_reference}/
```

#### Update Booking
```http
PUT /api/v1/bookings/{booking_reference}/update/
```

#### Cancel Booking
```http
POST /api/v1/bookings/{booking_reference}/cancel/
```

#### Confirm Booking
```http
POST /api/v1/bookings/{booking_reference}/confirm/
```

### Check-in/Check-out Operations

#### Check-in
```http
POST /api/v1/bookings/{booking_reference}/checkin/
```

#### Check-out
```http
POST /api/v1/bookings/{booking_reference}/checkout/
```

## 🔍 Advanced Search Features

### Hotel Search with Availability
```http
GET /api/v1/hotels/search-availability/
```

### Hotel Search by Capacity
```http
GET /api/v1/hotels/search-capacity/
```

### Flexible Hotel Search
```http
GET /api/v1/hotels/search-flexible/
```

## 👥 User Profile Management

### Get Profile
```http
GET /api/v1/auth/profile/
```

### Update Profile
```http
PUT /api/v1/auth/profile/update/
```

### Change Password
```http
POST /api/v1/auth/password/change/
```

### Password Reset Request
```http
POST /api/v1/auth/password/reset/request/
```

### Password Reset Confirm
```http
POST /api/v1/auth/password/reset/confirm/{token}/
```

### Email Verification
```http
GET /api/v1/auth/verify-email/{token}/
```

## ⚙️ Key Features

### 🔍 **Flexible Search**
- **Hotel ID Optional**: Search across all hotels or target specific ones
- **Location-based Search**: Find hotels by city/region
- **Date Range Availability**: Real-time room availability checking
- **Guest Capacity Filtering**: Filter by number of guests
- **Price Range Filtering**: Set minimum and maximum price limits

### 💰 **Dynamic Pricing**
- Real-time price calculation including taxes and extras
- Support for room extras and add-ons
- Transparent pricing breakdown
- Seasonal and demand-based pricing support

### 📧 **Email Notifications**
- Booking confirmation emails with complete details
- Booking modification notifications
- Cancellation confirmations
- HTML email templates with hotel branding

### 🔒 **Security & Validation**
- JWT token-based authentication
- Comprehensive input validation
- Transactional safety (rollback on failure)
- Rate limiting and security headers

### 📱 **API Design**
- RESTful API design principles
- Consistent response formats
- Comprehensive error handling
- OpenAPI/Swagger documentation

## 🗂️ Data Models

### Core Entities
- **Hotel**: Property information, location, amenities, policies
- **Room**: Individual rooms with types, pricing, availability
- **RoomType**: Room categories with features and capacity
- **Booking**: Reservation records with guest details and status
- **User**: Customer accounts with profiles and preferences
- **Amenity**: Hotel and room features/services

### Key Relationships
- Hotels have multiple Rooms and RoomTypes
- Bookings link Users to specific Rooms
- RoomTypes define pricing and capacity rules
- Amenities can be associated with Hotels or RoomTypes

## 🚨 Error Handling

### Standard Error Response Format
```json
{
  "error": "Error message description",
  "code": "ERROR_CODE",
  "details": {
    "field": "Specific field error details"
  }
}
```

### Common HTTP Status Codes
- `200 OK`: Successful request
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `409 Conflict`: Resource conflict (e.g., room already booked)
- `422 Unprocessable Entity`: Validation errors
- `500 Internal Server Error`: Server error

### Common Error Examples

#### Room Not Available
```json
{
  "error": "No available rooms found for the specified criteria",
  "code": "NO_ROOMS_AVAILABLE",
  "search_criteria": {
    "check_in": "2024-03-15",
    "check_out": "2024-03-17",
    "guests": 2
  }
}
```

#### Invalid Date Range
```json
{
  "error": "Check-out date must be after check-in date",
  "code": "INVALID_DATE_RANGE",
  "details": {
    "check_in": "2024-03-17",
    "check_out": "2024-03-15"
  }
}
```

#### Payment Failed
```json
{
  "error": "Payment processing failed",
  "code": "PAYMENT_FAILED",
  "details": {
    "payment_method": "card",
    "reason": "Insufficient funds"
  }
}
```

## 📋 Usage Examples

### Example 1: Search and Book Flow
```bash
# 1. Search for available rooms
curl -X GET "http://localhost:8000/api/v1/bookings/search-rooms/?check_in=2024-03-15&check_out=2024-03-17&guests=2&location=New York"

# 2. Complete booking with search results
curl -X POST "http://localhost:8000/api/v1/bookings/complete-booking/" \
  -H "Authorization: Bearer your-jwt-token" \
  -H "Content-Type: application/json" \
  -d '{
    "search_criteria": {
      "check_in": "2024-03-15",
      "check_out": "2024-03-17",
      "guests": 2,
      "location": "New York"
    },
    "booking_details": {
      "primary_guest_name": "John Doe",
      "primary_guest_email": "john@example.com",
      "primary_guest_phone": "+1234567890"
    },
    "payment_info": {
      "payment_method": "card"
    }
  }'
```

### Example 2: Direct Room Booking
```bash
curl -X POST "http://localhost:8000/api/v1/bookings/complete-booking/" \
  -H "Authorization: Bearer your-jwt-token" \
  -H "Content-Type: application/json" \
  -d '{
    "search_criteria": {
      "check_in": "2024-03-15",
      "check_out": "2024-03-17",
      "guests": 2
    },
    "booking_details": {
      "room_id": "550e8400-e29b-41d4-a716-446655440001",
      "primary_guest_name": "John Doe",
      "primary_guest_email": "john@example.com",
      "primary_guest_phone": "+1234567890",
      "special_requests": "Late checkout if possible"
    },
    "payment_info": {
      "payment_method": "card"
    }
  }'
```

### Example 3: Hotel Search with Filters
```bash
curl -X GET "http://localhost:8000/api/v1/hotels/search/?location=Miami&star_rating=4&min_price=100&max_price=300"
```

## 🧪 Testing

### Run Tests
```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test bookings
python manage.py test core
python manage.py test accounts

# Run with coverage
pip install coverage
coverage run --source='.' manage.py test
coverage report
```

### Test API Endpoints
Use the provided Postman collection or test with curl:

```bash
# Test authentication
curl -X POST "http://localhost:8000/api/v1/auth/login/" \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testpass"}'

# Test hotel search
curl -X GET "http://localhost:8000/api/v1/hotels/search/?location=New York"
```

## 🚀 Deployment

### Production Checklist
- [ ] Set `DJANGO_SETTINGS_MODULE=hotel_booking.deployment`
- [ ] Configure PostgreSQL database
- [ ] Set up Redis for caching
- [ ] Configure email backend
- [ ] Set up file storage (AWS S3 recommended)
- [ ] Configure domain and SSL certificate
- [ ] Set up monitoring and logging
- [ ] Configure backup strategy

### Environment Variables
```bash
# Required for production
DJANGO_SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:pass@host:port/db
REDIS_URL=redis://host:port/db
EMAIL_HOST=smtp.yourdomain.com
EMAIL_HOST_USER=noreply@yourdomain.com
EMAIL_HOST_PASSWORD=your-email-password
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
AWS_STORAGE_BUCKET_NAME=your-bucket-name
```
