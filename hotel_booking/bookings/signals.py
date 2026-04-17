from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.mail import send_mail
from django.template.loader import render_to_string
from .models import Booking, BookingAuditLog


@receiver(post_save, sender=Booking)
def send_booking_email_notification(sender, instance, created, **kwargs):
    """
    Send email notification to guest when booking is created or status changes.
    Triggered automatically via Django signals.
    """
    try:
        # Determine action based on booking status
        action = 'created' if created else 'updated'
        
        if instance.status == 'confirmed':
            action = 'confirmed'
        elif instance.status == 'cancelled':
            action = 'cancelled'
        elif instance.status == 'completed':
            action = 'completed'
        
        # Compose email
        subject_map = {
            'created': f'Booking Confirmation - {instance.booking_id}',
            'updated': f'Booking Updated - {instance.booking_id}',
            'confirmed': f'Booking Confirmed - {instance.booking_id}',
            'cancelled': f'Booking Cancelled - {instance.booking_id}',
            'completed': f'Thank You for Staying at {instance.hotel.name}',
        }
        
        subject = subject_map.get(action, 'Booking Update')
        
        # Simple email content (can be replaced with template rendering)
        message = f"""
        Dear {instance.guest_full_name()},
        
        {'Your booking has been confirmed!' if action == 'confirmed' else 'Your booking has been updated.'}
        
        Booking Details:
        ===============
        Booking ID: {instance.booking_id}
        Hotel: {instance.hotel.name}
        Room: {instance.room.room_type.name} #{instance.room.room_number}
        Check-in: {instance.check_in_date.strftime('%B %d, %Y')}
        Check-out: {instance.check_out_date.strftime('%B %d, %Y')}
        Nights: {instance.nights}
        
        Guest Information:
        ==================
        Name: {instance.guest_full_name()}
        Email: {instance.guest_email}
        Phone: {instance.guest_phone}
        
        Pricing:
        ========
        Room Rate: ${instance.room_rate:.2f}
        Tax: ${instance.tax_amount:.2f}
        Discount: ${instance.discount_amount:.2f}
        Total: ${instance.total_amount:.2f}
        
        Status: {instance.get_status_display()}
        Payment Status: {instance.get_payment_status_display()}
        
        If you have any questions, please contact us at support@hotelbooking.com or call our 24/7 support line.
        
        Best regards,
        Hotel Booking System
        """
        
        # Send email
        send_mail(
            subject,
            message,
            'noreply@hotelbooking.com',
            [instance.guest_email],
            fail_silently=True
        )
        
    except Exception as e:
        # Log error but don't crash the booking process
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error sending booking email: {str(e)}")


@receiver(post_save, sender=BookingAuditLog)
def notify_on_booking_audit(sender, instance, created, **kwargs):
    """
    Send notification email to manager when important booking changes occur.
    """
    if not created:
        return
    
    try:
        # Only send emails for significant changes
        significant_changes = [
            'status_change',
            'payment_status_change',
            'refund_issued',
            'cancelled',
            'deleted'
        ]
        
        if instance.change_type not in significant_changes:
            return
        
        # Get booking details
        booking = instance.booking
        changed_by = instance.changed_by
        
        subject = f'Booking Alert: {booking.booking_id} - {instance.get_change_type_display()}'
        
        message = f"""
        Booking Alert
        =============
        
        Change Type: {instance.get_change_type_display()}
        Booking ID: {booking.booking_id}
        Guest: {booking.guest_full_name()}
        Hotel: {booking.hotel.name}
        
        Changed By: {changed_by.first_name} {changed_by.last_name} ({changed_by.email})
        Changed At: {instance.changed_at.strftime('%Y-%m-%d %H:%M:%S')}
        
        Reason: {instance.reason or 'N/A'}
        
        This is an automated alert from the Hotel Booking System.
        """
        
        # Send to admin email (configure in settings)
        from django.conf import settings
        admin_email = getattr(settings, 'ADMIN_EMAIL', 'admin@hotelbooking.com')
        
        send_mail(
            subject,
            message,
            'noreply@hotelbooking.com',
            [admin_email],
            fail_silently=True
        )
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error sending audit notification: {str(e)}")


def ready(self):
    """Connect all signals when app is ready"""
    import bookings.signals
