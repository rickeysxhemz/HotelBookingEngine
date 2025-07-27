from django.urls import path
from . import dashboard_views

urlpatterns = [
    # Dashboard
    path('', dashboard_views.dashboard_view, name='dashboard'),
    
    # Dashboard API endpoints
    path('api/dashboard/stats/', dashboard_views.api_stats, name='dashboard_stats'),
    path('api/dashboard/health/', dashboard_views.api_health, name='dashboard_health'),
]
