"""
Complete Booking API Routes - Separate CRUD Endpoints with Additional Operations

CRUD Operations:
1. GET /bookings/ - List all bookings (READ)
2. POST /bookings/create/ - Create new booking (CREATE)
3. GET /bookings/<id>/ - Get specific booking details (READ)
4. PUT /bookings/<id>/update/ - Update specific booking (UPDATE)
5. DELETE /bookings/<id>/delete/ - Delete/Cancel specific booking (DELETE)

Additional Endpoints:
6. POST /bookings/<id>/confirm/ - Confirm pending booking
7. POST /bookings/<id>/cancel/ - Cancel booking with refund calculation
8. GET /bookings/<id>/audit-history/ - Get booking change audit trail
9. GET /bookings/user/<user_id>/ - Get bookings for specific user
10. GET /bookings/room/<room_id>/ - Get bookings for specific room
"""
from django.urls import path
from . import views

app_name = 'bookings'

urlpatterns = [
    # CRUD Operations - Separate endpoints for clarity
    path('', views.BookingListAPIView.as_view(), name='booking-list'),                          # READ (List)
    path('create/', views.BookingCreateAPIView.as_view(), name='booking-create'),               # CREATE
    path('<int:pk>/', views.BookingDetailAPIView.as_view(), name='booking-detail'),             # READ (Detail)
    path('<int:pk>/update/', views.BookingUpdateAPIView.as_view(), name='booking-update'),      # UPDATE
    path('<int:pk>/delete/', views.BookingDeleteAPIView.as_view(), name='booking-delete'),      # DELETE (Soft)
    
    # NEW: Additional business operations
    path('<int:pk>/confirm/', views.BookingConfirmationAPIView.as_view(), name='booking-confirm'),           # Confirm pending booking
    path('<int:pk>/cancel/', views.BookingCancellationAPIView.as_view(), name='booking-cancel'),            # Cancel with refund
    path('<int:pk>/audit-history/', views.BookingAuditHistoryAPIView.as_view(), name='booking-audit-history'), # Audit trail
    
    # User and Room specific bookings
    path('user/<uuid:user_id>/', views.UserBookingListAPIView.as_view(), name='user-bookings'),
    path('room/<uuid:room_id>/', views.RoomBookingListAPIView.as_view(), name='room-bookings'),
]

