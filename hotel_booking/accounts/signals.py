from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Sum, Q
from decimal import Decimal
from .models import CustomUser, UserProfile


@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    """Create user profile when user is created"""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=CustomUser)
def save_user_profile(sender, instance, **kwargs):
    """Save user profile when user is saved"""
    if hasattr(instance, 'profile'):
        instance.profile.save()


# Booking-related signals to sync profile statistics
@receiver(post_save, sender='bookings.Booking')
def sync_user_booking_stats_on_create(sender, instance, created, **kwargs):
    """
    Update user profile stats when booking is created or completed.
    This keeps total_bookings and total_spent in sync automatically.
    """
    if instance.user and instance.user.is_authenticated:
        profile = instance.user.profile
        
        if created or instance.status == 'completed':
            # Recalculate stats from all completed bookings
            from bookings.models import Booking
            
            completed_bookings = Booking.objects.filter(
                user=instance.user,
                status__in=['completed', 'confirmed'],
                payment_status='paid'
            )
            
            profile.total_bookings = completed_bookings.count()
            total_spent = completed_bookings.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
            profile.total_spent = total_spent
            profile.save()


@receiver(post_save, sender='bookings.Booking')
def sync_user_booking_stats_on_cancel(sender, instance, **kwargs):
    """
    Update user profile stats when booking is cancelled.
    """
    if instance.user and instance.status == 'cancelled':
        profile = instance.user.profile
        
        from bookings.models import Booking
        
        # Recount completed/confirmed paid bookings
        completed_bookings = Booking.objects.filter(
            user=instance.user,
            status__in=['completed', 'confirmed'],
            payment_status='paid'
        )
        
        profile.total_bookings = completed_bookings.count()
        total_spent = completed_bookings.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        profile.total_spent = total_spent
        profile.save()
