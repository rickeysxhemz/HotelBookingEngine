# Django imports
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

# Local imports
from .models import Offer, OfferCategory, OfferHighlight, OfferImage


class OfferHighlightInline(admin.TabularInline):
    """Inline admin for offer highlights"""
    model = OfferHighlight
    extra = 1
    fields = ('title', 'description', 'order')
    ordering = ('order',)


class OfferImageInline(admin.TabularInline):
    """Inline admin for offer images"""
    model = OfferImage
    extra = 1
    fields = ('image', 'alt_text', 'caption', 'is_primary', 'order', 'image_preview')
    readonly_fields = ('image_preview',)
    ordering = ('order',)
    
    def image_preview(self, obj):
        """Display image preview in admin"""
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 100px; max-height: 100px;" />',
                obj.image.url
            )
        return "No image"
    image_preview.short_description = "Preview"


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    """Admin interface for offers"""
    
    list_display = [
        'name', 'hotel', 'category', 'offer_type', 'discount_display', 
        'valid_from', 'valid_to', 'is_active', 'is_featured',
        'is_valid_status', 'bookings_used', 'created_at'
    ]
    list_filter = [
        'category', 'offer_type', 'discount_type', 'is_active', 'is_featured',
        'is_combinable', 'hotel', 'valid_from', 'valid_to', 'created_at'
    ]
    search_fields = [
        'name', 'description', 'hotel__name', 'category__name', 'slug'
    ]
    prepopulated_fields = {'slug': ('name',)}
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description', 'short_description', 'category', 'hotel')
        }),
        ('Offer Details', {
            'fields': (
                'offer_type', 'discount_type', 
                'discount_percentage', 'discount_amount', 'package_price'
            )
        }),
        ('Validity Period', {
            'fields': ('valid_from', 'valid_to')
        }),
        ('Booking Requirements', {
            'fields': (
                'minimum_stay', 'maximum_stay',
                'minimum_advance_booking', 'maximum_advance_booking'
            )
        }),

        ('Availability Limits', {
            'fields': ('total_bookings_limit', 'bookings_used')
        }),
        ('Day Restrictions', {
            'fields': (
                'applies_monday', 'applies_tuesday', 'applies_wednesday',
                'applies_thursday', 'applies_friday', 'applies_saturday', 'applies_sunday'
            ),
            'classes': ('collapse',)
        }),
        ('Status & Features', {
            'fields': ('is_active', 'is_featured', 'is_combinable')
        }),
        ('Terms & Conditions', {
            'fields': ('terms_and_conditions',),
            'classes': ('collapse',)
        }),
    )
    

    readonly_fields = ('bookings_used',)
    
    inlines = [OfferHighlightInline, OfferImageInline]
    
    def is_valid_status(self, obj):
        """Display offer validity status with color coding"""
        if obj.is_valid:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Valid</span>'
            )
        else:
            return format_html(
                '<span style="color: red; font-weight: bold;">✗ Invalid</span>'
            )
    is_valid_status.short_description = "Status"
    is_valid_status.admin_order_field = 'valid_from'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('hotel')
    
    def save_model(self, request, obj, form, change):
        """Custom save logic"""
        super().save_model(request, obj, form, change)
        
        # If this is a featured offer, we might want to limit total featured offers
        if obj.is_featured:
            featured_count = Offer.objects.filter(
                hotel=obj.hotel, 
                is_featured=True, 
                is_active=True
            ).count()
            
            if featured_count > 5:  # Limit to 5 featured offers per hotel
                self.message_user(
                    request,
                    f"Warning: Hotel now has {featured_count} featured offers. "
                    "Consider limiting featured offers for better user experience.",
                    level='WARNING'
                )
    
    actions = ['make_active', 'make_inactive', 'make_featured', 'remove_featured']
    
    def make_active(self, request, queryset):
        """Bulk action to activate offers"""
        count = queryset.update(is_active=True)
        self.message_user(
            request, 
            f"{count} offers were successfully activated."
        )
    make_active.short_description = "Activate selected offers"
    
    def make_inactive(self, request, queryset):
        """Bulk action to deactivate offers"""
        count = queryset.update(is_active=False)
        self.message_user(
            request, 
            f"{count} offers were successfully deactivated."
        )
    make_inactive.short_description = "Deactivate selected offers"
    
    def make_featured(self, request, queryset):
        """Bulk action to make offers featured"""
        count = queryset.update(is_featured=True)
        self.message_user(
            request, 
            f"{count} offers were successfully marked as featured."
        )
    make_featured.short_description = "Mark as featured"
    
    def remove_featured(self, request, queryset):
        """Bulk action to remove featured status"""
        count = queryset.update(is_featured=False)
        self.message_user(
            request, 
            f"{count} offers were successfully removed from featured."
        )
    remove_featured.short_description = "Remove featured status"


@admin.register(OfferHighlight)
class OfferHighlightAdmin(admin.ModelAdmin):
    """Admin interface for offer highlights"""
    
    list_display = ['title', 'offer', 'order', 'created_at']
    list_filter = ['offer__hotel', 'created_at']
    search_fields = ['title', 'description', 'offer__name']
    list_editable = ['order']
    ordering = ['offer', 'order']
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('offer', 'offer__hotel')


@admin.register(OfferImage)
class OfferImageAdmin(admin.ModelAdmin):
    """Admin interface for offer images"""
    
    list_display = ['offer', 'image_preview', 'alt_text', 'is_primary', 'order', 'created_at']
    list_filter = ['is_primary', 'offer__hotel', 'created_at']
    search_fields = ['alt_text', 'caption', 'offer__name']
    list_editable = ['is_primary', 'order']
    ordering = ['offer', 'order']
    
    def image_preview(self, obj):
        """Display image preview in admin list"""
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 50px; max-height: 50px;" />',
                obj.image.url
            )
        return "No image"
    image_preview.short_description = "Preview"
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('offer', 'offer__hotel')


@admin.register(OfferCategory)
class OfferCategoryAdmin(admin.ModelAdmin):
    """Admin interface for offer categories"""
    
    list_display = ['name', 'slug', 'color_preview', 'order', 'is_active', 'offer_count', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description', 'slug']
    list_editable = ['order', 'is_active']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['order', 'name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description')
        }),
        ('Display Settings', {
            'fields': ('color', 'order')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )
    
    def color_preview(self, obj):
        """Display color preview in admin"""
        if obj.color:
            return format_html(
                '<div style="width: 20px; height: 20px; background-color: {}; border-radius: 50%; display: inline-block;"></div> {}',
                obj.color,
                obj.color
            )
        return "No color"
    color_preview.short_description = "Color"
    
    def offer_count(self, obj):
        """Display number of offers in this category"""
        return obj.offer_count
    offer_count.short_description = "Offers"
    
    actions = ['make_active', 'make_inactive']
    
    def make_active(self, request, queryset):
        """Bulk action to activate categories"""
        count = queryset.update(is_active=True)
        self.message_user(
            request, 
            f"{count} categories were successfully activated."
        )
    make_active.short_description = "Activate selected categories"
    
    def make_inactive(self, request, queryset):
        """Bulk action to deactivate categories"""
        count = queryset.update(is_active=False)
        self.message_user(
            request, 
            f"{count} categories were successfully deactivated."
        )
    make_inactive.short_description = "Deactivate selected categories"
