# Django REST Framework imports
from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from decimal import Decimal
from datetime import datetime, date

# Local imports
from .models import Booking, BookingExtra, BookingGuest, BookingHistory
from core.models import Room, Extra, Hotel, RoomType
from core.services import (
    BookingValidationService, 
    PricingService, 
    RoomAvailabilityService
)


class CompleteBookingFlowSerializer(serializers.Serializer):
    """Serializer for complete booking flow API"""
    
    # Search criteria
    hotel_id = serializers.UUIDField(
        required=False, 
        allow_null=True,
        help_text="(Optional) Hotel ID to search in. If not provided, will search across all hotels in the location or all available hotels."
    )
    location = serializers.CharField(
        required=False, 
        allow_blank=True,
        help_text="(Optional) City or location to search for hotels. If hotel_id is provided, this field is ignored. If neither hotel_id nor location is provided, searches all hotels."
    )
    check_in = serializers.DateField(
        help_text="Check-in date in YYYY-MM-DD format. Must be today or in the future."
    )
    check_out = serializers.DateField(
        help_text="Check-out date in YYYY-MM-DD format. Must be after check-in date."
    )
    guests = serializers.IntegerField(
        min_value=1, 
        max_value=10, 
        default=1,
        help_text="Number of guests. Defaults to 1 if not specified."
    )
    
    # Booking details
    room_id = serializers.UUIDField(
        required=False, 
        allow_null=True,
        help_text="Specific room ID to book. If not provided, system will assign an available room of the selected type."
    )
    primary_guest_name = serializers.CharField(
        max_length=100,
        help_text="Full name of the primary guest as it appears on ID."
    )
    primary_guest_email = serializers.EmailField(
        help_text="Email address for booking confirmation and communication."
    )
    primary_guest_phone = serializers.CharField(
        max_length=20,
        help_text="Phone number for contact purposes."
    )
    special_requests = serializers.CharField(
        required=False, 
        allow_blank=True,
        help_text="Any special requests or notes for the hotel staff."
    )
    
    # Extras
    extras = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        allow_empty=True,
        help_text="List of extra services. Each item should contain 'extra_id' and optionally 'quantity'."
    )
    
    # Payment
    payment_method = serializers.CharField(
        default='card',
        help_text="Payment method. Defaults to 'card'."
    )
    save_payment_method = serializers.BooleanField(
        default=False,
        help_text="Whether to save payment method for future bookings. Defaults to false."
    )
    
    def validate(self, data):
        """Validate booking data"""
        check_in = data.get('check_in')
        check_out = data.get('check_out')
        
        # Validate dates
        if check_in and check_out:
            if check_in >= check_out:
                raise serializers.ValidationError("Check-out date must be after check-in date")
            
            if check_in < date.today():
                raise serializers.ValidationError("Check-in date cannot be in the past")
        
        # Validate extras format
        extras = data.get('extras', [])
        for extra in extras:
            if 'extra_id' not in extra:
                raise serializers.ValidationError("Each extra must have an 'extra_id'")
            if 'quantity' not in extra:
                extra['quantity'] = 1
        
        return data


class RoomSearchResultSerializer(serializers.Serializer):
    """Serializer for room search results"""
    room_id = serializers.UUIDField(help_text="Unique identifier for the room")
    room_number = serializers.CharField(help_text="Room number as displayed in the hotel")
    room_type = serializers.DictField(help_text="Detailed room type information including amenities and features")
    hotel = serializers.DictField(help_text="Hotel information including name, address, and contact details")
    pricing = serializers.DictField(help_text="Pricing information for the specified dates")
    images = serializers.ListField(help_text="List of room images with URLs and metadata")
    availability_info = serializers.DictField(
        required=False,
        help_text="Additional availability information if applicable"
    )


class BookingConfirmationSerializer(serializers.Serializer):
    """Serializer for booking confirmation response"""
    success = serializers.BooleanField(help_text="Whether the booking was successful")
    message = serializers.CharField(help_text="Status message or error description")
    booking = serializers.DictField(help_text="Complete booking details including confirmation number")
    available_rooms = serializers.ListField(
        required=False,
        help_text="Alternative room options if the requested room is not available"
    )
    payment = serializers.DictField(help_text="Payment processing information and status")
    email_notification = serializers.DictField(help_text="Email notification status and details")


