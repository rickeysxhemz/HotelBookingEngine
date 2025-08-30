# Django imports
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from datetime import datetime, date, timedelta
import uuid

# Local imports
from core.models import Room, Extra, TimestampedModel


class BookingManager(models.Manager):
    """Custom manager for Booking model"""
    
    def active_bookings(self):
        """Get active bookings (confirmed, checked_in)"""
        return self.filter(status__in=['confirmed', 'checked_in'])
    
    def for_hotel(self, hotel):
        """Get bookings for a specific hotel"""
        return self.filter(room__hotel=hotel)
    
    def for_date_range(self, start_date, end_date):
        """Get bookings that overlap with date range"""
        return self.filter(
            check_in__lt=end_date,
            check_out__gt=start_date
        )
    
    def upcoming(self):
        """Get upcoming bookings"""
        today = timezone.now().date()
        return self.filter(check_in__gte=today, status='confirmed')
    
    def current(self):
        """Get current bookings (checked in)"""
        return self.filter(status='checked_in')


class Booking(TimestampedModel):
    """Enhanced booking model with complete booking lifecycle"""
    
    BOOKING_STATUS_CHOICES = [
        ('pending', 'Pending Confirmation'),
        ('confirmed', 'Confirmed'),
        ('checked_in', 'Checked In'),
        ('checked_out', 'Checked Out'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Payment Pending'),
        ('partial', 'Partially Paid'),
        ('paid', 'Fully Paid'),
        ('refunded', 'Refunded'),
        ('failed', 'Payment Failed'),
    ]
    
    CANCELLATION_REASON_CHOICES = [
        ('guest_request', 'Guest Request'),
        ('hotel_request', 'Hotel Request'),
        ('payment_failure', 'Payment Failure'),
        ('no_show', 'No Show'),
        ('overbooking', 'Overbooking'),
        ('force_majeure', 'Force Majeure'),
        ('other', 'Other'),
    ]
    
    # Primary fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking_reference = models.CharField(max_length=20, unique=True, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='bookings'
    )
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='bookings')
    
    # Booking details
    check_in = models.DateField()
    check_out = models.DateField()
    guests = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        null=True
    )
    
    # Status tracking
    status = models.CharField(
        max_length=20, 
        choices=BOOKING_STATUS_CHOICES, 
        default='pending'
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending'
    )
    
    # Pricing
    room_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    extras_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    tax_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    total_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    # Guest information
    primary_guest_name = models.CharField(max_length=100, blank=True,null=True)
    primary_guest_email = models.EmailField(blank=True,null=True)
    primary_guest_phone = models.CharField(max_length=20, blank=True,null=True)

    # Special requests and notes
    special_requests = models.TextField(blank=True, help_text='Guest special requests',null=True)
    internal_notes = models.TextField(blank=True, help_text='Internal hotel notes',null=True)

    # Timestamps for booking lifecycle
    booking_date = models.DateTimeField(auto_now_add=True)
    confirmation_date = models.DateTimeField(null=True, blank=True)
    check_in_time = models.DateTimeField(null=True, blank=True)
    check_out_time = models.DateTimeField(null=True, blank=True)
    
    # Cancellation details
    cancellation_date = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.CharField(
        max_length=20,
        choices=CANCELLATION_REASON_CHOICES,
        blank=True,
        null=True
    )
    cancellation_notes = models.TextField(blank=True,null=True)

    # Source tracking
    booking_source = models.CharField(
        max_length=50,
        choices=[
            ('direct', 'Direct Booking'),
            ('phone', 'Phone Booking'),
            ('walk_in', 'Walk-in'),
            ('agent', 'Travel Agent'),
        ],
        default='walk_in'
    )
    
    # Relationships
    extras = models.ManyToManyField(Extra, through='BookingExtra', blank=True,null=True)
    
    objects = BookingManager()
    
    class Meta:
        verbose_name = 'Booking'
        verbose_name_plural = 'Bookings'
        ordering = ['-booking_date']
        indexes = [
            models.Index(fields=['status', 'check_in']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['room', 'check_in', 'check_out']),
            models.Index(fields=['booking_reference']),
        ]
    
    def __str__(self):
        return f"Booking {self.booking_reference} - {self.primary_guest_name}"
    
    def save(self, *args, **kwargs):
        # Generate booking reference if not exists
        if not self.booking_reference:
            self.booking_reference = self._generate_booking_reference()
        
        # Auto-populate guest info from user if not provided
        if not self.primary_guest_name and self.user:
            self.primary_guest_name = self.user.get_full_name() or self.user.username
        if not self.primary_guest_email and self.user:
            self.primary_guest_email = self.user.email
        if not self.primary_guest_phone and self.user:
            self.primary_guest_phone = self.user.phone_number or ''
        
        super().save(*args, **kwargs)
    
    def clean(self):
        """Validate booking data"""
        # Validate dates
        if self.check_in >= self.check_out:
            raise ValidationError('Check-out date must be after check-in date')
        
        # Validate guest count
        if self.room and self.guests > self.room.capacity:
            raise ValidationError(
                f'Number of guests ({self.guests}) exceeds room capacity ({self.room.capacity})'
            )
        
        # Validate past dates
        if self.check_in < timezone.now().date():
            raise ValidationError('Check-in date cannot be in the past')
    
    def _generate_booking_reference(self):
        """Generate unique booking reference"""
        import string
        import random
        
        # Format: BK + YYYYMMDD + 4 random chars
        date_part = timezone.now().strftime('%Y%m%d')
        random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        
        reference = f"BK{date_part}{random_part}"
        
        # Ensure uniqueness
        while Booking.objects.filter(booking_reference=reference).exists():
            random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
            reference = f"BK{date_part}{random_part}"
        
        return reference
    
    @property
    def nights(self):
        """Number of nights for the booking"""
        return (self.check_out - self.check_in).days
    
    @property
    def is_active(self):
        """Check if booking is active (confirmed or checked in)"""
        return self.status in ['confirmed', 'checked_in']
    
    @property
    def can_be_cancelled(self):
        """Check if booking can be cancelled"""
        if self.status in ['cancelled', 'checked_out', 'no_show']:
            return False
        
        # Check cancellation policy (24 hours before check-in)
        cutoff_time = timezone.now() + timedelta(hours=24)
        check_in_datetime = timezone.make_aware(
            datetime.combine(self.check_in, timezone.now().time())
        )
        
        return cutoff_time < check_in_datetime
    
    @property
    def can_check_in(self):
        """Check if guest can check in"""
        if self.status != 'confirmed':
            return False
        
        today = timezone.now().date()
        return self.check_in == today
    
    @property
    def can_check_out(self):
        """Check if guest can check out"""
        return self.status == 'checked_in'
    
    def calculate_total_price(self):
        """Calculate total booking price including extras and taxes"""
        from core.services import PricingService
        
        # Calculate room price
        room_price = PricingService.calculate_room_price(
            self.room, self.check_in, self.check_out
        )
        
        # Calculate extras price
        extras_price = sum(
            booking_extra.calculate_total_price()
            for booking_extra in self.booking_extras.all()
        )
        
        # Calculate tax (10% for example)
        subtotal = room_price + extras_price
        tax_rate = Decimal('0.10')
        tax_amount = subtotal * tax_rate
        
        total_price = subtotal + tax_amount
        
        # Update booking prices
        self.room_price = room_price
        self.extras_price = extras_price
        self.tax_amount = tax_amount
        self.total_price = total_price
        
        return {
            'room_price': room_price,
            'extras_price': extras_price,
            'subtotal': subtotal,
            'tax_amount': tax_amount,
            'total_price': total_price
        }
    
    def confirm_booking(self):
        """Confirm the booking"""
        if self.status == 'pending':
            self.status = 'confirmed'
            self.confirmation_date = timezone.now()
            self.save(update_fields=['status', 'confirmation_date'])
    
    def check_in_guest(self):
        """Check in the guest"""
        if self.status == 'confirmed' and self.can_check_in:
            self.status = 'checked_in'
            self.check_in_time = timezone.now()
            self.save(update_fields=['status', 'check_in_time'])
    
    def check_out_guest(self):
        """Check out the guest"""
        if self.status == 'checked_in':
            self.status = 'checked_out'
            self.check_out_time = timezone.now()
            self.save(update_fields=['status', 'check_out_time'])
    
    def cancel_booking(self, reason='guest_request', notes=''):
        """Cancel the booking"""
        if self.can_be_cancelled:
            self.status = 'cancelled'
            self.cancellation_date = timezone.now()
            self.cancellation_reason = reason
            self.cancellation_notes = notes
            self.save(update_fields=[
                'status', 'cancellation_date', 'cancellation_reason', 'cancellation_notes'
            ])


