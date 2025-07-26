# Django imports
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from datetime import datetime, date
import uuid


class TimestampedModel(models.Model):
    """Abstract base class for models with timestamp fields"""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True


class Hotel(TimestampedModel):
    """Hotel model with complete hotel information"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    address_line_1 = models.CharField(max_length=255)
    address_line_2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100, default='United States')
    phone_number = models.CharField(max_length=20)
    email = models.EmailField()
    website = models.URLField(blank=True)
    
    # Hotel features
    star_rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        default=3
    )
    check_in_time = models.TimeField(default='15:00')
    check_out_time = models.TimeField(default='11:00')
    
    # Policies
    cancellation_policy = models.TextField(default='Free cancellation 24 hours before check-in')
    pet_policy = models.TextField(default='Pets not allowed')
    smoking_policy = models.TextField(default='Non-smoking property')
    
    # Status
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Hotel'
        verbose_name_plural = 'Hotels'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    @property
    def full_address(self):
        """Get full formatted address"""
        address_parts = [self.address_line_1]
        if self.address_line_2:
            address_parts.append(self.address_line_2)
        address_parts.extend([self.city, self.state, self.postal_code, self.country])
        return ', '.join(address_parts)
    
    def get_available_rooms(self, check_in, check_out, guests=1):
        """Get available rooms for given dates and guest count"""
        from .services import RoomAvailabilityService
        return RoomAvailabilityService.get_available_rooms(
            hotel=self, 
            check_in=check_in, 
            check_out=check_out, 
            guests=guests
        )


class RoomType(TimestampedModel):
    """Room type model with detailed specifications"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    max_capacity = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    
    # Room features
    bed_type = models.CharField(max_length=50, default='Queen Bed')
    bed_count = models.PositiveIntegerField(default=1)
    bathroom_count = models.PositiveIntegerField(default=1)
    room_size_sqm = models.PositiveIntegerField(null=True, blank=True, help_text='Room size in square meters')
    
    # Amenities
    has_wifi = models.BooleanField(default=True)
    has_tv = models.BooleanField(default=True)
    has_air_conditioning = models.BooleanField(default=True)
    has_balcony = models.BooleanField(default=False)
    has_kitchenette = models.BooleanField(default=False)
    has_minibar = models.BooleanField(default=False)
    has_safe = models.BooleanField(default=True)
    
    # Accessibility
    is_accessible = models.BooleanField(default=False, help_text='Wheelchair accessible')
    
    class Meta:
        verbose_name = 'Room Type'
        verbose_name_plural = 'Room Types'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} (Max {self.max_capacity} guests)"
    
    @property
    def amenities_list(self):
        """Get list of available amenities"""
        amenities = []
        if self.has_wifi:
            amenities.append('WiFi')
        if self.has_tv:
            amenities.append('TV')
        if self.has_air_conditioning:
            amenities.append('Air Conditioning')
        if self.has_balcony:
            amenities.append('Balcony')
        if self.has_kitchenette:
            amenities.append('Kitchenette')
        if self.has_minibar:
            amenities.append('Minibar')
        if self.has_safe:
            amenities.append('Safe')
        if self.is_accessible:
            amenities.append('Wheelchair Accessible')
        return amenities


