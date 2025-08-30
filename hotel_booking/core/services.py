# Django imports
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Tuple

# Local imports
from .models import Hotel, Room, RoomType, Extra, SeasonalPricing


class RoomAvailabilityService:
    """Service class for handling room availability logic"""
    
    @staticmethod
    def get_available_rooms(hotel: Hotel, check_in: date, check_out: date, guests: int = 1) -> models.QuerySet:
        """
        Get available rooms for given criteria.
        Returns rooms that can accommodate the guests and are available for the dates.
        """
        from bookings.models import Booking
        
        # Get all active rooms that can accommodate the guests
        base_queryset = Room.objects.filter(
            hotel=hotel,
            capacity__gte=guests,
            is_active=True,
            is_maintenance=False
        ).select_related('room_type', 'hotel')
        
        # Exclude rooms with conflicting bookings
        conflicting_bookings = Booking.objects.filter(
            room__hotel=hotel,
            status__in=['confirmed', 'checked_in'],
            check_in__lt=check_out,
            check_out__gt=check_in
        ).values_list('room_id', flat=True)
        
        available_rooms = base_queryset.exclude(id__in=conflicting_bookings)
        
        return available_rooms.order_by('capacity', 'base_price')
    
    @staticmethod
    def get_room_combinations_for_guests(hotel: Hotel, check_in: date, check_out: date, guests: int) -> List[Dict]:
        """
        Get different room combinations that can accommodate the requested number of guests.
        Returns combinations like: single room for 3 guests, or 1+2 capacity rooms, etc.
        """
        available_rooms = RoomAvailabilityService.get_available_rooms(
            hotel, check_in, check_out, guests=1  # Get all available rooms
        )
        
        combinations = []
        
        # Single room solutions
        single_rooms = available_rooms.filter(capacity__gte=guests)
        for room in single_rooms:
            price = PricingService.calculate_room_price(room, check_in, check_out)
            combinations.append({
                'type': 'single_room',
                'rooms': [room],
                'total_capacity': room.capacity,
                'total_price': price,
                'room_count': 1
            })
        
        # Multi-room solutions 
        # Include multi-room options when:
        # 1. Large groups (>2 guests) that might prefer separate rooms
        # 2. When no single room can accommodate all guests
        # 3. To provide customers with accommodation flexibility
        single_room_available = single_rooms.exists()
        
        if guests > 2 or not single_room_available:
            multi_room_combinations = RoomAvailabilityService._get_multi_room_combinations(
                available_rooms, guests, check_in, check_out
            )
            combinations.extend(multi_room_combinations)
        
        # Sort by total price
        combinations.sort(key=lambda x: x['total_price'])
        
        return combinations
    
    @staticmethod
    def _get_multi_room_combinations(available_rooms: models.QuerySet, guests: int, 
                                   check_in: date, check_out: date) -> List[Dict]:
        """Generate multi-room combinations for large groups"""
        combinations = []
        rooms_list = list(available_rooms)
        
        # Try 2-room combinations
        for i, room1 in enumerate(rooms_list):
            for room2 in rooms_list[i+1:]:
                if room1.capacity + room2.capacity >= guests:
                    price1 = PricingService.calculate_room_price(room1, check_in, check_out)
                    price2 = PricingService.calculate_room_price(room2, check_in, check_out)
                    
                    combinations.append({
                        'type': 'multi_room',
                        'rooms': [room1, room2],
                        'total_capacity': room1.capacity + room2.capacity,
                        'total_price': price1 + price2,
                        'room_count': 2
                    })
        
        return combinations
    
    @staticmethod
    def check_room_availability(room: Room, check_in: date, check_out: date) -> bool:
        """Check if a specific room is available for given dates"""
        return room.is_available(check_in, check_out)


