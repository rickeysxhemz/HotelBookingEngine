# Django REST Framework imports
from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from decimal import Decimal

# Local imports
from .models import Offer, OfferCategory, OfferHighlight, OfferImage
from core.models import Hotel, RoomType


def validate_offer_data(data, instance=None):
    """Shared validation logic for offer data"""
    # Validate date range
    valid_from = data.get('valid_from')
    valid_to = data.get('valid_to')
    
    if valid_from and valid_to:
        if valid_from > valid_to:
            raise serializers.ValidationError({
                'valid_to': 'Valid to date must be after valid from date'
            })
        
        # Check if valid_from is not in the past (for new offers)
        if not instance and valid_from < timezone.now().date():
            raise serializers.ValidationError({
                'valid_from': 'Valid from date cannot be in the past'
            })
    
    # Validate stay requirements
    minimum_stay = data.get('minimum_stay')
    maximum_stay = data.get('maximum_stay')
    
    if minimum_stay and maximum_stay:
        if minimum_stay > maximum_stay:
            raise serializers.ValidationError({
                'maximum_stay': 'Maximum stay cannot be less than minimum stay'
            })
    
    # Validate advance booking requirements
    min_advance = data.get('minimum_advance_booking')
    max_advance = data.get('maximum_advance_booking')
    
    if min_advance and max_advance:
        if min_advance > max_advance:
            raise serializers.ValidationError({
                'maximum_advance_booking': 'Maximum advance booking cannot be less than minimum advance booking'
            })
    
    # Validate discount values based on offer type
    offer_type = data.get('offer_type')
    
    if offer_type == 'percentage':
        discount_percentage = data.get('discount_percentage')
        if not discount_percentage:
            raise serializers.ValidationError({
                'discount_percentage': 'Percentage discount is required for percentage offers'
            })
        if discount_percentage <= 0 or discount_percentage > 100:
            raise serializers.ValidationError({
                'discount_percentage': 'Discount percentage must be between 0 and 100'
            })
    
    elif offer_type == 'fixed_amount':
        discount_amount = data.get('discount_amount')
        if not discount_amount:
            raise serializers.ValidationError({
                'discount_amount': 'Discount amount is required for fixed amount offers'
            })
        if discount_amount <= 0:
            raise serializers.ValidationError({
                'discount_amount': 'Discount amount must be greater than 0'
            })
    
    elif offer_type == 'package':
        package_price = data.get('package_price')
        if not package_price:
            raise serializers.ValidationError({
                'package_price': 'Package price is required for package offers'
            })
        if package_price <= 0:
            raise serializers.ValidationError({
                'package_price': 'Package price must be greater than 0'
            })
    
    return data