class BookingExtra(TimestampedModel):
    """Through model for booking extras with quantities and pricing"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.ForeignKey(
        Booking, 
        on_delete=models.CASCADE, 
        related_name='booking_extras'
    )
    extra = models.ForeignKey(Extra, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)]
    )
    unit_price = models.DecimalField(
        max_digits=8, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    total_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    class Meta:
        verbose_name = 'Booking Extra'
        verbose_name_plural = 'Booking Extras'
        unique_together = ['booking', 'extra']
    
    def __str__(self):
        return f"{self.booking.booking_reference} - {self.extra.name} (x{self.quantity})"
    
    def save(self, *args, **kwargs):
        # Auto-calculate prices if not set
        if not self.unit_price:
            self.unit_price = self.extra.price
        
        if not self.total_price:
            self.total_price = self.calculate_total_price()
        
        super().save(*args, **kwargs)
    
    def calculate_total_price(self):
        """Calculate total price for this extra"""
        return self.extra.calculate_total_price(
            quantity=self.quantity,
            nights=self.booking.nights,
            guests=self.booking.guests
        )


class BookingHistory(TimestampedModel):
    """Track booking status changes and activities"""
    
    ACTION_CHOICES = [
        ('created', 'Booking Created'),
        ('confirmed', 'Booking Confirmed'),
        ('modified', 'Booking Modified'),
        ('checked_in', 'Guest Checked In'),
        ('checked_out', 'Guest Checked Out'),
        ('cancelled', 'Booking Cancelled'),
        ('payment_received', 'Payment Received'),
        ('refund_processed', 'Refund Processed'),
        ('note_added', 'Note Added'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.ForeignKey(
        Booking, 
        on_delete=models.CASCADE, 
        related_name='history'
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES,default='created')
    description = models.TextField(null=True, blank=True)
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Store old and new values for changes
    old_values = models.JSONField(blank=True, null=True)
    new_values = models.JSONField(blank=True, null=True)
    
    class Meta:
        verbose_name = 'Booking History'
        verbose_name_plural = 'Booking Histories'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.booking.booking_reference} - {self.get_action_display()}"


class BookingGuest(TimestampedModel):
    """Additional guests for a booking"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.ForeignKey(
        Booking, 
        on_delete=models.CASCADE, 
        related_name='additional_guests'
    )
    first_name = models.CharField(max_length=50,null=True, blank=True)
    last_name = models.CharField(max_length=50,null=True, blank=True)
    age_group = models.CharField(
        max_length=10,
        choices=[
            ('adult', 'Adult'),
            ('child', 'Child'),
            ('infant', 'Infant'),
        ],
        default='adult'
    )
    
    class Meta:
        verbose_name = 'Booking Guest'
        verbose_name_plural = 'Booking Guests'
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.get_age_group_display()})"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
