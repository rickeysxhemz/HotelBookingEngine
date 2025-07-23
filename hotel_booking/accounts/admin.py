# Django imports
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html

# Local imports
from .models import CustomUser, UserProfile, EmailVerificationToken, PasswordResetToken, BlacklistedToken


class UserProfileInline(admin.StackedInline):
    """Inline admin for user profile"""
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile Information'
    fields = ('emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relationship',
              'preferred_room_type', 'dietary_restrictions', 'accessibility_needs', 'special_requests',
              'total_bookings', 'total_spent')


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Custom user admin"""
    inlines = [UserProfileInline]
    list_display = ['email', 'username', 'get_full_name', 'user_type', 'is_active', 'is_verified', 'date_joined']
    list_filter = ['user_type', 'is_active', 'is_staff', 'is_verified', 'gender', 'date_joined']
    search_fields = ['email', 'username', 'first_name', 'last_name', 'phone_number']
    ordering = ['-date_joined']
    readonly_fields = ['id', 'date_joined', 'last_updated', 'last_login', 'failed_login_attempts', 'last_login_ip']

    fieldsets = (
        ('Authentication', {'fields': ('id', 'email', 'username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'date_of_birth', 'gender', 'phone_number', 'profile_picture', 'bio')}),
        ('Address', {'fields': ('address_line_1', 'address_line_2', 'city', 'state', 'postal_code', 'country'), 'classes': ['collapse']}),
        ('Permissions', {'fields': ('user_type', 'is_active', 'is_staff', 'is_superuser', 'is_verified', 'groups', 'user_permissions')}),
        ('Security', {'fields': ('last_login', 'last_login_ip', 'failed_login_attempts', 'date_joined', 'last_updated'), 'classes': ['collapse']}),
    )

    add_fieldsets = (
        ('Create User', {
            'classes': ['wide'],
            'fields': ['email', 'username', 'password1', 'password2', 'first_name', 'last_name', 'user_type']
        }),
    )

    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = 'Full Name'


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """User profile admin"""
    list_display = ['user', 'total_bookings', 'total_spent', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'emergency_contact_name']
    readonly_fields = ['created_at', 'updated_at']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(EmailVerificationToken)
class EmailVerificationTokenAdmin(admin.ModelAdmin):
    """Email verification token admin"""
    list_display = ['user', 'token', 'created_at', 'expires_at', 'used', 'is_expired_display']
    list_filter = ['used', 'created_at', 'expires_at']
    search_fields = ['user__email', 'user__username']
    readonly_fields = ['token', 'created_at', 'is_expired_display']

    def is_expired_display(self, obj):
        return obj.is_expired()
    is_expired_display.short_description = 'Expired'
    is_expired_display.boolean = True


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    """Password reset token admin"""
    list_display = ['user', 'token', 'created_at', 'expires_at', 'used', 'is_expired_display']
    list_filter = ['used', 'created_at', 'expires_at']
    search_fields = ['user__email', 'user__username']
    readonly_fields = ['token', 'created_at', 'is_expired_display']

    def is_expired_display(self, obj):
        return obj.is_expired()
    is_expired_display.short_description = 'Expired'
    is_expired_display.boolean = True


@admin.register(BlacklistedToken)
class BlacklistedTokenAdmin(admin.ModelAdmin):
    """Blacklisted token admin"""
    list_display = ['jti_display', 'user', 'token_type', 'blacklisted_at', 'reason']
    list_filter = ['token_type', 'reason', 'blacklisted_at']
    search_fields = ['jti', 'user__email', 'user__username']
    readonly_fields = ['jti', 'blacklisted_at']
    ordering = ['-blacklisted_at']

    def jti_display(self, obj):
        return f"{obj.jti[:8]}...{obj.jti[-8:]}" if len(obj.jti) > 16 else obj.jti
    jti_display.short_description = 'JTI'


# Customize admin site headers
admin.site.site_header = "Hotel Booking Engine Administration"
admin.site.site_title = "Hotel Admin"
admin.site.index_title = "Welcome to Hotel Booking Administration"
