# Django imports
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
import logging

logger = logging.getLogger(__name__)


class BookingEmailService:
    """Service class for handling booking-related emails"""
    
    @staticmethod
    def send_booking_confirmation(booking):
        """Send booking confirmation email to guest"""
        try:
            subject = f'Booking Confirmation - {booking.booking_reference}'
            
            # Create email context
            context = {
                'booking': booking,
                'guest_name': booking.primary_guest_name,
                'hotel': booking.room.hotel,
                'room': booking.room,
                'room_type': booking.room.room_type,
                'nights': (booking.check_out - booking.check_in).days,
            }
            
            # Render HTML email template
            html_message = render_to_string('emails/booking_confirmation.html', context)
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL or 'noreply@hotelbooking.com',
                recipient_list=[booking.primary_guest_email],
                html_message=html_message,
                fail_silently=False
            )
            
            logger.info(f"Booking confirmation email sent for {booking.booking_reference}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send booking confirmation email for {booking.booking_reference}: {e}")
            return False
    
    @staticmethod
    def send_booking_cancellation(booking):
        """Send booking cancellation email to guest"""
        try:
            subject = f'Booking Cancellation - {booking.booking_reference}'
            
            context = {
                'booking': booking,
                'guest_name': booking.primary_guest_name,
                'hotel': booking.room.hotel,
                'room': booking.room,
                'room_type': booking.room.room_type,
            }
            
            html_message = render_to_string('emails/booking_cancellation.html', context)
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL or 'noreply@hotelbooking.com',
                recipient_list=[booking.primary_guest_email],
                html_message=html_message,
                fail_silently=False
            )
            
            logger.info(f"Booking cancellation email sent for {booking.booking_reference}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send booking cancellation email for {booking.booking_reference}: {e}")
            return False
    
    @staticmethod
    def send_booking_modification(booking):
        """Send booking modification email to guest"""
        try:
            subject = f'Booking Modified - {booking.booking_reference}'
            
            context = {
                'booking': booking,
                'guest_name': booking.primary_guest_name,
                'hotel': booking.room.hotel,
                'room': booking.room,
                'room_type': booking.room.room_type,
                'nights': (booking.check_out - booking.check_in).days,
            }
            
            html_message = render_to_string('emails/booking_modification.html', context)
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL or 'noreply@hotelbooking.com',
                recipient_list=[booking.primary_guest_email],
                html_message=html_message,
                fail_silently=False
            )
            
            logger.info(f"Booking modification email sent for {booking.booking_reference}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send booking modification email for {booking.booking_reference}: {e}")
            return False