class Room(TimestampedModel):
    """Room model with availability and pricing"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='rooms')
    room_type = models.ForeignKey(RoomType, on_delete=models.CASCADE, related_name='rooms')
    room_number = models.CharField(max_length=10)
    floor = models.PositiveIntegerField()
    
    # Capacity and pricing
    capacity = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    base_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    is_maintenance = models.BooleanField(default=False)
    maintenance_notes = models.TextField(blank=True)
    
    # Special features
    view_type = models.CharField(
        max_length=50, 
        choices=[
            ('city', 'City View'),
            ('sea', 'Sea View'),
            ('mountain', 'Mountain View'),
            ('garden', 'Garden View'),
            ('pool', 'Pool View'),
            ('courtyard', 'Courtyard View'),
        ],
        default='city'
    )
    
    class Meta:
        verbose_name = 'Room'
        verbose_name_plural = 'Rooms'
        ordering = ['hotel', 'floor', 'room_number']
        unique_together = ['hotel', 'room_number']
        indexes = [
            models.Index(fields=['hotel', 'capacity']),
            models.Index(fields=['is_active', 'is_maintenance']),
        ]
    
    def __str__(self):
        return f"{self.hotel.name} - Room {self.room_number} ({self.room_type.name})"
    
    def clean(self):
        """Validate room capacity against room type"""
        if self.capacity > self.room_type.max_capacity:
            raise ValidationError(
                f'Room capacity ({self.capacity}) cannot exceed room type max capacity ({self.room_type.max_capacity})'
            )
    
    @property
    def is_available_for_booking(self):
        """Check if room is available for booking"""
        return self.is_active and not self.is_maintenance
    
    def get_price_for_dates(self, check_in, check_out):
        """Get price for specific dates including seasonal pricing"""
        from .services import PricingService
        return PricingService.calculate_room_price(self, check_in, check_out)
    
    def is_available(self, check_in, check_out):
        """Check if room is available for given dates"""
        if not self.is_available_for_booking:
            return False
        
        from bookings.models import Booking
        conflicting_bookings = Booking.objects.filter(
            room=self,
            status__in=['confirmed', 'checked_in'],
            check_in__lt=check_out,
            check_out__gt=check_in
        )
        return not conflicting_bookings.exists()


class Extra(TimestampedModel):
    """Extra services/amenities model"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='extras')
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(
        max_digits=8, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    # Pricing type
    pricing_type = models.CharField(
        max_length=20,
        choices=[
            ('per_night', 'Per Night'),
            ('per_stay', 'Per Stay'),
            ('per_person', 'Per Person'),
            ('per_person_night', 'Per Person Per Night'),
        ],
        default='per_stay'
    )
    
    # Availability
    is_active = models.BooleanField(default=True)
    max_quantity = models.PositiveIntegerField(
        default=1, 
        help_text='Maximum quantity per booking'
    )
    
    # Category
    category = models.CharField(
        max_length=50,
        choices=[
            ('breakfast', 'Breakfast'),
            ('parking', 'Parking'),
            ('wifi', 'WiFi'),
            ('spa', 'Spa & Wellness'),
            ('transport', 'Transportation'),
            ('dining', 'Dining'),
            ('recreation', 'Recreation'),
            ('business', 'Business Services'),
            ('other', 'Other'),
        ],
        default='other'
    )
    
    class Meta:
        verbose_name = 'Extra Service'
        verbose_name_plural = 'Extra Services'
        ordering = ['hotel', 'category', 'name']
        unique_together = ['hotel', 'name']
    
    def __str__(self):
        return f"{self.name} - ${self.price} ({self.get_pricing_type_display()})"
    
    def calculate_total_price(self, quantity=1, nights=1, guests=1):
        """Calculate total price based on pricing type"""
        base_price = self.price * quantity
        
        if self.pricing_type == 'per_night':
            return base_price * nights
        elif self.pricing_type == 'per_person':
            return base_price * guests
        elif self.pricing_type == 'per_person_night':
            return base_price * guests * nights
        else:  # per_stay
            return base_price


class SeasonalPricing(TimestampedModel):
    """Seasonal pricing model for dynamic pricing"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='seasonal_pricing')
    room_type = models.ForeignKey(RoomType, on_delete=models.CASCADE, related_name='seasonal_pricing')
    
    name = models.CharField(max_length=100, help_text='e.g., Summer Season, Holiday Season')
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Pricing modifiers
    price_multiplier = models.DecimalField(
        max_digits=4, 
        decimal_places=2, 
        default=Decimal('1.00'),
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text='Multiplier for base price (1.0 = no change, 1.5 = 50% increase)'
    )
    
    # Days of week (for recurring patterns)
    apply_monday = models.BooleanField(default=True)
    apply_tuesday = models.BooleanField(default=True)
    apply_wednesday = models.BooleanField(default=True)
    apply_thursday = models.BooleanField(default=True)
    apply_friday = models.BooleanField(default=True)
    apply_saturday = models.BooleanField(default=True)
    apply_sunday = models.BooleanField(default=True)
    
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Seasonal Pricing'
        verbose_name_plural = 'Seasonal Pricing'
        ordering = ['hotel', 'start_date']
    
    def __str__(self):
        return f"{self.hotel.name} - {self.name} ({self.start_date} to {self.end_date})"
    
    def clean(self):
        """Validate date range"""
        if self.start_date >= self.end_date:
            raise ValidationError('End date must be after start date')
    
    def applies_to_date(self, check_date):
        """Check if pricing applies to given date"""
        if not self.is_active:
            return False
        
        if not (self.start_date <= check_date <= self.end_date):
            return False
        
        # Check day of week
        weekday = check_date.weekday()  # 0=Monday, 6=Sunday
        day_applies = [
            self.apply_monday, self.apply_tuesday, self.apply_wednesday,
            self.apply_thursday, self.apply_friday, self.apply_saturday, self.apply_sunday
        ]
        
        return day_applies[weekday]