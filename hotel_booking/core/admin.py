# Django imports
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count

# Local imports
from .models import Hotel, RoomType, Room, Extra, SeasonalPricing


class RoomInline(admin.TabularInline):
    """Inline admin for rooms"""
    model = Room
    extra = 0
    fields = ['room_number', 'floor', 'room_type', 'capacity', 'base_price', 'view_type', 'is_active']
    readonly_fields = []


class ExtraInline(admin.TabularInline):
    """Inline admin for hotel extras"""
    model = Extra
    extra = 0
    fields = ['name', 'category', 'price', 'pricing_type', 'is_active']


class SeasonalPricingInline(admin.TabularInline):
    """Inline admin for seasonal pricing"""
    model = SeasonalPricing
    extra = 0
    fields = ['name', 'room_type', 'start_date', 'end_date', 'price_multiplier', 'is_active']


@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    """Admin interface for hotels"""
    list_display = [
        'name', 'city', 'state', 'star_rating', 'total_rooms', 
        'phone_number', 'email', 'is_active'
    ]
    list_filter = ['star_rating', 'city', 'state', 'is_active']
    search_fields = ['name', 'city', 'email', 'phone_number']
    readonly_fields = ['id', 'created_at', 'updated_at', 'full_address']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'name', 'description', 'star_rating', 'is_active')
        }),
        ('Address', {
            'fields': (
                'address_line_1', 'address_line_2', 'city', 'state',
                'postal_code', 'country', 'full_address'
            )
        }),
        ('Contact Information', {
            'fields': ('phone_number', 'email', 'website')
        }),
        ('Policies & Timing', {
            'fields': (
                'check_in_time', 'check_out_time', 'cancellation_policy',
                'pet_policy', 'smoking_policy'
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [RoomInline, ExtraInline, SeasonalPricingInline]
    
    def get_queryset(self, request):
        """Add annotations for room count"""
        return super().get_queryset(request).annotate(
            room_count=Count('rooms')
        )
    
    def total_rooms(self, obj):
        """Get total number of rooms"""
        return obj.room_count
    total_rooms.short_description = 'Total Rooms'
    total_rooms.admin_order_field = 'room_count'


@admin.register(RoomType)
class RoomTypeAdmin(admin.ModelAdmin):
    """Admin interface for room types"""
    list_display = [
        'name', 'max_capacity', 'bed_type', 'bed_count', 'bathroom_count',
        'room_size_sqm', 'total_rooms', 'is_accessible'
    ]
    list_filter = ['max_capacity', 'bed_type', 'is_accessible']
    search_fields = ['name', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at', 'amenities_summary']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'name', 'description', 'max_capacity')
        }),
        ('Room Specifications', {
            'fields': (
                'bed_type', 'bed_count', 'bathroom_count', 'room_size_sqm'
            )
        }),
        ('Amenities', {
            'fields': (
                'has_wifi', 'has_tv', 'has_air_conditioning', 'has_balcony',
                'has_kitchenette', 'has_minibar', 'has_safe', 'amenities_summary'
            )
        }),
        ('Accessibility', {
            'fields': ('is_accessible',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Add annotations for room count"""
        return super().get_queryset(request).annotate(
            room_count=Count('rooms')
        )
    
    def total_rooms(self, obj):
        """Get total number of rooms of this type"""
        return obj.room_count
    total_rooms.short_description = 'Total Rooms'
    total_rooms.admin_order_field = 'room_count'
    
    def amenities_summary(self, obj):
        """Display amenities summary"""
        amenities = obj.amenities_list
        if amenities:
            return ', '.join(amenities[:5])  # Show first 5 amenities
        return 'No amenities'
    amenities_summary.short_description = 'Amenities'


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    """Admin interface for rooms"""
    list_display = [
        'room_number', 'hotel_name', 'room_type_name', 'floor', 'capacity',
        'base_price', 'view_type', 'is_active', 'is_maintenance'
    ]
    list_filter = [
        'hotel', 'room_type', 'floor', 'capacity', 'view_type',
        'is_active', 'is_maintenance'
    ]
    search_fields = ['room_number', 'hotel__name', 'room_type__name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'hotel', 'room_number', 'floor', 'room_type')
        }),
        ('Capacity & Pricing', {
            'fields': ('capacity', 'base_price', 'view_type')
        }),
        ('Status', {
            'fields': ('is_active', 'is_maintenance', 'maintenance_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    # Custom actions
    actions = ['activate_rooms', 'deactivate_rooms', 'mark_maintenance', 'clear_maintenance']
    
    def get_queryset(self, request):
        """Optimize queryset"""
        return super().get_queryset(request).select_related(
            'hotel', 'room_type'
        )
    
    def hotel_name(self, obj):
        """Get hotel name"""
        return obj.hotel.name
    hotel_name.short_description = 'Hotel'
    hotel_name.admin_order_field = 'hotel__name'
    
    def room_type_name(self, obj):
        """Get room type name"""
        return obj.room_type.name
    room_type_name.short_description = 'Room Type'
    room_type_name.admin_order_field = 'room_type__name'
    
    def activate_rooms(self, request, queryset):
        """Activate selected rooms"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'Successfully activated {updated} rooms.')
    activate_rooms.short_description = 'Activate selected rooms'
    
    def deactivate_rooms(self, request, queryset):
        """Deactivate selected rooms"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'Successfully deactivated {updated} rooms.')
    deactivate_rooms.short_description = 'Deactivate selected rooms'
    
    def mark_maintenance(self, request, queryset):
        """Mark rooms for maintenance"""
        updated = queryset.update(is_maintenance=True, maintenance_notes='Marked for maintenance via admin')
        self.message_user(request, f'Successfully marked {updated} rooms for maintenance.')
    mark_maintenance.short_description = 'Mark for maintenance'
    
    def clear_maintenance(self, request, queryset):
        """Clear maintenance status"""
        updated = queryset.update(is_maintenance=False, maintenance_notes='')
        self.message_user(request, f'Successfully cleared maintenance for {updated} rooms.')
    clear_maintenance.short_description = 'Clear maintenance'


@admin.register(Extra)
class ExtraAdmin(admin.ModelAdmin):
    """Admin interface for extra services"""
    list_display = [
        'name', 'hotel_name', 'category', 'price', 'pricing_type',
        'max_quantity', 'is_active'
    ]
    list_filter = ['hotel', 'category', 'pricing_type', 'is_active']
    search_fields = ['name', 'description', 'hotel__name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'hotel', 'name', 'description', 'category')
        }),
        ('Pricing', {
            'fields': ('price', 'pricing_type', 'max_quantity')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset"""
        return super().get_queryset(request).select_related('hotel')
    
    def hotel_name(self, obj):
        """Get hotel name"""
        return obj.hotel.name
    hotel_name.short_description = 'Hotel'
    hotel_name.admin_order_field = 'hotel__name'


@admin.register(SeasonalPricing)
class SeasonalPricingAdmin(admin.ModelAdmin):
    """Admin interface for seasonal pricing"""
    list_display = [
        'name', 'hotel_name', 'room_type_name', 'start_date', 'end_date',
        'price_multiplier', 'applicable_days', 'is_active'
    ]
    list_filter = ['hotel', 'room_type', 'is_active', 'start_date']
    search_fields = ['name', 'hotel__name', 'room_type__name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'hotel', 'room_type', 'name')
        }),
        ('Date Range', {
            'fields': ('start_date', 'end_date')
        }),
        ('Pricing', {
            'fields': ('price_multiplier',)
        }),
        ('Days of Week', {
            'fields': (
                'apply_monday', 'apply_tuesday', 'apply_wednesday',
                'apply_thursday', 'apply_friday', 'apply_saturday', 'apply_sunday'
            )
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset"""
        return super().get_queryset(request).select_related('hotel', 'room_type')
    
    def hotel_name(self, obj):
        """Get hotel name"""
        return obj.hotel.name
    hotel_name.short_description = 'Hotel'
    hotel_name.admin_order_field = 'hotel__name'
    
    def room_type_name(self, obj):
        """Get room type name"""
        return obj.room_type.name
    room_type_name.short_description = 'Room Type'
    room_type_name.admin_order_field = 'room_type__name'
    
    def applicable_days(self, obj):
        """Get applicable days summary"""
        days = []
        if obj.apply_monday: days.append('Mon')
        if obj.apply_tuesday: days.append('Tue')
        if obj.apply_wednesday: days.append('Wed')
        if obj.apply_thursday: days.append('Thu')
        if obj.apply_friday: days.append('Fri')
        if obj.apply_saturday: days.append('Sat')
        if obj.apply_sunday: days.append('Sun')
        
        if len(days) == 7:
            return 'All days'
        elif len(days) == 5 and not obj.apply_saturday and not obj.apply_sunday:
            return 'Weekdays'
        elif len(days) == 2 and obj.apply_saturday and obj.apply_sunday:
            return 'Weekends'
        else:
            return ', '.join(days)
    applicable_days.short_description = 'Applicable Days'
