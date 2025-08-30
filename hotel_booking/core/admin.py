

# Django imports
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count

# Local imports
from .models import (
    Hotel, RoomType, Room, Extra, SeasonalPricing, 
    RoomImage, RoomAmenity, RoomTypeAmenity
)


class RoomInline(admin.TabularInline):
    """Inline admin for rooms"""
    model = Room
    extra = 0
    fields = [
        'room_number', 'floor', 'room_type', 'capacity', 'base_price', 
        'view_type', 'housekeeping_status', 'is_active', 'is_maintenance'
    ]
    readonly_fields = []


class RoomImageInline(admin.TabularInline):
    """Inline admin for room images"""
    model = RoomImage
    extra = 0
    fields = ['image', 'image_type', 'is_primary', 'display_order', 'is_active']


class RoomTypeAmenityInline(admin.TabularInline):
    """Inline admin for room type amenities"""
    model = RoomTypeAmenity
    extra = 0
    fields = ['amenity', 'is_included', 'additional_charge']


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
        'name', 'category', 'max_capacity', 'bed_configuration_display',
        'room_size_display', 'total_rooms', 'is_accessible'
    ]
    list_filter = [
        'category', 'max_capacity', 'bed_type', 'is_accessible', 
        'children_allowed', 'pets_allowed', 'smoking_allowed'
    ]
    search_fields = ['name', 'description', 'short_description']
    readonly_fields = ['id', 'created_at', 'updated_at', 'amenities_summary', 'bed_configuration']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'name', 'short_description', 'description', 'category', 'max_capacity')
        }),
        ('Room Specifications', {
            'fields': (
                'bed_type', 'bed_count', 'bathroom_count', 
                'room_size_sqm', 'room_size_sqft', 'bed_configuration'
            )
        }),
        ('Basic Amenities', {
            'fields': (
                'has_wifi', 'has_tv', 'has_smart_tv', 'has_air_conditioning', 'has_heating',
                'has_balcony', 'has_kitchenette', 'has_minibar', 'has_safe', 
                'has_desk', 'has_seating_area'
            ),
            'classes': ('collapse',)
        }),
        ('Bathroom Amenities', {
            'fields': (
                'has_bathtub', 'has_shower', 'has_hairdryer', 'has_toiletries',
                'has_towels', 'has_bathrobes', 'has_slippers'
            ),
            'classes': ('collapse',)
        }),
        ('Technology', {
            'fields': (
                'has_streaming_service', 'has_phone', 'has_usb_charging', 'has_bluetooth_speaker'
            ),
            'classes': ('collapse',)
        }),
        ('Comfort Features', {
            'fields': (
                'has_coffee_maker', 'has_tea_kettle', 'has_refrigerator', 'has_microwave',
                'has_iron', 'has_ironing_board', 'has_blackout_curtains', 'has_soundproofing'
            ),
            'classes': ('collapse',)
        }),
        ('Child & Extra Bed Policies', {
            'fields': (
                'children_allowed', 'max_children', 'infant_bed_available',
                'extra_bed_available', 'extra_bed_charge'
            ),
            'classes': ('collapse',)
        }),
        ('Accessibility Features', {
            'fields': (
                'is_accessible', 'has_accessible_bathroom', 'has_grab_bars',
                'has_roll_in_shower', 'has_lowered_fixtures', 'has_braille_signage',
                'has_hearing_assistance'
            ),
            'classes': ('collapse',)
        }),
        ('Policies', {
            'fields': (
                'smoking_allowed', 'pets_allowed', 'pet_charge',
                'early_checkin_available', 'early_checkin_charge',
                'late_checkout_available', 'late_checkout_charge',
                'cancellation_policy'
            ),
            'classes': ('collapse',)
        }),
        ('Media', {
            'fields': ('virtual_tour_url', 'featured_image'),
            'classes': ('collapse',)
        }),
        ('Summary', {
            'fields': ('amenities_summary',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [RoomTypeAmenityInline]
    
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
    
    def bed_configuration_display(self, obj):
        """Display bed configuration"""
        return obj.bed_configuration
    bed_configuration_display.short_description = 'Bed Config'
    
    def room_size_display(self, obj):
        """Display room size"""
        return obj.room_size_display
    room_size_display.short_description = 'Room Size'
    
    def amenities_summary(self, obj):
        """Display amenities summary"""
        amenities = obj.amenities_list
        if amenities:
            return format_html('<br>'.join(amenities[:10]))  # Show first 10 amenities
        return 'No amenities'
    amenities_summary.short_description = 'Amenities'


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    """Admin interface for rooms"""
    list_display = [
        'room_number', 'hotel_name', 'room_type_name', 'floor', 'capacity',
        'base_price', 'view_type', 'housekeeping_status', 'condition_status',
        'is_active', 'maintenance_status_display'
    ]
    list_filter = [
        'hotel', 'room_type', 'floor', 'capacity', 'view_type',
        'housekeeping_status', 'condition', 'is_active', 'is_maintenance',
        'needs_maintenance', 'is_corner_room', 'is_connecting_room'
    ]
    search_fields = ['room_number', 'hotel__name', 'room_type__name', 'special_features']
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'display_name', 
        'room_features', 'maintenance_status_info'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'hotel', 'room_number', 'floor', 'room_type', 'display_name')
        }),
        ('Capacity & Pricing', {
            'fields': ('capacity', 'base_price', 'view_type')
        }),
        ('Room Features', {
            'fields': (
                'is_corner_room', 'is_connecting_room', 'connecting_room',
                'special_features', 'room_features'
            )
        }),
        ('Status & Condition', {
            'fields': (
                'is_active', 'condition', 'housekeeping_status',
                'last_cleaned', 'last_inspected'
            )
        }),
        ('Maintenance', {
            'fields': (
                'is_maintenance', 'needs_maintenance', 'maintenance_priority',
                'maintenance_notes', 'maintenance_status_info'
            )
        }),
        ('Renovation History', {
            'fields': ('last_renovated', 'renovation_notes'),
            'classes': ('collapse',)
        }),
        ('Images & Media', {
            'fields': ('room_images',),
            'classes': ('collapse',)
        }),
        ('Staff Notes', {
            'fields': ('staff_notes',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [RoomImageInline]
    
    # Custom actions
    actions = [
        'activate_rooms', 'deactivate_rooms', 'mark_maintenance', 'clear_maintenance',
        'mark_clean', 'mark_dirty', 'mark_inspected'
    ]
    
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
    
    def condition_status(self, obj):
        """Get condition status with color coding"""
        colors = {
            'excellent': 'green',
            'very_good': 'blue',
            'good': 'orange',
            'fair': 'red',
            'needs_renovation': 'darkred'
        }
        color = colors.get(obj.condition, 'black')
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            obj.get_condition_display()
        )
    condition_status.short_description = 'Condition'
    condition_status.admin_order_field = 'condition'
    
    def maintenance_status_display(self, obj):
        """Display maintenance status with color coding"""
        if obj.is_maintenance:
            return format_html('<span style="color: red;">Under Maintenance</span>')
        elif obj.needs_maintenance:
            return format_html('<span style="color: orange;">Needs Maintenance</span>')
        else:
            return format_html('<span style="color: green;">Good</span>')
    maintenance_status_display.short_description = 'Maintenance'
    
    def maintenance_status_info(self, obj):
        """Get detailed maintenance status"""
        status = obj.maintenance_status
        return f"Status: {status['status']}, Priority: {status['priority'] or 'N/A'}"
    maintenance_status_info.short_description = 'Maintenance Info'
    
    # Actions
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
    
    def mark_clean(self, request, queryset):
        """Mark rooms as clean"""
        for room in queryset:
            room.update_housekeeping_status('clean')
        self.message_user(request, f'Successfully marked {queryset.count()} rooms as clean.')
    mark_clean.short_description = 'Mark as clean'
    
    def mark_dirty(self, request, queryset):
        """Mark rooms as dirty"""
        updated = queryset.update(housekeeping_status='dirty')
        self.message_user(request, f'Successfully marked {updated} rooms as dirty.')
    mark_dirty.short_description = 'Mark as dirty'
    
    def mark_inspected(self, request, queryset):
        """Mark rooms as inspected"""
        updated = queryset.update(housekeeping_status='inspected')
        self.message_user(request, f'Successfully marked {updated} rooms as inspected.')
    mark_inspected.short_description = 'Mark as inspected'


@admin.register(RoomImage)
class RoomImageAdmin(admin.ModelAdmin):
    """Admin interface for room images"""
    list_display = [
        'room_display', 'image_type', 'is_primary', 'display_order', 'is_active'
    ]
    list_filter = ['image_type', 'is_primary', 'is_active', 'room__hotel']
    search_fields = ['room__room_number', 'room__hotel__name', 'caption', 'image_alt_text']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'room', 'room_type', 'image', 'image_alt_text', 'caption')
        }),
        ('Display Settings', {
            'fields': ('image_type', 'is_primary', 'display_order', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def room_display(self, obj):
        """Display room information"""
        if obj.room:
            return f"{obj.room.hotel.name} - Room {obj.room.room_number}"
        elif obj.room_type:
            return f"Room Type: {obj.room_type.name}"
        return "No room assigned"
    room_display.short_description = 'Room/Type'


@admin.register(RoomAmenity)
class RoomAmenityAdmin(admin.ModelAdmin):
    """Admin interface for room amenities"""
    list_display = ['name', 'category', 'is_premium', 'icon_class']
    list_filter = ['category', 'is_premium']
    search_fields = ['name', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'name', 'description', 'category')
        }),
        ('Display', {
            'fields': ('icon_class', 'is_premium')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
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


# Manager admin removed — use only the default admin site (admin.site)

# Restrict the default admin site to superusers only so manager staff cannot access it
def _admin_site_has_permission(request):
    user = getattr(request, 'user', None)
    return bool(user and user.is_authenticated and user.is_active and getattr(user, 'is_superuser', False))

# Patch the default admin.site permission check
admin.site.has_permission = _admin_site_has_permission

# Make admin logout redirect to API root for both admin sites
from django.contrib.auth import logout as auth_logout
from django.shortcuts import redirect

def _admin_logout_view(request, extra_context=None):
    """Logout the user and redirect to API root."""
    # perform django logout
    auth_logout(request)
    return redirect('/api/v1/')

# Assign the logout handler to both admin sites. Django resolves the view from the
# AdminSite instance, so assigning a callable that accepts (request, extra_context=None)
# will be used when admin logout URL is invoked.
admin.site.logout = _admin_logout_view

# Improve default admin index behavior: if a logged-in user lacks permission (e.g., a manager
# account), show a helpful 403 page with a logout link instead of a 404 which is confusing.
from django.http import HttpResponse
from django.utils.safestring import mark_safe

def _default_admin_index(request, extra_context=None):
    # If allowed, render normal admin index
    if admin.site.has_permission(request):
        return admin.site._orig_index(request, extra_context=extra_context) if hasattr(admin.site, '_orig_index') else admin.site.index(request, extra_context=extra_context)

    # Not allowed: if not authenticated, show login
    if not getattr(request, 'user', None) or not request.user.is_authenticated:
        return admin.site.login(request, extra_context=extra_context)

    # Authenticated but lacks permission -> show message with logout link
    logout_url = reverse(f'{admin.site.name}:logout')
    body = (
        f"<h1>Access denied</h1>"
        f"<p>You are signed in as <strong>{request.user}</strong> but do not have access to this admin panel.</p>"
        f"<p><a href='{logout_url}'>Click here to log out</a> and sign in with a different account.</p>"
    )
    return HttpResponse(mark_safe(body), status=403)

# Backup original index if present then patch
if hasattr(admin.site, 'index'):
    admin.site._orig_index = admin.site.index
admin.site.index = _default_admin_index