class RoomTypeSerializer(serializers.ModelSerializer):
    """Comprehensive serializer for room type information"""
    amenities = serializers.SerializerMethodField()
    room_features = serializers.SerializerMethodField()
    policies = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()
    
    class Meta:
        model = RoomType
        fields = [
            'id', 'name', 'category', 'short_description', 'description', 
            'max_capacity', 'bed_type', 'bed_count', 'bathroom_count', 
            'room_size_sqm', 'room_size_sqft', 'is_accessible',
            'amenities', 'room_features', 'policies', 'images'
        ]
    
    def get_amenities(self, obj):
        """Get basic amenities list"""
        return obj.amenities_list
    
    def get_room_features(self, obj):
        """Get comprehensive room features"""
        return {
            # Technology & Entertainment
            'technology': {
                'wifi': obj.has_wifi,
                'smart_tv': obj.has_smart_tv,
                'regular_tv': obj.has_tv,
                'streaming_service': obj.has_streaming_service,
                'bluetooth_speaker': obj.has_bluetooth_speaker,
                'usb_charging': obj.has_usb_charging,
                'phone': obj.has_phone,
            },
            # Comfort & Convenience
            'comfort': {
                'air_conditioning': obj.has_air_conditioning,
                'heating': obj.has_heating,
                'desk': obj.has_desk,
                'seating_area': obj.has_seating_area,
                'balcony': obj.has_balcony,
                'safe': obj.has_safe,
                'blackout_curtains': obj.has_blackout_curtains,
                'soundproofing': obj.has_soundproofing,
            },
            # Kitchen & Dining
            'kitchen': {
                'kitchenette': obj.has_kitchenette,
                'coffee_maker': obj.has_coffee_maker,
                'tea_kettle': obj.has_tea_kettle,
                'refrigerator': obj.has_refrigerator,
                'microwave': obj.has_microwave,
                'minibar': obj.has_minibar,
            },
            # Bathroom Features
            'bathroom': {
                'shower': obj.has_shower,
                'bathtub': obj.has_bathtub,
                'hairdryer': obj.has_hairdryer,
                'toiletries': obj.has_toiletries,
                'towels': obj.has_towels,
                'bathrobes': obj.has_bathrobes,
                'slippers': obj.has_slippers,
            },
            # Additional Services
            'services': {
                'iron': obj.has_iron,
                'ironing_board': obj.has_ironing_board,
            }
        }
    
    def get_policies(self, obj):
        """Get room policies"""
        return {
            'children': {
                'allowed': obj.children_allowed,
                'max_children': obj.max_children,
            },
            'beds': {
                'extra_bed_available': obj.extra_bed_available,
                'extra_bed_charge': float(obj.extra_bed_charge) if obj.extra_bed_charge else 0,
                'infant_bed_available': obj.infant_bed_available,
            },
            'check_in_out': {
                'early_checkin_available': obj.early_checkin_available,
                'early_checkin_charge': float(obj.early_checkin_charge) if obj.early_checkin_charge else 0,
                'late_checkout_available': obj.late_checkout_available,
                'late_checkout_charge': float(obj.late_checkout_charge) if obj.late_checkout_charge else 0,
            }
        }
    
    def get_images(self, obj):
        """Get room type images"""
        from core.models import RoomImage
        images = RoomImage.objects.filter(room_type=obj, is_active=True).order_by('display_order')
        return [{
            'id': str(img.id),
            'image_url': img.image.url if img.image else '',
            'alt_text': img.image_alt_text,
            'caption': img.caption,
            'image_type': img.image_type,
            'is_primary': img.is_primary,
            'display_order': img.display_order
        } for img in images]


class RoomSerializer(serializers.ModelSerializer):
    """Comprehensive serializer for room information"""
    room_type = RoomTypeSerializer(read_only=True)
    price_for_dates = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()
    room_status = serializers.SerializerMethodField()
    room_features = serializers.SerializerMethodField()
    
    class Meta:
        model = Room
        fields = [
            'id', 'room_number', 'floor', 'capacity', 'base_price', 
            'view_type', 'condition', 'housekeeping_status', 'last_renovated',
            'is_corner_room', 'is_connecting_room', 'special_features',
            'room_type', 'price_for_dates', 'images', 'room_status', 'room_features'
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
    
    def get_images(self, obj):
        """Get room images - both room-specific and room type images"""
        from core.models import RoomImage

        # Get room-specific images first
        room_images = RoomImage.objects.filter(room=obj, is_active=True).order_by('display_order')

        # If no room-specific images, get room type images
        if not room_images.exists():
            room_images = RoomImage.objects.filter(room_type=obj.room_type, is_active=True).order_by('display_order')

        return [{
            'id': str(img.id),
            'image_url': img.image.url if img.image else '',
            'alt_text': img.image_alt_text,
            'caption': img.caption,
            'image_type': img.image_type,
            'is_primary': img.is_primary,
            'display_order': img.display_order
        } for img in room_images]
    
    def get_room_status(self, obj):
        """Get comprehensive room status"""
        return {
            'is_active': obj.is_active,
            'is_maintenance': obj.is_maintenance,
            'condition': obj.condition,
            'housekeeping_status': obj.housekeeping_status,
            'last_renovated': obj.last_renovated.isoformat() if obj.last_renovated else None,
            'last_cleaned': obj.last_cleaned.isoformat() if obj.last_cleaned else None,
            'last_inspected': obj.last_inspected.isoformat() if obj.last_inspected else None,
            'maintenance_notes': obj.maintenance_notes,
            'needs_maintenance': obj.needs_maintenance,
            'maintenance_priority': obj.maintenance_priority,
        }
    
    def get_room_features(self, obj):
        """Get room-specific features"""
        return {
            'location': {
                'floor': obj.floor,
                'is_corner_room': obj.is_corner_room,
                'is_connecting_room': obj.is_connecting_room,
                'view_type': obj.view_type,
            },
            'special_features': obj.special_features,
            'capacity': obj.capacity,
            'room_size': {
                'sqm': obj.room_type.room_size_sqm,
                'sqft': obj.room_type.room_size_sqft,
            }
        }


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
    check_in = serializers.DateField(
        help_text="Check-in date in YYYY-MM-DD format"
    )
    check_out = serializers.DateField(
        help_text="Check-out date in YYYY-MM-DD format"
    )
    guests = serializers.IntegerField(
        min_value=1, 
        max_value=10,
        help_text="Number of guests (1-10)"
    )
    hotel_id = serializers.UUIDField(
        required=False,
        help_text="(Optional) Specific hotel ID to search. If not provided, searches all available hotels."
    )
    room_type_id = serializers.UUIDField(
        required=False,
        help_text="(Optional) Specific room type ID to filter by."
    )
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
