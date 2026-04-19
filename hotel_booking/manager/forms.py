from django import forms
from core.models import Hotel, Room, RoomType, Extra, SeasonalPricing, RoomAmenity, RoomImage, RoomTypeAmenity
from bookings.models import Booking, RefundPolicy
from core.models import RoomAmenity, RoomImage, RoomTypeAmenity, SeasonalPricing
from offers.models import Offer, OfferCategory, OfferHighlight, OfferImage
from payments.models import Payment
from accounts.models import CustomUser


class BaseForm(forms.ModelForm):
    """Base form class with common widget customization"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add proper widgets and attributes to all fields
        for field_name, field in self.fields.items():
            if hasattr(field, 'widget') and field.widget:
                # Set placeholder if defined in mapping
                if field_name in self.placeholder_mapping:
                    field.widget.attrs['placeholder'] = self.placeholder_mapping[field_name]
                
                # Set appropriate classes based on field type
                if isinstance(field, forms.BooleanField):
                    field.widget.attrs['class'] = 'form-check-input'
                elif isinstance(field, forms.FileField):
                    field.widget.attrs['class'] = 'form-control file-input'
                elif isinstance(field, forms.DateField):
                    field.widget.attrs['class'] = 'form-control date-input'
                elif isinstance(field, forms.URLField):
                    field.widget.attrs['class'] = 'form-control url-input'
                elif isinstance(field, forms.EmailField):
                    field.widget.attrs['class'] = 'form-control email-input'
                elif isinstance(field, forms.IntegerField) or isinstance(field, forms.DecimalField):
                    field.widget.attrs['class'] = 'form-control number-input'
                elif isinstance(field, forms.ChoiceField):
                    field.widget.attrs['class'] = 'form-select'
                else:
                    field.widget.attrs['class'] = 'form-control'
                
                # Set aria-label for accessibility
                field.widget.attrs['aria-label'] = field.label or field_name.replace('_', ' ').title()


class HotelForm(BaseForm):
    placeholder_mapping = {
        'name': 'e.g., Grand Hotel Metropolitan',
        'description': 'Describe the hotel facilities and amenities',
        'address_line_1': 'e.g., 123 Main Street',
        'address_line_2': 'e.g., Suite 456 (optional)',
        'city': 'e.g., New York',
        'state': 'e.g., NY',
        'postal_code': 'e.g., 10001',
        'country': 'e.g., United States',
        'phone_number': 'e.g., +1-555-0123',
        'email': 'e.g., info@hotel.com',
        'website': 'e.g., https://www.hotel.com',
        'star_rating': '1-5 stars',
        'check_in_time': 'HH:MM format',
        'check_out_time': 'HH:MM format',
        'cancellation_policy': 'Describe cancellation terms',
        'pet_policy': 'Describe pet policy',
        'smoking_policy': 'Describe smoking policy',
    }
    
    class Meta:
        model = Hotel
        fields = '__all__'
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Describe hotel features and amenities'}),
            'cancellation_policy': forms.Textarea(attrs={'rows': 3}),
            'pet_policy': forms.Textarea(attrs={'rows': 3}),
            'smoking_policy': forms.Textarea(attrs={'rows': 3}),
        }


class RoomTypeForm(BaseForm):
    placeholder_mapping = {
        'name': 'e.g., Deluxe King Room',
        'description': 'Describe the room type features',
        'short_description': 'Brief description for listings',
        'max_capacity': 'e.g., 2',
        'room_size_sqm': 'e.g., 35',
        'room_size_sqft': 'e.g., 375',
        'extra_bed_charge': 'e.g., 25.00',
        'pet_charge': 'e.g., 50.00',
        'early_checkin_charge': 'e.g., 25.00',
        'late_checkout_charge': 'e.g., 25.00',
        'cancellation_policy': 'Room-specific cancellation terms',
        'virtual_tour_url': 'e.g., https://tour.example.com',
        'featured_image': 'Select an image file to upload',
    }
    
    class Meta:
        model = RoomType
        fields = '__all__'
        widgets = {
            'description': forms.Textarea(attrs={'rows': 6}),
            'cancellation_policy': forms.Textarea(attrs={'rows': 3}),
        }


class RoomForm(BaseForm):
    placeholder_mapping = {
        'room_number': 'e.g., 101',
        'floor': 'e.g., 1',
        'capacity': 'e.g., 2',
        'base_price': 'e.g., 199.99',
        'maintenance_notes': 'Notes about maintenance',
        'special_features': 'Unique features of this room',
        'renovation_notes': 'Renovation details',
        'staff_notes': 'Internal staff notes',
    }
    
    class Meta:
        model = Room
        fields = '__all__'
        widgets = {
            'maintenance_notes': forms.Textarea(attrs={'rows': 3}),
            'special_features': forms.Textarea(attrs={'rows': 3}),
            'renovation_notes': forms.Textarea(attrs={'rows': 3}),
            'staff_notes': forms.Textarea(attrs={'rows': 3}),
        }


class ExtraForm(BaseForm):
    placeholder_mapping = {
        'name': 'e.g., Breakfast Buffet',
        'description': 'Describe the extra service',
        'price': 'e.g., 15.00',
        'max_quantity': 'e.g., 4',
    }
    
    class Meta:
        model = Extra
        fields = '__all__'
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class SeasonalPricingForm(BaseForm):
    placeholder_mapping = {
        'name': 'e.g., Summer Season, Holiday Pricing',
        'price_multiplier': 'e.g., 1.25 (25% increase)',
    }
    
    class Meta:
        model = SeasonalPricing
        fields = '__all__'
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'placeholder': 'Select start date'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'placeholder': 'Select end date'}),
        }


class BookingForm(BaseForm):
    placeholder_mapping = {
        'guest_first_name': 'e.g., John',
        'guest_last_name': 'e.g., Smith',
        'guest_email': 'e.g., john.smith@email.com',
        'guest_phone': 'e.g., +1-555-0123',
        'guest_country': 'e.g., United States',
        'guest_address': 'e.g., 123 Main Street, Apt 4B',
        'guest_city': 'e.g., New York',
        'guest_postal_code': 'e.g., 10001',
        'guest_passport_number': 'e.g., AB123456789 (optional)',
        'room_rate': 'e.g., 250.00',
        'tax_amount': 'e.g., 37.50',
        'discount_amount': 'e.g., 25.00',
        'discount_type': 'e.g., Early Bird Discount',
        'special_requests': 'Any special requests or notes',
        'adults': 'e.g., 2',
        'children': 'e.g., 1',
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter user field to exclude managers and admins
        if 'user' in self.fields:
            self.fields['user'].queryset = self.fields['user'].queryset.exclude(
                user_type__in=['staff', 'admin']
            ).exclude(is_superuser=True)
        
        # Set room field to show room info clearly
        if 'room' in self.fields:
            self.fields['room'].queryset = self.fields['room'].queryset.select_related(
                'hotel', 'room_type'
            )
            self.fields['room'].label_from_instance = lambda obj: f"{obj.hotel.name} - {obj.room_type.name} #{obj.room_number}"

    class Meta:
        model = Booking
        fields = [
            # Core booking info
            'user', 'hotel', 'room', 'status', 'payment_status',
            
            # Guest information
            'guest_first_name', 'guest_last_name', 'guest_email', 'guest_phone',
            'guest_passport_number',
            
            # Address information
            'guest_country', 'guest_address', 'guest_city', 'guest_postal_code',
            
            # Dates and time
            'check_in_date', 'check_out_date', 'check_in_time', 'check_out_time',
            
            # Guest count
            'adults', 'children',
            
            # Pricing
            'room_rate', 'tax_amount', 'discount_amount', 'discount_type',
            
            # Additional
            'special_requests',
        ]
        widgets = {
            'check_in_date': forms.DateInput(attrs={'type': 'date', 'placeholder': 'Select check-in date'}),
            'check_out_date': forms.DateInput(attrs={'type': 'date', 'placeholder': 'Select check-out date'}),
            'check_in_time': forms.TimeInput(attrs={'type': 'time', 'placeholder': '15:00'}),
            'check_out_time': forms.TimeInput(attrs={'type': 'time', 'placeholder': '11:00'}),
            'guest_address': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Full address including street, apartment/unit number'}),
            'special_requests': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Dietary restrictions, accessibility needs, early check-in, etc.'}),
            'room_rate': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'tax_amount': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'discount_amount': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        check_in_date = cleaned_data.get('check_in_date')
        check_out_date = cleaned_data.get('check_out_date')
        room = cleaned_data.get('room')
        adults = cleaned_data.get('adults', 0)
        children = cleaned_data.get('children', 0)
        guest_email = cleaned_data.get('guest_email')
        guest_phone = cleaned_data.get('guest_phone')
        instance_pk = self.instance.pk if self.instance else None

        # Validate dates
        if check_in_date and check_out_date:
            if check_in_date >= check_out_date:
                raise forms.ValidationError('Check-out date must be after check-in date.')

        # CRITICAL: Validate room availability (prevent overbooking)
        if room and check_in_date and check_out_date:
            from django.db.models import Q
            # Find overlapping bookings (exclude current booking if editing)
            overlapping_bookings = Booking.objects.filter(
                Q(room=room) &
                Q(status__in=['confirmed', 'pending']) &
                Q(check_in_date__lt=check_out_date) &
                Q(check_out_date__gt=check_in_date)
            )
            # Exclude current booking if editing
            if instance_pk:
                overlapping_bookings = overlapping_bookings.exclude(pk=instance_pk)
            
            if overlapping_bookings.exists():
                existing_booking = overlapping_bookings.first()
                raise forms.ValidationError(
                    f'Room is already booked from {existing_booking.check_in_date} to {existing_booking.check_out_date}. '
                    f'Please select a different room or dates.'
                )

        # Validate room capacity
        if room and (adults + children) > room.capacity:
            raise forms.ValidationError(f'Total guests ({adults + children}) exceed room capacity ({room.capacity}).')

        # Validate email format (comprehensive check)
        if guest_email:
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, guest_email):
                raise forms.ValidationError('Please enter a valid email address (e.g., john@example.com).')

        # Validate phone number (comprehensive check)
        if guest_phone:
            import re
            # Phone pattern: allows formats like +1-555-0123, (555) 012-3456, +1 555 0123, etc.
            # Requires at least 7 digits
            digits_only = re.sub(r'\D', '', guest_phone)
            if len(digits_only) < 7:
                raise forms.ValidationError('Please enter a valid phone number with at least 7 digits.')
            if len(digits_only) > 15:
                raise forms.ValidationError('Phone number appears to be invalid (too long).')

        return cleaned_data


class RoomAmenityForm(BaseForm):
    placeholder_mapping = {
        'name': 'e.g., High-speed WiFi, Mini Bar',
        'description': 'Describe the amenity',
    }
    
    class Meta:
        model = RoomAmenity
        fields = '__all__'
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class RoomImageForm(BaseForm):
    placeholder_mapping = {
        'image': 'Select an image file to upload',
        'image_alt_text': 'e.g., Deluxe room with king bed',
        'caption': 'e.g., Spacious room with city view',
    }
    
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
    
    def clean(self):
        cleaned_data = super().clean()
        image = cleaned_data.get('image')
        
        if image:
            # Validate file size
            if image.size > self.MAX_FILE_SIZE:
                raise forms.ValidationError(f'Image file is too large. Maximum size is 5MB, but you uploaded {image.size / 1024 / 1024:.2f}MB.')
            
            # Validate file extension
            import os
            ext = os.path.splitext(image.name)[1].lower().lstrip('.')
            if ext not in self.ALLOWED_EXTENSIONS:
                raise forms.ValidationError(f'Invalid file type. Allowed types: {', '.join(self.ALLOWED_EXTENSIONS)}')
        
        return cleaned_data

    class Meta:
        model = RoomImage
        fields = '__all__'


class RoomTypeAmenityForm(BaseForm):
    placeholder_mapping = {
        'additional_charge': 'e.g., 10.00',
    }
    
    class Meta:
        model = RoomTypeAmenity
        fields = '__all__'


# Offer Management Forms
class OfferForm(BaseForm):
    """Form for creating and editing offers"""
    placeholder_mapping = {
        'name': 'e.g., Summer Special Discount',
        'description': 'Describe the offer details and terms',
        'short_description': 'Brief description for listings',
        'discount_percentage': 'e.g., 15',
        'discount_amount': 'e.g., 50.00',
        'package_price': 'e.g., 299.99',
        'minimum_stay': 'e.g., 2',
        'maximum_stay': 'e.g., 7',
        'minimum_advance_booking': 'e.g., 7',
        'maximum_advance_booking': 'e.g., 90',
        'total_bookings_limit': 'e.g., 100',
        'terms_and_conditions': 'Enter the terms and conditions for this offer',
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set date widgets
        self.fields['valid_from'].widget = forms.DateInput(attrs={'type': 'date'})
        self.fields['valid_to'].widget = forms.DateInput(attrs={'type': 'date'})

        # Limit hotel choices to active hotels only
        self.fields['hotel'].queryset = Hotel.objects.filter(is_active=True)

        # Limit category choices to active categories
        self.fields['category'].queryset = OfferCategory.objects.filter(is_active=True)

    def clean(self):
        cleaned_data = super().clean()
        valid_from = cleaned_data.get('valid_from')
        valid_to = cleaned_data.get('valid_to')

        # Validate date range
        if valid_from and valid_to:
            if valid_from > valid_to:
                raise forms.ValidationError(
                    'Offer start date (valid_from) must be before or equal to end date (valid_to).'
                )

        return cleaned_data

    class Meta:
        model = Offer
        fields = [
            'hotel', 'category', 'name', 'description', 'short_description', 'offer_type',
            'discount_type', 'discount_percentage', 'discount_amount', 'package_price',
            'valid_from', 'valid_to', 'minimum_stay', 'maximum_stay',
            'minimum_advance_booking', 'maximum_advance_booking',
            'total_bookings_limit', 'is_featured', 'is_active', 'is_combinable',
            'terms_and_conditions'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'short_description': forms.Textarea(attrs={'rows': 2}),
            'terms_and_conditions': forms.Textarea(attrs={'rows': 6}),
        }


class OfferCategoryForm(BaseForm):
    """Form for creating and editing offer categories"""
    placeholder_mapping = {
        'name': 'e.g., Seasonal Offers',
        'description': 'Describe this category of offers',
        'order': 'e.g., 1',
    }
    
    class Meta:
        model = OfferCategory
        fields = ['name', 'description', 'order', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class OfferHighlightForm(BaseForm):
    """Form for creating and editing offer highlights"""
    placeholder_mapping = {
        'title': 'e.g., Free Breakfast Included',
        'description': 'Optional detailed description of the highlight',
        'order': 'e.g., 1',
    }

    def __init__(self, *args, **kwargs):
        self.offer_id = kwargs.pop('offer_id', None)
        super().__init__(*args, **kwargs)
        
        # If no offer_id is provided (global create), show offer selection
        if not self.offer_id:
            self.fields['offer'] = forms.ModelChoiceField(
                queryset=Offer.objects.filter(is_active=True),
                empty_label="Select an offer",
                widget=forms.Select(attrs={'class': 'form-select'})
            )
        else:
            # If offer_id is provided, hide the offer field but keep it in the form
            self.fields['offer'] = forms.ModelChoiceField(
                queryset=Offer.objects.filter(is_active=True),
                widget=forms.HiddenInput()
            )

    class Meta:
        model = OfferHighlight
        fields = ['offer', 'title', 'description', 'order']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class BulkBookingStatusForm(forms.Form):
    STATUS_CHOICES = Booking.STATUS_CHOICES
    
    booking_ids = forms.CharField(
        widget=forms.HiddenInput(),
        required=True,
        help_text="Comma-separated booking IDs"
    )
    new_status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='New Status',
        help_text='Select the status to apply to all selected bookings'
    )
    reason = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        required=False,
        label='Reason for Status Change',
        help_text='Optional reason for the bulk status update'
    )
    
    def clean_booking_ids(self):
        booking_ids = self.cleaned_data.get('booking_ids', '').strip()
        if not booking_ids:
            raise forms.ValidationError('At least one booking ID is required.')
        return [id.strip() for id in booking_ids.split(',') if id.strip()]

class OfferImageForm(BaseForm):
    """Form for creating and editing offer images"""
    placeholder_mapping = {
        'alt_text': 'e.g., Beautiful ocean view from deluxe suite',
        'caption': 'e.g., Luxury suite with ocean view',
        'order': 'e.g., 1',
    }
    
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
    
    def __init__(self, *args, **kwargs):
        self.offer_id = kwargs.pop('offer_id', None)
        super().__init__(*args, **kwargs)
        
        # If offer_id is provided, add it as a hidden field
        if self.offer_id:
            try:
                offer = Offer.objects.get(id=self.offer_id)
                self.fields['offer'] = forms.ModelChoiceField(
                    queryset=Offer.objects.filter(id=self.offer_id),
                    initial=offer,
                    widget=forms.HiddenInput(),
                    required=True
                )
                # Set the initial value for the instance
                if not self.instance.pk:
                    self.instance.offer = offer
            except Offer.DoesNotExist:
                # If offer doesn't exist, show selection dropdown
                self.fields['offer'] = forms.ModelChoiceField(
                    queryset=Offer.objects.filter(is_active=True),
                    empty_label="Select an offer",
                    widget=forms.Select(attrs={'class': 'form-select'}),
                    required=True
                )
        else:
            # If no offer_id is provided (global create), show offer selection
            self.fields['offer'] = forms.ModelChoiceField(
                queryset=Offer.objects.filter(is_active=True),
                empty_label="Select an offer",
                widget=forms.Select(attrs={'class': 'form-select'}),
                required=True
            )
    
    def clean(self):
        cleaned_data = super().clean()
        image = cleaned_data.get('image')
        
        if image:
            # Validate file size
            if image.size > self.MAX_FILE_SIZE:
                raise forms.ValidationError(f'Image file is too large. Maximum size is 5MB.')
            
            # Validate file extension
            import os
            ext = os.path.splitext(image.name)[1].lower().lstrip('.')
            if ext not in self.ALLOWED_EXTENSIONS:
                raise forms.ValidationError(f'Invalid file type. Allowed types: {", ".join(self.ALLOWED_EXTENSIONS)}')
        
        return cleaned_data
    
    class Meta:
        model = OfferImage
        fields = ['offer', 'image', 'alt_text', 'caption', 'order']


class RefundPolicyForm(BaseForm):
    """Form for configuring hotel refund policies"""
    
    placeholder_mapping = {
        'free_cancellation_days': 'e.g., 7 (free cancellation up to 7 days before check-in)',
        'non_refundable_deposit_percentage': 'e.g., 10 (10/% service fee non-refundable)',
        'policy_description': 'Guest-friendly explanation of refund policy',
    }
    
    class Meta:
        model = RefundPolicy
        fields = [
            'free_cancellation_days',
            'refund_schedule',
            'non_refundable_deposit_percentage',
            'policy_description'
        ]
        widgets = {
            'refund_schedule': forms.Textarea(attrs={
                'rows': 6,
                'placeholder': 'JSON format: {"7": 100, "3": 75, "1": 50, "0": 0}',
                'help_text': 'Days before check-in: refund percentage'
            }),
            'policy_description': forms.Textarea(attrs={'rows': 4}),
        }


class PaymentForm(BaseForm):
    """Form for creating and managing payments"""
    placeholder_mapping = {
        'amount': 'e.g., 250.00',
        'currency': 'e.g., SAR',
        'transaction_id': 'Transaction ID from payment gateway (if available)',
        'idempotency_key': 'Unique request key for idempotency',
    }
    
    class Meta:
        model = Payment
        fields = ['booking', 'amount', 'currency', 'method', 'status', 'transaction_id', 'idempotency_key']
        widgets = {
            'booking': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'currency': forms.TextInput(attrs={'maxlength': '3'}),
            'method': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'transaction_id': forms.TextInput(attrs={'maxlength': '100'}),
            'idempotency_key': forms.TextInput(attrs={'maxlength': '100'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        booking = cleaned_data.get('booking')
        amount = cleaned_data.get('amount')
        
        # Validate that amount is positive
        if amount and amount <= 0:
            raise forms.ValidationError('Payment amount must be greater than zero.')
        
        # Validate currency code
        currency = cleaned_data.get('currency', 'SAR').upper()
        if len(currency) != 3:
            raise forms.ValidationError('Currency code must be exactly 3 characters (e.g., SAR, USD).')
        cleaned_data['currency'] = currency
        
        return cleaned_data


class ProfileUpdateForm(forms.ModelForm):
    """Form for updating manager profile information"""
    
    email = forms.EmailField(
        label='Email Address',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'your.email@example.com'
        })
    )
    
    username = forms.CharField(
        label='Username',
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your login username'
        })
    )
    
    first_name = forms.CharField(
        label='First Name',
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your first name'
        })
    )
    
    last_name = forms.CharField(
        label='Last Name',
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your last name'
        })
    )
    
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name']
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        # Check if username is already taken by another user
        from accounts.models import CustomUser
        if CustomUser.objects.filter(username=username).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('This username is already taken. Please choose a different one.')
        return username
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        # Check if email is already taken by another user
        from accounts.models import CustomUser
        if CustomUser.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('This email address is already in use. Please use a different one.')
        return email


class ChangePasswordForm(forms.Form):
    """Form for changing password"""
    
    current_password = forms.CharField(
        label='Current Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your current password',
            'autocomplete': 'current-password'
        })
    )
    
    new_password = forms.CharField(
        label='New Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your new password',
            'autocomplete': 'new-password'
        }),
        help_text='Password must be at least 8 characters long.'
    )
    
    confirm_password = forms.CharField(
        label='Confirm New Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Re-enter your new password',
            'autocomplete': 'new-password'
        })
    )
    
    def clean_new_password(self):
        new_password = self.cleaned_data.get('new_password')
        if new_password and len(new_password) < 8:
            raise forms.ValidationError('Password must be at least 8 characters long.')
        return new_password
    
    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if new_password and confirm_password:
            if new_password != confirm_password:
                raise forms.ValidationError('The new passwords do not match. Please try again.')
        
        return cleaned_data
