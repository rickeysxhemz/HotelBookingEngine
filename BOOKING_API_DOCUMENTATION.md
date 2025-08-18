# Hotel Booking API - Complete Booking Flow

This document describes the complete booking flow API that handles room searching, booking creation, payment processing, and email notifications.

## API Endpoints

### 1. Complete Booking Flow API
**Endpoint:** `POST /api/bookings/complete-booking/`
**Description:** Handles the complete booking flow from room search to confirmation email.

#### Request Payload:
```json
{
    "search_criteria": {
        "hotel_id": "550e8400-e29b-41d4-a716-446655440000",  // Optional
        "location": "New York",  // Optional - search by city
        "check_in": "2024-01-15",
        "check_out": "2024-01-18",
        "guests": 2
    },
    "booking_details": {
        "room_id": "550e8400-e29b-41d4-a716-446655440001",  // Optional if searching
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

#### Response:
```json
{
    "success": true,
    "message": "Booking completed successfully",
    "booking": {
        "id": "550e8400-e29b-41d4-a716-446655440003",
        "booking_reference": "BK001234",
        "status": "confirmed",
        "payment_status": "paid",
        "check_in": "2024-01-15",
        "check_out": "2024-01-18",
        "guests": 2,
        "primary_guest_name": "John Doe",
        "primary_guest_email": "john@example.com",
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
    "available_rooms": [],  // Only populated if room search was performed
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

### 2. Room Search Only API
**Endpoint:** `GET /api/bookings/search-rooms/`
**Description:** Search for available rooms without creating a booking.

#### Query Parameters:
- `hotel_id` (optional): UUID of specific hotel
- `location` (optional): City name to search in
- `check_in`: Check-in date (YYYY-MM-DD)
- `check_out`: Check-out date (YYYY-MM-DD)
- `guests`: Number of guests (default: 1)

#### Example Request:
```
GET /api/bookings/search-rooms/?check_in=2024-01-15&check_out=2024-01-18&guests=2&location=New York
```

#### Response:
```json
{
    "search_criteria": {
        "check_in": "2024-01-15",
        "check_out": "2024-01-18",
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
                "nights": 3,
                "price_per_night": "100.00"
            },
            "images": [
                {
                    "id": "img001",
                    "image_url": "/media/rooms/deluxe-room-1.jpg",
                    "alt_text": "Deluxe Room Interior",
                    "is_primary": true
                }
            ]
        }
    ],
    "total_found": 1
}
```

## Features of the Complete Booking Flow

### 1. Room Search
- Search by specific hotel or by location
- Availability checking for date range
- Guest capacity validation
- Real-time pricing calculation

### 2. Booking Creation
- Automatic room availability validation
- Price calculation including extras and taxes
- Guest information capture
- Special requests handling

### 3. Payment Processing
- Simulated payment processing (ready for real payment gateway integration)
- Payment method selection
- Transaction tracking
- Payment failure handling

### 4. Email Notifications
- Booking confirmation emails with complete details
- Booking modification notifications
- Cancellation confirmations
- HTML email templates with hotel branding

### 5. Error Handling
- Comprehensive validation
- Transactional safety (rollback on failure)
- Detailed error messages
- Logging for debugging

## Email Templates

The system includes three email templates:

1. **Booking Confirmation** (`templates/emails/booking_confirmation.html`)
   - Complete booking details
   - Hotel information
   - Check-in instructions
   - Contact information

2. **Booking Modification** (`templates/emails/booking_modification.html`)
   - Updated booking details
   - Change summary
   - New pricing information

3. **Booking Cancellation** (`templates/emails/booking_cancellation.html`)
   - Cancellation confirmation
   - Refund information
   - Rebooking assistance

## Integration with Existing System

The complete booking flow integrates with existing services:

- **RoomAvailabilityService**: Room search and availability checking
- **PricingService**: Dynamic pricing calculation
- **BookingValidationService**: Booking validation rules
- **EmailService**: Email notification handling

## Authentication

All booking operations require user authentication using JWT tokens:

```
Authorization: Bearer <your-jwt-token>
```

## Error Responses

Common error responses:

```json
{
    "error": "No available rooms found for the specified criteria",
    "search_criteria": {
        "check_in": "2024-01-15",
        "check_out": "2024-01-18",
        "guests": 2
    }
}
```

```json
{
    "error": "Selected room is no longer available"
}
```

```json
{
    "error": "Payment failed: Insufficient funds"
}
```

## Usage Examples

### Simple Room Search
```bash
curl -X GET "http://localhost:8000/api/bookings/search-rooms/?check_in=2024-01-15&check_out=2024-01-18&guests=2"
```

### Complete Booking with Search
```bash
curl -X POST "http://localhost:8000/api/bookings/complete-booking/" \
  -H "Authorization: Bearer your-jwt-token" \
  -H "Content-Type: application/json" \
  -d '{
    "search_criteria": {
      "check_in": "2024-01-15",
      "check_out": "2024-01-18",
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

### Direct Booking with Known Room
```bash
curl -X POST "http://localhost:8000/api/bookings/complete-booking/" \
  -H "Authorization: Bearer your-jwt-token" \
  -H "Content-Type: application/json" \
  -d '{
    "search_criteria": {
      "check_in": "2024-01-15",
      "check_out": "2024-01-18",
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
