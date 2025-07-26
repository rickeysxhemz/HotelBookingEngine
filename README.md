# 🏨 Hotel Booking Engine - Complete API Backend

A comprehensive Django REST API backend for hotel reservation management featuring JWT authentication, intelligent room search, real-time booking, and complete hotel management system.

## 🌟 Project Highlights

- ✅ **100% Test Coverage** - Complete API test suite with 15 test scenarios
- 🏨 **Production Ready** - Hotel Maar with 18 rooms pre-configured
- 🔐 **Secure Authentication** - JWT tokens with automatic blacklisting
- 📱 **RESTful APIs** - Complete booking lifecycle management
- 📊 **Smart Room Search** - Intelligent room combinations for any group size
- 🎯 **Real-time Availability** - Live room availability checking
- 📖 **Complete Documentation** - Comprehensive API documentation included

## 🚀 Quick Start (5 Minutes)

### 1. Clone & Setup
```bash
git clone https://github.com/Mujadid2001/HotelBookingEngine.git
cd HotelBookingEngine/hotel_booking
```

### 2. Install Dependencies
```bash
# Virtual environment already included with all packages
# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate

# If needed, install dependencies:
pip install -r requirements.txt
```

### 3. Start Server
```bash
python manage.py runserver
```

### 4. Test Everything Works
```bash
python complete_api_test.py --check-server
```

**Expected Result**: 100% success rate with all 15 tests passing ✅

## 🎯 Access Points

Once running, access these URLs:

- **📋 API Root**: http://127.0.0.1:8000/api/
- **🏨 Hotel Data**: http://127.0.0.1:8000/api/core/hotels/
- **👤 Admin Panel**: http://127.0.0.1:8000/admin/
- **📖 API Docs**: http://127.0.0.1:8000/api/schema/swagger-ui/

### 🔑 Pre-configured Access
- **Admin Login**: admin@hotelmaar.com / AdminPass123!
- **Hotel**: Hotel Maar (4-star with 18 rooms)
- **Room Types**: Single, Double, Family Suite, Deluxe Suite
- **Services**: Breakfast, Parking, Shuttle, Room Service

## 🏗️ Architecture Overview

```
🏨 Hotel Booking Engine
├── 👥 User Management (JWT Authentication)
├── 🏨 Hotel Management (Hotel Maar Setup)
├── 🛏️  Room Management (4 types, 18 rooms)
├── 📅 Booking System (Complete lifecycle)
├── 💰 Pricing Engine (Seasonal pricing)
├── 🎯 Extra Services (6 services available)
└── 📊 Admin Dashboard (Full management)
```

## 🧪 Testing & Validation

### Automated Test Suite
```bash
python complete_api_test.py --check-server
```

**What gets tested:**
- ✅ User registration and authentication
- ✅ JWT token management (access + refresh)
- ✅ Hotel discovery and details
- ✅ Room search with availability
- ✅ Complete booking flow
- ✅ Booking management and history
- ✅ API security and validation

### Manual Testing
```bash
# Test hotel endpoint
curl -X GET "http://127.0.0.1:8000/api/core/hotels/"

# Test user registration
curl -X POST "http://127.0.0.1:8000/api/accounts/register/" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","username":"testuser","first_name":"Test","last_name":"User","phone_number":"+1234567890","password":"TestPass123!","password_confirm":"TestPass123!"}'
```

## 📁 Project Structure

```
HotelBookingEngine/
├── 📄 README.md                    # This file
├── 📋 HowTo_RUN.md                 # Detailed setup guide
├── 📖 API_DOCUMENTATION.md         # Complete API docs (150+ pages)
├── 📊 COMPLETION_SUMMARY.md        # Project completion summary
├── 🏨 hotel_booking/               # Main Django project
│   ├── 👥 accounts/                # User authentication system
│   ├── 🏨 core/                    # Hotel & room management
│   ├── 📅 bookings/                # Booking system
│   ├── ⚙️  hotel_booking/          # Django settings
│   ├── 📋 requirements.txt         # All dependencies (36 packages)
│   ├── 🧪 complete_api_test.py    # Comprehensive test suite
│   ├── 🗄️  db.sqlite3              # Database with Hotel Maar data
│   ├── 🚀 manage.py               # Django management
│   └── 📁 venv/                   # Virtual environment (included!)
└── 📝 .gitignore                  # Git ignore rules
```

