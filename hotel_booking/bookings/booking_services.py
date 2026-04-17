"""
Enhanced booking services with database-level locking and transactional safety.
Prevents double-booking in high-concurrency scenarios with SELECT FOR UPDATE.
"""

from django.db import transaction, IntegrityError
from django.db.models import Q
from django.utils import timezone
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import date, timedelta
import logging

from core.models import Room, Hotel
from .models import Booking, BookingAuditLog, BookingRefund, RefundPolicy

logger = logging.getLogger(__name__)


class RoomReservationService:
    """
    Service for atomically reserving rooms with database-level locking.
    Prevents double-booking through SELECT FOR UPDATE and transactions.
    """
    
    @staticmethod
    def reserve_room(room_id, check_in_date, check_out_date, guest_data, user=None):
        """
        Atomically reserve a room using database locking.
        
        Uses SELECT FOR UPDATE to lock the room record for the duration of the transaction,
        ensuring no other request can book this room for overlapping dates.
        
        Args:
            room_id: ID of room to reserve
            check_in_date: Check-in date
            check_out_date: Check-out date
            guest_data: Dictionary with guest information
            user: Optional associated user
            
        Returns:
            (success: bool, booking: Booking or None, error: str or None)
        """
        try:
            with transaction.atomic():
                # Step 1: Lock the room for update
                room = Room.objects.select_for_update().get(id=room_id)
                
                # Step 2: Re-check availability with locked room
                conflicting = Booking.objects.filter(
                    room=room,
                    status__in=['confirmed', 'pending'],
                    check_in_date__lt=check_out_date,
                    check_out_date__gt=check_in_date
                ).exists()
                
                if conflicting:
                    logger.warning(
                        f"Double-booking prevented for room {room_id} "
                        f"({check_in_date} to {check_out_date})"
                    )
                    return False, None, 'Room is not available for selected dates'
                
                # Step 3: Create booking within transaction
                booking = Booking.objects.create(
                    room=room,
                    hotel=room.hotel,
                    check_in_date=check_in_date,
                    check_out_date=check_out_date,
                    user=user,
                    status='pending',
                    payment_status='pending',
                    **guest_data
                )
                
                # Step 4: Create audit log for booking creation
                BookingAuditLog.objects.create(
                    booking=booking,
                    changed_by=user,
                    change_type='created',
                    new_value={
                        'booking_id': booking.booking_id,
                        'status': 'pending',
                        'amount': str(booking.total_amount)
                    },
                    reason='Guest initiated booking',
                    ip_address=None  # Will be set from request in view
                )
                
                logger.info(
                    f"Room reserved successfully: {room_id} for "
                    f"{guest_data.get('guest_first_name')} {guest_data.get('guest_last_name')} "
                    f"({check_in_date} to {check_out_date})"
                )
                
                return True, booking, None
        
        except Room.DoesNotExist:
            logger.error(f"Room {room_id} not found")
            return False, None, 'Selected room does not exist'
        
        except ValidationError as e:
            logger.error(f"Validation error during room reservation: {str(e)}")
            return False, None, f'Validation error: {str(e)}'
        
        except IntegrityError as e:
            logger.error(f"Integrity error during room reservation: {str(e)}")
            return False, None, 'Database integrity error - booking failed'
        
        except Exception as e:
            logger.error(f"Unexpected error during room reservation: {str(e)}", exc_info=True)
            return False, None, f'Unexpected error: {str(e)}'
    
    @staticmethod
    def is_room_available(room_id, check_in_date, check_out_date):
        """
        Check if room is available for given dates.
        
        Args:
            room_id: Room ID to check
            check_in_date: Check-in date
            check_out_date: Check-out date
            
        Returns:
            bool: True if room is available, False otherwise
        """
        try:
            room = Room.objects.get(id=room_id)
            
            if not room.is_active or room.is_maintenance:
                return False
            
            # Check for conflicting bookings (pending or confirmed only)
            conflicting = Booking.objects.filter(
                room=room,
                status__in=['confirmed', 'pending'],
                check_in_date__lt=check_out_date,
                check_out_date__gt=check_in_date
            ).exists()
            
            return not conflicting
        
        except Room.DoesNotExist:
            return False
        except Exception as e:
            logger.error(f"Error checking room availability: {str(e)}")
            return False


class BookingConfirmationService:
    """
    Service for confirming bookings and managing confirmation workflow.
    """
    
    @staticmethod
    def confirm_booking(booking, confirmed_by=None):
        """
        Confirm a pending booking, moving it from pending to confirmed status.
        
        Args:
            booking: Booking instance to confirm
            confirmed_by: User who confirmed the booking (staff/admin)
            
        Returns:
            (success: bool, error: str or None)
        """
        try:
            if booking.status != 'pending':
                return False, f'Booking is {booking.get_status_display()}, not pending'
            
            # Update booking status
            booking.status = 'confirmed'
            booking.updated_at = timezone.now()
            booking.save()
            
            # Create audit log
            BookingAuditLog.objects.create(
                booking=booking,
                changed_by=confirmed_by,
                change_type='confirmed',
                old_value={'status': 'pending'},
                new_value={'status': 'confirmed'},
                reason='Booking confirmed by staff',
                ip_address=None
            )
            
            logger.info(f"Booking {booking.booking_id} confirmed by {confirmed_by or 'system'}")
            return True, None
        
        except Exception as e:
            logger.error(f"Error confirming booking: {str(e)}")
            return False, str(e)


