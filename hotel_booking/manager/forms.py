from django import forms
from core.models import Hotel, Room, RoomType, Extra, SeasonalPricing, RoomAmenity, RoomImage, RoomTypeAmenity
from bookings.models import Booking, BookingExtra, BookingGuest
from bookings.models import BookingHistory
from core.models import RoomAmenity, RoomImage, RoomTypeAmenity, SeasonalPricing


class HotelForm(forms.ModelForm):
    class Meta:
        model = Hotel
        fields = '__all__'


class RoomTypeForm(forms.ModelForm):
    class Meta:
        model = RoomType
        fields = '__all__'


class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = '__all__'


class ExtraForm(forms.ModelForm):
    class Meta:
        model = Extra
        fields = '__all__'


class SeasonalPricingForm(forms.ModelForm):
    class Meta:
        model = SeasonalPricing
        fields = '__all__'


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = [
            'user', 'room', 'check_in', 'check_out', 'guests',
            'status', 'payment_status', 'primary_guest_name',
            'primary_guest_email', 'primary_guest_phone', 'special_requests',
        ]


class BookingExtraForm(forms.ModelForm):
    class Meta:
        model = BookingExtra
        fields = '__all__'


class BookingGuestForm(forms.ModelForm):
    class Meta:
        model = BookingGuest
        fields = '__all__'


class BookingHistoryForm(forms.ModelForm):
    class Meta:
        model = BookingHistory
        fields = ['booking', 'action', 'description', 'performed_by']


class RoomAmenityForm(forms.ModelForm):
    class Meta:
        model = RoomAmenity
        fields = '__all__'


class RoomImageForm(forms.ModelForm):
    class Meta:
        model = RoomImage
        fields = '__all__'


class RoomTypeAmenityForm(forms.ModelForm):
    class Meta:
        model = RoomTypeAmenity
        fields = '__all__'

