from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from django.core.validators import RegexValidator
from django.urls import reverse
from core.validators import validate_image_file
import uuid


class CustomUserManager(BaseUserManager):
    def create_user(self, email, username, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set.")
        if not username:
            raise ValueError("The Username field must be set.")
        
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.is_active = True
        
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if not extra_fields.get('is_staff'):
            raise ValueError("Superuser must have is_staff=True.")
        if not extra_fields.get('is_superuser'):
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, username, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('P', 'Prefer not to say'),
    ]
    
    USER_TYPE_CHOICES = [
        ('guest', 'Guest'),
        ('staff', 'Staff'),
        ('admin', 'Admin'),
    ]
    
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, verbose_name='Email Address')
    username = models.CharField(max_length=150, unique=True)
    first_name = models.CharField(max_length=30, blank=True, verbose_name='First Name')
    last_name = models.CharField(max_length=30, blank=True, verbose_name='Last Name')
    phone_number = models.CharField(
        validators=[phone_regex], 
        max_length=17, 
        blank=True, 
        verbose_name='Phone Number'
    )
    date_of_birth = models.DateField(null=True, blank=True, verbose_name='Date of Birth')
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='guest')
    
    # Address information
    address_line_1 = models.CharField(max_length=255, blank=True, verbose_name='Address Line 1')
    address_line_2 = models.CharField(max_length=255, blank=True, verbose_name='Address Line 2')
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True, default='United States')
    
    # Preferences
    newsletter_subscription = models.BooleanField(default=False, verbose_name='Subscribe to Newsletter')
    
    # Profile information
    profile_picture = models.ImageField(
        upload_to='profile_pictures/', 
        blank=True, 
        null=True,
        verbose_name='Profile Picture',
        validators=[validate_image_file]
    )
    bio = models.TextField(max_length=500, blank=True, verbose_name='Bio')
    
    # System fields
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False, verbose_name='Email Verified')
    date_joined = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)
    
    # Authentication
    failed_login_attempts = models.PositiveIntegerField(default=0)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        db_table = 'accounts_customuser'
        ordering = ['-date_joined']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['username']),
            models.Index(fields=['is_active', 'is_verified']),
            models.Index(fields=['user_type']),
        ]

    def __repr__(self):
        return f"<CustomUser {self.email}>"

    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"

    def get_full_name(self):
        """Return the first_name plus the last_name, with a space in between."""
        full_name = f'{self.first_name} {self.last_name}'
        return full_name.strip() or self.username

    def get_short_name(self):
        """Return the short name for the user."""
        return self.first_name or self.username

    def get_absolute_url(self):
        """Return the URL for the user's profile."""
        return reverse('accounts:profile', kwargs={'pk': self.pk})
    
    def get_full_address(self):
        """Return the full address as a formatted string."""
        address_parts = [
            self.address_line_1,
            self.address_line_2,
            f"{self.city}, {self.state} {self.postal_code}",
            self.country
        ]
        return ', '.join([part for part in address_parts if part])
    
    def age(self):
        """Calculate and return the user's age."""
        if self.date_of_birth:
            today = timezone.now().date()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return None
    
    @property
    def is_guest(self):
        return self.user_type == 'guest'
    
    @property
    def is_hotel_staff(self):
        return self.user_type == 'staff'
    
    @property
    def is_admin_user(self):
        return self.user_type == 'admin' or self.is_superuser


class UserProfile(models.Model):
    """Extended profile for additional user information"""
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile')
    
    # Emergency contact
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=17, blank=True)
    emergency_contact_relationship = models.CharField(max_length=50, blank=True)
    
    # Travel preferences
    preferred_room_type = models.CharField(max_length=50, blank=True)
    dietary_restrictions = models.TextField(blank=True)
    accessibility_needs = models.TextField(blank=True)
    special_requests = models.TextField(blank=True)
    
    # Basic statistics
    total_bookings = models.PositiveIntegerField(default=0)
    total_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
    
    def __str__(self):
        return f"{self.user.get_full_name()}'s Profile"


class EmailVerificationToken(models.Model):
    """Token for email verification"""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'Email Verification Token'
        verbose_name_plural = 'Email Verification Tokens'
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['user', 'used']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"Verification token for {self.user.email}"
    
    def is_expired(self):
        return timezone.now() > self.expires_at


class PasswordResetToken(models.Model):
    """Token for password reset"""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'Password Reset Token'
        verbose_name_plural = 'Password Reset Tokens'
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['user', 'used']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"Password reset token for {self.user.email}"
    
    def is_expired(self):
        return timezone.now() > self.expires_at


class BlacklistedToken(models.Model):
    """Model to store blacklisted JWT tokens"""
    jti = models.CharField(max_length=255, unique=True, db_index=True, 
                          help_text="JWT Token Identifier")
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    token_type = models.CharField(max_length=20, choices=[
        ('access', 'Access Token'),
        ('refresh', 'Refresh Token'),
    ], default='refresh')
    blacklisted_at = models.DateTimeField(auto_now_add=True)
    reason = models.CharField(max_length=100, default='logout', 
                             help_text="Reason for blacklisting")
    
    class Meta:
        verbose_name = 'Blacklisted Token'
        verbose_name_plural = 'Blacklisted Tokens'
        ordering = ['-blacklisted_at']
        indexes = [
            models.Index(fields=['jti']),
        ]
    
    def __str__(self):
        return f"Blacklisted {self.token_type} token ({self.jti[:8]}...)"
    
    @classmethod
    def is_blacklisted(cls, jti):
        """Check if a token JTI is blacklisted"""
        return cls.objects.filter(jti=jti).exists()
    
    @classmethod
    def blacklist_token(cls, jti, user=None, token_type='refresh', reason='logout'):
        """Blacklist a token by its JTI"""
        token, created = cls.objects.get_or_create(
            jti=jti,
            defaults={
                'user': user,
                'token_type': token_type,
                'reason': reason,
            }
        )
        return token, created
    