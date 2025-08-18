# Django imports
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import datetime, date
from decimal import Decimal
from typing import Dict, List, Optional

# Django REST Framework imports
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes

# Local imports
from .models import Booking, BookingExtra, BookingHistory
from .serializers import (
    BookingCreateSerializer, BookingDetailSerializer,
    BookingConfirmationSerializer, CompleteBookingFlowSerializer,
    RoomSearchResultSerializer
)
from .email_service import BookingEmailService
from core.models import Hotel, Room, RoomType, Extra
from core.services import RoomAvailabilityService, PricingService
import logging

logger = logging.getLogger(__name__)


@extend_schema(
    summary="Complete Booking Flow",
    description="Handle complete booking flow including room search, booking creation, payment processing, and email confirmation. Hotel ID is optional in search criteria.",
    request=CompleteBookingFlowSerializer,
    responses={201: BookingConfirmationSerializer},
    examples=[
        OpenApiExample(
            'Book Any Available Hotel',
            summary='Search all hotels and book',
            description='Complete booking flow without specifying hotel_id - searches all available hotels',
            value={
                "search_criteria": {
                    "check_in": "2025-08-20",
                    "check_out": "2025-08-23",
                    "guests": 2
                },
                "booking_details": {
                    "room_id": "123e4567-e89b-12d3-a456-426614174000",
                    "primary_guest_name": "John Doe",
                    "primary_guest_email": "john@example.com",
                    "primary_guest_phone": "+1234567890",
                    "special_requests": "Early check-in if possible"
                },
                "payment_info": {
                    "payment_method": "card",
                    "save_payment_method": False
                }
            }
        ),
        OpenApiExample(
            'Book Specific Hotel',
            summary='Search specific hotel and book',
            description='Complete booking flow for a specific hotel using hotel_id',
            value={
                "search_criteria": {
                    "hotel_id": "987fcdeb-51d3-12a3-b456-426614174001",
                    "check_in": "2025-08-20",
                    "check_out": "2025-08-23",
                    "guests": 2
                },
                "booking_details": {
                    "room_id": "123e4567-e89b-12d3-a456-426614174000",
                    "primary_guest_name": "John Doe",
                    "primary_guest_email": "john@example.com",
                    "primary_guest_phone": "+1234567890"
                },
                "payment_info": {
                    "payment_method": "card"
                }
            }
        ),
    ]
)
class CompleteBookingFlowAPIView(generics.GenericAPIView):
    """
    Complete booking flow API that handles:
    1. Finding available rooms
    2. Creating booking
    3. Processing payment
    4. Sending confirmation email
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """
        Handle complete booking flow
        
        Expected payload:
        {
            "search_criteria": {
                "hotel_id": "uuid",  # Optional - if not provided, searches all hotels
                "location": "city_name",  # Optional - filters hotels by city if provided
                "check_in": "2024-01-15",
                "check_out": "2024-01-18",
                "guests": 2
            },
            "booking_details": {
                "room_id": "uuid",  # Selected from search results
                "primary_guest_name": "John Doe",
                "primary_guest_email": "john@example.com",
                "primary_guest_phone": "+1234567890",
                "special_requests": "Early check-in if possible",
                "extras": [
                    {"extra_id": "uuid", "quantity": 1}
                ]
            },
            "payment_info": {
                "payment_method": "card",
                "save_payment_method": false
            }
        }
        
        Note: Both hotel_id and location are optional in search_criteria.
        - If hotel_id is provided, searches only that specific hotel
        - If location is provided (without hotel_id), searches hotels in that city
        - If neither is provided, searches all available hotels
        """
        try:
            with transaction.atomic():
                # Step 1: Validate search criteria
                search_data = request.data.get('search_criteria', {})
                booking_data = request.data.get('booking_details', {})
                payment_data = request.data.get('payment_info', {})
                
                if not search_data or not booking_data:
                    return Response(
                        {'error': 'Both search_criteria and booking_details are required'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Step 2: Find available rooms (if room not already selected)
                available_rooms = []
                if not booking_data.get('room_id'):
                    available_rooms = self._search_available_rooms(search_data)
                    if not available_rooms:
                        return Response(
                            {
                                'error': 'No available rooms found for the specified criteria',
                                'search_criteria': search_data
                            },
                            status=status.HTTP_404_NOT_FOUND
                        )
                
                # Step 3: Validate selected room availability
                room_id = booking_data.get('room_id')
                if room_id:
                    if not self._validate_room_availability(room_id, search_data):
                        return Response(
                            {'error': 'Selected room is no longer available'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                
                # Step 4: Create booking
                booking = self._create_booking(search_data, booking_data, request.user)
                
                # Step 5: Process payment (simulate for now)
                payment_result = self._process_payment(booking, payment_data)
                if not payment_result['success']:
                    booking.status = 'cancelled'
                    booking.payment_status = 'failed'
                    booking.save()
                    return Response(
                        {'error': f'Payment failed: {payment_result["error"]}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Step 6: Confirm booking
                booking.status = 'confirmed'
                booking.payment_status = 'paid'
                booking.confirmation_date = timezone.now()
                booking.save()
                
                # Create booking history
                BookingHistory.objects.create(
                    booking=booking,
                    action='confirmed',
                    description='Booking confirmed and payment processed',
                    performed_by=request.user
                )
                
                # Step 7: Send confirmation email
                email_sent = BookingEmailService.send_booking_confirmation(booking)
                
                # Step 8: Return comprehensive response
                serializer = BookingDetailSerializer(booking, context={'request': request})
                
                return Response({
                    'success': True,
                    'message': 'Booking completed successfully',
                    'booking': serializer.data,
                    'available_rooms': available_rooms if not room_id else [],
                    'payment': {
                        'status': 'success',
                        'transaction_id': payment_result.get('transaction_id')
                    },
                    'email_notification': {
                        'sent': email_sent,
                        'recipient': booking.primary_guest_email
                    }
                }, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            logger.error(f"Complete booking flow failed: {str(e)}")
            return Response(
                {'error': f'Booking failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _search_available_rooms(self, search_criteria: Dict) -> List[Dict]:
        """Search for available rooms based on criteria"""
        try:
            check_in = datetime.strptime(search_criteria['check_in'], '%Y-%m-%d').date()
            check_out = datetime.strptime(search_criteria['check_out'], '%Y-%m-%d').date()
            guests = search_criteria.get('guests', 1)
            hotel_id = search_criteria.get('hotel_id')
            location = search_criteria.get('location')
            
            if hotel_id:
                hotel = Hotel.objects.get(id=hotel_id)
                available_rooms = RoomAvailabilityService.get_available_rooms(
                    hotel, check_in, check_out, guests
                )
            else:
                # Search across all hotels
                hotels = Hotel.objects.filter(is_active=True)
                if location:
                    hotels = hotels.filter(city__icontains=location)
                
                available_rooms = []
                for hotel in hotels:
                    hotel_rooms = RoomAvailabilityService.get_available_rooms(
                        hotel, check_in, check_out, guests
                    )
                    available_rooms.extend(hotel_rooms)
            
            # Format room data with pricing
            rooms_data = []
            for room in available_rooms:
                pricing = PricingService.calculate_booking_total(
                    room, check_in, check_out, guests=guests
                )
                
                # Get room images
                images = []
                if hasattr(room.room_type, 'roomimage_set'):
                    for img in room.room_type.roomimage_set.filter(is_active=True).order_by('display_order'):
                        images.append({
                            'id': str(img.id),
                            'image_url': img.image_url,
                            'alt_text': img.image_alt_text,
                            'caption': img.caption,
                            'is_primary': img.is_primary
                        })
                
                rooms_data.append({
                    'room_id': str(room.id),
                    'room_number': room.room_number,
                    'room_type': {
                        'id': str(room.room_type.id),
                        'name': room.room_type.name,
                        'description': room.room_type.description,
                        'capacity': room.room_type.max_capacity,
                        'amenities': getattr(room.room_type, 'amenities_list', [])
                    },
                    'hotel': {
                        'id': str(room.hotel.id),
                        'name': room.hotel.name,
                        'address': f"{room.hotel.address_line_1}, {room.hotel.city}, {room.hotel.state}".strip(', '),
                        'city': room.hotel.city,
                        'rating': getattr(room.hotel, 'star_rating', None)
                    },
                    'pricing': {
                        'room_price': str(pricing['room_price']),
                        'extras_price': str(pricing['extras_price']),
                        'subtotal': str(pricing['subtotal']),
                        'tax_amount': str(pricing['tax_amount']),
                        'tax_rate': str(pricing['tax_rate']),
                        'total_price': str(pricing['total_price']),
                        'nights': pricing['nights'],
                        'price_per_night': str(pricing['price_per_night'])
                    },
                    'images': images
                })
            
            return rooms_data
            
        except Exception as e:
            logger.error(f"Room search failed: {str(e)}")
            return []
    
    def _validate_room_availability(self, room_id: str, search_criteria: Dict) -> bool:
        """Validate that selected room is still available"""
        try:
            room = Room.objects.get(id=room_id)
            check_in = datetime.strptime(search_criteria['check_in'], '%Y-%m-%d').date()
            check_out = datetime.strptime(search_criteria['check_out'], '%Y-%m-%d').date()
            guests = search_criteria.get('guests', 1)
            
            available_rooms = RoomAvailabilityService.get_available_rooms(
                room.hotel, check_in, check_out, guests
            )
            
            return room in available_rooms
            
        except Exception as e:
            logger.error(f"Room availability validation failed: {str(e)}")
            return False
    
    def _create_booking(self, search_criteria: Dict, booking_data: Dict, user) -> Booking:
        """Create booking with all details"""
        try:
            room = Room.objects.get(id=booking_data['room_id'])
            check_in = datetime.strptime(search_criteria['check_in'], '%Y-%m-%d').date()
            check_out = datetime.strptime(search_criteria['check_out'], '%Y-%m-%d').date()
            guests = search_criteria.get('guests', 1)
            
            # Calculate pricing
            extras = []
            extra_quantities = {}
            if booking_data.get('extras'):
                for extra_item in booking_data['extras']:
                    extra = Extra.objects.get(id=extra_item['extra_id'])
                    extras.append(extra)
                    extra_quantities[str(extra.id)] = extra_item.get('quantity', 1)
            
            pricing = PricingService.calculate_booking_total(
                room, check_in, check_out, extras, extra_quantities, guests
            )
            
            # Create booking
            booking = Booking.objects.create(
                user=user,
                room=room,
                check_in=check_in,
                check_out=check_out,
                guests=guests,
                primary_guest_name=booking_data['primary_guest_name'],
                primary_guest_email=booking_data['primary_guest_email'],
                primary_guest_phone=booking_data['primary_guest_phone'],
                special_requests=booking_data.get('special_requests', ''),
                room_price=pricing['room_price'],
                extras_price=pricing['extras_price'],
                tax_amount=pricing['tax_amount'],
                total_price=pricing['total_price'],
                status='pending',
                payment_status='pending'
            )
            
            # Create booking extras
            for extra in extras:
                quantity = extra_quantities.get(str(extra.id), 1)
                BookingExtra.objects.create(
                    booking=booking,
                    extra=extra,
                    quantity=quantity,
                    price=extra.price
                )
            
            return booking
            
        except Exception as e:
            logger.error(f"Booking creation failed: {str(e)}")
            raise
    
    def _process_payment(self, booking: Booking, payment_data: Dict) -> Dict:
        """Process payment (simulated for demo)"""
        try:
            # Simulate payment processing
            import uuid
            
            # In a real implementation, you would integrate with payment gateways like:
            # - Stripe
            # - PayPal
            # - Square
            # - etc.
            
            payment_method = payment_data.get('payment_method', 'card')
            
            # Simulate payment success/failure
            if booking.total_price > 0:
                return {
                    'success': True,
                    'transaction_id': str(uuid.uuid4()),
                    'payment_method': payment_method,
                    'amount': float(booking.total_price)
                }
            else:
                return {
                    'success': False,
                    'error': 'Invalid amount'
                }
                
        except Exception as e:
            logger.error(f"Payment processing failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }


@extend_schema(
    summary="Search Available Rooms",
    description="Search for available rooms without creating a booking. Hotel ID is optional - if not provided, searches all hotels.",
    parameters=[
        OpenApiParameter(
            name='check_in',
            type=OpenApiTypes.DATE,
            location=OpenApiParameter.QUERY,
            required=True,
            description='Check-in date (YYYY-MM-DD format)'
        ),
        OpenApiParameter(
            name='check_out',
            type=OpenApiTypes.DATE,
            location=OpenApiParameter.QUERY,
            required=True,
            description='Check-out date (YYYY-MM-DD format)'
        ),
        OpenApiParameter(
            name='guests',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            required=False,
            description='Number of guests (default: 1)'
        ),
        OpenApiParameter(
            name='hotel_id',
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.QUERY,
            required=False,
            description='(Optional) Specific hotel ID to search in'
        ),
        OpenApiParameter(
            name='location',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            required=False,
            description='(Optional) City or location to filter hotels by'
        ),
    ],
    examples=[
        OpenApiExample(
            'Search All Hotels',
            summary='Search all hotels for available rooms',
            description='Search across all hotels without specifying hotel_id or location',
            value={
                'check_in': '2025-08-20',
                'check_out': '2025-08-23',
                'guests': 2
            }
        ),
        OpenApiExample(
            'Search Specific Hotel',
            summary='Search a specific hotel',
            description='Search only a specific hotel using hotel_id',
            value={
                'hotel_id': '123e4567-e89b-12d3-a456-426614174000',
                'check_in': '2025-08-20',
                'check_out': '2025-08-23',
                'guests': 2
            }
        ),
        OpenApiExample(
            'Search by Location',
            summary='Search hotels by city/location',
            description='Search hotels in a specific city or location',
            value={
                'location': 'New York',
                'check_in': '2025-08-20',
                'check_out': '2025-08-23',
                'guests': 2
            }
        ),
    ]
)
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def search_rooms_only(request):
    """
    Search for available rooms without creating booking
    
    Query Parameters:
    - check_in: Required - Check-in date (YYYY-MM-DD)
    - check_out: Required - Check-out date (YYYY-MM-DD)
    - guests: Optional - Number of guests (default: 1)
    - hotel_id: Optional - Specific hotel ID to search in
    - location: Optional - City/location to filter hotels by
    
    Note: hotel_id and location are both optional.
    - If hotel_id is provided, searches only that specific hotel
    - If location is provided (without hotel_id), searches hotels in that city
    - If neither is provided, searches all available hotels
    """
    try:
        # Get search parameters
        hotel_id = request.query_params.get('hotel_id')
        location = request.query_params.get('location')
        check_in = request.query_params.get('check_in')
        check_out = request.query_params.get('check_out')
        guests = int(request.query_params.get('guests', 1))
        
        if not check_in or not check_out:
            return Response(
                {'error': 'check_in and check_out dates are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create search criteria
        search_criteria = {
            'check_in': check_in,
            'check_out': check_out,
            'guests': guests
        }
        
        if hotel_id:
            search_criteria['hotel_id'] = hotel_id
        if location:
            search_criteria['location'] = location
        
        # Use the same search logic from CompleteBookingFlowAPIView
        booking_flow = CompleteBookingFlowAPIView()
        available_rooms = booking_flow._search_available_rooms(search_criteria)
        
        return Response({
            'search_criteria': search_criteria,
            'available_rooms': available_rooms,
            'total_found': len(available_rooms)
        })
        
    except Exception as e:
        logger.error(f"Room search failed: {str(e)}")
        return Response(
            {'error': f'Search failed: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
