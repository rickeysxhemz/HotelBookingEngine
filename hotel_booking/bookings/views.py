"""
Complete Booking API Views with Separate CRUD Operations
Optimized for production with high concurrency, async tasks, and rate limiting.
"""
from django.utils import timezone
from django.db.models import Q
from django.core.exceptions import ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
import logging

from django.contrib.auth import get_user_model
from core.models import Room
from .models import Booking
from .serializers import (
    BookingSerializer,
    BookingCreateSerializer,
    BookingUpdateSerializer,
    BookingListSerializer,
    BookingQuickSerializer
)
from .services import RoomAvailabilityService
from .tasks import send_confirmation_email_async, send_cancellation_email_async

# Get User model
User = get_user_model()

# Set up logging for email functionality
logger = logging.getLogger(__name__)


class BookingPagination(PageNumberPagination):
    """Custom pagination for booking lists."""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


def send_booking_confirmation_email(booking):
    """
    Send booking confirmation email to the guest.
    
    Args:
        booking: Booking instance
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        # Prepare email data
        subject = f'Booking Confirmation - {booking.booking_id}'
        
        # Email context
        context = {
            'booking': booking,
            'guest_name': booking.guest_full_name(),
            'hotel_name': booking.hotel.name,
            'room_name': f"{booking.room.room_type.name} #{booking.room.room_number}",
            'check_in_date': booking.check_in_date,
            'check_out_date': booking.check_out_date,
            'total_amount': booking.total_amount,
            'booking_reference': booking.booking_id,
            'adults': booking.adults,
            'children': booking.children,
        }
        
        # Create HTML email content
        html_message = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px;">
                    Booking Confirmation
                </h2>
                
                <p>Dear {context['guest_name']},</p>
                
                <p>Thank you for your booking! Your reservation has been confirmed.</p>
                
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="color: #2c3e50; margin-top: 0;">Booking Details</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold;">Booking Reference:</td>
                            <td style="padding: 8px 0;">{context['booking_reference']}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold;">Hotel:</td>
                            <td style="padding: 8px 0;">{context['hotel_name']}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold;">Room:</td>
                            <td style="padding: 8px 0;">{context['room_name']}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold;">Check-in:</td>
                            <td style="padding: 8px 0;">{context['check_in_date']}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold;">Check-out:</td>
                            <td style="padding: 8px 0;">{context['check_out_date']}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold;">Guests:</td>
                            <td style="padding: 8px 0;">{context['adults']} Adults, {context['children']} Children</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold;">Total Amount:</td>
                            <td style="padding: 8px 0; font-size: 18px; color: #27ae60;">${context['total_amount']}</td>
                        </tr>
                    </table>
                </div>
                
                <div style="background-color: #e8f5e8; padding: 15px; border-radius: 5px; border-left: 4px solid #27ae60;">
                    <p style="margin: 0;"><strong>Important:</strong> Please keep this confirmation email for your records. You will need your booking reference for check-in.</p>
                </div>
                
                <p style="margin-top: 30px;">
                    We look forward to welcoming you to {context['hotel_name']}!
                </p>
                
                <p>Best regards,<br>
                The Hotel Booking Team</p>
                
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">
                <p style="font-size: 12px; color: #666;">
                    This is an automated message. Please do not reply to this email.
                    If you have any questions, please contact our customer service.
                </p>
            </div>
        </body>
        </html>
        """
        
        # Plain text version (fallback)
        plain_message = f"""
        Booking Confirmation
        
        Dear {context['guest_name']},
        
        Thank you for your booking! Your reservation has been confirmed.
        
        Booking Details:
        - Booking Reference: {context['booking_reference']}
        - Hotel: {context['hotel_name']}
        - Room: {context['room_name']}
        - Check-in: {context['check_in_date']}
        - Check-out: {context['check_out_date']}
        - Guests: {context['adults']} Adults, {context['children']} Children
        - Total Amount: ${context['total_amount']}
        
        Please keep this confirmation email for your records.
        
        We look forward to welcoming you!
        
        Best regards,
        The Hotel Booking Team
        """
        
        # Send email
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@hotelbooking.com')
        recipient_list = [booking.guest_email]
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=from_email,
            recipient_list=recipient_list,
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Booking confirmation email sent successfully to {booking.guest_email} for booking {booking.booking_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send booking confirmation email to {booking.guest_email}: {str(e)}")
        return False


def send_booking_cancellation_email(booking):
    """
    Send booking cancellation confirmation email to the guest.
    
    Args:
        booking: Booking instance (cancelled)
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        # Prepare email data
        subject = f'Booking Cancellation Confirmation - {booking.booking_id}'
        
        # Email context
        context = {
            'booking': booking,
            'guest_name': booking.guest_full_name(),
            'hotel_name': booking.hotel.name,
            'room_name': f"{booking.room.room_type.name} #{booking.room.room_number}",
            'check_in_date': booking.check_in_date,
            'check_out_date': booking.check_out_date,
            'total_amount': booking.total_amount,
            'booking_reference': booking.booking_id,
            'adults': booking.adults,
            'children': booking.children,
            'cancellation_date': timezone.now().date(),
        }
        
        # Create HTML email content
        html_message = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #e74c3c; border-bottom: 2px solid #e74c3c; padding-bottom: 10px;">
                    Booking Cancellation Confirmation
                </h2>
                
                <p>Dear {context['guest_name']},</p>
                
                <p>We confirm that your booking has been successfully cancelled as requested.</p>
                
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="color: #2c3e50; margin-top: 0;">Cancelled Booking Details</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold;">Booking Reference:</td>
                            <td style="padding: 8px 0;">{context['booking_reference']}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold;">Hotel:</td>
                            <td style="padding: 8px 0;">{context['hotel_name']}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold;">Room:</td>
                            <td style="padding: 8px 0;">{context['room_name']}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold;">Check-in:</td>
                            <td style="padding: 8px 0;">{context['check_in_date']}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold;">Check-out:</td>
                            <td style="padding: 8px 0;">{context['check_out_date']}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold;">Guests:</td>
                            <td style="padding: 8px 0;">{context['adults']} Adults, {context['children']} Children</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold;">Original Amount:</td>
                            <td style="padding: 8px 0;">${context['total_amount']}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold;">Cancellation Date:</td>
                            <td style="padding: 8px 0;">{context['cancellation_date']}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold;">Status:</td>
                            <td style="padding: 8px 0; color: #e74c3c; font-weight: bold;">CANCELLED</td>
                        </tr>
                    </table>
                </div>
                
                <div style="background-color: #fff3cd; padding: 15px; border-radius: 5px; border-left: 4px solid #ffc107;">
                    <p style="margin: 0;"><strong>Refund Information:</strong> If applicable, refunds will be processed according to our cancellation policy. Please allow 5-7 business days for the refund to appear in your account.</p>
                </div>
                
                <div style="background-color: #f0f9ff; padding: 15px; border-radius: 5px; border-left: 4px solid #3b82f6; margin-top: 15px;">
                    <p style="margin: 0;"><strong>Need to make a new booking?</strong> We'd be happy to help you find alternative accommodations. Please contact our customer service team or visit our website.</p>
                </div>
                
                <p style="margin-top: 30px;">
                    We're sorry to see your plans change, but we understand that sometimes cancellations are necessary. We hope to welcome you to {context['hotel_name']} in the future!
                </p>
                
                <p>If you have any questions about this cancellation or need assistance with a new booking, please don't hesitate to contact us.</p>
                
                <p>Best regards,<br>
                The Hotel Booking Team</p>
                
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">
                <p style="font-size: 12px; color: #666;">
                    This is an automated message. Please do not reply to this email.
                    If you have any questions, please contact our customer service.
                </p>
            </div>
        </body>
        </html>
        """
        
        # Plain text version (fallback)
        plain_message = f"""
        Booking Cancellation Confirmation
        
        Dear {context['guest_name']},
        
        We confirm that your booking has been successfully cancelled as requested.
        
        Cancelled Booking Details:
        - Booking Reference: {context['booking_reference']}
        - Hotel: {context['hotel_name']}
        - Room: {context['room_name']}
        - Check-in: {context['check_in_date']}
        - Check-out: {context['check_out_date']}
        - Guests: {context['adults']} Adults, {context['children']} Children
        - Original Amount: ${context['total_amount']}
        - Cancellation Date: {context['cancellation_date']}
        - Status: CANCELLED
        
        Refund Information: If applicable, refunds will be processed according to our 
        cancellation policy. Please allow 5-7 business days for the refund to appear 
        in your account.
        
        We're sorry to see your plans change, but we hope to welcome you in the future!
        
        If you have any questions about this cancellation, please contact our customer service.
        
        Best regards,
        The Hotel Booking Team
        """
        
        # Send email
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@hotelbooking.com')
        recipient_list = [booking.guest_email]
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=from_email,
            recipient_list=recipient_list,
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Booking cancellation email sent successfully to {booking.guest_email} for booking {booking.booking_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send booking cancellation email to {booking.guest_email}: {str(e)}")
        return False


# CRUD Operation 1: READ (List all bookings)
class BookingListAPIView(generics.ListAPIView):
    """
    List all bookings with filtering and search capabilities.
    
    GET: Returns paginated list of bookings
    """
    queryset = Booking.objects.all()
    serializer_class = BookingListSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = BookingPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    # Filtering options
    filterset_fields = {
        'status': ['exact', 'in'],
        'payment_status': ['exact', 'in'],
        'check_in_date': ['gte', 'lte', 'exact'],
        'check_out_date': ['gte', 'lte', 'exact'],
        'created_at': ['gte', 'lte'],
        'room': ['exact'],
        'user': ['exact'],
    }
    
    # Search across guest information
    search_fields = [
        'guest_first_name',
        'guest_last_name', 
        'guest_email',
        'guest_phone',
        'booking_id',
        'room__room_type__name',
        'room__room_number'
    ]
    
    # Ordering options
    ordering_fields = [
        'created_at',
        'check_in_date',
        'check_out_date',
        'total_amount',
        'status'
    ]
    ordering = ['-created_at']  # Default ordering
    
    def get_queryset(self):
        """Enhanced queryset with optimized queries."""
        queryset = Booking.objects.select_related(
            'user', 'room', 'room__hotel', 'room__room_type'
        ).prefetch_related(
            'room__room_type__additional_amenities'
        )
        
        # Additional filtering based on query parameters
        guest_name = self.request.query_params.get('guest_name')
        if guest_name:
            queryset = queryset.filter(
                Q(guest_first_name__icontains=guest_name) |
                Q(guest_last_name__icontains=guest_name)
            )
        
        # Filter by date range
        check_in_from = self.request.query_params.get('check_in_from')
        check_in_to = self.request.query_params.get('check_in_to')
        if check_in_from:
            queryset = queryset.filter(check_in_date__gte=check_in_from)
        if check_in_to:
            queryset = queryset.filter(check_in_date__lte=check_in_to)
            
        # Filter upcoming bookings
        upcoming = self.request.query_params.get('upcoming')
        if upcoming == 'true':
            today = timezone.now().date()
            queryset = queryset.filter(check_in_date__gte=today)
            
        # Filter current bookings (checked in)
        current = self.request.query_params.get('current')
        if current == 'true':
            today = timezone.now().date()
            queryset = queryset.filter(
                check_in_date__lte=today,
                check_out_date__gte=today,
                status='confirmed'
            )
        
        return queryset


# CRUD Operation 2: CREATE (Create new booking)
@method_decorator(ratelimit(key='user', rate='10/h', method='POST'), 'dispatch')
class BookingCreateAPIView(generics.CreateAPIView):
    """
    Create a new booking with availability checking and async email confirmation.
    
    POST: Creates a new booking with validation and sends confirmation email asynchronously.
    Rate limited to 10 requests per hour per user to prevent abuse.
    
    Uses database-level locking to prevent double-booking in high-concurrency scenarios.
    """
    queryset = Booking.objects.all()
    serializer_class = BookingCreateSerializer
    permission_classes = [IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        """
        Enhanced create with availability checking and transactional safety.
        """
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            # Extract validated data
            validated_data = serializer.validated_data
            room_id = validated_data.get('room').id
            check_in_date = validated_data.get('check_in_date')
            check_out_date = validated_data.get('check_out_date')
            
            # Check room availability with database locking
            if not RoomAvailabilityService.is_room_available(room_id, check_in_date, check_out_date):
                return Response(
                    {
                        'success': False,
                        'message': 'Room is not available for the selected dates',
                        'error_code': 'ROOM_UNAVAILABLE',
                        'requested_dates': {
                            'check_in': check_in_date,
                            'check_out': check_out_date
                        }
                    },
                    status=status.HTTP_409_CONFLICT
                )
            
            # Prepare guest data for reservation
            guest_data = {
                'guest_first_name': validated_data.get('guest_first_name'),
                'guest_last_name': validated_data.get('guest_last_name'),
                'guest_email': validated_data.get('guest_email'),
                'guest_phone': validated_data.get('guest_phone'),
                'guest_country': validated_data.get('guest_country'),
                'guest_address': validated_data.get('guest_address'),
                'guest_city': validated_data.get('guest_city'),
                'guest_postal_code': validated_data.get('guest_postal_code'),
                'guest_passport_number': validated_data.get('guest_passport_number'),
                'adults': validated_data.get('adults', 1),
                'children': validated_data.get('children', 0),
                'room_rate': validated_data.get('room_rate'),
                'tax_amount': validated_data.get('tax_amount', 0),
                'discount_amount': validated_data.get('discount_amount', 0),
                'discount_type': validated_data.get('discount_type'),
                'special_requests': validated_data.get('special_requests'),
            }
            
            # Atomically reserve the room
            success, booking, error = RoomAvailabilityService.reserve_room(
                room_id=room_id,
                check_in_date=check_in_date,
                check_out_date=check_out_date,
                guest_data=guest_data,
                user=request.user if request.user.is_authenticated else None
            )
            
            if not success:
                return Response(
                    {
                        'success': False,
                        'message': error,
                        'error_code': 'BOOKING_FAILED'
                    },
                    status=status.HTTP_409_CONFLICT
                )
            
            # Send confirmation email asynchronously
            send_confirmation_email_async.delay(booking.id)
            
            # Serialize booking response
            booking_serializer = BookingSerializer(booking)
            
            return Response(
                {
                    'success': True,
                    'message': 'Booking created successfully',
                    'booking': booking_serializer.data,
                    'email_confirmation': {
                        'message': 'Confirmation email will be sent shortly',
                        'recipient': booking.guest_email,
                        'async': True
                    }
                },
                status=status.HTTP_201_CREATED
            )
        
        except ValidationError as e:
            return Response(
                {
                    'success': False,
                    'message': 'Validation error',
                    'errors': e.detail if hasattr(e, 'detail') else str(e),
                    'error_code': 'VALIDATION_ERROR'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error creating booking: {str(e)}", exc_info=True)
            return Response(
                {
                    'success': False,
                    'message': 'An unexpected error occurred while creating the booking',
                    'error_code': 'INTERNAL_ERROR'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# CRUD Operation 3: READ (Get specific booking details)
class BookingDetailAPIView(generics.RetrieveAPIView):
    """
    Get detailed booking information.
    
    GET: Returns detailed booking information
    """
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'pk'
    
    def get_queryset(self):
        """Optimized queryset for detailed view."""
        return Booking.objects.select_related(
            'user', 'room', 'room__hotel', 'room__room_type'
        ).prefetch_related(
            'room__room_type__additional_amenities', 'room__images'
        )


# CRUD Operation 4: UPDATE (Update specific booking)
class BookingUpdateAPIView(generics.UpdateAPIView):
    """
    Update booking details and handle status changes.
    
    PUT/PATCH: Updates booking details and sends emails for status changes
    """
    queryset = Booking.objects.all()
    serializer_class = BookingUpdateSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'pk'
    
    def get_queryset(self):
        """Optimized queryset for update view."""
        return Booking.objects.select_related(
            'user', 'room', 'room__hotel', 'room__room_type'
        )
    
    def perform_update(self, serializer):
        """Enhanced update with timestamp tracking and async email handling."""
        # Get the original status before update
        original_status = self.get_object().status
        
        # Save the updated booking
        booking = serializer.save(updated_at=timezone.now())
        
        # Check if status changed to cancelled
        if original_status != 'cancelled' and booking.status == 'cancelled':
            # Send cancellation email asynchronously
            send_cancellation_email_async.delay(booking.id)
            
            logger.info(f"Booking {booking.booking_id} status updated to cancelled - email queued")
            self.cancellation_email_sent = True
        else:
            self.cancellation_email_sent = False
        
        self.booking_instance = booking
    
    def update(self, request, *args, **kwargs):
        """Custom update response with email status."""
        response = super().update(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            # Get email status from perform_update
            cancellation_email_sent = getattr(self, 'cancellation_email_sent', False)
            booking = getattr(self, 'booking_instance', None)
            
            response_data = {
                'success': True,
                'message': 'Booking updated successfully',
                'booking': response.data
            }
            
            # Add email status if cancellation email was queued
            if cancellation_email_sent and booking:
                response_data['email_confirmation'] = {
                    'type': 'cancellation',
                    'status': 'queued',
                    'recipient': booking.guest_email,
                    'message': 'Cancellation confirmation email queued for delivery'
                }
            
            response.data = response_data
            
            response.data = response_data
        return response


# CRUD Operation 5: DELETE (Cancel/Delete booking)
class BookingDeleteAPIView(generics.DestroyAPIView):
    """
    Cancel or delete a booking and send cancellation email.
    
    DELETE: Cancels booking (soft delete) and sends cancellation confirmation email
    """
    queryset = Booking.objects.all()
    permission_classes = [IsAuthenticated]
    lookup_field = 'pk'
    
    def get_queryset(self):
        """Optimized queryset for cancellation view."""
        return Booking.objects.select_related(
            'user', 'room', 'room__hotel', 'room__room_type'
        )
    
    def perform_destroy(self, instance):
        """Soft delete - mark as cancelled instead of deleting and send async email."""
        # Store original status for email decision
        was_active = instance.status in ['pending', 'confirmed']
        
        # Mark as cancelled
        instance.status = 'cancelled'
        instance.updated_at = timezone.now()
        instance.save()
        
        # Send cancellation email asynchronously only if booking was active
        if was_active:
            send_cancellation_email_async.delay(instance.id)
            logger.info(f"Booking {instance.booking_id} cancelled - cancellation email queued")
            self.email_sent = True
        else:
            self.email_sent = False
            logger.info(f"Booking {instance.booking_id} was already cancelled - no email sent")
        
        self.booking_instance = instance
        
    def destroy(self, request, *args, **kwargs):
        """Override destroy to return appropriate response with email status."""
        instance = self.get_object()
        
        # Check if booking is already cancelled
        if instance.status == 'cancelled':
            return Response(
                {
                    'success': False,
                    'message': 'Booking is already cancelled',
                    'booking_id': instance.id,
                    'booking_reference': instance.booking_id
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Perform cancellation
        self.perform_destroy(instance)
        
        # Get email status from perform_destroy
        email_queued = getattr(self, 'email_sent', False)
        booking = getattr(self, 'booking_instance', instance)
        
        return Response(
            {
                'success': True,
                'message': 'Booking cancelled successfully',
                'booking_id': booking.id,
                'booking_reference': booking.booking_id,
                'cancellation_date': timezone.now().date().isoformat(),
                'email_confirmation': {
                    'status': 'queued' if email_queued else 'not_sent',
                    'recipient': booking.guest_email if email_queued else None,
                    'message': 'Cancellation email queued for delivery' if email_queued else 'Cancellation email not queued (booking was already inactive)'
                }
            },
            status=status.HTTP_200_OK
        )


class UserBookingListAPIView(generics.ListAPIView):
    """
    Get all bookings for a specific user.
    Useful for user profiles and booking history.
    """
    serializer_class = BookingListSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = BookingPagination
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at', 'check_in_date', 'status']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Return bookings for specific user."""
        user_id = self.kwargs['user_id']
        return Booking.objects.filter(
            user_id=user_id
        ).select_related(
            'room', 'room__hotel', 'room__room_type'
        ).order_by('-created_at')
    
    def list(self, request, *args, **kwargs):
        """Enhanced list response with user info."""
        try:
            user = User.objects.get(id=self.kwargs['user_id'])
            response = super().list(request, *args, **kwargs)
            response.data['user_info'] = {
                'id': user.id,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email
            }
            return response
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class RoomBookingListAPIView(generics.ListAPIView):
    """
    Get all bookings for a specific room.
    Useful for room management and availability checking.
    """
    serializer_class = BookingQuickSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = BookingPagination
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['check_in_date', 'created_at', 'status']
    ordering = ['check_in_date']
    
    def get_queryset(self):
        """Return bookings for specific room."""
        room_id = self.kwargs['room_id']
        queryset = Booking.objects.filter(
            room_id=room_id
        ).select_related('user')
        
        # Filter by status if provided
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by date range if provided
        from_date = self.request.query_params.get('from_date')
        to_date = self.request.query_params.get('to_date')
        if from_date:
            queryset = queryset.filter(check_out_date__gte=from_date)
        if to_date:
            queryset = queryset.filter(check_in_date__lte=to_date)
            
        return queryset.order_by('check_in_date')
    
    def list(self, request, *args, **kwargs):
        """Enhanced list response with room info and availability stats."""
        try:
            room = Room.objects.get(id=self.kwargs['room_id'])
            response = super().list(request, *args, **kwargs)
            
            # Add room information
            response.data['room_info'] = {
                'id': room.id,
                'room_number': room.room_number,
                'room_type': room.room_type.name,
                'hotel': room.hotel.name,
                'capacity': room.capacity,
                'base_price': str(room.base_price),
                'floor': room.floor,
                'view_type': room.view_type,
                'is_active': room.is_active
            }
            
            # Add booking statistics
            today = timezone.now().date()
            total_bookings = self.get_queryset().count()
            upcoming_bookings = self.get_queryset().filter(
                check_in_date__gte=today,
                status__in=['confirmed', 'pending']
            ).count()
            
            response.data['stats'] = {
                'total_bookings': total_bookings,
                'upcoming_bookings': upcoming_bookings,
                'is_currently_occupied': self.get_queryset().filter(
                    check_in_date__lte=today,
                    check_out_date__gte=today,
                    status='confirmed'
                ).exists()
            }
            
            return response
        except Room.DoesNotExist:
            return Response(
                {'error': 'Room not found'},
                status=status.HTTP_404_NOT_FOUND
            )
