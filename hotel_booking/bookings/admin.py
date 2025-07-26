# Django imports
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone

# Local imports
from .models import Booking, BookingExtra, BookingGuest, BookingHistory


class BookingExtraInline(admin.TabularInline):
    """Inline admin for booking extras"""
    model = BookingExtra
    extra = 0
    readonly_fields = ['total_price']
    fields = ['extra', 'quantity', 'unit_price', 'total_price']


class BookingGuestInline(admin.TabularInline):
    """Inline admin for additional booking guests"""
    model = BookingGuest
    extra = 0


class BookingHistoryInline(admin.TabularInline):
    """Inline admin for booking history"""
    model = BookingHistory
    extra = 0
    readonly_fields = ['action', 'description', 'performed_by', 'timestamp']
    fields = ['action', 'description', 'performed_by', 'timestamp']
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    """Admin interface for bookings"""
    list_display = [
        'booking_reference', 'primary_guest_name', 'hotel_name', 'room_info',
        'check_in', 'check_out', 'nights', 'guests', 'status', 'payment_status',
        'total_price', 'booking_date'
    ]
    list_filter = [
        'status', 'payment_status', 'booking_source', 'room__hotel',
        'check_in', 'booking_date'
    ]
    search_fields = [
        'booking_reference', 'primary_guest_name', 'primary_guest_email',
        'user__email', 'user__first_name', 'user__last_name'
    ]
    readonly_fields = [
        'id', 'booking_reference', 'booking_date', 'confirmation_date',
        'check_in_time', 'check_out_time', 'cancellation_date', 'nights',
        'room_price', 'extras_price', 'tax_amount', 'total_price'
    ]
    fieldsets = (
        ('Booking Information', {
            'fields': (
                'id', 'booking_reference', 'status', 'payment_status',
                'booking_source', 'booking_date'
            )
        }),
        ('Guest Information', {
            'fields': (
                'user', 'primary_guest_name', 'primary_guest_email',
                'primary_guest_phone'
            )
        }),
        ('Stay Details', {
            'fields': (
                'room', 'check_in', 'check_out', 'nights', 'guests'
            )
        }),
        ('Pricing', {
            'fields': (
                'room_price', 'extras_price', 'tax_amount', 'total_price'
            )
        }),
        ('Special Requests & Notes', {
            'fields': ('special_requests', 'internal_notes'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': (
                'confirmation_date', 'check_in_time', 'check_out_time'
            ),
            'classes': ('collapse',)
        }),
        ('Cancellation Details', {
            'fields': (
                'cancellation_date', 'cancellation_reason', 'cancellation_notes'
            ),
            'classes': ('collapse',)
        }),
    )
    inlines = [BookingExtraInline, BookingGuestInline, BookingHistoryInline]
    
    # Custom actions
    actions = ['confirm_bookings', 'cancel_bookings']
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related(
            'user', 'room__hotel', 'room__room_type'
        )
    
    def hotel_name(self, obj):
        """Get hotel name"""
        return obj.room.hotel.name
    hotel_name.short_description = 'Hotel'
    hotel_name.admin_order_field = 'room__hotel__name'
    
    def room_info(self, obj):
        """Get room information"""
        return f"Room {obj.room.room_number} ({obj.room.room_type.name})"
    room_info.short_description = 'Room'
    room_info.admin_order_field = 'room__room_number'
    
    def nights(self, obj):
        """Get number of nights"""
        return obj.nights
    nights.short_description = 'Nights'
    
    def confirm_bookings(self, request, queryset):
        """Admin action to confirm multiple bookings"""
        updated = 0
        for booking in queryset.filter(status='pending'):
            booking.confirm_booking()
            updated += 1
        
        self.message_user(
            request,
            f'Successfully confirmed {updated} bookings.'
        )
    confirm_bookings.short_description = 'Confirm selected bookings'
    
    def cancel_bookings(self, request, queryset):
        """Admin action to cancel multiple bookings"""
        updated = 0
        for booking in queryset:
            if booking.can_be_cancelled:
                booking.cancel_booking(reason='hotel_request', notes='Cancelled by admin')
                updated += 1
        
        self.message_user(
            request,
            f'Successfully cancelled {updated} bookings.'
        )
    cancel_bookings.short_description = 'Cancel selected bookings'


@admin.register(BookingExtra)
class BookingExtraAdmin(admin.ModelAdmin):
    """Admin interface for booking extras"""
    list_display = [
        'booking_reference', 'extra_name', 'quantity', 'unit_price', 'total_price'
    ]
    list_filter = ['extra__category', 'extra__hotel']
    search_fields = [
        'booking__booking_reference', 'extra__name'
    ]
    readonly_fields = ['total_price']
    
    def get_queryset(self, request):
        """Optimize queryset"""
        return super().get_queryset(request).select_related(
            'booking', 'extra'
        )
    
    def booking_reference(self, obj):
        """Get booking reference"""
        return obj.booking.booking_reference
    booking_reference.short_description = 'Booking'
    booking_reference.admin_order_field = 'booking__booking_reference'
    
    def extra_name(self, obj):
        """Get extra name"""
        return obj.extra.name
    extra_name.short_description = 'Extra Service'
    extra_name.admin_order_field = 'extra__name'


@admin.register(BookingGuest)
class BookingGuestAdmin(admin.ModelAdmin):
    """Admin interface for booking guests"""
    list_display = [
        'booking_reference', 'full_name', 'age_group'
    ]
    list_filter = ['age_group']
    search_fields = [
        'booking__booking_reference', 'first_name', 'last_name'
    ]
    
    def get_queryset(self, request):
        """Optimize queryset"""
        return super().get_queryset(request).select_related('booking')
    
    def booking_reference(self, obj):
        """Get booking reference"""
        return obj.booking.booking_reference
    booking_reference.short_description = 'Booking'
    booking_reference.admin_order_field = 'booking__booking_reference'


@admin.register(BookingHistory)
class BookingHistoryAdmin(admin.ModelAdmin):
    """Admin interface for booking history"""
    list_display = [
        'booking_reference', 'action', 'description', 'performed_by_name', 'timestamp'
    ]
    list_filter = ['action', 'timestamp']
    search_fields = [
        'booking__booking_reference', 'description', 'performed_by__email'
    ]
    readonly_fields = [
        'booking', 'action', 'description', 'performed_by', 'timestamp',
        'old_values', 'new_values'
    ]
    
    def get_queryset(self, request):
        """Optimize queryset"""
        return super().get_queryset(request).select_related(
            'booking', 'performed_by'
        )
    
    def booking_reference(self, obj):
        """Get booking reference"""
        return obj.booking.booking_reference
    booking_reference.short_description = 'Booking'
    booking_reference.admin_order_field = 'booking__booking_reference'
    
    def performed_by_name(self, obj):
        """Get performer name"""
        if obj.performed_by:
            return obj.performed_by.get_full_name() or obj.performed_by.username
        return 'System'
    performed_by_name.short_description = 'Performed By'
    performed_by_name.admin_order_field = 'performed_by__first_name'
    
    def has_add_permission(self, request):
        """Disable adding history entries manually"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Disable deleting history entries"""
        return False


# Customize admin site
admin.site.site_header = "Hotel Booking Engine Administration"
admin.site.site_title = "Hotel Admin"
admin.site.index_title = "Hotel Booking Management"
