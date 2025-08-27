from django.shortcuts import render
from django.contrib.auth.decorators import login_required, permission_required
from bookings.models import Booking
from core.models import Hotel, Room, Extra
from django.utils import timezone


@login_required
@permission_required('auth.view_group', raise_exception=True)
def dashboard(request):
    """Enhanced dashboard with quick stats for the manager UI."""
    today = timezone.now().date()
    total_bookings = Booking.objects.count()
    new_bookings = Booking.objects.filter(booking_date__date=today).count()
    checked_in = Booking.objects.filter(status='checked_in').count()
    upcoming = Booking.objects.filter(check_in__gte=today).count()

    hotels_count = Hotel.objects.count()
    rooms_count = Room.objects.count()
    extras_count = Extra.objects.count()

    recent_bookings = Booking.objects.order_by('-booking_date')[:8]

    context = {
        'total_bookings': total_bookings,
        'new_bookings': new_bookings,
        'checked_in': checked_in,
        'upcoming': upcoming,
        'hotels_count': hotels_count,
        'rooms_count': rooms_count,
        'extras_count': extras_count,
        'recent_bookings': recent_bookings,
    }

    return render(request, 'manager/dashboard.html', context)