class OfferCategorySerializer(serializers.ModelSerializer):
    """Serializer for offer categories"""
    
    offer_count = serializers.ReadOnlyField()
    
    class Meta:
        model = OfferCategory
        fields = [
            'id', 'name', 'description', 'slug',
            'color', 'is_active', 'order', 'offer_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class OfferCategoryListSerializer(serializers.ModelSerializer):
    """Serializer for offer category list view (minimal data)"""
    
    offer_count = serializers.ReadOnlyField()
    
    class Meta:
        model = OfferCategory
        fields = [
            'id', 'name', 'description', 'slug',
            'color', 'offer_count'
        ]
        read_only_fields = ['id']


class OfferImageSerializer(serializers.ModelSerializer):
    """Serializer for offer images"""
    
    class Meta:
        model = OfferImage
        fields = [
            'id', 'image', 'alt_text', 'caption', 
            'is_primary', 'order', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class OfferHighlightSerializer(serializers.ModelSerializer):
    """Serializer for offer highlights"""
    
    class Meta:
        model = OfferHighlight
        fields = [
            'id', 'title', 'description',
            'order', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class OfferListSerializer(serializers.ModelSerializer):
    """Serializer for offer list view (minimal data)"""
    
    hotel_name = serializers.CharField(source='hotel.name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_slug = serializers.CharField(source='category.slug', read_only=True)
    category_color = serializers.CharField(source='category.color', read_only=True)
    primary_image = serializers.SerializerMethodField()
    discount_display = serializers.ReadOnlyField()
    is_valid = serializers.ReadOnlyField()
    is_available = serializers.ReadOnlyField()
    highlights_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Offer
        fields = [
            'id', 'name', 'short_description', 'offer_type',
            'discount_display', 'valid_from', 'valid_to',
            'minimum_stay', 'hotel_name', 'category_name',
            'category_slug', 'category_color',
            'primary_image', 'is_featured', 'is_valid',
            'is_available', 'highlights_count', 'slug', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_primary_image(self, obj):
        """Get the primary image URL"""
        primary_image = obj.images.filter(is_primary=True).first()
        if primary_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(primary_image.image.url)
            return primary_image.image.url
        return None
    
    def get_highlights_count(self, obj):
        """Get the number of highlights"""
        return obj.highlights.count()


class OfferDetailSerializer(serializers.ModelSerializer):
    """Serializer for offer detail view (complete data)"""
    
    hotel_name = serializers.CharField(source='hotel.name', read_only=True)
    hotel_id = serializers.UUIDField(source='hotel.id', read_only=True)
    category = OfferCategoryListSerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=OfferCategory.objects.all(),
        source='category',
        write_only=True,
        required=False
    )
    highlights = OfferHighlightSerializer(many=True, read_only=True)
    images = OfferImageSerializer(many=True, read_only=True)
    discount_display = serializers.ReadOnlyField()
    is_valid = serializers.ReadOnlyField()
    is_available = serializers.ReadOnlyField()
    days_remaining = serializers.SerializerMethodField()
    
    class Meta:
        model = Offer
        fields = [
            'id', 'name', 'description', 'short_description',
            'category', 'category_id', 'offer_type', 'discount_type',
            'discount_percentage', 'discount_amount', 'package_price',
            'valid_from', 'valid_to', 'minimum_stay', 'maximum_stay',
            'minimum_advance_booking', 'maximum_advance_booking',
            'hotel_name', 'hotel_id', 'total_bookings_limit',
            'bookings_used', 'applies_monday', 'applies_tuesday',
            'applies_wednesday', 'applies_thursday', 'applies_friday',
            'applies_saturday', 'applies_sunday', 'is_active',
            'is_featured', 'is_combinable', 'slug', 'terms_and_conditions',
            'highlights', 'images', 'discount_display', 'is_valid',
            'is_available', 'days_remaining', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'bookings_used', 'created_at', 'updated_at']
    
    def get_days_remaining(self, obj):
        """Get the number of days remaining for the offer"""
        if not obj.is_valid:
            return 0
        
        today = timezone.now().date()
        delta = obj.valid_to - today
        return max(0, delta.days)
    
    def validate(self, data):
        """Validate the offer data"""
        return validate_offer_data(data, self.instance)


class OfferCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating offers"""

    class Meta:
        model = Offer
        fields = [
            'name', 'description', 'short_description', 'category',
            'offer_type', 'discount_type', 'discount_percentage',
            'discount_amount', 'package_price', 'valid_from', 'valid_to',
            'minimum_stay', 'maximum_stay', 'minimum_advance_booking',
            'maximum_advance_booking', 'hotel',
            'total_bookings_limit', 'applies_monday', 'applies_tuesday',
            'applies_wednesday', 'applies_thursday', 'applies_friday',
            'applies_saturday', 'applies_sunday', 'is_active', 'is_featured',
            'is_combinable', 'terms_and_conditions'
        ]
    
    def validate(self, data):
        """Validate the offer data using shared validation logic"""
        return validate_offer_data(data, self.instance)


class OfferSearchSerializer(serializers.Serializer):
    """Serializer for offer search parameters"""
    
    hotel_id = serializers.UUIDField(
        required=False,
        help_text="Filter offers by hotel ID"
    )
    category_id = serializers.UUIDField(
        required=False,
        help_text="Filter offers by category ID"
    )
    category_slug = serializers.CharField(
        required=False,
        help_text="Filter offers by category slug"
    )
    check_in = serializers.DateField(
        required=False,
        help_text="Check-in date to filter applicable offers"
    )
    check_out = serializers.DateField(
        required=False,
        help_text="Check-out date to filter applicable offers"
    )
    offer_type = serializers.ChoiceField(
        choices=Offer.OFFER_TYPE_CHOICES,
        required=False,
        help_text="Filter by offer type"
    )
    is_featured = serializers.BooleanField(
        required=False,
        help_text="Filter featured offers only"
    )
    min_discount = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        required=False,
        help_text="Minimum discount percentage (for percentage offers)"
    )
    max_nights = serializers.IntegerField(
        required=False,
        help_text="Maximum nights stay to filter by minimum stay requirement"
    )
    
    def validate(self, data):
        """Validate search parameters"""
        check_in = data.get('check_in')
        check_out = data.get('check_out')
        
        if check_in and check_out:
            if check_in >= check_out:
                raise serializers.ValidationError({
                    'check_out': 'Check-out date must be after check-in date'
                })
        
        if check_in and check_in < timezone.now().date():
            raise serializers.ValidationError({
                'check_in': 'Check-in date cannot be in the past'
            })
        
        return data


class OfferCalculationSerializer(serializers.Serializer):
    """Serializer for calculating offer discounts"""
    
    offer_id = serializers.UUIDField(help_text="Offer ID to calculate discount for")
    base_price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Base room price per night"
    )
    nights = serializers.IntegerField(
        min_value=1,
        help_text="Number of nights"
    )
    check_in = serializers.DateField(
        help_text="Check-in date"
    )
    check_out = serializers.DateField(
        help_text="Check-out date"
    )
    
    def validate(self, data):
        """Validate calculation parameters"""
        check_in = data.get('check_in')
        check_out = data.get('check_out')
        nights = data.get('nights')
        
        if check_in >= check_out:
            raise serializers.ValidationError({
                'check_out': 'Check-out date must be after check-in date'
            })
        
        # Validate nights matches date range
        calculated_nights = (check_out - check_in).days
        if calculated_nights != nights:
            raise serializers.ValidationError({
                'nights': f'Number of nights ({nights}) does not match date range ({calculated_nights} nights)'
            })
        
        return data


class OfferCalculationResponseSerializer(serializers.Serializer):
    """Serializer for offer calculation response"""
    
    offer_id = serializers.UUIDField()
    offer_name = serializers.CharField()
    is_applicable = serializers.BooleanField()
    discount_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    discounted_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    original_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    savings = serializers.DecimalField(max_digits=10, decimal_places=2)
    message = serializers.CharField(required=False)