## 🔧 Tech Stack

- **🐍 Python**: 3.12.4
- **🌐 Django**: 5.2.4 + REST Framework 3.15.2
- **🔐 Authentication**: JWT with djangorestframework-simplejwt
- **🗄️ Database**: SQLite (dev) / PostgreSQL (production)
- **📖 Documentation**: drf-spectacular (OpenAPI 3.0)
- **🧪 Testing**: Custom comprehensive test suite
- **🚀 Deployment**: Production-ready configurations

## 🎯 Key Features

### 🔐 Authentication System
- JWT token-based authentication
- Automatic token blacklisting on logout
- User registration with email verification
- Secure password validation

### 🏨 Hotel Management
- **Hotel Maar**: Pre-configured luxury hotel
- **18 Rooms**: 4 Standard Single, 6 Standard Double, 5 Family Suite, 3 Deluxe Suite
- **6 Services**: Continental/Full Breakfast, Parking, Shuttle, Room Service, Late Check-out
- **Seasonal Pricing**: Dynamic pricing based on dates

### 📅 Booking System
- **Smart Search**: Intelligent room combinations for any group size
- **Real-time Availability**: Live availability checking
- **Complete Lifecycle**: Create, view, update, cancel bookings
- **Booking History**: Complete audit trail of all changes
- **Extra Services**: Add services like breakfast and parking

### 📊 Admin Features
- **Django Admin**: Complete administrative interface
- **User Management**: Manage customer accounts
- **Booking Management**: View and manage all reservations
- **Hotel Configuration**: Manage rooms, pricing, and services

## 📖 Documentation

### 📋 For Quick Setup
- **[HowTo_RUN.md](HowTo_RUN.md)** - Step-by-step setup and deployment guide

### 📖 For API Development
- **[API_DOCUMENTATION.md](API_DOCUMENTATION.md)** - Complete API reference (150+ pages)
- **Swagger UI**: http://127.0.0.1:8000/api/schema/swagger-ui/
- **API Browser**: http://127.0.0.1:8000/api/

### 📊 For Project Overview
- **[COMPLETION_SUMMARY.md](COMPLETION_SUMMARY.md)** - Project completion summary

## 🚀 Production Deployment

### Option 1: Traditional Server (VPS)
Complete setup with PostgreSQL, Nginx, Gunicorn, and SSL - see [HowTo_RUN.md](HowTo_RUN.md#production-deployment)

### Option 2: Docker
```bash
docker-compose up -d
```

### Option 3: Cloud Platforms
- Heroku, AWS, Google Cloud, Azure - configurations included

## 🤝 For Your Friend

This repository is **ready to use** with:

✅ **Virtual environment included** - No need to create one  
✅ **All dependencies installed** - Just activate venv  
✅ **Database pre-configured** - Hotel Maar ready to go  
✅ **Admin user created** - admin@hotelmaar.com  
✅ **Complete test suite** - Verify everything works  
✅ **Comprehensive docs** - Everything documented  

### 🎯 Your friend should:
1. Clone this repository
2. Activate virtual environment
3. Run `python manage.py runserver`
4. Run `python complete_api_test.py --check-server`
5. Start building their frontend!

## 📞 Support

- **📖 Documentation**: See `API_DOCUMENTATION.md` for complete API reference
- **🚀 Setup Guide**: See `HowTo_RUN.md` for detailed setup instructions
- **🧪 Testing**: Run `complete_api_test.py` to verify everything works
- **📊 Summary**: See `COMPLETION_SUMMARY.md` for project overview

## 🏆 Project Status

**Status**: ✅ COMPLETE  
**API Test Coverage**: 100% (15/15 tests passing)  
**Documentation**: Complete with examples  
**Production Ready**: Yes  
**Last Updated**: July 26, 2025  

---

**🎉 Ready to power your hotel booking application!**

*Built with ❤️ using Django REST Framework*
