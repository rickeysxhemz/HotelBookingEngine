# Django imports
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone
from django.db.models import Q, Prefetch

# Django REST Framework imports
from rest_framework import generics, status, permissions, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

# Local imports
from .models import Booking, BookingHistory
from .serializers import (
    BookingCreateSerializer, BookingDetailSerializer, BookingListSerializer,
    BookingUpdateSerializer, RoomAvailabilitySerializer, BookingCancellationSerializer,
    RoomSerializer, ExtraSerializer
)
from core.models import Hotel, Room, Extra
from core.services import HotelSearchService, RoomAvailabilityService


class BookingPagination(PageNumberPagination):
    """Custom pagination for bookings"""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50


class BookingListAPIView(generics.ListAPIView):
    """List user's bookings with filtering and pagination"""
    serializer_class = BookingListSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = BookingPagination
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    search_fields = ['booking_reference', 'primary_guest_name']
    ordering_fields = ['booking_date', 'check_in', 'total_price']
    ordering = ['-booking_date']
    
    def get_queryset(self):
        """Get bookings for the authenticated user"""
        return Booking.objects.filter(
            user=self.request.user
        ).select_related(
            'room__hotel', 'room__room_type'
        ).prefetch_related(
            'booking_extras__extra'
        )


class BookingDetailAPIView(generics.RetrieveAPIView):
    """Get detailed booking information"""
    serializer_class = BookingDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'booking_reference'
    
    def get_queryset(self):
        """Get booking for the authenticated user"""
        return Booking.objects.filter(
            user=self.request.user
        ).select_related(
            'room__hotel', 'room__room_type', 'user'
        ).prefetch_related(
            'booking_extras__extra',
            'additional_guests',
            'history__performed_by'
        )


