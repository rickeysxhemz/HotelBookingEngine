"""
Authentication and User Management API Routes

Design Principles:
- Clear action-based naming
- Essential authentication endpoints only
- RESTful where applicable
"""
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

app_name = 'accounts'

urlpatterns = [
    # === AUTHENTICATION ===
    path('register/', views.RegisterAPIView.as_view(), name='register'),
    path('login/', views.login_api_view, name='login'),
    path('logout/', views.logout_api_view, name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # === PASSWORD MANAGEMENT ===
    path('password/change/', views.PasswordChangeAPIView.as_view(), name='password_change'),
    path('password/reset/request/', views.password_reset_request, name='password_reset_request'),
    path('password/reset/confirm/<uuid:token>/', views.password_reset_confirm, name='password_reset_confirm'),
    
    # === USER PROFILE ===
    path('profile/', views.ProfileAPIView.as_view(), name='profile'),
    path('profile/update/', views.ProfileUpdateAPIView.as_view(), name='profile_update'),
    
    # === VERIFICATION ===
    path('verify-email/<uuid:token>/', views.verify_email, name='verify_email'),
]