class BookingCancellationService:
    """
    Service for cancelling bookings with refund calculation and processing.
    """
    
    @staticmethod
    def cancel_booking(booking, cancel_reason='Guest requested cancellation', cancelled_by=None):
        """
        Cancel a booking and calculate refund based on policy.
        
        Args:
            booking: Booking instance to cancel
            cancel_reason: Reason for cancellation
            cancelled_by: User who cancelled (None if guest-initiated)
            
        Returns:
            {
                'success': bool,
                'message': str,
                'refund': refund_dict or None,
                'error': str or None
            }
        """
        try:
            if booking.status in ['cancelled', 'completed']:
                return {
                    'success': False,
                    'message': f'Cannot cancel {booking.get_status_display()} booking',
                    'refund': None,
                    'error': f'Booking is already {booking.status}'
                }
            
            # Check if cancellation is within allowed window
            days_until_checkin = (booking.check_in_date - timezone.now().date()).days
            if days_until_checkin < 0:
                return {
                    'success': False,
                    'message': 'Cannot cancel booking after check-in date',
                    'refund': None,
                    'error': 'Check-in date has passed'
                }
            
            # Get refund policy for hotel
            try:
                refund_policy = RefundPolicy.objects.get(hotel=booking.hotel)
            except RefundPolicy.DoesNotExist:
                # Create default policy if not exists
                refund_policy = RefundPolicy.objects.create(
                    hotel=booking.hotel,
                    free_cancellation_days=1,
                    refund_schedule={'3': 50, '0': 0},
                    non_refundable_deposit_percentage=0
                )
                logger.info(f"Created default refund policy for {booking.hotel.name}")
            
            # Calculate refund
            refund_info = refund_policy.calculate_refund(booking)
            
            # Update booking status
            booking.status = 'cancelled'
            booking.updated_at = timezone.now()
            booking.save()
            
            # Create refund record
            refund = BookingRefund.objects.create(
                booking=booking,
                refund_amount=refund_info['refund_amount'],
                non_refundable_amount=refund_info['non_refundable_amount'],
                refund_reason=cancel_reason,
                refund_status='pending',
                refund_method='original_payment',
                notes=f'Cancelled {days_until_checkin} days before check-in'
            )
            
            # Create audit log
            BookingAuditLog.objects.create(
                booking=booking,
                changed_by=cancelled_by,
                change_type='cancelled',
                old_value={'status': booking.status, 'payment_status': booking.payment_status},
                new_value={
                    'status': 'cancelled',
                    'refund_amount': str(refund.refund_amount),
                    'refund_status': 'pending'
                },
                reason=cancel_reason,
                ip_address=None
            )
            
            logger.info(
                f"Booking {booking.booking_id} cancelled - "
                f"Refund: ${refund_info['refund_amount']} "
                f"({refund_info['refund_percentage']}%)"
            )
            
            return {
                'success': True,
                'message': 'Booking cancelled successfully',
                'refund': {
                    'refund_amount': float(refund_info['refund_amount']),
                    'refund_percentage': refund_info['refund_percentage'],
                    'non_refundable_amount': float(refund_info['non_refundable_amount']),
                    'reason': refund_info['reason'],
                    'days_until_checkin': days_until_checkin,
                    'refund_status': 'pending'
                },
                'error': None
            }
        
        except Exception as e:
            logger.error(f"Error cancelling booking {booking.booking_id}: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': 'Error processing cancellation',
                'refund': None,
                'error': str(e)
            }


class BookingAuditService:
    """
    Service for recording audit logs and generating audit trails.
    """
    
    @staticmethod
    def log_change(booking, change_type, old_value=None, new_value=None, 
                   changed_by=None, reason='', ip_address=None):
        """
        Log a booking change for audit trail.
        
        Args:
            booking: Booking instance
            change_type: Type of change (from CHANGE_TYPE_CHOICES)
            old_value: Previous value (dict)
            new_value: New value (dict)
            changed_by: User who made change
            reason: Reason for change
            ip_address: IP address of requester
            
        Returns:
            BookingAuditLog instance
        """
        return BookingAuditLog.objects.create(
            booking=booking,
            changed_by=changed_by,
            change_type=change_type,
            old_value=old_value,
            new_value=new_value,
            reason=reason,
            ip_address=ip_address
        )
    
    @staticmethod
    def get_booking_history(booking):
        """
        Get complete audit history for a booking.
        
        Args:
            booking: Booking instance
            
        Returns:
            QuerySet of BookingAuditLog ordered by date
        """
        return BookingAuditLog.objects.filter(booking=booking).order_by('-changed_at')
