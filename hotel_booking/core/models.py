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
    description = models.TextField(blank=True, null=True)
    address_line_1 = models.CharField(max_length=255)
    address_line_2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=100, default='Saudi Arabia')
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField()
    website = models.URLField(blank=True, null=True)

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
        # Filter out None or empty strings
        address_parts.extend([part for part in [self.city, self.state, self.postal_code, self.country] if part])
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
    description = models.TextField(blank=True, null=True)
    short_description = models.CharField(max_length=255, blank=True, null=True, help_text='Brief description for listings')
    max_capacity = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        default=1
    )
    
    # Room category
    category = models.CharField(
        max_length=50,
        choices=[
            ('standard', 'Standard'),
            ('deluxe', 'Deluxe'),
            ('premium', 'Premium'),
            ('suite', 'Suite'),
            ('presidential', 'Presidential'),
            ('family', 'Family'),
            ('accessible', 'Accessible'),
        ],
        default='standard'
    )
    
    # Room features
    bed_type = models.CharField(
        max_length=50, 
        choices=[
            ('single', 'Single Bed'),
            ('twin', 'Twin Beds'),
            ('double', 'Double Bed'),
            ('queen', 'Queen Bed'),
            ('king', 'King Bed'),
            ('sofa_bed', 'Sofa Bed'),
            ('bunk_bed', 'Bunk Bed'),
        ],
        default='queen'
    )
    bed_count = models.PositiveIntegerField(default=1)
    bathroom_count = models.PositiveIntegerField(default=1)
    room_size_sqm = models.PositiveIntegerField(null=True, blank=True, help_text='Room size in square meters')
    room_size_sqft = models.PositiveIntegerField(null=True, blank=True, help_text='Room size in square feet')
    
    # Basic Amenities
    has_wifi = models.BooleanField(default=False)
    has_tv = models.BooleanField(default=False)
    has_air_conditioning = models.BooleanField(default=False)
    has_heating = models.BooleanField(default=False)
    has_balcony = models.BooleanField(default=False)
    has_kitchenette = models.BooleanField(default=False)
    has_minibar = models.BooleanField(default=False)
    has_safe = models.BooleanField(default=False)
    has_desk = models.BooleanField(default=False)
    has_seating_area = models.BooleanField(default=False)
    
    # Bathroom amenities
    has_bathtub = models.BooleanField(default=False)
    has_shower = models.BooleanField(default=False)
    has_hairdryer = models.BooleanField(default=False)
    has_toiletries = models.BooleanField(default=False)
    has_towels = models.BooleanField(default=False)
    has_bathrobes = models.BooleanField(default=False)
    has_slippers = models.BooleanField(default=False)
    
    # Technology
    has_smart_tv = models.BooleanField(default=False)
    has_streaming_service = models.BooleanField(default=False)
    has_phone = models.BooleanField(default=False)
    has_usb_charging = models.BooleanField(default=False)
    has_bluetooth_speaker = models.BooleanField(default=False)
    
    # Comfort features
    has_coffee_maker = models.BooleanField(default=False)
    has_tea_kettle = models.BooleanField(default=False)
    has_refrigerator = models.BooleanField(default=False)
    has_microwave = models.BooleanField(default=False)
    has_iron = models.BooleanField(default=False)
    has_ironing_board = models.BooleanField(default=False)
    has_blackout_curtains = models.BooleanField(default=True)
    has_soundproofing = models.BooleanField(default=False)
    
    # Child and extra bed policies
    children_allowed = models.BooleanField(default=False)
    max_children = models.PositiveIntegerField(default=2)
    infant_bed_available = models.BooleanField(default=False)
    extra_bed_available = models.BooleanField(default=False)
    extra_bed_charge = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        default=Decimal('0.00'),
        help_text='Extra charge per night for additional bed'
    )
    
    # Accessibility features
    is_accessible = models.BooleanField(default=False, help_text='Wheelchair accessible')
    has_accessible_bathroom = models.BooleanField(default=False)
    has_grab_bars = models.BooleanField(default=False)
    has_roll_in_shower = models.BooleanField(default=False)
    has_lowered_fixtures = models.BooleanField(default=False)
    has_braille_signage = models.BooleanField(default=False)
    has_hearing_assistance = models.BooleanField(default=False)
    
    # Policies and restrictions
    smoking_allowed = models.BooleanField(default=False)
    pets_allowed = models.BooleanField(default=False)
    pet_charge = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        default=Decimal('0.00'),
        help_text='Pet charge per night'
    )
    
    # Check-in/Check-out policies
    early_checkin_available = models.BooleanField(default=False)
    late_checkout_available = models.BooleanField(default=False)
    early_checkin_charge = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        default=Decimal('0.00')
    )
    late_checkout_charge = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        default=Decimal('0.00')
    )
    
    # Cancellation policy specific to room type
    cancellation_policy = models.TextField(
        blank=True,
        null=True,
        help_text='Room type specific cancellation policy'
    )
    
    # Virtual tour and media
    virtual_tour_url = models.URLField(blank=True, null=True, help_text='360° virtual tour URL')
    featured_image = models.ImageField(upload_to='room_type_images/', blank=True, null=True, help_text='Main image for this room type')
    
    # Additional amenities (many-to-many relationship will be added after RoomAmenity is defined)
    
    class Meta:
        verbose_name = 'Room Type'
        verbose_name_plural = 'Room Types'
        ordering = ['category', 'name']
    
    def __str__(self):
        return f"{self.name} (Max {self.max_capacity} guests)"
    
    @property
    def amenities_list(self):
        """Get list of available amenities"""
        amenities = []
        
        # Basic amenities
        if self.has_wifi:
            amenities.append('WiFi')
        if self.has_tv:
            amenities.append('TV')
        if self.has_smart_tv:
            amenities.append('Smart TV')
        if self.has_air_conditioning:
            amenities.append('Air Conditioning')
        if self.has_heating:
            amenities.append('Heating')
        if self.has_balcony:
            amenities.append('Balcony')
        if self.has_kitchenette:
            amenities.append('Kitchenette')
        if self.has_minibar:
            amenities.append('Minibar')
        if self.has_safe:
            amenities.append('Safe')
        if self.has_desk:
            amenities.append('Work Desk')
        if self.has_seating_area:
            amenities.append('Seating Area')
            
        # Bathroom amenities
        if self.has_bathtub:
            amenities.append('Bathtub')
        if self.has_hairdryer:
            amenities.append('Hair Dryer')
        if self.has_bathrobes:
            amenities.append('Bathrobes')
        if self.has_slippers:
            amenities.append('Slippers')
            
        # Technology
        if self.has_streaming_service:
            amenities.append('Streaming Services')
        if self.has_usb_charging:
            amenities.append('USB Charging Ports')
        if self.has_bluetooth_speaker:
            amenities.append('Bluetooth Speaker')
            
        # Comfort features
        if self.has_coffee_maker:
            amenities.append('Coffee Maker')
        if self.has_tea_kettle:
            amenities.append('Tea Kettle')
        if self.has_refrigerator:
            amenities.append('Refrigerator')
        if self.has_microwave:
            amenities.append('Microwave')
        if self.has_iron:
            amenities.append('Iron & Ironing Board')
        if self.has_blackout_curtains:
            amenities.append('Blackout Curtains')
        if self.has_soundproofing:
            amenities.append('Soundproofing')
            
        # Accessibility
        if self.is_accessible:
            amenities.append('Wheelchair Accessible')
        if self.has_accessible_bathroom:
            amenities.append('Accessible Bathroom')
        if self.has_grab_bars:
            amenities.append('Grab Bars')
        if self.has_roll_in_shower:
            amenities.append('Roll-in Shower')
        if self.has_hearing_assistance:
            amenities.append('Hearing Assistance')
            
        return amenities
    
    @property
    def bed_configuration(self):
        """Get bed configuration description"""
        bed_types = {
            'single': 'Single',
            'twin': 'Twin',
            'double': 'Double',
            'queen': 'Queen',
            'king': 'King',
            'sofa_bed': 'Sofa',
            'bunk_bed': 'Bunk',
        }
        bed_name = bed_types.get(self.bed_type, self.bed_type)
        if self.bed_count == 1:
            return f"1 {bed_name} Bed"
        else:
            return f"{self.bed_count} {bed_name} Beds"
    
    @property
    def accessibility_features(self):
        """Get list of accessibility features"""
        features = []
        if self.is_accessible:
            features.append('Wheelchair Accessible')
        if self.has_accessible_bathroom:
            features.append('Accessible Bathroom')
        if self.has_grab_bars:
            features.append('Grab Bars')
        if self.has_roll_in_shower:
            features.append('Roll-in Shower')
        if self.has_lowered_fixtures:
            features.append('Lowered Fixtures')
        if self.has_braille_signage:
            features.append('Braille Signage')
        if self.has_hearing_assistance:
            features.append('Hearing Assistance')
        return features
    
    @property
    def room_size_display(self):
        """Get formatted room size"""
        if self.room_size_sqm and self.room_size_sqft:
            return f"{self.room_size_sqm} m² / {self.room_size_sqft} ft²"
        elif self.room_size_sqm:
            return f"{self.room_size_sqm} m²"
        elif self.room_size_sqft:
            return f"{self.room_size_sqft} ft²"
        return "Size not specified"