class PricingService:
    """Service class for handling pricing calculations"""
    
    @staticmethod
    def calculate_room_price(room: Room, check_in: date, check_out: date) -> Decimal:
        """Calculate total price for a room for given dates including seasonal pricing"""
        if check_in >= check_out:
            raise ValidationError("Check-out date must be after check-in date")
        
        total_price = Decimal('0.00')
        current_date = check_in
        
        while current_date < check_out:
            daily_price = PricingService._get_daily_room_price(room, current_date)
            total_price += daily_price
            current_date += timedelta(days=1)
        
        return total_price
    
    @staticmethod
    def _get_daily_room_price(room: Room, date: date) -> Decimal:
        """Get price for a specific date considering seasonal pricing"""
        base_price = room.base_price
        
        # Get applicable seasonal pricing
        seasonal_pricing = SeasonalPricing.objects.filter(
            hotel=room.hotel,
            room_type=room.room_type,
            is_active=True,
            start_date__lte=date,
            end_date__gte=date
        ).first()
        
        if seasonal_pricing and seasonal_pricing.applies_to_date(date):
            return base_price * seasonal_pricing.price_multiplier
        
        return base_price
    
    @staticmethod
    def calculate_extras_price(extras: List[Extra], quantity_map: Dict[str, int], 
                             nights: int, guests: int) -> Decimal:
        """Calculate total price for extras"""
        total_price = Decimal('0.00')
        
        for extra in extras:
            quantity = quantity_map.get(str(extra.id), 0)
            if quantity > 0:
                extra_price = extra.calculate_total_price(quantity, nights, guests)
                total_price += extra_price
        
        return total_price
    
    @staticmethod
    def calculate_booking_total(room: Room, check_in: date, check_out: date,
                              extras: List[Extra] = None, extra_quantities: Dict = None,
                              guests: int = 1) -> Dict:
        """Calculate complete booking total with breakdown"""
        nights = (check_out - check_in).days
        
        # Room price
        room_price = PricingService.calculate_room_price(room, check_in, check_out)
        
        # Extras price
        extras_price = Decimal('0.00')
        if extras and extra_quantities:
            extras_price = PricingService.calculate_extras_price(
                extras, extra_quantities, nights, guests
            )
        
        # Calculate taxes (example: 10% tax)
        subtotal = room_price + extras_price
        tax_rate = Decimal('0.10')  # 10%
        tax_amount = subtotal * tax_rate
        
        total_price = subtotal + tax_amount
        
        return {
            'room_price': room_price,
            'extras_price': extras_price,
            'subtotal': subtotal,
            'tax_amount': tax_amount,
            'tax_rate': tax_rate,
            'total_price': total_price,
            'nights': nights,
            'price_per_night': room_price / nights if nights > 0 else room_price
        }


class HotelSearchService:
    """Service class for hotel search functionality"""
    
    @staticmethod
    def search_available_rooms(check_in: date, check_out: date, guests: int,
                             hotel_id: str = None, room_type_id: str = None,
                             max_price: Decimal = None, amenities: List[str] = None) -> Dict:
        """
        Search for available rooms with filters.
        For now, focuses on the single hotel 'Maar' but designed for multi-hotel expansion.
        """
        from django.db.models import Q
        
        # Base query for hotels
        hotels_query = Hotel.objects.filter(is_active=True)
        
        # If specific hotel requested
        if hotel_id:
            hotels_query = hotels_query.filter(id=hotel_id)
        
        results = []
        
        for hotel in hotels_query:
            # Get available rooms for this hotel
            available_rooms = RoomAvailabilityService.get_available_rooms(
                hotel, check_in, check_out, guests
            )
            
            # Apply filters
            if room_type_id:
                available_rooms = available_rooms.filter(room_type_id=room_type_id)
            
            if max_price:
                # Filter by maximum price (this is approximate, actual calculation is complex)
                nights = (check_out - check_in).days
                max_base_price = max_price / nights if nights > 0 else max_price
                available_rooms = available_rooms.filter(base_price__lte=max_base_price)
            
            # Apply amenity filters
            if amenities:
                amenity_filters = Q()
                for amenity in amenities:
                    if amenity == 'wifi':
                        amenity_filters &= Q(room_type__has_wifi=True)
                    elif amenity == 'balcony':
                        amenity_filters &= Q(room_type__has_balcony=True)
                    elif amenity == 'accessible':
                        amenity_filters &= Q(room_type__is_accessible=True)
                    # Add more amenity filters as needed
                
                available_rooms = available_rooms.filter(amenity_filters)
            
            # Get room combinations
            room_combinations = RoomAvailabilityService.get_room_combinations_for_guests(
                hotel, check_in, check_out, guests
            )
            
            if room_combinations:
                results.append({
                    'hotel': hotel,
                    'available_room_count': available_rooms.count(),
                    'room_combinations': room_combinations[:5],  # Limit to top 5 combinations
                    'hotel_extras': hotel.extras.filter(is_active=True)
                })
        
        return {
            'results': results,
            'search_params': {
                'check_in': check_in,
                'check_out': check_out,
                'guests': guests,
                'nights': (check_out - check_in).days
            }
        }


