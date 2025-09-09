# Django imports
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
import uuid

# Local imports
from core.models import TimestampedModel, Hotel, RoomType


class OfferCategory(TimestampedModel):
    """Categories for organizing offers"""
    
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Category name (e.g., 'Romance Package', 'Business Travel')"
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Description of the offer category"
    )
    slug = models.SlugField(
        max_length=100,
        unique=True,
        help_text="URL-friendly version of the category name"
    )
    # Removed icon field to reduce unnecessary data for frontend
    # icon = models.CharField(
    #     max_length=50,
    #     blank=True,
    #     null=True,
    #     help_text="CSS icon class or emoji for the category"
    # )
    color = models.CharField(
        max_length=7,
        blank=True,
        null=True,
        help_text="Hex color code for category display (e.g., #FF5722)"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this category is active and visible"
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text="Display order (lower numbers appear first)"
    )
    
    class Meta:
        ordering = ['order', 'name']
        verbose_name = "Offer Category"
        verbose_name_plural = "Offer Categories"
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # Auto-generate slug if not provided
        if not self.slug:
            from django.utils.text import slugify
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while OfferCategory.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        
        super().save(*args, **kwargs)
    
    @property
    def offer_count(self):
        """Get the number of active offers in this category"""
        return self.offers.filter(is_active=True).count()


class OfferManager(models.Manager):
    """Custom manager for Offer model"""
    
    def active_offers(self):
        """Get active offers that are currently valid"""
        now = timezone.now().date()
        return self.filter(
            is_active=True,
            valid_from__lte=now,
            valid_to__gte=now
        )
    
    def for_hotel(self, hotel):
        """Get offers for a specific hotel"""
        return self.filter(hotel=hotel)
    
    def for_category(self, category):
        """Get offers for a specific category"""
        return self.filter(category=category)
    
    def for_date_range(self, start_date, end_date):
        """Get offers valid for a specific date range"""
        return self.filter(
            is_active=True,
            valid_from__lte=end_date,
            valid_to__gte=start_date
        )
    
    def featured_offers(self):
        """Get featured offers"""
        return self.active_offers().filter(is_featured=True)
    
    def by_category(self):
        """Get offers grouped by category"""
        return self.active_offers().select_related('category').order_by(
            'category__order', 'category__name', '-is_featured', '-created_at'
        )


