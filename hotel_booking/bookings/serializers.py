# Django REST Framework imports
from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from decimal import Decimal

# Local imports
from .models import Booking, BookingExtra, BookingGuest, BookingHistory
from core.models import Room, Extra, Hotel, RoomType
from core.services import (
    BookingValidationService, 
    PricingService, 
    RoomAvailabilityService
)


class RoomTypeSerializer(serializers.ModelSerializer):
    """Serializer for room type information"""
    amenities = serializers.SerializerMethodField()
    
    class Meta:
        model = RoomType
        fields = [
            'id', 'name', 'description', 'max_capacity', 'bed_type', 'bed_count',
            'bathroom_count', 'room_size_sqm', 'amenities', 'is_accessible'
        ]
    
    def get_amenities(self, obj):
        return obj.amenities_list


class RoomSerializer(serializers.ModelSerializer):
    """Serializer for room information"""
    room_type = RoomTypeSerializer(read_only=True)
    price_for_dates = serializers.SerializerMethodField()
    
    class Meta:
        model = Room
        fields = [
            'id', 'room_number', 'floor', 'capacity', 'base_price', 
            'view_type', 'room_type', 'price_for_dates'
        ]
    
    def get_price_for_dates(self, obj):
        """Get price for specific dates if provided in context"""
        request = self.context.get('request')
        if request and hasattr(request, 'query_params'):
            check_in = request.query_params.get('check_in')
            check_out = request.query_params.get('check_out')
            
            if check_in and check_out:
                try:
                    from datetime import datetime
                    check_in_date = datetime.strptime(check_in, '%Y-%m-%d').date()
                    check_out_date = datetime.strptime(check_out, '%Y-%m-%d').date()
                    return PricingService.calculate_room_price(obj, check_in_date, check_out_date)
                except (ValueError, DjangoValidationError):
                    pass
        
        return None


class ExtraSerializer(serializers.ModelSerializer):
    """Serializer for extra services"""
    
    class Meta:
        model = Extra
        fields = [
            'id', 'name', 'description', 'price', 'pricing_type', 
            'category', 'max_quantity'
        ]


class BookingExtraSerializer(serializers.ModelSerializer):
    """Serializer for booking extras"""
    extra = ExtraSerializer(read_only=True)
    extra_id = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = BookingExtra
        fields = [
            'id', 'extra', 'extra_id', 'quantity', 'unit_price', 'total_price'
        ]
        read_only_fields = ['unit_price', 'total_price']


class BookingGuestSerializer(serializers.ModelSerializer):
    """Serializer for additional booking guests"""
    
    class Meta:
        model = BookingGuest
        fields = ['id', 'first_name', 'last_name', 'age_group']


class BookingHistorySerializer(serializers.ModelSerializer):
    """Serializer for booking history"""
    performed_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = BookingHistory
        fields = [
            'id', 'action', 'description', 'performed_by_name', 'timestamp',
            'old_values', 'new_values'
        ]
    
    def get_performed_by_name(self, obj):
        if obj.performed_by:
            return obj.performed_by.get_full_name() or obj.performed_by.username
        return 'System'


class BookingDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for booking with all related information"""
    room = RoomSerializer(read_only=True)
    booking_extras = BookingExtraSerializer(many=True, read_only=True)
    additional_guests = BookingGuestSerializer(many=True, read_only=True)
    history = BookingHistorySerializer(many=True, read_only=True)
    
    # Computed fields
    nights = serializers.SerializerMethodField()
    can_cancel = serializers.SerializerMethodField()
    can_check_in = serializers.SerializerMethodField()
    can_check_out = serializers.SerializerMethodField()
    
    class Meta:
        model = Booking
        fields = [
            'id', 'booking_reference', 'status', 'payment_status',
            'check_in', 'check_out', 'nights', 'guests',
            'room', 'booking_extras', 'additional_guests',
            'room_price', 'extras_price', 'tax_amount', 'total_price',
            'primary_guest_name', 'primary_guest_email', 'primary_guest_phone',
            'special_requests', 'booking_date', 'confirmation_date',
            'check_in_time', 'check_out_time', 'booking_source',
            'can_cancel', 'can_check_in', 'can_check_out', 'history'
        ]
    
    def get_nights(self, obj):
        return obj.nights
    
    def get_can_cancel(self, obj):
        return obj.can_be_cancelled
    
    def get_can_check_in(self, obj):
        return obj.can_check_in
    
    def get_can_check_out(self, obj):
        return obj.can_check_out


class BookingListSerializer(serializers.ModelSerializer):
    """Simplified serializer for booking lists"""
    room_info = serializers.SerializerMethodField()
    hotel_name = serializers.SerializerMethodField()
    nights = serializers.SerializerMethodField()
    
    class Meta:
        model = Booking
        fields = [
            'id', 'booking_reference', 'status', 'payment_status',
            'check_in', 'check_out', 'nights', 'guests',
            'room_info', 'hotel_name', 'total_price',
            'primary_guest_name', 'booking_date'
        ]
    
    def get_room_info(self, obj):
        return {
            'room_number': obj.room.room_number,
            'room_type': obj.room.room_type.name,
            'capacity': obj.room.capacity
        }
    
    def get_hotel_name(self, obj):
        return obj.room.hotel.name
    
    def get_nights(self, obj):
        return obj.nights


class BookingCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new bookings"""
    room_id = serializers.UUIDField(write_only=True)
    extras_data = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        required=False,
        allow_empty=True
    )
    additional_guests_data = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        required=False,
        allow_empty=True
    )
    
    # Price breakdown (read-only)
    price_breakdown = serializers.SerializerMethodField()
    
    class Meta:
        model = Booking
        fields = [
            'room_id', 'check_in', 'check_out', 'guests',
            'primary_guest_name', 'primary_guest_email', 'primary_guest_phone',
            'special_requests', 'extras_data', 'additional_guests_data',
            'price_breakdown'
        ]
        extra_kwargs = {
            'primary_guest_name': {'required': False},
            'primary_guest_email': {'required': False},
            'primary_guest_phone': {'required': False},
        }
    
    def get_price_breakdown(self, obj):
        """Get detailed price breakdown"""
        if hasattr(obj, 'id'):  # Only for existing objects
            return obj.calculate_total_price()
        return None
    
    def validate(self, attrs):
        """Validate booking data"""
        # Get room
        try:
            room = Room.objects.get(id=attrs['room_id'])
        except Room.DoesNotExist:
            raise serializers.ValidationError("Room not found")
        
        check_in = attrs['check_in']
        check_out = attrs['check_out']
        guests = attrs['guests']
        
        # Validate dates
        is_valid, message = BookingValidationService.validate_booking_dates(check_in, check_out)
        if not is_valid:
            raise serializers.ValidationError({'check_in': message})
        
        # Validate guest count
        is_valid, message = BookingValidationService.validate_guest_count(guests, room)
        if not is_valid:
            raise serializers.ValidationError({'guests': message})
        
        # Validate room availability
        is_valid, message = BookingValidationService.validate_room_availability(room, check_in, check_out)
        if not is_valid:
            raise serializers.ValidationError({'room_id': message})
        
        # Validate extras
        extras_data = attrs.get('extras_data', [])
        if extras_data:
            is_valid, message, validated_extras = BookingValidationService.validate_extras(
                extras_data, room.hotel
            )
            if not is_valid:
                raise serializers.ValidationError({'extras_data': message})
            attrs['validated_extras'] = validated_extras
        
        attrs['room'] = room
        return attrs
    
    def create(self, validated_data):
        """Create booking with all related objects"""
        # Extract nested data
        room = validated_data.pop('room')
        validated_data.pop('room_id')
        extras_data = validated_data.pop('extras_data', [])
        additional_guests_data = validated_data.pop('additional_guests_data', [])
        validated_extras = validated_data.pop('validated_extras', [])
        
        # Set user from request
        user = self.context['request'].user
        validated_data['user'] = user
        validated_data['room'] = room
        
        # Calculate pricing
        pricing_data = PricingService.calculate_booking_total(
            room=room,
            check_in=validated_data['check_in'],
            check_out=validated_data['check_out'],
            extras=validated_extras,
            extra_quantities={str(extra.id): 1 for extra in validated_extras},  # Default quantity
            guests=validated_data['guests']
        )
        
        # Set calculated prices
        validated_data.update({
            'room_price': pricing_data['room_price'],
            'extras_price': pricing_data['extras_price'],
            'tax_amount': pricing_data['tax_amount'],
            'total_price': pricing_data['total_price'],
        })
        
        # Create booking
        booking = Booking.objects.create(**validated_data)
        
        # Create booking extras
        for extra_data in extras_data:
            try:
                extra = Extra.objects.get(
                    id=extra_data['extra_id'], 
                    hotel=room.hotel, 
                    is_active=True
                )
                BookingExtra.objects.create(
                    booking=booking,
                    extra=extra,
                    quantity=extra_data.get('quantity', 1)
                )
            except Extra.DoesNotExist:
                continue
        
        # Create additional guests
        for guest_data in additional_guests_data:
            BookingGuest.objects.create(
                booking=booking,
                **guest_data
            )
        
        # Create booking history entry
        BookingHistory.objects.create(
            booking=booking,
            action='created',
            description=f'Booking created for {booking.nights} nights',
            performed_by=user
        )
        
        # Auto-confirm booking (or set to pending based on payment method)
        booking.confirm_booking()
        
        return booking


class BookingUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating booking details"""
    
    class Meta:
        model = Booking
        fields = [
            'primary_guest_name', 'primary_guest_email', 'primary_guest_phone',
            'special_requests'
        ]
    
    def update(self, instance, validated_data):
        """Update booking and create history entry"""
        old_values = {
            field: getattr(instance, field) 
            for field in validated_data.keys()
        }
        
        # Update booking
        booking = super().update(instance, validated_data)
        
        # Create history entry
        BookingHistory.objects.create(
            booking=booking,
            action='modified',
            description='Booking details updated',
            performed_by=self.context['request'].user,
            old_values=old_values,
            new_values=validated_data
        )
        
        return booking


class RoomAvailabilitySerializer(serializers.Serializer):
    """Serializer for room availability search"""
    check_in = serializers.DateField()
    check_out = serializers.DateField()
    guests = serializers.IntegerField(min_value=1, max_value=10)
    hotel_id = serializers.UUIDField(required=False)
    room_type_id = serializers.UUIDField(required=False)
    max_price = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        required=False,
        min_value=Decimal('0.01')
    )
    
    def validate(self, attrs):
        """Validate search parameters"""
        check_in = attrs['check_in']
        check_out = attrs['check_out']
        
        # Validate dates
        is_valid, message = BookingValidationService.validate_booking_dates(check_in, check_out)
        if not is_valid:
            raise serializers.ValidationError({'check_in': message})
        
        return attrs


class BookingCancellationSerializer(serializers.Serializer):
    """Serializer for booking cancellation"""
    reason = serializers.ChoiceField(
        choices=Booking.CANCELLATION_REASON_CHOICES,
        default='guest_request'
    )
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, attrs):
        """Validate cancellation request"""
        booking = self.context['booking']
        
        if not booking.can_be_cancelled:
            raise serializers.ValidationError(
                'This booking cannot be cancelled. Please check the cancellation policy.'
            )
        
        return attrs