class BookingCreateAPIView(generics.CreateAPIView):
    """Create a new booking"""
    serializer_class = BookingCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        """Create booking with transaction safety"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            with transaction.atomic():
                booking = serializer.save()
                
                # Return detailed booking information
                detail_serializer = BookingDetailSerializer(
                    booking, context={'request': request}
                )
                
                return Response(
                    {
                        'message': 'Booking created successfully',
                        'booking': detail_serializer.data
                    },
                    status=status.HTTP_201_CREATED
                )
        except Exception as e:
            return Response(
                {'error': f'Failed to create booking: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )


class BookingUpdateAPIView(generics.UpdateAPIView):
    """Update booking details"""
    serializer_class = BookingUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'booking_reference'
    
    def get_queryset(self):
        """Get booking for the authenticated user"""
        return Booking.objects.filter(
            user=self.request.user,
            status__in=['pending', 'confirmed']  # Only allow updates for certain statuses
        )
    
    def update(self, request, *args, **kwargs):
        """Update booking and return detailed information"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        # Check if booking can be updated
        if instance.status not in ['pending', 'confirmed']:
            return Response(
                {'error': 'Booking cannot be updated in current status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        booking = serializer.save()
        
        # Return updated booking details
        detail_serializer = BookingDetailSerializer(
            booking, context={'request': request}
        )
        
        return Response({
            'message': 'Booking updated successfully',
            'booking': detail_serializer.data
        })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def cancel_booking(request, booking_reference):
    """Cancel a booking"""
    try:
        booking = get_object_or_404(
            Booking, 
            booking_reference=booking_reference,
            user=request.user
        )
        
        # Validate cancellation
        serializer = BookingCancellationSerializer(
            data=request.data,
            context={'booking': booking}
        )
        serializer.is_valid(raise_exception=True)
        
        # Cancel booking
        with transaction.atomic():
            booking.cancel_booking(
                reason=serializer.validated_data['reason'],
                notes=serializer.validated_data.get('notes', '')
            )
            
            # Create history entry
            BookingHistory.objects.create(
                booking=booking,
                action='cancelled',
                description=f"Booking cancelled - {serializer.validated_data['reason']}",
                performed_by=request.user
            )
        
        return Response({
            'message': 'Booking cancelled successfully',
            'booking_reference': booking.booking_reference
        })
        
    except Exception as e:
        return Response(
            {'error': f'Failed to cancel booking: {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def check_in_booking(request, booking_reference):
    """Check in a guest (for hotel staff)"""
    try:
        booking = get_object_or_404(
            Booking,
            booking_reference=booking_reference
        )
        
        # Check if user has permission (hotel staff or admin)
        if not (request.user.is_hotel_staff or request.user.is_admin_user):
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if not booking.can_check_in:
            return Response(
                {'error': 'Guest cannot check in at this time'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check in guest
        with transaction.atomic():
            booking.check_in_guest()
            
            # Create history entry
            BookingHistory.objects.create(
                booking=booking,
                action='checked_in',
                description='Guest checked in',
                performed_by=request.user
            )
        
        return Response({
            'message': 'Guest checked in successfully',
            'booking_reference': booking.booking_reference,
            'check_in_time': booking.check_in_time
        })
        
    except Exception as e:
        return Response(
            {'error': f'Failed to check in guest: {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def check_out_booking(request, booking_reference):
    """Check out a guest (for hotel staff)"""
    try:
        booking = get_object_or_404(
            Booking,
            booking_reference=booking_reference
        )
        
        # Check if user has permission (hotel staff or admin)
        if not (request.user.is_hotel_staff or request.user.is_admin_user):
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if not booking.can_check_out:
            return Response(
                {'error': 'Guest cannot check out at this time'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check out guest
        with transaction.atomic():
            booking.check_out_guest()
            
            # Create history entry
            BookingHistory.objects.create(
                booking=booking,
                action='checked_out',
                description='Guest checked out',
                performed_by=request.user
            )
        
        return Response({
            'message': 'Guest checked out successfully',
            'booking_reference': booking.booking_reference,
            'check_out_time': booking.check_out_time
        })
        
    except Exception as e:
        return Response(
            {'error': f'Failed to check out guest: {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def search_rooms(request):
    """Search for available rooms"""
    serializer = RoomAvailabilitySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    search_params = serializer.validated_data
    
    try:
        # Use the search service
        results = HotelSearchService.search_available_rooms(
            check_in=search_params['check_in'],
            check_out=search_params['check_out'],
            guests=search_params['guests'],
            hotel_id=search_params.get('hotel_id'),
            room_type_id=search_params.get('room_type_id'),
            max_price=search_params.get('max_price')
        )
        
        # Serialize room combinations
        serialized_results = []
        for hotel_result in results['results']:
            hotel_data = {
                'hotel': {
                    'id': str(hotel_result['hotel'].id),
                    'name': hotel_result['hotel'].name,
                    'star_rating': hotel_result['hotel'].star_rating,
                    'address': hotel_result['hotel'].full_address
                },
                'available_rooms': hotel_result['available_room_count'],
                'room_combinations': []
            }
            
            # Add room combinations
            for combination in hotel_result['room_combinations']:
                room_data = []
                for room in combination['rooms']:
                    room_serializer = RoomSerializer(
                        room, 
                        context={'request': request}
                    )
                    room_data.append(room_serializer.data)
                
                hotel_data['room_combinations'].append({
                    'type': combination['type'],
                    'rooms': room_data,
                    'total_capacity': combination['total_capacity'],
                    'total_price': combination['total_price'],
                    'room_count': combination['room_count']
                })
            
            # Add hotel extras
            extras_serializer = ExtraSerializer(
                hotel_result['hotel_extras'],
                many=True
            )
            hotel_data['available_extras'] = extras_serializer.data
            
            serialized_results.append(hotel_data)
        
        return Response({
            'results': serialized_results,
            'search_params': results['search_params']
        })
        
    except Exception as e:
        return Response(
            {'error': f'Search failed: {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_hotel_extras(request, hotel_id):
    """Get available extras for a hotel"""
    try:
        hotel = get_object_or_404(Hotel, id=hotel_id, is_active=True)
        extras = hotel.extras.filter(is_active=True)
        
        serializer = ExtraSerializer(extras, many=True)
        
        return Response({
            'hotel': {
                'id': str(hotel.id),
                'name': hotel.name
            },
            'extras': serializer.data
        })
        
    except Exception as e:
        return Response(
            {'error': f'Failed to get hotel extras: {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_booking_history(request, booking_reference):
    """Get booking history for a specific booking"""
    try:
        booking = get_object_or_404(
            Booking,
            booking_reference=booking_reference,
            user=request.user
        )
        
        history = booking.history.all().order_by('-timestamp')
        
        history_data = []
        for entry in history:
            history_data.append({
                'action': entry.get_action_display(),
                'description': entry.description,
                'timestamp': entry.timestamp,
                'performed_by': entry.performed_by.get_full_name() if entry.performed_by else 'System'
            })
        
        return Response({
            'booking_reference': booking.booking_reference,
            'history': history_data
        })
        
    except Exception as e:
        return Response(
            {'error': f'Failed to get booking history: {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST
        )


# Staff-only views for hotel management
class StaffBookingListAPIView(generics.ListAPIView):
    """List all bookings for hotel staff"""
    serializer_class = BookingListSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = BookingPagination
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    search_fields = ['booking_reference', 'primary_guest_name', 'primary_guest_email']
    ordering_fields = ['booking_date', 'check_in', 'total_price']
    ordering = ['-booking_date']
    
    def get_queryset(self):
        """Get all bookings for hotel staff"""
        # Check if user is hotel staff or admin
        if not (self.request.user.is_hotel_staff or self.request.user.is_admin_user):
            return Booking.objects.none()
        
        return Booking.objects.all().select_related(
            'room__hotel', 'room__room_type', 'user'
        ).prefetch_related(
            'booking_extras__extra'
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_hotel_dashboard(request):
    """Get hotel dashboard data for staff"""
    # Check if user is hotel staff or admin
    if not (request.user.is_hotel_staff or request.user.is_admin_user):
        return Response(
            {'error': 'Permission denied'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        today = timezone.now().date()
        
        # Get today's metrics
        todays_checkins = Booking.objects.filter(
            check_in=today,
            status='confirmed'
        ).count()
        
        todays_checkouts = Booking.objects.filter(
            check_out=today,
            status='checked_in'
        ).count()
        
        current_guests = Booking.objects.filter(
            status='checked_in'
        ).count()
        
        # Get upcoming bookings
        upcoming_bookings = Booking.objects.filter(
            check_in__gte=today,
            status='confirmed'
        ).order_by('check_in')[:10]
        
        upcoming_serializer = BookingListSerializer(upcoming_bookings, many=True)
        
        return Response({
            'todays_metrics': {
                'checkins': todays_checkins,
                'checkouts': todays_checkouts,
                'current_guests': current_guests
            },
            'upcoming_bookings': upcoming_serializer.data
        })
        
    except Exception as e:
        return Response(
            {'error': f'Failed to get dashboard data: {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST
        )
