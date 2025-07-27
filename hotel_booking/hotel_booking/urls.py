"""
URL configuration for hotel_booking project.
Backend API for Hotel Booking Engine

API Version: 1.0
Base URL: /api/v1/

Route Design Principles:
- RESTful resource naming
- Logical hierarchy (hotels -> rooms -> bookings)
- Clear, intuitive paths
- Professional API structure
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

# Try to import API documentation packages
try:
    from rest_framework import permissions
    from drf_yasg.views import get_schema_view
    from drf_yasg import openapi
    HAS_SWAGGER = True
except ImportError:
    HAS_SWAGGER = False

def api_root(request):
    """API root endpoint with navigation links"""
    return JsonResponse({
        'message': '🏨 Welcome to Hotel Booking Engine API',
        'version': 'v1.0',
        'documentation': f'{request.build_absolute_uri()}docs/' if HAS_SWAGGER else 'Not available',
        'endpoints': {
            'authentication': f'{request.build_absolute_uri()}auth/',
            'hotels': f'{request.build_absolute_uri()}hotels/',
            'bookings': f'{request.build_absolute_uri()}bookings/',
            'user_profile': f'{request.build_absolute_uri()}auth/profile/',
        },
        'quick_start': {
            'register': 'POST /api/v1/auth/register/',
            'login': 'POST /api/v1/auth/login/',
            'search_hotels': 'GET /api/v1/hotels/',
            'check_availability': 'GET /api/v1/hotels/{id}/availability/',
            'create_booking': 'POST /api/v1/bookings/',
        }
    })

# Base URL patterns
urlpatterns = [
    # Dashboard Interface
    path('', include('core.dashboard_urls')),
    
    # Admin Interface
    path('admin/', admin.site.urls),
    
    # API Root
    path('api/v1/', api_root, name='api_root'),
    
    # API Endpoints (v1)
    path('api/v1/auth/', include('accounts.urls')),
    path('api/v1/hotels/', include('core.urls')),
    path('api/v1/bookings/', include('bookings.urls')),
]

# Add Swagger documentation if available
if HAS_SWAGGER:
    # API Documentation Setup
    schema_view = get_schema_view(
        openapi.Info(
            title="Hotel Booking Engine API",
            default_version='v1',
            description="""
            🏨 **Hotel Booking Engine API Documentation**
            
            A comprehensive REST API for hotel booking and management system.
            
            **Features:**
            - 🔐 JWT Authentication with automatic token refresh
            - 🏨 Complete hotel and room management
            - 📅 Real-time availability checking
            - 💳 Booking creation and management
            - 👤 User profile and account management
            
            **Getting Started:**
            1. Register a new account: `POST /api/v1/auth/register/`
            2. Login to get tokens: `POST /api/v1/auth/login/`
            3. Use access token in Authorization header: `Bearer <token>`
            4. Explore hotels: `GET /api/v1/hotels/`
            5. Make a booking: `POST /api/v1/bookings/`
            
            **Authentication:**
            - Use Bearer token in Authorization header
            - Tokens auto-refresh for seamless experience
            - Logout invalidates all user tokens
            """,
            terms_of_service="https://www.yourhotel.com/terms/",
            contact=openapi.Contact(email="api@hotelmaar.com"),
            license=openapi.License(name="MIT License"),
        ),
        public=True,
        permission_classes=(permissions.AllowAny,),
    )
    
    # Add documentation URLs
    urlpatterns += [
        path('api/v1/docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
        path('api/v1/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
        path('api/v1/schema/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    ]
