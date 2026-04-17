from rest_framework import serializers
from django.utils import timezone
from decimal import Decimal
from .models import Booking, BookingAuditLog
from core.models import Hotel, Room


class BookingSerializer(serializers.ModelSerializer):
    """
    Complete booking serializer for read operations with all details
    """
    
    # Read-only computed fields
    booking_id = serializers.CharField(read_only=True)
    nights = serializers.IntegerField(read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    # Method fields for calculated values
    guest_full_name = serializers.SerializerMethodField()
    guest_address_formatted = serializers.SerializerMethodField()
    total_guests = serializers.SerializerMethodField()
    can_be_cancelled = serializers.SerializerMethodField()
    tax_percentage = serializers.SerializerMethodField()
    discount_percentage = serializers.SerializerMethodField()
    
    # Hotel and room details (read-only nested)
    hotel_name = serializers.CharField(source='hotel.name', read_only=True)
    hotel_city = serializers.CharField(source='hotel.city', read_only=True)
    hotel_address = serializers.CharField(source='hotel.address', read_only=True)
    room_number = serializers.CharField(source='room.room_number', read_only=True)
    room_type = serializers.CharField(source='room.room_type.name', read_only=True)
    room_max_occupancy = serializers.IntegerField(source='room.capacity', read_only=True)
    
    # User details (if associated)
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    # Format timestamps
    created_at = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M:%S')
    updated_at = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M:%S')
    
    class Meta:
        model = Booking
        fields = [
            # Basic info
            'id', 'booking_id', 'status', 'payment_status',
            
            # Guest information
            'guest_first_name', 'guest_last_name', 'guest_full_name',
            'guest_email', 'guest_phone', 'guest_passport_number',
            
            # Address information
            'guest_country', 'guest_address', 'guest_city', 'guest_postal_code',
            'guest_address_formatted',
            
            # Hotel and room details
            'hotel', 'hotel_name', 'hotel_city', 'hotel_address',
            'room', 'room_number', 'room_type', 'room_max_occupancy',
            
            # Date and time information
            'check_in_date', 'check_out_date', 'check_in_time', 'check_out_time', 'nights',
            
            # Guest count
            'adults', 'children', 'total_guests',
            
            # Pricing breakdown
            'room_rate', 'subtotal', 'tax_amount', 'discount_amount', 'discount_type',
            'total_amount', 'tax_percentage', 'discount_percentage',
            
            # Additional info
            'special_requests', 'can_be_cancelled',
            
            # User association
            'user', 'user_username',
            
            # Timestamps
            'created_at', 'updated_at'
        ]
    
    def get_guest_full_name(self, obj):
        return obj.guest_full_name()
    
    def get_guest_address_formatted(self, obj):
        return obj.guest_address_formatted()
    
    def get_total_guests(self, obj):
        return obj.total_guests()
    
    def get_can_be_cancelled(self, obj):
        return obj.can_be_cancelled()
    
    def get_tax_percentage(self, obj):
        return obj.tax_percentage()
    
    def get_discount_percentage(self, obj):
        return obj.discount_percentage()


class BookingCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new bookings with full validation
    """
    
    # Make computed fields read-only
    booking_id = serializers.CharField(read_only=True)
    nights = serializers.IntegerField(read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = Booking
        fields = [
            # Guest information (required)
            'guest_first_name', 'guest_last_name', 'guest_email', 'guest_phone',
            
            # Address information (required)
            'guest_country', 'guest_address', 'guest_city', 'guest_postal_code',
            
            # Optional passport
            'guest_passport_number',
            
            # Booking details (required)
            'hotel', 'room', 'check_in_date', 'check_out_date',
            'check_in_time', 'check_out_time',
            
            # Guest count (required)
            'adults', 'children',
            
            # Pricing (required)
            'room_rate', 'tax_amount', 'discount_amount', 'discount_type',
            
            # Optional
            'special_requests',
            
            # Read-only computed fields
            'booking_id', 'nights', 'subtotal', 'total_amount'
        ]
        extra_kwargs = {
            'guest_first_name': {'required': True},
            'guest_last_name': {'required': True},
            'guest_email': {'required': True},
            'guest_phone': {'required': True},
            'guest_country': {'required': True},
            'guest_address': {'required': True},
            'guest_city': {'required': True},
            'guest_postal_code': {'required': True},
            'hotel': {'required': True},
            'room': {'required': True},
            'check_in_date': {'required': True},
            'check_out_date': {'required': True},
            'room_rate': {'required': True},
        }
    
    def validate(self, data):
        """
        Comprehensive validation for booking data
        """
        errors = {}
        
        # Validate dates
        check_in = data.get('check_in_date')
        check_out = data.get('check_out_date')
        
        if check_in and check_out:
            if check_in >= check_out:
                errors['check_out_date'] = 'Check-out date must be after check-in date'
            
            if check_in < timezone.now().date():
                errors['check_in_date'] = 'Check-in date cannot be in the past'
            
            # Check if dates are too far in the future (optional business rule)
            max_advance_days = 365
            if (check_in - timezone.now().date()).days > max_advance_days:
                errors['check_in_date'] = f'Cannot book more than {max_advance_days} days in advance'
        
        # Validate room capacity
        room = data.get('room')
        adults = data.get('adults', 1)
        children = data.get('children', 0)
        total_guests = adults + children
        
        if room and total_guests > room.capacity:
            errors['adults'] = f'Total guests ({total_guests}) exceed room capacity ({room.capacity})'
        
        # Validate hotel and room relationship
        hotel = data.get('hotel')
        if hotel and room and room.hotel != hotel:
            errors['room'] = 'Selected room does not belong to the selected hotel'
        
        # Validate pricing
        room_rate = data.get('room_rate')
        tax_amount = data.get('tax_amount', 0)
        discount_amount = data.get('discount_amount', 0)
        
        if room_rate and room_rate <= 0:
            errors['room_rate'] = 'Room rate must be greater than 0'
        
        if tax_amount and tax_amount < 0:
            errors['tax_amount'] = 'Tax amount cannot be negative'
        
        if discount_amount and discount_amount < 0:
            errors['discount_amount'] = 'Discount amount cannot be negative'
        
        # Validate discount doesn't exceed subtotal
        if room_rate and check_in and check_out:
            nights = (check_out - check_in).days
            subtotal = room_rate * nights
            if discount_amount and discount_amount > subtotal:
                errors['discount_amount'] = 'Discount amount cannot exceed subtotal'
        
        # Validate email format (additional check)
        email = data.get('guest_email')
        if email and '@' not in email:
            errors['guest_email'] = 'Please enter a valid email address'
        
        # Validate phone number (basic check)
        phone = data.get('guest_phone')
        if phone and len(phone.replace('+', '').replace('-', '').replace(' ', '')) < 7:
            errors['guest_phone'] = 'Please enter a valid phone number'
        
        if errors:
            raise serializers.ValidationError(errors)
        
        return data
    
    def create(self, validated_data):
        """
        Create a new booking with proper user association
        """
        # Associate with logged-in user if available
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['user'] = request.user
        
        # The model's save method will handle booking_id generation and calculations
        return Booking.objects.create(**validated_data)


class BookingUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating existing bookings (limited fields for safety)
    """
    
    class Meta:
        model = Booking
        fields = [
            # Guest information (updatable)
            'guest_first_name', 'guest_last_name', 'guest_email', 'guest_phone',
            'guest_country', 'guest_address', 'guest_city', 'guest_postal_code',
            'guest_passport_number',
            
            # Guest count (updatable if room allows)
            'adults', 'children',
            
            # Times (updatable)
            'check_in_time', 'check_out_time',
            
            # Status updates
            'status', 'payment_status',
            
            # Notes
            'special_requests',
        ]
    
    def validate_status(self, value):
        """
        Validate status changes based on current status
        """
        instance = self.instance
        
        if not instance:
            return value
        
        # Don't allow changes to completed or cancelled bookings
        if instance.status in ['completed', 'cancelled']:
            if value != instance.status:
                raise serializers.ValidationError(
                    f'Cannot change status of {instance.get_status_display()} booking'
                )
        
        # Only allow specific status transitions
        valid_transitions = {
            'pending': ['confirmed', 'cancelled'],
            'confirmed': ['completed', 'cancelled'],
            'cancelled': [],  # No transitions from cancelled
            'completed': []   # No transitions from completed
        }
        
        if instance.status not in valid_transitions:
            raise serializers.ValidationError(f'Invalid current status: {instance.status}')
        
        if value not in valid_transitions[instance.status] and value != instance.status:
            raise serializers.ValidationError(
                f'Cannot change status from {instance.get_status_display()} to {dict(Booking.STATUS_CHOICES)[value]}'
            )
        
        return value
    
    def validate(self, data):
        """
        Validate update data
        """
        instance = self.instance
        errors = {}
        
        # Validate room capacity if guest count changes
        adults = data.get('adults', instance.adults if instance else 1)
        children = data.get('children', instance.children if instance else 0)
        total_guests = adults + children
        
        if instance and instance.room and total_guests > instance.room.capacity:
            errors['adults'] = f'Total guests ({total_guests}) exceed room capacity ({instance.room.capacity})'
        
        # Don't allow updates to completed or cancelled bookings (except status)
        if instance and instance.status in ['completed', 'cancelled']:
            restricted_fields = set(data.keys()) - {'status', 'special_requests'}
            if restricted_fields:
                errors['non_field_errors'] = f'Cannot update {instance.get_status_display()} booking except status and special requests'
        
        # Validate email if provided
        email = data.get('guest_email')
        if email and '@' not in email:
            errors['guest_email'] = 'Please enter a valid email address'
        
        if errors:
            raise serializers.ValidationError(errors)
        
        return data


class BookingListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for listing bookings (optimized for performance)
    """
    
    guest_full_name = serializers.SerializerMethodField()
    hotel_name = serializers.CharField(source='hotel.name', read_only=True)
    room_number = serializers.CharField(source='room.room_number', read_only=True)
    room_type = serializers.CharField(source='room.room_type.name', read_only=True)
    nights = serializers.IntegerField(read_only=True)
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total_guests = serializers.SerializerMethodField()
    can_be_cancelled = serializers.SerializerMethodField()
    
    class Meta:
        model = Booking
        fields = [
            'id', 'booking_id', 'guest_full_name', 'guest_email', 'guest_phone',
            'hotel_name', 'room_number', 'room_type',
            'check_in_date', 'check_out_date', 'nights',
            'total_guests', 'total_amount', 'status', 'payment_status',
            'can_be_cancelled', 'created_at'
        ]
    
    def get_guest_full_name(self, obj):
        return obj.guest_full_name()
    
    def get_total_guests(self, obj):
        return obj.total_guests()
    
    def get_can_be_cancelled(self, obj):
        return obj.can_be_cancelled()


class BookingQuickSerializer(serializers.ModelSerializer):
    """
    Minimal serializer for quick responses (e.g., after creation)
    """
    
    guest_full_name = serializers.SerializerMethodField()
    hotel_name = serializers.CharField(source='hotel.name', read_only=True)
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = Booking
        fields = [
            'id', 'booking_id', 'guest_full_name', 'hotel_name',
            'check_in_date', 'check_out_date', 'total_amount',
            'status', 'payment_status', 'created_at'
        ]
    
    def get_guest_full_name(self, obj):
        return obj.guest_full_name()


class BookingAuditLogSerializer(serializers.ModelSerializer):
    """
    Serializer for booking audit logs (compliance and dispute resolution)
    """
    
    changed_by_username = serializers.CharField(source='changed_by.username', read_only=True, allow_null=True)
    changed_by_email = serializers.CharField(source='changed_by.email', read_only=True, allow_null=True)
    change_type_display = serializers.CharField(source='get_change_type_display', read_only=True)
    
    class Meta:
        model = BookingAuditLog
        fields = [
            'id', 'booking', 'change_type', 'change_type_display',
            'old_value', 'new_value', 'reason',
            'changed_by', 'changed_by_username', 'changed_by_email',
            'ip_address', 'changed_at'
        ]
        read_only_fields = [
            'id', 'booking', 'change_type', 'change_type_display',
            'old_value', 'new_value', 'reason',
            'changed_by', 'changed_by_username', 'changed_by_email',
            'ip_address', 'changed_at'
        ]