class Offer(TimestampedModel):
    """Comprehensive offer model for hotel deals and packages"""
    
    OFFER_TYPE_CHOICES = [
        ('percentage', 'Percentage Discount'),
        ('fixed_amount', 'Fixed Amount Discount'),
        ('package', 'Package Deal'),
        ('seasonal', 'Seasonal Offer'),
        ('early_bird', 'Early Bird Discount'),
        ('last_minute', 'Last Minute Deal'),
        ('loyalty', 'Loyalty Program'),
        ('group', 'Group Booking Discount'),
    ]
    
    DISCOUNT_TYPE_CHOICES = [
        ('room_rate', 'Room Rate Discount'),
        ('total_booking', 'Total Booking Discount'),
        ('per_night', 'Per Night Discount'),
        ('package_price', 'Package Price'),
    ]
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(
        max_length=255,
        help_text="Name of the offer (e.g., 'Summer Special 2025')"
    )
    description = models.TextField(
        help_text="Detailed description of the offer"
    )
    short_description = models.CharField(
        max_length=500,
        null=True,
        blank=True,
        help_text="Brief description for listings"
    )
    
    # Category
    category = models.ForeignKey(
        OfferCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='offers',
        help_text="Category this offer belongs to"
    )
    
    # Offer Classification
    offer_type = models.CharField(
        max_length=20,
        choices=OFFER_TYPE_CHOICES,
        default='percentage'
    )
    discount_type = models.CharField(
        max_length=20,
        choices=DISCOUNT_TYPE_CHOICES,
        default='room_rate'
    )
    
    # Pricing
    discount_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Discount percentage (0-100)"
    )
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Fixed discount amount"
    )
    package_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Package price for package deals"
    )
    
    # Validity
    valid_from = models.DateField(
        help_text="Start date of the offer"
    )
    valid_to = models.DateField(
        help_text="End date of the offer"
    )
    
    # Booking Requirements
    minimum_stay = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
        help_text="Minimum number of nights required"
    )
    maximum_stay = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
        help_text="Maximum number of nights allowed"
    )
    minimum_advance_booking = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Minimum days in advance booking is required"
    )
    maximum_advance_booking = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Maximum days in advance booking is allowed"
    )
    
    # Applicability
    hotel = models.ForeignKey(
        Hotel,
        on_delete=models.CASCADE,
        related_name='offers'
    )
    # Removed applicable_room_types field as per request
    # applicable_room_types = models.ManyToManyField(
    #     RoomType,
    #     blank=True,
    #     help_text="Room types this offer applies to. Leave empty for all room types."
    # )
    
    # Availability
    total_bookings_limit = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Maximum number of bookings for this offer"
    )
    bookings_used = models.PositiveIntegerField(
        default=0,
        help_text="Number of bookings already made with this offer"
    )
    
    # Days of week applicability
    applies_monday = models.BooleanField(default=True)
    applies_tuesday = models.BooleanField(default=True)
    applies_wednesday = models.BooleanField(default=True)
    applies_thursday = models.BooleanField(default=True)
    applies_friday = models.BooleanField(default=True)
    applies_saturday = models.BooleanField(default=True)
    applies_sunday = models.BooleanField(default=True)
    
    # Status and Features
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(
        default=False,
        help_text="Featured offers appear prominently on the website"
    )
    is_combinable = models.BooleanField(
        default=False,
        help_text="Can this offer be combined with other offers"
    )
    
    # SEO and Marketing
    slug = models.SlugField(
        max_length=255,
        unique=True,
        blank=True,
        help_text="URL-friendly version of the offer name"
    )
    terms_and_conditions = models.TextField(
        blank=True,
        null=True,
        help_text="Terms and conditions for this offer"
    )
    
    objects = OfferManager()
    
    class Meta:
        ordering = ['-is_featured', '-created_at']
        indexes = [
            models.Index(fields=['hotel', 'is_active']),
            models.Index(fields=['valid_from', 'valid_to']),
            models.Index(fields=['is_featured', 'is_active']),
            models.Index(fields=['category', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.hotel.name}"
    
    def clean(self):
        """Validate the offer data"""
        super().clean()
        
        # Validate date range
        if self.valid_from and self.valid_to:
            if self.valid_from > self.valid_to:
                raise ValidationError("Valid from date must be before valid to date")
        
        # Validate stay requirements
        if self.maximum_stay and self.minimum_stay:
            if self.minimum_stay > self.maximum_stay:
                raise ValidationError("Minimum stay cannot be greater than maximum stay")
        
        # Validate advance booking requirements
        if self.maximum_advance_booking and self.minimum_advance_booking:
            if self.minimum_advance_booking > self.maximum_advance_booking:
                raise ValidationError("Minimum advance booking cannot be greater than maximum advance booking")
        
        # Validate discount values based on offer type
        if self.offer_type == 'percentage':
            if not self.discount_percentage:
                raise ValidationError("Percentage discount is required for percentage offers")
            if self.discount_percentage <= 0 or self.discount_percentage > 100:
                raise ValidationError("Discount percentage must be between 0 and 100")
        
        elif self.offer_type == 'fixed_amount':
            if not self.discount_amount:
                raise ValidationError("Discount amount is required for fixed amount offers")
            if self.discount_amount <= 0:
                raise ValidationError("Discount amount must be greater than 0")
        
        elif self.offer_type == 'package':
            if not self.package_price:
                raise ValidationError("Package price is required for package offers")
            if self.package_price <= 0:
                raise ValidationError("Package price must be greater than 0")
    
    def save(self, *args, **kwargs):
        # Auto-generate slug if not provided
        if not self.slug:
            from django.utils.text import slugify
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Offer.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        
        super().save(*args, **kwargs)
    
    @property
    def is_valid(self):
        """Check if the offer is currently valid"""
        if not self.is_active:
            return False
        
        now = timezone.now().date()
        return self.valid_from <= now <= self.valid_to
    
    @property
    def is_available(self):
        """Check if the offer is available for booking"""
        if not self.is_valid:
            return False
        
        if self.total_bookings_limit:
            return self.bookings_used < self.total_bookings_limit
        
        return True
    
    @property
    def discount_display(self):
        """Human-readable discount display"""
        if self.offer_type == 'percentage':
            return f"{self.discount_percentage}% off"
        elif self.offer_type == 'fixed_amount':
            return f"${self.discount_amount} off"
        elif self.offer_type == 'package':
            return f"Package from ${self.package_price}"
        return "Special offer"
    
    def applies_to_date(self, check_date):
        """Check if offer applies to a specific date"""
        if not self.is_valid:
            return False
        
        if check_date < self.valid_from or check_date > self.valid_to:
            return False
        
        # More efficient day-of-week check using a list
        day_applicability = [
            self.applies_monday, self.applies_tuesday, self.applies_wednesday,
            self.applies_thursday, self.applies_friday, self.applies_saturday, self.applies_sunday
        ]
        
        weekday = check_date.weekday()  # 0=Monday, 6=Sunday
        return day_applicability[weekday]
    
    def calculate_discount(self, base_price, nights=1):
        """Calculate the discount amount for given base price and nights"""
        if not self.is_available:
            return Decimal('0.00')
        
        if self.offer_type == 'percentage':
            if self.discount_type == 'per_night':
                return (base_price * self.discount_percentage / 100) * nights
            else:
                total_price = base_price * nights
                return total_price * self.discount_percentage / 100
        
        elif self.offer_type == 'fixed_amount':
            if self.discount_type == 'per_night':
                return self.discount_amount * nights
            else:
                return self.discount_amount
        
        return Decimal('0.00')


class OfferHighlight(TimestampedModel):
    """Key highlights or features of an offer"""
    
    offer = models.ForeignKey(
        Offer,
        on_delete=models.CASCADE,
        related_name='highlights'
    )
    title = models.CharField(
        max_length=255,
        help_text="Highlight title (e.g., 'Free Breakfast')"
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Optional detailed description of the highlight"
    )
    # Removed icon field to reduce unnecessary data for frontend
    # icon = models.CharField(
    #     max_length=50,
    #     blank=True,
    #     null=True,
    #     help_text="CSS icon class or emoji for the highlight"
    # )
    order = models.PositiveIntegerField(
        default=0,
        help_text="Display order (lower numbers appear first)"
    )
    
    class Meta:
        ordering = ['order', 'created_at']
        unique_together = ['offer', 'title']
    
    def __str__(self):
        return f"{self.offer.name} - {self.title}"


def offer_image_upload_path(instance, filename):
    """Generate upload path for offer images"""
    # Create path: media/offer_images/hotel_id/offer_id/filename
    if instance.offer and instance.offer.hotel:
        return f'offer_images/{instance.offer.hotel.id}/{instance.offer.id}/{filename}'
    else:
        # Fallback path when offer is not set yet
        return f'offer_images/temp/{filename}'


class OfferImage(TimestampedModel):
    """Images associated with offers"""
    
    offer = models.ForeignKey(
        Offer,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(
        upload_to=offer_image_upload_path,
        max_length=500,
        help_text="Offer promotional image"
    )
    alt_text = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Alternative text for accessibility"
    )
    caption = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Image caption"
    )
    is_primary = models.BooleanField(
        default=False,
        help_text="Primary image displayed in listings"
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text="Display order (lower numbers appear first)"
    )
    
    class Meta:
        ordering = ['order', 'created_at']
    
    def __str__(self):
        if self.offer:
            return f"{self.offer.name} - Image {self.order + 1}"
        return f"OfferImage {self.id or 'New'} - Image {self.order + 1}"
    
    def save(self, *args, **kwargs):
        # Ensure only one primary image per offer
        if self.is_primary and self.offer:
            OfferImage.objects.filter(
                offer=self.offer,
                is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        
        super().save(*args, **kwargs)
