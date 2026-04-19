from django.urls import path

from . import views_cbv

app_name = 'manager'

urlpatterns = [
    path('login/', views_cbv.ManagerLoginView.as_view(), name='login'),
    path('logout/', views_cbv.manager_logout, name='logout'),
    path('', views_cbv.DashboardView.as_view(), name='dashboard'),
    
    # Profile Management
    path('profile/', views_cbv.ProfileView.as_view(), name='profile'),
    path('profile/edit/', views_cbv.ProfileEditView.as_view(), name='profile_edit'),
    path('profile/change-password/', views_cbv.ChangePasswordView.as_view(), name='change_password'),
    
    path('hotels/', views_cbv.HotelListView.as_view(), name='hotels'),
    path('hotels/add/', views_cbv.HotelCreateView.as_view(), name='hotel_add'),
    
    path('hotels/<uuid:pk>/edit/', views_cbv.HotelUpdateView.as_view(), name='hotel_edit'),
    path('hotels/<uuid:pk>/delete/', views_cbv.HotelDeleteView.as_view(), name='hotel_delete'),

    # Bookings
    path('bookings/', views_cbv.BookingListView.as_view(), name='bookings'),
    path('bookings/add/', views_cbv.BookingCreateView.as_view(), name='booking_add'),
    path('bookings/<int:pk>/', views_cbv.BookingDetailView.as_view(), name='booking_detail'),
    path('bookings/<int:pk>/edit/', views_cbv.BookingUpdateView.as_view(), name='booking_edit'),
    path('bookings/<int:pk>/delete/', views_cbv.BookingDeleteView.as_view(), name='booking_delete'),
    path('bookings/export/', views_cbv.BookingExportView.as_view(), name='booking_export'),
    # Room types
    path('roomtypes/', views_cbv.RoomTypeListView.as_view(), name='roomtypes'),
    path('roomtypes/add/', views_cbv.RoomTypeCreateView.as_view(), name='roomtype_add'),
    path('roomtypes/<uuid:pk>/edit/', views_cbv.RoomTypeUpdateView.as_view(), name='roomtype_edit'),
    path('roomtypes/<uuid:pk>/delete/', views_cbv.RoomTypeDeleteView.as_view(), name='roomtype_delete'),

    # Rooms
    path('rooms/', views_cbv.RoomListView.as_view(), name='rooms'),
    path('rooms/add/', views_cbv.RoomCreateView.as_view(), name='room_add'),
    path('rooms/<uuid:pk>/edit/', views_cbv.RoomUpdateView.as_view(), name='room_edit'),
    path('rooms/<uuid:pk>/delete/', views_cbv.RoomDeleteView.as_view(), name='room_delete'),

    # Extras
    path('extras/', views_cbv.ExtraListView.as_view(), name='extras'),
    path('extras/add/', views_cbv.ExtraCreateView.as_view(), name='extra_add'),
    path('extras/<uuid:pk>/edit/', views_cbv.ExtraUpdateView.as_view(), name='extra_edit'),
    path('extras/<uuid:pk>/delete/', views_cbv.ExtraDeleteView.as_view(), name='extra_delete'),

    # Room amenities
    path('room-amenities/', views_cbv.RoomAmenityListView.as_view(), name='roomamenities'),
    path('room-amenities/add/', views_cbv.RoomAmenityCreateView.as_view(), name='roomamenity_add'),
    path('room-amenities/<uuid:pk>/edit/', views_cbv.RoomAmenityUpdateView.as_view(), name='roomamenity_edit'),
    path('room-amenities/<uuid:pk>/delete/', views_cbv.RoomAmenityDeleteView.as_view(), name='roomamenity_delete'),
    path('room-amenities/bulk-delete/', views_cbv.RoomAmenityListView.as_view(), name='roomamenity_bulk_delete'),

    # Room images
    path('room-images/', views_cbv.RoomImageListView.as_view(), name='roomimages'),
    path('room-images/add/', views_cbv.RoomImageCreateView.as_view(), name='roomimage_add'),
    path('room-images/<uuid:pk>/edit/', views_cbv.RoomImageUpdateView.as_view(), name='roomimage_edit'),
    path('room-images/<uuid:pk>/delete/', views_cbv.RoomImageDeleteView.as_view(), name='roomimage_delete'),
    path('room-images/bulk-delete/', views_cbv.RoomImageListView.as_view(), name='roomimage_bulk_delete'),

    # RoomType amenities
    path('roomtype-amenities/', views_cbv.RoomTypeAmenityListView.as_view(), name='roomtypeamenities'),
    path('roomtype-amenities/add/', views_cbv.RoomTypeAmenityCreateView.as_view(), name='roomtypeamenity_add'),
    path('roomtype-amenities/<int:pk>/edit/', views_cbv.RoomTypeAmenityUpdateView.as_view(), name='roomtypeamenity_edit'),
    path('roomtype-amenities/<int:pk>/delete/', views_cbv.RoomTypeAmenityDeleteView.as_view(), name='roomtypeamenity_delete'),
    path('roomtype-amenities/bulk-delete/', views_cbv.RoomTypeAmenityListView.as_view(), name='roomtypeamenity_bulk_delete'),

    # Seasonal pricing
    path('seasonal-pricing/', views_cbv.SeasonalPricingListView.as_view(), name='seasonalpricing'),
    path('seasonal-pricing/add/', views_cbv.SeasonalPricingCreateView.as_view(), name='seasonalpricing_add'),
    path('seasonal-pricing/<uuid:pk>/edit/', views_cbv.SeasonalPricingUpdateView.as_view(), name='seasonalpricing_edit'),
    path('seasonal-pricing/<uuid:pk>/delete/', views_cbv.SeasonalPricingDeleteView.as_view(), name='seasonalpricing_delete'),
    path('seasonal-pricing/bulk-delete/', views_cbv.SeasonalPricingListView.as_view(), name='seasonalpricing_bulk_delete'),

    # Offers Management
    path('offers/', views_cbv.OfferListView.as_view(), name='offers'),
    path('offers/add/', views_cbv.OfferCreateView.as_view(), name='offer_add'),
    path('offers/<uuid:pk>/', views_cbv.OfferDetailView.as_view(), name='offer_detail'),
    path('offers/<uuid:pk>/edit/', views_cbv.OfferUpdateView.as_view(), name='offer_edit'),
    path('offers/<uuid:pk>/delete/', views_cbv.OfferDeleteView.as_view(), name='offer_delete'),
    path('offers/bulk-delete/', views_cbv.OfferListView.as_view(), name='offer_bulk_delete'),

    # Offer Categories
    path('offer-categories/', views_cbv.OfferCategoryListView.as_view(), name='offer_categories'),
    path('offer-categories/add/', views_cbv.OfferCategoryCreateView.as_view(), name='offer_category_add'),
    path('offer-categories/<int:pk>/edit/', views_cbv.OfferCategoryUpdateView.as_view(), name='offer_category_edit'),
    path('offer-categories/<int:pk>/delete/', views_cbv.OfferCategoryDeleteView.as_view(), name='offer_category_delete'),
    path('offer-categories/bulk-delete/', views_cbv.OfferCategoryListView.as_view(), name='offer_category_bulk_delete'),

    # Offer Highlights
    path('offers/<uuid:offer_id>/highlights/', views_cbv.OfferHighlightListView.as_view(), name='offer_highlights'),
    path('offers/<uuid:offer_id>/highlights/add/', views_cbv.OfferHighlightCreateView.as_view(), name='offer_highlight_add'),
    path('offer-highlights/', views_cbv.OfferHighlightListView.as_view(), name='offer_highlights_all'),
    path('offer-highlights/add/', views_cbv.OfferHighlightCreateView.as_view(), name='offer_highlight_add_global'),
    path('offer-highlights/<int:pk>/edit/', views_cbv.OfferHighlightUpdateView.as_view(), name='offer_highlight_edit'),
    path('offer-highlights/<int:pk>/delete/', views_cbv.OfferHighlightDeleteView.as_view(), name='offer_highlight_delete'),
    path('offer-highlights/bulk-delete/', views_cbv.OfferHighlightListView.as_view(), name='offer_highlight_bulk_delete'),

    # Offer Images
    path('offers/<uuid:offer_id>/images/', views_cbv.OfferImageListView.as_view(), name='offer_images'),
    path('offers/<uuid:offer_id>/images/add/', views_cbv.OfferImageCreateView.as_view(), name='offer_image_add'),
    path('offer-images/', views_cbv.OfferImageListView.as_view(), name='offer_images_all'),
    path('offer-images/add/', views_cbv.OfferImageCreateView.as_view(), name='offer_image_add_global'),
    path('offer-images/<int:pk>/edit/', views_cbv.OfferImageUpdateView.as_view(), name='offer_image_edit'),
    path('offer-images/<int:pk>/delete/', views_cbv.OfferImageDeleteView.as_view(), name='offer_image_delete'),
    path('offer-images/bulk-delete/', views_cbv.OfferImageListView.as_view(), name='offer_image_bulk_delete'),

    # Global search
    path('search/', views_cbv.GlobalSearchView.as_view(), name='global_search'),
    
    # ========== NEW FEATURE URLS ==========
    
    # 1. Occupancy Calendar
    path('calendar/', views_cbv.OccupancyCalendarView.as_view(), name='occupancy_calendar'),
    
    # 2. Bulk Booking Status Updates
    path('bookings/bulk-status/', views_cbv.BulkBookingStatusUpdateView.as_view(), name='bulk_booking_status'),
    
    # 3. Booking Modification History
    path('bookings/<int:pk>/history/', views_cbv.BookingHistoryView.as_view(), name='booking_history'),
    
    # 4. Email Notifications (automatic via signals, no separate URL needed)
    
    # 5. Refund Management
    path('refunds/', views_cbv.BookingRefundListView.as_view(), name='booking_refunds'),
    path('refunds/<int:pk>/', views_cbv.BookingRefundDetailView.as_view(), name='booking_refund_detail'),
    path('hotels/<uuid:hotel_id>/refund-policy/', views_cbv.RefundPolicyView.as_view(), name='refund_policy'),
    
    # 6. Reports
    path('reports/revenue/', views_cbv.RevenueReportView.as_view(), name='revenue_report'),
    path('reports/occupancy/', views_cbv.OccupancyReportView.as_view(), name='occupancy_report'),
    
    # 7. Manager Roles and Property Scoping
    path('managers/<uuid:user_id>/properties/', views_cbv.ManagerPropertyAssignmentView.as_view(), name='manager_properties'),
    
    # 8. Payments Management
    path('payments/', views_cbv.PaymentListView.as_view(), name='payments'),
    path('payments/add/', views_cbv.PaymentCreateView.as_view(), name='payment_add'),
    path('payments/<int:pk>/edit/', views_cbv.PaymentUpdateView.as_view(), name='payment_edit'),
    path('payments/<int:pk>/delete/', views_cbv.PaymentDeleteView.as_view(), name='payment_delete'),
]
