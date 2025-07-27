from django.shortcuts import render
from django.http import JsonResponse
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response
from core.models import Hotel, Room, RoomType
from bookings.models import Booking
from accounts.models import CustomUser


def dashboard_view(request):
    """Main dashboard view"""
    return render(request, 'dashboard.html')


@api_view(['GET'])
def api_stats(request):
    """Get API statistics for dashboard"""
    try:
        stats = {
            'hotels': Hotel.objects.count(),
            'rooms': Room.objects.count(),
            'room_types': RoomType.objects.count(),
            'bookings': Booking.objects.count(),
            'users': CustomUser.objects.count(),
            'active_rooms': Room.objects.filter(is_active=True).count(),
            'active_hotels': Hotel.objects.filter(is_active=True).count(),
        }
        
        return Response(stats)
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
def api_health(request):
    """API health check endpoint"""
    try:
        # Test database connection
        hotel_count = Hotel.objects.count()
        
        return Response({
            'status': 'healthy',
            'database': 'connected',
            'hotels': hotel_count,
            'timestamp': timezone.now().isoformat()
        })
    except Exception as e:
        return Response({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=500)
