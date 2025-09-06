from django import forms
from core.models import Hotel, Room, RoomType, Extra, SeasonalPricing, RoomAmenity, RoomImage, RoomTypeAmenity
from bookings.models import Booking, BookingExtra, BookingGuest
from bookings.models import BookingHistory
from core.models import RoomAmenity, RoomImage, RoomTypeAmenity, SeasonalPricing
from offers.models import Offer, OfferCategory, OfferHighlight, OfferImage


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
        'primary_guest_name': 'e.g., John Smith',
        'primary_guest_email': 'e.g., john.smith@email.com',
        'primary_guest_phone': 'e.g., +1-555-0123',
        'special_requests': 'Any special requests or notes',
        'guests': 'e.g., 2',
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter user field to exclude managers and admins
        if 'user' in self.fields:
            self.fields['user'].queryset = self.fields['user'].queryset.exclude(
                user_type__in=['staff', 'admin']
            ).exclude(is_superuser=True)

    class Meta:
        model = Booking
        fields = [
            'user', 'room', 'check_in', 'check_out', 'guests',
            'status', 'payment_status', 'primary_guest_name',
            'primary_guest_email', 'primary_guest_phone', 'special_requests',
        ]
        widgets = {
            'check_in': forms.DateInput(attrs={'type': 'date', 'placeholder': 'Select check-in date'}),
            'check_out': forms.DateInput(attrs={'type': 'date', 'placeholder': 'Select check-out date'}),
            'special_requests': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Dietary restrictions, accessibility needs, etc.'}),
        }


class BookingExtraForm(BaseForm):
    placeholder_mapping = {
        'quantity': 'e.g., 2',
        'unit_price': 'e.g., 15.00',
        'total_price': 'e.g., 30.00',
    }
    
    class Meta:
        model = BookingExtra
        fields = '__all__'


class BookingGuestForm(BaseForm):
    placeholder_mapping = {
        'first_name': 'e.g., Jane',
        'last_name': 'e.g., Doe',
        'email': 'e.g., jane.doe@email.com',
        'phone': 'e.g., +1-555-0123',
        'date_of_birth': 'YYYY-MM-DD format',
    }
    
    class Meta:
        model = BookingGuest
        fields = '__all__'
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'placeholder': 'Select date of birth'}),
        }


class BookingHistoryForm(BaseForm):
    placeholder_mapping = {
        'action': 'e.g., Check-in, Payment, Status Change',
        'description': 'Describe the action taken',
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter performed_by field to exclude managers and admins - only normal users
        if 'performed_by' in self.fields:
            self.fields['performed_by'].queryset = self.fields['performed_by'].queryset.exclude(
                user_type__in=['staff', 'admin']
            ).exclude(is_superuser=True)

    class Meta:
        model = BookingHistory
        fields = ['booking', 'action', 'description', 'performed_by']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


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

    class Meta:
        model = OfferHighlight
        fields = ['title', 'description', 'order']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class OfferImageForm(BaseForm):
    """Form for creating and editing offer images"""
    placeholder_mapping = {
        'caption': 'e.g., Luxury suite with ocean view',
        'order': 'e.g., 1',
    }
    
    class Meta:
        model = OfferImage
        fields = ['image', 'caption', 'order', 'is_primary']
        widgets = {
            'image': forms.FileInput(attrs={'accept': 'image/*'}),
        }

