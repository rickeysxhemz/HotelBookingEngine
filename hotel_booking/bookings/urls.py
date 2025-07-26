from django.urls import path
from . import views

app_name = 'bookings'

urlpatterns = [
    # Public booking search
    path('search/', views.search_rooms, name='search_rooms'),
    path('hotels/<uuid:hotel_id>/extras/', views.get_hotel_extras, name='hotel_extras'),
    
    # User booking management
    path('', views.BookingListAPIView.as_view(), name='booking_list'),
    path('create/', views.BookingCreateAPIView.as_view(), name='booking_create'),
    path('<str:booking_reference>/', views.BookingDetailAPIView.as_view(), name='booking_detail'),
    path('<str:booking_reference>/update/', views.BookingUpdateAPIView.as_view(), name='booking_update'),
    path('<str:booking_reference>/cancel/', views.cancel_booking, name='booking_cancel'),
    path('<str:booking_reference>/history/', views.get_booking_history, name='booking_history'),
    
    # Staff operations
    path('staff/all/', views.StaffBookingListAPIView.as_view(), name='staff_booking_list'),
    path('staff/dashboard/', views.get_hotel_dashboard, name='hotel_dashboard'),
    path('<str:booking_reference>/check-in/', views.check_in_booking, name='booking_check_in'),
    path('<str:booking_reference>/check-out/', views.check_out_booking, name='booking_check_out'),
]

