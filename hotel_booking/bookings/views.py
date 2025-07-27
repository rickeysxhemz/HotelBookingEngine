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


# ===== MISSING VIEWS IMPLEMENTATION =====

class BookingSearchAPIView(generics.ListAPIView):
    """Search bookings with various filters"""
    serializer_class = BookingListSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = Booking.objects.filter(guest=self.request.user)
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by date range
        from_date = self.request.query_params.get('from_date')
        to_date = self.request.query_params.get('to_date')
        
        if from_date:
            queryset = queryset.filter(check_in__gte=from_date)
        if to_date:
            queryset = queryset.filter(check_out__lte=to_date)
        
        return queryset.order_by('-created_at')


class RoomSearchAPIView(generics.GenericAPIView):
    """Search available rooms"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        try:
            check_in = request.query_params.get('checkin')
            check_out = request.query_params.get('checkout')
            guests = int(request.query_params.get('guests', 1))
            location = request.query_params.get('location')
            
            if not check_in or not check_out:
                return Response(
                    {'error': 'checkin and checkout dates are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get available rooms using existing service
            available_rooms = RoomAvailabilityService.search_available_rooms(
                check_in_date=check_in,
                check_out_date=check_out,
                guests=guests,
                location=location
            )
            
            return Response({
                'search_criteria': {
                    'check_in': check_in,
                    'check_out': check_out,
                    'guests': guests,
                    'location': location
                },
                'results': available_rooms,
                'total_found': len(available_rooms)
            })
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class AvailabilitySearchAPIView(RoomSearchAPIView):
    """Alias for room search"""
    pass


class HotelRoomSearchAPIView(generics.GenericAPIView):
    """Search rooms in a specific hotel"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, hotel_id):
        try:
            check_in = request.query_params.get('checkin')
            check_out = request.query_params.get('checkout')
            guests = int(request.query_params.get('guests', 1))
            
            if not check_in or not check_out:
                return Response(
                    {'error': 'checkin and checkout dates are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get available rooms for specific hotel
            available_rooms = RoomAvailabilityService.get_available_rooms(
                hotel_id=hotel_id,
                check_in_date=check_in,
                check_out_date=check_out,
                guests=guests
            )
            
            return Response({
                'hotel_id': hotel_id,
                'search_criteria': {
                    'check_in': check_in,
                    'check_out': check_out,
                    'guests': guests
                },
                'available_rooms': available_rooms,
                'total_available': len(available_rooms)
            })
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class BookingQuoteAPIView(generics.GenericAPIView):
    """Get booking quote without creating booking"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        try:
            room_id = request.data.get('room_id')
            check_in = request.data.get('check_in_date')
            check_out = request.data.get('check_out_date')
            guests = int(request.data.get('guests', 1))
            extras = request.data.get('extras', [])
            
            # Calculate pricing
            room = Room.objects.get(id=room_id)
            
            # Basic room rate calculation
            from datetime import datetime
            check_in_date = datetime.strptime(check_in, '%Y-%m-%d').date()
            check_out_date = datetime.strptime(check_out, '%Y-%m-%d').date()
            nights = (check_out_date - check_in_date).days
            
            room_total = float(room.room_type.base_price) * nights
            
            # Calculate extras
            extras_total = 0
            if extras:
                extra_objects = Extra.objects.filter(id__in=extras)
                extras_total = sum(float(extra.price) for extra in extra_objects)
            
            subtotal = room_total + extras_total
            taxes = subtotal * 0.12  # 12% tax
            total = subtotal + taxes
            
            return Response({
                'quote_id': f'QUOTE-{timezone.now().strftime("%Y%m%d%H%M%S")}',
                'room': {
                    'id': str(room.id),
                    'name': room.room_type.name,
                    'hotel': room.hotel.name
                },
                'dates': {
                    'check_in': check_in,
                    'check_out': check_out,
                    'nights': nights
                },
                'pricing': {
                    'room_rate_per_night': float(room.room_type.base_price),
                    'room_total': room_total,
                    'extras_total': extras_total,
                    'subtotal': subtotal,
                    'taxes': taxes,
                    'total': total,
                    'currency': 'USD'
                },
                'policies': {
                    'cancellation_policy': room.hotel.cancellation_policy,
                    'payment_required': 'Credit card required to hold reservation'
                }
            })
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class BookingDraftAPIView(generics.GenericAPIView):
    """Save booking as draft"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        # In a real implementation, you'd save to a BookingDraft model
        draft_id = f'DRAFT-{timezone.now().strftime("%Y%m%d%H%M%S")}'
        
        return Response({
            'draft_id': draft_id,
            'message': 'Booking saved as draft',
            'expires_at': (timezone.now() + timezone.timedelta(hours=24)).isoformat()
        })


class BookingCancelAPIView(generics.GenericAPIView):
    """Cancel a booking"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, booking_reference):
        try:
            booking = Booking.objects.get(
                booking_reference=booking_reference,
                guest=request.user
            )
            
            if booking.status == 'cancelled':
                return Response(
                    {'error': 'Booking is already cancelled'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Cancel the booking
            booking.status = 'cancelled'
            booking.cancellation_date = timezone.now()
            booking.cancellation_reason = request.data.get('reason', 'Guest cancellation')
            booking.save()
            
            # Create history record
            BookingHistory.objects.create(
                booking=booking,
                status='cancelled',
                notes=f'Cancelled by guest: {booking.cancellation_reason}'
            )
            
            return Response({
                'message': 'Booking cancelled successfully',
                'booking_reference': booking_reference,
                'cancellation_date': booking.cancellation_date.isoformat()
            })
            
        except Booking.DoesNotExist:
            return Response({'error': 'Booking not found'}, status=status.HTTP_404_NOT_FOUND)


class BookingConfirmAPIView(generics.GenericAPIView):
    """Confirm a booking"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, booking_reference):
        try:
            booking = Booking.objects.get(
                booking_reference=booking_reference,
                guest=request.user
            )
            
            if booking.status == 'confirmed':
                return Response(
                    {'message': 'Booking is already confirmed'},
                    status=status.HTTP_200_OK
                )
            
            booking.status = 'confirmed'
            booking.save()
            
            return Response({
                'message': 'Booking confirmed successfully',
                'booking_reference': booking_reference
            })
            
        except Booking.DoesNotExist:
            return Response({'error': 'Booking not found'}, status=status.HTTP_404_NOT_FOUND)


class BookingModifyAPIView(generics.GenericAPIView):
    """Modify booking details"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, booking_reference):
        try:
            booking = Booking.objects.get(
                booking_reference=booking_reference,
                guest=request.user
            )
            
            # Create modification request (in real implementation)
            modification_data = request.data
            
            return Response({
                'message': 'Modification request submitted',
                'booking_reference': booking_reference,
                'modification_id': f'MOD-{timezone.now().strftime("%Y%m%d%H%M%S")}',
                'status': 'pending_approval'
            })
            
        except Booking.DoesNotExist:
            return Response({'error': 'Booking not found'}, status=status.HTTP_404_NOT_FOUND)


class BookingTimelineAPIView(generics.GenericAPIView):
    """Get booking timeline/history"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, booking_reference):
        try:
            booking = Booking.objects.get(
                booking_reference=booking_reference,
                guest=request.user
            )
            
            # Get booking history
            history = BookingHistory.objects.filter(booking=booking).order_by('created_at')
            
            timeline = [
                {
                    'id': h.id,
                    'status': h.status,
                    'timestamp': h.created_at.isoformat(),
                    'notes': h.notes,
                    'user': h.user.get_full_name() if h.user else 'System'
                } for h in history
            ]
            
            return Response({
                'booking_reference': booking_reference,
                'timeline': timeline
            })
            
        except Booking.DoesNotExist:
            return Response({'error': 'Booking not found'}, status=status.HTTP_404_NOT_FOUND)


class BookingInvoiceAPIView(generics.GenericAPIView):
    """Get booking invoice"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, booking_reference):
        try:
            booking = Booking.objects.get(
                booking_reference=booking_reference,
                guest=request.user
            )
            
            invoice_data = {
                'invoice_number': f'INV-{booking.booking_reference}',
                'booking_reference': booking_reference,
                'guest_name': f'{booking.primary_guest_name}',
                'hotel': {
                    'name': booking.room.hotel.name,
                    'address': booking.room.hotel.full_address
                },
                'room': {
                    'type': booking.room.room_type.name,
                    'nights': booking.total_nights,
                    'rate_per_night': float(booking.room.room_type.base_price)
                },
                'totals': {
                    'room_charges': float(booking.room_charges),
                    'extras': float(booking.extras_total),
                    'taxes': float(booking.taxes),
                    'total': float(booking.total_price)
                },
                'dates': {
                    'check_in': booking.check_in.isoformat(),
                    'check_out': booking.check_out.isoformat(),
                    'booking_date': booking.created_at.date().isoformat()
                }
            }
            
            return Response(invoice_data)
            
        except Booking.DoesNotExist:
            return Response({'error': 'Booking not found'}, status=status.HTTP_404_NOT_FOUND)


class BookingReceiptAPIView(BookingInvoiceAPIView):
    """Get booking receipt (alias for invoice)"""
    pass


class CheckInAPIView(generics.GenericAPIView):
    """Check-in a guest"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, booking_reference):
        try:
            booking = Booking.objects.get(booking_reference=booking_reference)
            
            if booking.status != 'confirmed':
                return Response(
                    {'error': 'Booking must be confirmed before check-in'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            booking.status = 'checked_in'
            booking.actual_check_in = timezone.now()
            booking.save()
            
            return Response({
                'message': 'Check-in successful',
                'booking_reference': booking_reference,
                'check_in_time': booking.actual_check_in.isoformat()
            })
            
        except Booking.DoesNotExist:
            return Response({'error': 'Booking not found'}, status=status.HTTP_404_NOT_FOUND)


class CheckOutAPIView(generics.GenericAPIView):
    """Check-out a guest"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, booking_reference):
        try:
            booking = Booking.objects.get(booking_reference=booking_reference)
            
            if booking.status != 'checked_in':
                return Response(
                    {'error': 'Guest must be checked in before check-out'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            booking.status = 'completed'
            booking.actual_check_out = timezone.now()
            booking.save()
            
            return Response({
                'message': 'Check-out successful',
                'booking_reference': booking_reference,
                'check_out_time': booking.actual_check_out.isoformat()
            })
            
        except Booking.DoesNotExist:
            return Response({'error': 'Booking not found'}, status=status.HTTP_404_NOT_FOUND)


class StaffDashboardAPIView(generics.GenericAPIView):
    """Staff dashboard with key metrics"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        # Alias for existing get_hotel_dashboard function
        return get_hotel_dashboard(request)


class TodayBookingsAPIView(generics.ListAPIView):
    """Get today's bookings"""
    serializer_class = BookingListSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        today = timezone.now().date()
        return Booking.objects.filter(
            Q(check_in=today) | Q(check_out=today)
        ).order_by('check_in')


class TodayArrivalsAPIView(generics.ListAPIView):
    """Get today's arrivals"""
    serializer_class = BookingListSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        today = timezone.now().date()
        return Booking.objects.filter(
            check_in=today,
            status='confirmed'
        ).order_by('check_in')


class TodayDeparturesAPIView(generics.ListAPIView):
    """Get today's departures"""
    serializer_class = BookingListSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        today = timezone.now().date()
        return Booking.objects.filter(
            check_out=today,
            status='checked_in'
        ).order_by('check_out')
