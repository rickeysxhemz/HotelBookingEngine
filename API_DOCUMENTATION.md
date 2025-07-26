# Hotel Booking Engine - Complete API Documentation

## Table of Contents
- [Overview](#overview)
- [Quick Start Guide](#quick-start-guide)
- [Authentication](#authentication)
- [Base URL & Response Format](#base-url--response-format)
- [Error Handling](#error-handling)
- [API Endpoints](#api-endpoints)
  - [Authentication Endpoints](#1-accounts-api-apiaccounts)
  - [Hotel Management Endpoints](#2-core-api-apicore)
  - [Booking Management Endpoints](#3-bookings-api-apibookings)
- [Complete Booking Flow Example](#complete-booking-flow-example)
- [Testing the API](#testing-the-api)
- [Production Deployment](#production-deployment)

## Overview
This is a comprehensive Django REST API backend for a hotel booking system featuring JWT authentication, intelligent room availability search, booking management, and industry-standard security practices.

### 🏨 Hotel Information
**Hotel Name**: Hotel Maar - A luxury 4-star hotel  
**Location**: 123 Luxury Boulevard, Premium District, Metropolitan City  
**Features**: 18 rooms across 4 room types, seasonal pricing, 6 extra services  
**Room Types**: Standard Single (1 guest), Standard Double (2 guests), Family Suite (3 guests), Deluxe Suite (3 guests)

### ✨ Key Features
- **Smart Room Search**: Intelligent room combinations for any group size
- **Real-time Availability**: Live room availability checking
- **Secure Authentication**: JWT tokens with automatic blacklisting
- **Booking Management**: Complete lifecycle from creation to history tracking
- **Seasonal Pricing**: Dynamic pricing based on seasons and demand
- **Extra Services**: Breakfast, parking, airport shuttle, and more
- **Admin Dashboard**: Full Django admin interface for management

### 🛠 Technology Stack
- **Framework**: Django 5.2.4 + Django REST Framework 3.15.2
- **Database**: SQLite (development) / PostgreSQL (production ready)
- **Authentication**: JWT with djangorestframework-simplejwt
- **Documentation**: drf-spectacular (OpenAPI 3.0 compliant)
- **Security**: Token blacklisting, CORS, secure middleware

## Quick Start Guide

### 🚀 1. Start the Server
```bash
cd hotel_booking
python manage.py runserver
```

### 🧪 2. Run Complete API Tests
```bash
python complete_api_test.py --check-server
```

### 🔗 3. Access API Browser
- **API Root**: http://127.0.0.1:8000/api/
- **Admin Panel**: http://127.0.0.1:8000/admin/ (admin@hotelmaar.com / AdminPass123!)
- **API Docs**: http://127.0.0.1:8000/api/schema/swagger-ui/

### 📝 4. Sample API Call
```bash
# Get hotels list
curl -X GET "http://127.0.0.1:8000/api/core/hotels/" \
     -H "Content-Type: application/json"
```

## Authentication

### JWT Token System
The API uses JWT (JSON Web Tokens) with automatic blacklisting for enhanced security.

#### Token Lifecycle
- **Access Token**: 15 minutes lifetime
- **Refresh Token**: 7 days lifetime  
- **Automatic Blacklisting**: On logout or security breach
- **Middleware Validation**: Every request is validated

#### Authentication Header
```http
Authorization: Bearer <access_token>
```

#### Token Flow
1. **Login** → Get access + refresh tokens
2. **API Calls** → Use access token in header
3. **Refresh** → Use refresh token to get new access token
4. **Logout** → Blacklist both tokens

## Base URL & Response Format

### Base URLs
```
Development: http://127.0.0.1:8000/api/
Production:  https://your-domain.com/api/
```

### Standard Headers
```http
Content-Type: application/json
Accept: application/json
Authorization: Bearer <token>  # For authenticated endpoints
```

### Response Formats

#### Success Response
```json
{
  "id": "uuid-string",
  "name": "Hotel Maar",
  "status": "success",
  "data": { /* response data */ }
}
```

#### Paginated Response
```json
{
  "count": 18,
  "next": "http://api.example.com/resource/?page=2",
  "previous": null,
  "results": [ /* array of objects */ ]
}
```

#### Error Response
```json
{
  "error": "Authentication credentials were not provided.",
  "detail": "Authorization header is required",
  "code": "authentication_failed"
}
```

## Error Handling

### HTTP Status Codes
| Code | Meaning | Description |
|------|---------|-------------|
| 200  | OK | Successful GET, PATCH, DELETE |
| 201  | Created | Successful POST (resource created) |
| 400  | Bad Request | Invalid request data or validation errors |
| 401  | Unauthorized | Missing or invalid authentication |
| 403  | Forbidden | Insufficient permissions |
| 404  | Not Found | Resource not found |
| 429  | Too Many Requests | Rate limit exceeded |
| 500  | Internal Server Error | Server error |

### Common Error Examples

#### Validation Error (400)
```json
{
  "email": ["This field is required."],
  "password": ["Password must be at least 8 characters."]
}
```

#### Authentication Error (401)
```json
{
  "detail": "Given token not valid for any token type",
  "code": "token_not_valid",
  "messages": [
    {
      "token_class": "AccessToken",
      "token_type": "access",
      "message": "Token is invalid or expired"
    }
  ]
}
```

#### Business Logic Error (400)
```json
{
  "error": "Room is not available for the selected dates",
  "detail": "Room 101 is already booked from 2025-08-01 to 2025-08-03",
  "available_alternatives": ["Room 102", "Room 103"]
}
```

## 1. ACCOUNTS API (`/api/accounts/`)

### User Registration
**Endpoint:** `POST /api/accounts/register/`
**Access:** Public

**Request Body:**
```json
{
    "email": "user@example.com",
    "username": "newuser",
    "first_name": "John",
    "last_name": "Doe",
    "phone_number": "+1234567890",
    "password": "securepassword123",
    "password_confirm": "securepassword123"
}
```

**Response (201):**
```json
{
    "message": "Registration successful! Please check your email to verify your account.",
    "user": {
        "id": "uuid",
        "email": "user@example.com",
        "username": "newuser",
        "first_name": "John",
        "last_name": "Doe",
        "full_name": "John Doe",
        "phone_number": "+1234567890",
        "is_verified": false,
        "date_joined": "2025-07-26T10:00:00Z"
    }
}
```

### User Login
**Endpoint:** `POST /api/accounts/login/`
**Access:** Public

**Request Body:**
```json
{
    "email": "user@example.com",
    "password": "securepassword123"
}
```

**Response (200):**
```json
{
    "message": "Welcome back, John!",
    "tokens": {
        "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    },
    "user": {
        "id": "uuid",
        "email": "user@example.com",
        "username": "newuser",
        "first_name": "John",
        "last_name": "Doe",
        "full_name": "John Doe"
    }
}
```

### User Logout
**Endpoint:** `POST /api/accounts/logout/`
**Access:** Authenticated
**Headers:** `Authorization: Bearer <access_token>`

**Request Body:**
```json
{
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Response (200):**
```json
{
    "message": "Successfully logged out"
}
```

### Get User Profile
**Endpoint:** `GET /api/accounts/profile/`
**Access:** Authenticated

**Response (200):**
```json
{
    "id": "uuid",
    "email": "user@example.com",
    "username": "newuser",
    "first_name": "John",
    "last_name": "Doe",
    "full_name": "John Doe",
    "phone_number": "+1234567890",
    "date_of_birth": "1990-01-01",
    "address_line_1": "123 Main St",
    "city": "New York",
    "state": "NY",
    "profile": {
        "total_bookings": 5,
        "total_spent": "1250.00",
        "preferred_room_type": "Family Suite"
    }
}
```

---

## 2. CORE API (`/api/core/`)

### List Hotels
**Endpoint:** `GET /api/core/hotels/`
**Access:** Public

**Response (200):**
```json
[
    {
        "id": "uuid",
        "name": "Hotel Maar",
        "description": "A luxurious hotel offering comfortable accommodations...",
        "full_address": "123 Luxury Boulevard, Premium District, Metropolitan City, State, 12345, United States",
        "phone_number": "+1-555-MAAR-HOTEL",
        "email": "info@hotelmaar.com",
        "website": "https://www.hotelmaar.com",
        "star_rating": 4,
        "check_in_time": "15:00:00",
        "check_out_time": "11:00:00",
        "room_types": [...],
        "amenities_count": 6
    }
]
```

### Get Hotel Details
**Endpoint:** `GET /api/core/hotels/<hotel_id>/`
**Access:** Public

**Response (200):**
```json
{
    "id": "uuid",
    "name": "Hotel Maar",
    "description": "A luxurious hotel offering comfortable accommodations...",
    "full_address": "123 Luxury Boulevard, Premium District, Metropolitan City, State, 12345, United States",
    "policies": {
        "cancellation_policy": "Free cancellation up to 24 hours before check-in...",
        "pet_policy": "Pets are welcome with prior notice...",
        "smoking_policy": "Non-smoking property..."
    },
    "total_rooms": 18,
    "room_types": [
        {
            "id": "uuid",
            "name": "Standard Single",
            "description": "Cozy single room perfect for solo travelers",
            "max_capacity": 1,
            "bed_type": "Single Bed",
            "bed_count": 1,
            "bathroom_count": 1,
            "room_size_sqm": 20,
            "amenities": ["WiFi", "TV", "Air Conditioning", "Safe"],
            "is_accessible": false
        }
    ]
}
```

### Get Hotel Room Types
**Endpoint:** `GET /api/core/hotels/<hotel_id>/room-types/`
**Access:** Public

**Response (200):**
```json
{
    "hotel": {
        "id": "uuid",
        "name": "Hotel Maar"
    },
    "room_types": [
        {
            "id": "uuid",
            "name": "Standard Single",
            "description": "Cozy single room perfect for solo travelers",
            "max_capacity": 1,
            "bed_type": "Single Bed",
            "available_rooms": 4,
            "price_range": {
                "min_price": "80.00",
                "max_price": "85.00"
            }
        },
        {
            "id": "uuid", 
            "name": "Family Suite",
            "description": "Spacious suite perfect for families",
            "max_capacity": 3,
            "bed_type": "King Bed + Sofa Bed",
            "available_rooms": 5,
            "price_range": {
                "min_price": "180.00",
                "max_price": "200.00"
            }
        }
    ]
}
```

### Get Hotel Amenities
**Endpoint:** `GET /api/core/hotels/<hotel_id>/amenities/`
**Access:** Public

**Response (200):**
```json
{
    "hotel": {
        "id": "uuid",
        "name": "Hotel Maar"
    },
    "room_amenities": [
        "WiFi", "TV", "Air Conditioning", "Safe", "Balcony", "Kitchenette", "Minibar"
    ],
    "hotel_services": {
        "Breakfast": [
            {
                "id": "uuid",
                "name": "Continental Breakfast",
                "description": "Fresh pastries, fruits, coffee, and juice",
                "price": "25.00",
                "pricing_type": "Per Person",
                "max_quantity": 10
            }
        ],
        "Parking": [
            {
                "id": "uuid",
                "name": "Parking",
                "description": "Secure parking space",
                "price": "15.00",
                "pricing_type": "Per Night",
                "max_quantity": 2
            }
        ]
    }
}
```

---

## 3. BOOKINGS API (`/api/bookings/`)

### Search Available Rooms
**Endpoint:** `POST /api/bookings/search/`
**Access:** Public

**Request Body:**
```json
{
    "check_in": "2025-08-01",
    "check_out": "2025-08-03",
    "guests": 3,
    "hotel_id": "uuid",
    "max_price": "500.00"
}
```

**Response (200):**
```json
{
    "results": [
        {
            "hotel": {
                "id": "uuid",
                "name": "Hotel Maar",
                "star_rating": 4,
                "address": "123 Luxury Boulevard, Premium District..."
            },
            "available_rooms": 8,
            "room_combinations": [
                {
                    "type": "single_room",
                    "rooms": [
                        {
                            "id": "uuid",
                            "room_number": "301",
                            "floor": 3,
                            "capacity": 3,
                            "base_price": "200.00",
                            "view_type": "city",
                            "room_type": {
                                "name": "Family Suite",
                                "description": "Spacious suite perfect for families",
                                "amenities": ["WiFi", "TV", "Balcony", "Kitchenette"]
                            },
                            "price_for_dates": "400.00"
                        }
                    ],
                    "total_capacity": 3,
                    "total_price": "400.00",
                    "room_count": 1
                },
                {
                    "type": "multi_room",
                    "rooms": [
                        {
                            "id": "uuid",
                            "room_number": "101",
                            "capacity": 1,
                            "price_for_dates": "160.00"
                        },
                        {
                            "id": "uuid",
                            "room_number": "103",
                            "capacity": 2,
                            "price_for_dates": "240.00"
                        }
                    ],
                    "total_capacity": 3,
                    "total_price": "400.00",
                    "room_count": 2
                }
            ],
            "available_extras": [
                {
                    "id": "uuid",
                    "name": "Continental Breakfast",
                    "description": "Fresh pastries, fruits, coffee, and juice",
                    "price": "25.00",
                    "pricing_type": "per_person",
                    "category": "breakfast"
                }
            ]
        }
    ],
    "search_params": {
        "check_in": "2025-08-01",
        "check_out": "2025-08-03",
        "guests": 3,
        "nights": 2
    }
}
```

### Create Booking
**Endpoint:** `POST /api/bookings/create/`
**Access:** Authenticated

**Request Body:**
```json
{
    "room_id": "uuid",
    "check_in": "2025-08-01",
    "check_out": "2025-08-03",
    "guests": 2,
    "primary_guest_name": "John Doe",
    "primary_guest_email": "john@example.com",
    "primary_guest_phone": "+1234567890",
    "special_requests": "Late check-in requested",
    "extras_data": [
        {
            "extra_id": "uuid",
            "quantity": 2
        }
    ],
    "additional_guests_data": [
        {
            "first_name": "Jane",
            "last_name": "Doe",
            "age_group": "adult"
        }
    ]
}
```

**Response (201):**
```json
{
    "message": "Booking created successfully",
    "booking": {
        "id": "uuid",
        "booking_reference": "BK2025072612AB",
        "status": "confirmed",
        "payment_status": "pending",
        "check_in": "2025-08-01",
        "check_out": "2025-08-03",
        "nights": 2,
        "guests": 2,
        "room": {
            "room_number": "103",
            "room_type": {
                "name": "Standard Double"
            }
        },
        "room_price": "240.00",
        "extras_price": "50.00",
        "tax_amount": "29.00",
        "total_price": "319.00",
        "primary_guest_name": "John Doe",
        "booking_date": "2025-07-26T10:00:00Z",
        "can_cancel": true,
        "can_check_in": false,
        "can_check_out": false,
        "price_breakdown": {
            "room_price": "240.00",
            "extras_price": "50.00",
            "subtotal": "290.00",
            "tax_amount": "29.00",
            "total_price": "319.00",
            "nights": 2,
            "price_per_night": "120.00"
        }
    }
}
```

### List User Bookings
**Endpoint:** `GET /api/bookings/`
**Access:** Authenticated

**Query Parameters:**
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 10, max: 50)
- `search`: Search by booking reference or guest name
- `ordering`: Sort by booking_date, check_in, total_price (prefix with `-` for descending)

**Response (200):**
```json
{
    "count": 25,
    "next": "http://127.0.0.1:8000/api/bookings/?page=2",
    "previous": null,
    "results": [
        {
            "id": "uuid",
            "booking_reference": "BK2025072612AB",
            "status": "confirmed",
            "payment_status": "pending",
            "check_in": "2025-08-01",
            "check_out": "2025-08-03",
            "nights": 2,
            "guests": 2,
            "room_info": {
                "room_number": "103",
                "room_type": "Standard Double",
                "capacity": 2
            },
            "hotel_name": "Hotel Maar",
            "total_price": "319.00",
            "primary_guest_name": "John Doe",
            "booking_date": "2025-07-26T10:00:00Z"
        }
    ]
}
```

### Get Booking Details
**Endpoint:** `GET /api/bookings/<booking_reference>/`
**Access:** Authenticated (own bookings only)

**Response (200):**
```json
{
    "id": "uuid",
    "booking_reference": "BK2025072612AB",
    "status": "confirmed",
    "payment_status": "pending",
    "check_in": "2025-08-01",
    "check_out": "2025-08-03",
    "nights": 2,
    "guests": 2,
    "room": {
        "id": "uuid",
        "room_number": "103",
        "floor": 1,
        "capacity": 2,
        "view_type": "city",
        "room_type": {
            "name": "Standard Double",
            "description": "Comfortable double room with modern amenities",
            "amenities": ["WiFi", "TV", "Air Conditioning", "Safe"]
        }
    },
    "booking_extras": [
        {
            "id": "uuid",
            "extra": {
                "name": "Continental Breakfast",
                "description": "Fresh pastries, fruits, coffee, and juice",
                "price": "25.00",
                "pricing_type": "per_person"
            },
            "quantity": 2,
            "unit_price": "25.00",
            "total_price": "50.00"
        }
    ],
    "additional_guests": [
        {
            "id": "uuid",
            "first_name": "Jane",
            "last_name": "Doe",
            "age_group": "adult"
        }
    ],
    "room_price": "240.00",
    "extras_price": "50.00",
    "tax_amount": "29.00",
    "total_price": "319.00",
    "primary_guest_name": "John Doe",
    "primary_guest_email": "john@example.com",
    "primary_guest_phone": "+1234567890",
    "special_requests": "Late check-in requested",
    "booking_date": "2025-07-26T10:00:00Z",
    "confirmation_date": "2025-07-26T10:01:00Z",
    "can_cancel": true,
    "can_check_in": false,
    "can_check_out": false,
    "history": [
        {
            "action": "Booking Created",
            "description": "Booking created for 2 nights",
            "timestamp": "2025-07-26T10:00:00Z",
            "performed_by": "John Doe"
        },
        {
            "action": "Booking Confirmed",
            "description": "Booking confirmed automatically",
            "timestamp": "2025-07-26T10:01:00Z",
            "performed_by": "System"
        }
    ]
}
```

### Update Booking
**Endpoint:** `PATCH /api/bookings/<booking_reference>/update/`
**Access:** Authenticated (own bookings only)
**Note:** Only allows updates for pending/confirmed bookings

**Request Body:**
```json
{
    "primary_guest_name": "John Smith",
    "primary_guest_phone": "+1987654321",
    "special_requests": "Room on upper floor preferred"
}
```

**Response (200):**
```json
{
    "message": "Booking updated successfully",
    "booking": {
        // Updated booking details
    }
}
```

### Cancel Booking
**Endpoint:** `POST /api/bookings/<booking_reference>/cancel/`
**Access:** Authenticated (own bookings only)

**Request Body:**
```json
{
    "reason": "guest_request",
    "notes": "Change of travel plans"
}
```

**Response (200):**
```json
{
    "message": "Booking cancelled successfully",
    "booking_reference": "BK2025072612AB"
}
```

### Get Booking History
**Endpoint:** `GET /api/bookings/<booking_reference>/history/`
**Access:** Authenticated (own bookings only)

**Response (200):**
```json
{
    "booking_reference": "BK2025072612AB",
    "history": [
        {
            "action": "Booking Created",
            "description": "Booking created for 2 nights",
            "timestamp": "2025-07-26T10:00:00Z",
            "performed_by": "John Doe"
        },
        {
            "action": "Booking Modified",
            "description": "Booking details updated",
            "timestamp": "2025-07-26T11:00:00Z",
            "performed_by": "John Doe"
        },
        {
            "action": "Booking Cancelled",
            "description": "Booking cancelled - guest_request",
            "timestamp": "2025-07-26T12:00:00Z",
            "performed_by": "John Doe"
        }
    ]
}
```

---

## 4. STAFF ENDPOINTS

### Staff Booking List
**Endpoint:** `GET /api/bookings/staff/all/`
**Access:** Staff/Admin only

**Response:** Similar to user booking list but includes all bookings

### Hotel Dashboard
**Endpoint:** `GET /api/bookings/staff/dashboard/`
**Access:** Staff/Admin only

**Response (200):**
```json
{
    "todays_metrics": {
        "checkins": 5,
        "checkouts": 3,
        "current_guests": 12
    },
    "upcoming_bookings": [
        // Array of upcoming bookings
    ]
}
```

### Check-in Guest
**Endpoint:** `POST /api/bookings/<booking_reference>/check-in/`
**Access:** Staff/Admin only

**Response (200):**
```json
{
    "message": "Guest checked in successfully",
    "booking_reference": "BK2025072612AB",
    "check_in_time": "2025-08-01T15:30:00Z"
}
```

### Check-out Guest
**Endpoint:** `POST /api/bookings/<booking_reference>/check-out/`
**Access:** Staff/Admin only

**Response (200):**
```json
{
    "message": "Guest checked out successfully",
    "booking_reference": "BK2025072612AB",
    "check_out_time": "2025-08-03T11:30:00Z"
}
```

---

## Error Responses

### Standard Error Format
```json
{
    "error": "Error message",
    "detail": "Detailed description",
    "code": "error_code"
}
```

---

## Complete Booking Flow Example

This section demonstrates a complete end-to-end booking process using the Hotel Booking Engine API.

### Step 1: User Registration
```bash
curl -X POST "http://127.0.0.1:8000/api/accounts/register/" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "customer@example.com",
    "username": "customer123",
    "first_name": "John",
    "last_name": "Smith",
    "phone_number": "+1234567890",
    "password": "SecurePass123!",
    "password_confirm": "SecurePass123!"
  }'
```

**Response:**
```json
{
  "message": "User registered successfully. Please check your email to verify your account.",
  "user": {
    "id": "uuid-string",
    "email": "customer@example.com",
    "full_name": "John Smith",
    "date_joined": "2025-07-26T12:00:00Z"
  }
}
```

### Step 2: User Login
```bash
curl -X POST "http://127.0.0.1:8000/api/accounts/login/" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "customer@example.com",
    "password": "SecurePass123!"
  }'
```

**Response:**
```json
{
  "message": "Login successful",
  "tokens": {
    "access": "eyJhbGciOiJIUzI1NiIs...",
    "refresh": "eyJhbGciOiJIUzI1NiIs..."
  },
  "user": {
    "id": "uuid-string",
    "email": "customer@example.com",
    "full_name": "John Smith"
  }
}
```

### Step 3: Browse Hotels
```bash
curl -X GET "http://127.0.0.1:8000/api/core/hotels/" \
  -H "Content-Type: application/json"
```

**Response:**
```json
{
  "count": 1,
  "results": [
    {
      "id": "hotel-uuid",
      "name": "Hotel Maar",
      "description": "A luxurious hotel offering comfortable accommodations",
      "star_rating": 4,
      "full_address": "123 Luxury Boulevard, Premium District",
      "room_types": [
        {
          "id": "room-type-uuid",
          "name": "Standard Double",
          "max_capacity": 2,
          "amenities": ["WiFi", "TV", "Air Conditioning"]
        }
      ]
    }
  ]
}
```

### Step 4: Search Available Rooms
```bash
curl -X POST "http://127.0.0.1:8000/api/bookings/search/" \
  -H "Content-Type: application/json" \
  -d '{
    "check_in": "2025-08-15",
    "check_out": "2025-08-17",
    "guests": 2,
    "hotel_id": "hotel-uuid",
    "max_price": "300.00"
  }'
```

**Response:**
```json
{
  "search_params": {
    "check_in": "2025-08-15",
    "check_out": "2025-08-17",
    "guests": 2,
    "nights": 2
  },
  "results": [
    {
      "hotel": {
        "id": "hotel-uuid",
        "name": "Hotel Maar"
      },
      "room_combinations": [
        {
          "type": "single_room",
          "room_count": 1,
          "total_price": "280.00",
          "rooms": [
            {
              "id": "room-uuid",
              "room_number": "201",
              "room_type": "Standard Double",
              "nightly_rate": "140.00"
            }
          ]
        }
      ],
      "available_extras": [
        {
          "id": "extra-uuid",
          "name": "Continental Breakfast",
          "price": "25.00",
          "pricing_type": "per_person"
        }
      ]
    }
  ]
}
```

### Step 5: Create Booking
```bash
curl -X POST "http://127.0.0.1:8000/api/bookings/create/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{
    "room_id": "room-uuid",
    "check_in": "2025-08-15",
    "check_out": "2025-08-17",
    "guests": 2,
    "primary_guest_name": "John Smith",
    "primary_guest_email": "customer@example.com",
    "primary_guest_phone": "+1234567890",
    "special_requests": "High floor room preferred",
    "extras_data": [
      {
        "extra_id": "extra-uuid",
        "quantity": 2
      }
    ],
    "additional_guests_data": [
      {
        "first_name": "Jane",
        "last_name": "Smith",
        "age_group": "adult"
      }
    ]
  }'
```

**Response:**
```json
{
  "message": "Booking created successfully",
  "booking": {
    "booking_reference": "BK20250726ABCD",
    "status": "confirmed",
    "check_in": "2025-08-15",
    "check_out": "2025-08-17",
    "guests": 2,
    "total_price": "330.00",
    "room": {
      "id": "room-uuid",
      "room_number": "201",
      "room_type": "Standard Double"
    },
    "price_breakdown": {
      "room_price": "280.00",
      "extras_price": "50.00",
      "tax_amount": "0.00",
      "total_price": "330.00"
    },
    "additional_guests": [
      {
        "first_name": "Jane",
        "last_name": "Smith",
        "age_group": "adult"
      }
    ]
  }
}
```

### Step 6: View Booking Details
```bash
curl -X GET "http://127.0.0.1:8000/api/bookings/BK20250726ABCD/" \
  -H "Authorization: Bearer <access_token>"
```

### Step 7: Update Booking (Optional)
```bash
curl -X PATCH "http://127.0.0.1:8000/api/bookings/BK20250726ABCD/update/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{
    "special_requests": "High floor room with city view, early check-in requested"
  }'
```

### Step 8: View Booking History
```bash
curl -X GET "http://127.0.0.1:8000/api/bookings/BK20250726ABCD/history/" \
  -H "Authorization: Bearer <access_token>"
```

**Response:**
```json
{
  "booking_reference": "BK20250726ABCD",
  "history": [
    {
      "id": "history-uuid",
      "action": "Booking Created",
      "description": "Booking created for 2 nights",
      "timestamp": "2025-07-26T12:30:00Z",
      "performed_by": "John Smith"
    },
    {
      "id": "history-uuid-2",
      "action": "Booking Updated",
      "description": "Special requests updated",
      "timestamp": "2025-07-26T12:35:00Z",
      "performed_by": "John Smith"
    }
  ]
}
```

---

## Testing the API

### Automated Testing Suite
We provide a comprehensive test suite that validates all API endpoints:

```bash
# Run complete API test suite
cd hotel_booking
python complete_api_test.py --check-server

# Expected output: 100% success rate with all endpoints tested
```

### Manual Testing Tools

#### 1. curl Commands
Use the examples provided in this documentation to test individual endpoints.

#### 2. API Browser
Visit http://127.0.0.1:8000/api/ for an interactive API browser interface.

#### 3. Swagger UI
Visit http://127.0.0.1:8000/api/schema/swagger-ui/ for full OpenAPI documentation.

#### 4. Postman Collection
Import the API endpoints into Postman for organized testing:
- Base URL: `http://127.0.0.1:8000`
- Add Authorization header with Bearer token for protected endpoints

### Test Data
The system comes pre-loaded with:
- **Hotel Maar**: 18 rooms across 4 room types
- **Admin User**: admin@hotelmaar.com / AdminPass123!
- **Sample Pricing**: Seasonal rates and extra services
- **Room Availability**: Real-time availability system

---

## Production Deployment

### Environment Variables
```bash
DEBUG=False
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:pass@host:port/dbname
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
CORS_ALLOWED_ORIGINS=https://your-frontend.com
```

### Database Migration
```bash
python manage.py migrate
python manage.py setup_initial_data
python manage.py createsuperuser
```

### Static Files
```bash
python manage.py collectstatic
```

### Security Checklist
- ✅ Use HTTPS in production
- ✅ Set strong SECRET_KEY
- ✅ Configure proper CORS settings
- ✅ Set up database backups
- ✅ Monitor API rate limits
- ✅ Enable logging and monitoring

### Performance Optimization
- **Database**: Use PostgreSQL with proper indexing
- **Caching**: Implement Redis for session and query caching
- **CDN**: Use CDN for static files
- **Load Balancing**: Scale horizontally with multiple instances

---

## Support and Contributing

### Getting Help
- **Documentation**: This API documentation
- **Issues**: Report bugs on the project repository
- **Email**: Contact the development team

### API Versioning
Current version: `v1`
Future versions will be accessible via `/api/v2/` endpoints.

### Rate Limits
- **Development**: No limits
- **Production**: 1000 requests per hour per authenticated user

---

**Last Updated**: July 26, 2025  
**API Version**: 1.0  
**Django Version**: 5.2.4  
**Python Version**: 3.12+
```json
{
    "error": "Error message description",
    "code": "error_code",
    "details": {
        "field_name": ["Field-specific error message"]
    }
}
```

### Common HTTP Status Codes
- **200 OK**: Request successful
- **201 Created**: Resource created successfully
- **400 Bad Request**: Invalid request data
- **401 Unauthorized**: Authentication required or invalid
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Resource not found
- **423 Locked**: Account locked (too many failed login attempts)
- **500 Internal Server Error**: Server error

### Validation Errors Example
```json
{
    "email": ["This field is required."],
    "password": ["This password is too short. It must contain at least 8 characters."],
    "check_in": ["Check-in date cannot be in the past"]
}
```

---

## Business Logic & Features

### Room Capacity Logic
For 3 guests, the system returns multiple accommodation options:
1. **Single room solutions**: Rooms with capacity ≥ 3
2. **Multi-room solutions**: Combinations like 1+2 capacity rooms
3. **Sorted by price**: Most affordable options first

### Pricing System
- **Base Pricing**: Each room has a base price per night
- **Seasonal Pricing**: Automatic price adjustments based on date
- **Extra Services**: Various pricing types (per stay, per person, per night)
- **Tax Calculation**: 10% tax applied to subtotal

### Booking Lifecycle
1. **Pending**: Initial booking creation
2. **Confirmed**: Payment processed or auto-confirmed
3. **Checked In**: Guest has arrived
4. **Checked Out**: Stay completed
5. **Cancelled**: Booking cancelled
6. **No Show**: Guest didn't arrive

### Security Features
- JWT token blacklisting on logout
- Middleware validation on every request
- Rate limiting on login attempts (5 attempts = account lock)
- Password validation with complexity requirements
- Email verification system

---

## Development Setup

### Prerequisites
- Python 3.8+
- Django 5.2+
- Django REST Framework
- SimpleJWT for authentication

### Installation
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run migrations: `python manage.py migrate`
4. Create superuser: `python manage.py createsuperuser`
5. Set up initial data: `python manage.py setup_initial_data`
6. Run server: `python manage.py runserver`

### Database Schema
- **CustomUser**: Extended user model with profile information
- **Hotel**: Hotel information and policies
- **RoomType**: Room categories with amenities
- **Room**: Individual rooms with pricing
- **Extra**: Additional services
- **Booking**: Booking records with lifecycle tracking
- **SeasonalPricing**: Dynamic pricing rules

### Testing
Run the test suite:
```bash
python manage.py test
```

Test coverage includes:
- User authentication and JWT tokens
- Room availability search algorithms
- Booking creation and management
- Pricing calculations
- Business logic validation

---

## Production Considerations

### Security
- Use environment variables for sensitive settings
- Enable HTTPS
- Configure proper CORS settings
- Set up rate limiting
- Regular security audits

### Performance
- Database indexing on search fields
- Query optimization with select_related/prefetch_related
- Caching for frequently accessed data
- Pagination for large datasets

### Monitoring
- Logging configuration
- Error tracking
- Performance monitoring
- Database performance metrics

---

## Support & Contact

For technical support or API questions, please contact:
- **Email**: dev-support@hotelmaar.com
- **Documentation**: [API Docs URL]
- **Status Page**: [Status URL]

**Version**: 1.0
**Last Updated**: July 26, 2025
