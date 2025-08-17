from django.shortcuts import render
from django.core.management import call_command
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Count, Avg, Q, Sum, Min, Max
from rest_framework.decorators import api_view
from rest_framework.response import Response
from core.models import (
    Hotel, Room, RoomType, Extra, SeasonalPricing,
    RoomImage, RoomAmenity, RoomTypeAmenity
)
from bookings.models import Booking
from accounts.models import CustomUser


def dashboard_view(request):
    """Main dashboard view"""
    return render(request, 'dashboard.html')


@api_view(['GET'])
def api_stats(request):
    """Get comprehensive API statistics for dashboard"""
    try:
        # Basic counts
        basic_stats = {
            'hotels': Hotel.objects.count(),
            'rooms': Room.objects.count(),
            'room_types': RoomType.objects.count(),
            'bookings': Booking.objects.count(),
            'users': CustomUser.objects.count(),
            'active_rooms': Room.objects.filter(is_active=True).count(),
            'active_hotels': Hotel.objects.filter(is_active=True).count(),
        }
        
        # Enhanced room features stats
        room_features = {
            'room_amenities': RoomAmenity.objects.count(),
            'room_images': RoomImage.objects.count(),
            'seasonal_pricing_rules': SeasonalPricing.objects.count(),
            'extras_services': Extra.objects.count(),
            'accessible_rooms': Room.objects.filter(room_type__is_accessible=True).count(),
            'corner_rooms': Room.objects.filter(is_corner_room=True).count(),
            'connecting_rooms': Room.objects.filter(is_connecting_room=True).count(),
            'rooms_with_balcony': Room.objects.filter(room_type__has_balcony=True).count(),
            'suite_rooms': Room.objects.filter(room_type__category__in=['suite', 'presidential']).count(),
        }
        
        # Room condition analysis
        room_conditions = {
            condition[0]: Room.objects.filter(condition=condition[0]).count()
            for condition in Room._meta.get_field('condition').choices
        }
        
        # Housekeeping status
        housekeeping_status = {
            status[0]: Room.objects.filter(housekeeping_status=status[0]).count()
            for status in Room._meta.get_field('housekeeping_status').choices
        }
        
        # Room type distribution
        room_type_distribution = list(
            RoomType.objects.annotate(
                room_count=Count('rooms')
            ).values('name', 'category', 'room_count', 'max_capacity')
        )
        
        # View type distribution
        view_distribution = list(
            Room.objects.values('view_type').annotate(
                count=Count('id')
            ).order_by('-count')
        )
        
        # Booking statistics
        booking_stats = {
            'confirmed_bookings': Booking.objects.filter(status='confirmed').count(),
            'checked_in': Booking.objects.filter(status='checked_in').count(),
            'checked_out': Booking.objects.filter(status='checked_out').count(),
            'cancelled': Booking.objects.filter(status='cancelled').count(),
            'total_revenue': float(
                Booking.objects.filter(
                    status__in=['confirmed', 'checked_in', 'checked_out']
                ).aggregate(
                    total=Sum('total_price')
                )['total'] or 0
            ),
        }
        
        # Amenity statistics
        amenity_stats = {
            'total_amenities': RoomAmenity.objects.count(),
            'premium_amenities': RoomAmenity.objects.filter(is_premium=True).count(),
            'technology_amenities': RoomAmenity.objects.filter(category='technology').count(),
            'luxury_amenities': RoomAmenity.objects.filter(category='luxury').count(),
            'accessibility_amenities': RoomAmenity.objects.filter(category='accessibility').count(),
            'family_amenities': RoomAmenity.objects.filter(category='family').count(),
        }
        
        # Price analysis
        price_stats = {
            'avg_room_price': float(Room.objects.aggregate(Avg('base_price'))['base_price__avg'] or 0),
            'min_room_price': float(Room.objects.aggregate(Min('base_price'))['base_price__min'] or 0),
            'max_room_price': float(Room.objects.aggregate(Max('base_price'))['base_price__max'] or 0),
        }
        
        return Response({
            'basic_stats': basic_stats,
            'room_features': room_features,
            'room_conditions': room_conditions,
            'housekeeping_status': housekeeping_status,
            'room_type_distribution': room_type_distribution,
            'view_distribution': view_distribution,
            'booking_stats': booking_stats,
            'amenity_stats': amenity_stats,
            'price_stats': price_stats,
            'last_updated': timezone.now().isoformat()
        })
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
