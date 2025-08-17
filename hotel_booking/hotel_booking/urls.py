from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

try:
    from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
    HAS_SPECTACULAR = True
except ImportError:
    HAS_SPECTACULAR = False

def api_root(request):
    return JsonResponse({
        'message': 'Hotel Booking Engine API',
        'version': 'v1.0',
        'endpoints': {
            'auth': f'{request.build_absolute_uri()}auth/',
            'hotels': f'{request.build_absolute_uri()}hotels/',
            'bookings': f'{request.build_absolute_uri()}bookings/',
        }
    })

urlpatterns = [
    path('', include('core.dashboard_urls')),
    path('admin/', admin.site.urls),
    path('api/v1/', api_root, name='api_root'),
    path('api/v1/auth/', include('accounts.urls')),
    path('api/v1/hotels/', include('core.urls')),
    path('api/v1/bookings/', include('bookings.urls')),
]

if HAS_SPECTACULAR:
    urlpatterns += [
        # API schema endpoint
        path('api/v1/schema/', SpectacularAPIView.as_view(), name='schema'),
        # Swagger UI endpoint
        path('api/v1/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
        # Redoc UI endpoint
        path('api/v1/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    ]
