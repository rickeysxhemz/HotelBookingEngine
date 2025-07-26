from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Hotel endpoints
    path('hotels/', views.HotelListAPIView.as_view(), name='hotel_list'),
    path('hotels/<uuid:hotel_id>/', views.HotelDetailAPIView.as_view(), name='hotel_detail'),
    
    # Room endpoints
    path('hotels/<uuid:hotel_id>/rooms/', views.HotelRoomsAPIView.as_view(), name='hotel_rooms'),
    path('hotels/<uuid:hotel_id>/room-types/', views.HotelRoomTypesAPIView.as_view(), name='hotel_room_types'),
    
    # Room availability
    path('availability/search/', views.room_availability_search, name='availability_search'),
    
    # Hotel information
    path('hotels/<uuid:hotel_id>/amenities/', views.get_hotel_amenities, name='hotel_amenities'),
    path('hotels/<uuid:hotel_id>/policies/', views.get_hotel_policies, name='hotel_policies'),
]