class Room(TimestampedModel):
    """Room model with availability and pricing"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='rooms')
    room_type = models.ForeignKey(RoomType, on_delete=models.CASCADE, related_name='rooms')
    room_number = models.CharField(max_length=10)
    floor = models.PositiveIntegerField(default=1)
    
    # Capacity and pricing
    capacity = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        default=1
    )
    base_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=Decimal('0.01'),
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    is_maintenance = models.BooleanField(default=False)
    maintenance_notes = models.TextField(blank=True,null=True)
    last_cleaned = models.DateTimeField(null=True, blank=True)
    last_inspected = models.DateTimeField(null=True, blank=True)
    
    # Room-specific features that may differ from room type
    view_type = models.CharField(
        max_length=50, 
        choices=[
            ('city', 'City View'),
            ('sea', 'Sea View'),
            ('ocean', 'Ocean View'),
            ('mountain', 'Mountain View'),
            ('garden', 'Garden View'),
            ('pool', 'Pool View'),
            ('courtyard', 'Courtyard View'),
            ('park', 'Park View'),
            ('lake', 'Lake View'),
            ('river', 'River View'),
            ('partial_sea', 'Partial Sea View'),
            ('partial_ocean', 'Partial Ocean View'),
            ('interior', 'Interior View'),
        ],
        default='city'
    )
    
    # Special designations
    is_corner_room = models.BooleanField(default=False)
    is_connecting_room = models.BooleanField(default=False)
    connecting_room = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text='Connected room for families'
    )
    
    # Room condition and features
    condition = models.CharField(
        max_length=20,
        choices=[
            ('excellent', 'Excellent'),
            ('very_good', 'Very Good'),
            ('good', 'Good'),
            ('fair', 'Fair'),
            ('needs_renovation', 'Needs Renovation'),
        ],
        default='good'
    )
    
    # Recent renovation
    last_renovated = models.DateField(null=True, blank=True)
    renovation_notes = models.TextField(blank=True, null=True)
    
    # Special features unique to this room
    special_features = models.TextField(
        blank=True,
        null=True,
        help_text='Any special features unique to this room'
    )
    
    # Housekeeping
    housekeeping_status = models.CharField(
        max_length=20,
        choices=[
            ('clean', 'Clean'),
            ('dirty', 'Dirty'),
            ('out_of_order', 'Out of Order'),
            ('inspected', 'Inspected'),
            ('maintenance', 'Under Maintenance'),
        ],
        default='clean'
    )
    
    # Inventory tracking
    needs_maintenance = models.BooleanField(default=False)
    maintenance_priority = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('urgent', 'Urgent'),
        ],
        default='low'
    )
    
    # Notes
    staff_notes = models.TextField(
        blank=True,
        null=True,
        help_text='Internal staff notes about this room'
    )
    
    class Meta:
        verbose_name = 'Room'
        verbose_name_plural = 'Rooms'
        ordering = ['hotel', 'floor', 'room_number']
        unique_together = ['hotel', 'room_number']
        indexes = [
            models.Index(fields=['hotel', 'capacity']),
            models.Index(fields=['is_active', 'is_maintenance']),
            models.Index(fields=['housekeeping_status']),
            models.Index(fields=['view_type']),
            models.Index(fields=['floor']),
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
        return (
            self.is_active and 
            not self.is_maintenance and 
            not self.needs_maintenance and
            self.housekeeping_status in ['clean', 'inspected']
        )
    
    @property
    def display_name(self):
        """Get display name for room"""
        features = []
        if self.is_corner_room:
            features.append('Corner')
        if self.view_type != 'city':
            features.append(self.get_view_type_display())
        
        base_name = f"Room {self.room_number}"
        if features:
            return f"{base_name} - {', '.join(features)}"
        return base_name
    
    @property
    def room_features(self):
        """Get list of special room features"""
        features = []
        if self.is_corner_room:
            features.append('Corner Room')
        if self.is_connecting_room:
            features.append('Connecting Room Available')
        if self.view_type != 'city':
            features.append(self.get_view_type_display())
        if self.last_renovated:
            from django.utils import timezone
            if (timezone.now().date() - self.last_renovated).days < 365:
                features.append('Recently Renovated')
        return features
    
    @property
    def maintenance_status(self):
        """Get maintenance status information"""
        if self.is_maintenance:
            return {
                'status': 'Under Maintenance',
                'priority': self.get_maintenance_priority_display(),
                'notes': self.maintenance_notes
            }
        elif self.needs_maintenance:
            return {
                'status': 'Needs Maintenance',
                'priority': self.get_maintenance_priority_display(),
                'notes': self.maintenance_notes
            }
        return {'status': 'Good', 'priority': None, 'notes': ''}
    
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
    
    def mark_for_maintenance(self, priority='medium', notes=''):
        """Mark room for maintenance"""
        self.needs_maintenance = True
        self.maintenance_priority = priority
        if notes:
            self.maintenance_notes = notes
        self.save()
    
    def complete_maintenance(self, notes=''):
        """Mark maintenance as complete"""
        self.is_maintenance = False
        self.needs_maintenance = False
        self.maintenance_priority = 'low'
        if notes:
            self.maintenance_notes = notes
        self.last_inspected = timezone.now()
        self.housekeeping_status = 'inspected'
        self.save()
    
    def update_housekeeping_status(self, status):
        """Update housekeeping status"""
        self.housekeeping_status = status
        if status == 'clean':
            self.last_cleaned = timezone.now()
        self.save()


class RoomImage(TimestampedModel):
    """Room image model for managing room photos"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='images', null=True, blank=True)
    room_type = models.ForeignKey(
        RoomType, 
        on_delete=models.CASCADE, 
        related_name='images',
        null=True,
        blank=True,
        help_text='If set, this image represents the room type rather than a specific room'
    )
    
    # Image details
    image = models.ImageField(upload_to='room_images/', null=True, blank=True, help_text='Upload room image')
    image_alt_text = models.CharField(max_length=255, blank=True, help_text='Alt text for accessibility', null=True)
    caption = models.CharField(max_length=255, blank=True, null=True)

    # Image type and ordering
    image_type = models.CharField(
        max_length=30,
        null=True,
        choices=[
            ('room_overview', 'Room Overview'),
            ('bed_area', 'Bed Area'),
            ('bathroom', 'Bathroom'),
            ('view', 'View from Room'),
            ('amenities', 'Amenities'),
            ('balcony', 'Balcony/Terrace'),
            ('kitchenette', 'Kitchenette'),
            ('seating_area', 'Seating Area'),
            ('entrance', 'Room Entrance'),
            ('other', 'Other'),
        ],
        default='room_overview'
    )
    
    is_primary = models.BooleanField(
        default=False,
        help_text='Primary image to display in listings'
    )
    
    display_order = models.PositiveIntegerField(
        default=1,
        null=True,
        help_text='Order to display images (1 = first)'
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Room Image'
        verbose_name_plural = 'Room Images'
        ordering = ['room', 'display_order']
        unique_together = ['room', 'display_order']
    
    def __str__(self):
        if self.room:
            return f"{self.room.room_number} - {self.get_image_type_display()}"
        elif self.room_type:
            return f"{self.room_type.name} - {self.get_image_type_display()}"
        return f"Image - {self.get_image_type_display()}"
    
    def save(self, *args, **kwargs):
        # Ensure only one primary image per room or room type
        if self.is_primary:
            if self.room:
                RoomImage.objects.filter(
                    room=self.room,
                    is_primary=True
                ).exclude(id=self.id).update(is_primary=False)
            elif self.room_type:
                RoomImage.objects.filter(
                    room_type=self.room_type,
                    is_primary=True
                ).exclude(id=self.id).update(is_primary=False)
        
        super().save(*args, **kwargs)


class RoomAmenity(TimestampedModel):
    """Additional amenities that can be added to rooms"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    category = models.CharField(
        max_length=50,
        null=True,
        choices=[
            ('technology', 'Technology'),
            ('comfort', 'Comfort'),
            ('convenience', 'Convenience'),
            ('entertainment', 'Entertainment'),
            ('accessibility', 'Accessibility'),
            ('business', 'Business'),
            ('family', 'Family'),
            ('luxury', 'Luxury'),
        ],
        default='comfort'
    )
    
    is_premium = models.BooleanField(
        default=False,
        help_text='Premium amenity that may affect pricing'
    )
    
    class Meta:
        verbose_name = 'Room Amenity'
        verbose_name_plural = 'Room Amenities'
        ordering = ['category', 'name']
    
    def __str__(self):
        return self.name


class RoomTypeAmenity(TimestampedModel):
    """Through model for room type amenities"""
    room_type = models.ForeignKey(RoomType, on_delete=models.CASCADE)
    amenity = models.ForeignKey(RoomAmenity, on_delete=models.CASCADE)
    is_included = models.BooleanField(default=True)
    additional_charge = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Additional charge for this amenity'
    )
    
    class Meta:
        unique_together = ['room_type', 'amenity']
        verbose_name = 'Room Type Amenity'
        verbose_name_plural = 'Room Type Amenities'
    
    def __str__(self):
        return f"{self.room_type.name} - {self.amenity.name}"


class Extra(TimestampedModel):
    """Extra services/amenities model"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='extras')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(
        max_digits=8, 
        null=True,
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
    
    name = models.CharField(max_length=100, help_text='e.g., Summer Season, Holiday Season', null=True)
    start_date = models.DateField(default=timezone.now, null=True, help_text='Start date of the seasonal pricing')
    end_date = models.DateField(null=True, help_text='End date of the seasonal pricing')
    
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
        if self.start_date and self.end_date and self.start_date >= self.end_date:
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


# Add the many-to-many relationship to RoomType after all models are defined
RoomType.add_to_class(
    'additional_amenities',
    models.ManyToManyField(
        'RoomAmenity',
        through='RoomTypeAmenity',
        blank=True,
        help_text='Additional amenities for this room type'
    )
)


class ContactMessage(TimestampedModel):
    """Model to store contact form messages"""
    full_name = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    subject = models.CharField(max_length=255, null=True, blank=True)
    message = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = 'Contact Message'
        verbose_name_plural = 'Contact Messages'
        ordering = ['-created_at']

    def __str__(self):
        return f"Message from {self.full_name} - {self.subject}"