class BookingValidationService:
    """Service class for booking validation logic"""
    
    @staticmethod
    def validate_booking_dates(check_in: date, check_out: date) -> Tuple[bool, str]:
        """Validate booking dates"""
        today = timezone.now().date()
        
        if check_in < today:
            return False, "Check-in date cannot be in the past"
        
        if check_out <= check_in:
            return False, "Check-out date must be after check-in date"
        
        # Max advance booking (e.g., 2 years)
        max_advance_days = 730
        if check_in > today + timedelta(days=max_advance_days):
            return False, f"Cannot book more than {max_advance_days} days in advance"
        
        # Max stay duration (e.g., 30 days)
        max_stay_days = 30
        if (check_out - check_in).days > max_stay_days:
            return False, f"Maximum stay duration is {max_stay_days} days"
        
        return True, "Valid dates"
    
    @staticmethod
    def validate_guest_count(guests: int, room: Room) -> Tuple[bool, str]:
        """Validate guest count against room capacity"""
        if guests < 1:
            return False, "At least 1 guest is required"
        
        if guests > room.capacity:
            return False, f"Room capacity is {room.capacity} guests, but {guests} requested"
        
        return True, "Valid guest count"
    
    @staticmethod
    def validate_room_availability(room: Room, check_in: date, check_out: date) -> Tuple[bool, str]:
        """Validate room availability for booking"""
        if not room.is_available_for_booking:
            if room.is_maintenance:
                return False, "Room is currently under maintenance"
            else:
                return False, "Room is not available for booking"
        
        if not room.is_available(check_in, check_out):
            return False, "Room is not available for the selected dates"
        
        return True, "Room is available"
    
    @staticmethod
    def validate_extras(extras_data: List[Dict], hotel: Hotel) -> Tuple[bool, str, List[Extra]]:
        """Validate requested extras"""
        if not extras_data:
            return True, "No extras requested", []
        
        validated_extras = []
        total_quantity_check = {}
        
        for extra_data in extras_data:
            extra_id = extra_data.get('extra_id')
            quantity = extra_data.get('quantity', 1)
            
            try:
                extra = Extra.objects.get(id=extra_id, hotel=hotel, is_active=True)
            except Extra.DoesNotExist:
                return False, f"Extra service not found or not available", []
            
            if quantity < 1:
                return False, f"Invalid quantity for {extra.name}", []
            
            if quantity > extra.max_quantity:
                return False, f"Maximum quantity for {extra.name} is {extra.max_quantity}", []
            
            # Track total quantity for each extra
            if extra.id in total_quantity_check:
                total_quantity_check[extra.id] += quantity
            else:
                total_quantity_check[extra.id] = quantity
                
            validated_extras.append(extra)
        
        # Check total quantities don't exceed limits
        for extra_id, total_qty in total_quantity_check.items():
            extra = next(e for e in validated_extras if e.id == extra_id)
            if total_qty > extra.max_quantity:
                return False, f"Total quantity for {extra.name} exceeds maximum ({extra.max_quantity})", []
        
        return True, "Extras validated", validated_extras


class ReportingService:
    """Service class for generating reports and analytics"""
    
    @staticmethod
    def get_hotel_occupancy_rate(hotel: Hotel, start_date: date, end_date: date) -> Dict:
        """Calculate hotel occupancy rate for a date range"""
        from bookings.models import Booking
        
        total_rooms = hotel.rooms.filter(is_active=True).count()
        total_days = (end_date - start_date).days
        total_room_nights = total_rooms * total_days
        
        # Count booked room nights
        booked_nights = Booking.objects.filter(
            room__hotel=hotel,
            status__in=['confirmed', 'checked_in', 'checked_out'],
            check_in__lt=end_date,
            check_out__gt=start_date
        ).aggregate(
            total_nights=models.Sum(
                models.Case(
                    models.When(
                        check_in__gte=start_date,
                        check_out__lte=end_date,
                        then=models.F('check_out') - models.F('check_in')
                    ),
                    default=0,
                    output_field=models.IntegerField()
                )
            )
        )['total_nights'] or 0
        
        occupancy_rate = (booked_nights / total_room_nights * 100) if total_room_nights > 0 else 0
        
        return {
            'hotel': hotel,
            'period': {'start': start_date, 'end': end_date},
            'total_rooms': total_rooms,
            'total_room_nights': total_room_nights,
            'booked_room_nights': booked_nights,
            'occupancy_rate': round(occupancy_rate, 2)
        }
    
    @staticmethod
    def get_revenue_report(hotel: Hotel, start_date: date, end_date: date) -> Dict:
        """Generate revenue report for a date range"""
        from bookings.models import Booking
        
        bookings = Booking.objects.filter(
            room__hotel=hotel,
            status__in=['confirmed', 'checked_in', 'checked_out'],
            check_in__gte=start_date,
            check_out__lte=end_date
        )
        
        total_revenue = bookings.aggregate(
            total=models.Sum('total_price')
        )['total'] or Decimal('0.00')
        
        booking_count = bookings.count()
        
        avg_booking_value = (total_revenue / booking_count) if booking_count > 0 else Decimal('0.00')
        
        return {
            'hotel': hotel,
            'period': {'start': start_date, 'end': end_date},
            'total_revenue': total_revenue,
            'booking_count': booking_count,
            'average_booking_value': avg_booking_value
        }
