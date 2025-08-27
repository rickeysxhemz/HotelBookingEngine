
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from core.health import health_check

try:
    from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
    HAS_SPECTACULAR = True
except ImportError:
    HAS_SPECTACULAR = False

def api_root(request):
    return JsonResponse({
        'message': 'Hotel Booking API',
        'version': 'v1.0',
        'status': 'operational',
        'endpoints': {
            'auth': f'{request.build_absolute_uri()}auth/',
            'hotels': f'{request.build_absolute_uri()}hotels/',
            'bookings': f'{request.build_absolute_uri()}bookings/',
            'docs': f'{request.build_absolute_uri()}docs/',
            'health': f'{request.build_absolute_uri()}health/',
        }
    })

urlpatterns = [
    # API endpoints
    path('admin/', admin.site.urls),
    path('manager/', include('manager.urls')),
    path('api/v1/', api_root, name='api_root'),
    path('api/v1/health/', health_check, name='health_check'),
    path('api/v1/auth/', include('accounts.urls')),
    path('api/v1/hotels/', include('core.urls')),
    path('api/v1/bookings/', include('bookings.urls')),
]


if HAS_SPECTACULAR:
    urlpatterns += [
        path('api/v1/schema/', SpectacularAPIView.as_view(), name='schema'),
        path('api/v1/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
        path('api/v1/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    ]

