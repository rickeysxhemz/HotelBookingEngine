"""
Booking Management API Routes

Design Principles:
- Clear booking lifecycle management
- RESTful resource operations
- Essential booking operations only
"""
from django.urls import path
from . import views

app_name = 'bookings'

urlpatterns = [
    # === BOOKING SEARCH ===
    path('search/', views.BookingSearchAPIView.as_view(), name='booking_search'),
    path('search/availability/', views.AvailabilitySearchAPIView.as_view(), name='availability_search'),
    
    # === BOOKING MANAGEMENT ===
    path('', views.BookingListAPIView.as_view(), name='booking_list'),
    path('create/', views.BookingCreateAPIView.as_view(), name='booking_create'),
    path('quote/', views.BookingQuoteAPIView.as_view(), name='booking_quote'),
    
    # === INDIVIDUAL BOOKING ===
    path('<str:booking_reference>/', views.BookingDetailAPIView.as_view(), name='booking_detail'),
    path('<str:booking_reference>/update/', views.BookingUpdateAPIView.as_view(), name='booking_update'),
    path('<str:booking_reference>/cancel/', views.BookingCancelAPIView.as_view(), name='booking_cancel'),
    path('<str:booking_reference>/confirm/', views.BookingConfirmAPIView.as_view(), name='booking_confirm'),
    
    # === BOOKING OPERATIONS ===
    path('<str:booking_reference>/checkin/', views.check_in_booking, name='booking_checkin'),
    path('<str:booking_reference>/checkout/', views.check_out_booking, name='booking_checkout'),
    
    # === STAFF OPERATIONS ===
    path('staff/', views.StaffBookingListAPIView.as_view(), name='staff_booking_list'),
    path('staff/dashboard/', views.get_hotel_dashboard, name='staff_dashboard'),
]

