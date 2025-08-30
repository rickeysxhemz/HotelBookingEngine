"""
Hotels and Rooms API Routes

Design Principles:
- Resource-based URLs following REST conventions
- Hierarchical structure: hotels -> rooms -> availability
- Clear, descriptive endpoint names
- Essential endpoints only for professional API
"""
from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # === HOTEL DISCOVERY ===
    path('', views.HotelListAPIView.as_view(), name='hotel_list'),
    path('search/', views.HotelSearchAPIView.as_view(), name='hotel_search'),
    path('search-availability/', views.hotel_search, name='hotel_search_availability'),
    path('search-capacity/', views.hotel_search_by_capacity, name='hotel_search_capacity'),
    path('search-flexible/', views.hotel_search_flexible, name='hotel_search_flexible'),
    path('featured/', views.FeaturedHotelsAPIView.as_view(), name='featured_hotels'),
    
    # === INDIVIDUAL HOTEL ===
    path('<uuid:hotel_id>/', views.HotelDetailAPIView.as_view(), name='hotel_detail'),
    path('<uuid:hotel_id>/gallery/', views.HotelGalleryAPIView.as_view(), name='hotel_gallery'),
    path('<uuid:hotel_id>/reviews/', views.HotelReviewsAPIView.as_view(), name='hotel_reviews'),
    path('<uuid:hotel_id>/policies/', views.HotelPoliciesAPIView.as_view(), name='hotel_policies'),
    
    # === HOTEL ROOMS ===
    path('<uuid:hotel_id>/rooms/', views.HotelRoomsAPIView.as_view(), name='hotel_rooms'),
    path('<uuid:hotel_id>/room-types/', views.HotelRoomTypesAPIView.as_view(), name='hotel_room_types'),
    path('<uuid:hotel_id>/rooms/<uuid:room_id>/', views.RoomDetailAPIView.as_view(), name='room_detail'),
    
    # === AVAILABILITY & PRICING ===
    path('<uuid:hotel_id>/availability/', views.HotelAvailabilityAPIView.as_view(), name='hotel_availability'),
    path('<uuid:hotel_id>/pricing/', views.HotelPricingAPIView.as_view(), name='hotel_pricing'),
    path('<uuid:hotel_id>/rooms/<uuid:room_id>/availability/', views.RoomAvailabilityAPIView.as_view(), name='room_availability'),
    
    # === HOTEL SERVICES ===
    path('<uuid:hotel_id>/amenities/', views.HotelAmenitiesAPIView.as_view(), name='hotel_amenities'),
    path('<uuid:hotel_id>/services/', views.HotelServicesAPIView.as_view(), name='hotel_services'),
    
    # === LOCATION ===
    path('<uuid:hotel_id>/location/', views.HotelLocationAPIView.as_view(), name='hotel_location'),
]
