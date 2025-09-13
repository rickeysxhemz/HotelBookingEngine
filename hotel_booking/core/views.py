# Django imports
from django.shortcuts import get_object_or_404
from django.db.models import Q, Prefetch, Avg
from decimal import Decimal

# Django REST Framework imports
from rest_framework import generics, status, permissions, serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

# Local imports
from .models import Hotel, Room, RoomType, Extra, ContactMessage
from .services import HotelSearchService, RoomAvailabilityService, ContactEmailService
from bookings.serializers import (
    RoomSerializer, RoomTypeSerializer, ExtraSerializer, RoomAvailabilitySerializer
)
from .serializers import ContactMessageSerializer


class HotelSerializer(serializers.ModelSerializer):
    """Comprehensive serializer for hotel information"""
    room_types = serializers.SerializerMethodField()
    amenities_count = serializers.SerializerMethodField()
    room_stats = serializers.SerializerMethodField()
    available_amenities = serializers.SerializerMethodField()
    
    class Meta:
        model = Hotel
        fields = [
            'id', 'name', 'description', 'full_address', 'phone_number',
            'email', 'website', 'star_rating', 'check_in_time', 'check_out_time',
            'room_types', 'amenities_count', 'room_stats', 'available_amenities'
        ]
    
    def get_room_types(self, obj):
        """Get comprehensive room types for this hotel"""
        room_types = RoomType.objects.filter(
            rooms__hotel=obj
        ).distinct()
        return RoomTypeSerializer(room_types, many=True).data
    
    def get_amenities_count(self, obj):
        """Get count of available amenities/extras"""
        return obj.extras.filter(is_active=True).count()
    
    def get_room_stats(self, obj):
        """Get comprehensive room statistics"""
        rooms = obj.rooms.filter(is_active=True)
        return {
            'total_rooms': rooms.count(),
            'available_rooms': rooms.filter(is_maintenance=False).count(),
            'room_types_count': rooms.values('room_type').distinct().count(),
            'floors': rooms.values_list('floor', flat=True).distinct().count(),
            'corner_rooms': rooms.filter(is_corner_room=True).count(),
            'accessible_rooms': rooms.filter(room_type__is_accessible=True).count(),
            'rooms_with_balcony': rooms.filter(room_type__has_balcony=True).count(),
            'suite_rooms': rooms.filter(room_type__category__in=['suite', 'presidential']).count(),
        }
    
    def get_available_amenities(self, obj):
        """Get list of available amenities and room features"""
        from core.models import RoomAmenity
        room_amenities = RoomAmenity.objects.filter(
            roomtypeamenity__room_type__rooms__hotel=obj
        ).distinct()
        
        return {
            'hotel_amenities': [
                {
                    'id': str(extra.id),
                    'name': extra.name,
                    'description': extra.description,
                    'category': extra.category
                } for extra in obj.extras.filter(is_active=True)
            ],
            'room_amenities': [
                {
                    'id': str(amenity.id),
                    'name': amenity.name,
                    'description': amenity.description,
                    'category': amenity.category,
                    'is_premium': amenity.is_premium
                } for amenity in room_amenities
            ]
        }


class RoomTypeSerializer(serializers.ModelSerializer):
    """Serializer for room type information"""
    amenities = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()
    
    class Meta:
        model = RoomType
        fields = [
            'id', 'name', 'description', 'max_capacity', 'bed_type', 'bed_count',
            'bathroom_count', 'room_size_sqm', 'amenities', 'is_accessible', 'images'
        ]
    
    def get_amenities(self, obj):
        return obj.amenities_list
    
    def get_images(self, obj):
        """Get room type images"""
        from core.models import RoomImage
        images = RoomImage.objects.filter(room_type=obj, is_active=True).order_by('display_order')
        return [{
            'id': str(img.id),
            'image_url': img.image.url if img.image else None,
            'alt_text': img.image_alt_text,
            'caption': img.caption,
            'image_type': img.image_type,
            'is_primary': img.is_primary,
            'display_order': img.display_order
        } for img in images]


class HotelListAPIView(generics.ListAPIView):
    """List all active hotels"""
    serializer_class = HotelSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        """Get active hotels"""
        return Hotel.objects.filter(is_active=True).prefetch_related(
            'rooms__room_type', 'extras'
        )


class HotelDetailAPIView(generics.RetrieveAPIView):
    """Get detailed hotel information"""
    serializer_class = HotelSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'id'
    lookup_url_kwarg = 'hotel_id'
    
    def get_queryset(self):
        """Get active hotels with related data"""
        return Hotel.objects.filter(is_active=True).prefetch_related(
            'rooms__room_type', 'extras', 'seasonal_pricing'
        )
    
    def retrieve(self, request, *args, **kwargs):
        """Add additional hotel information"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        
        # Add additional data
        data = serializer.data
        data['policies'] = {
            'cancellation_policy': instance.cancellation_policy,
            'pet_policy': instance.pet_policy,
            'smoking_policy': instance.smoking_policy
        }
        data['total_rooms'] = instance.rooms.filter(is_active=True).count()
        
        return Response(data)


class HotelRoomsAPIView(generics.ListAPIView):
    """List rooms for a specific hotel"""
    serializer_class = RoomSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        """Get active rooms for the hotel"""
        hotel_id = self.kwargs['hotel_id']
        return Room.objects.filter(
            hotel_id=hotel_id,
            is_active=True,
            is_maintenance=False
        ).select_related('room_type', 'hotel')
    
    def list(self, request, *args, **kwargs):
        """Add hotel information to response"""
        hotel_id = self.kwargs['hotel_id']
        hotel = get_object_or_404(Hotel, id=hotel_id, is_active=True)
        
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            'hotel': {
                'id': str(hotel.id),
                'name': hotel.name
            },
            'rooms': serializer.data,
            'total_rooms': len(serializer.data)
        })


class HotelRoomTypesAPIView(generics.ListAPIView):
    """List room types available at a hotel"""
    serializer_class = RoomTypeSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        """Get room types available at the hotel"""
        hotel_id = self.kwargs['hotel_id']
        return RoomType.objects.filter(
            rooms__hotel_id=hotel_id,
            rooms__is_active=True
        ).distinct()
    
    def list(self, request, *args, **kwargs):
        """Add hotel and pricing information"""
        hotel_id = self.kwargs['hotel_id']
        hotel = get_object_or_404(Hotel, id=hotel_id, is_active=True)
        
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        # Add room count and pricing info for each room type
        data = serializer.data
        for room_type_data in data:
            room_type_id = room_type_data['id']
            rooms = Room.objects.filter(
                hotel_id=hotel_id,
                room_type_id=room_type_id,
                is_active=True,
                is_maintenance=False
            )
            
            room_type_data['available_rooms'] = rooms.count()
            if rooms.exists():
                room_type_data['price_range'] = {
                    'min_price': min(room.base_price for room in rooms),
                    'max_price': max(room.base_price for room in rooms)
                }
        
        return Response({
            'hotel': {
                'id': str(hotel.id),
                'name': hotel.name
            },
            'room_types': data
        })


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def room_availability_search(request):
    """Search for room availability"""
    from rest_framework import serializers
    
    # Import serializers here to avoid circular imports
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
        
        # Serialize results
        serialized_results = []
        for hotel_result in results['results']:
            hotel_data = {
                'hotel': HotelSerializer(hotel_result['hotel']).data,
                'available_rooms': hotel_result['available_room_count'],
                'room_combinations': []
            }
            
            # Add room combinations
            for combination in hotel_result['room_combinations']:
                room_data = []
                for room in combination['rooms']:
                    room_serializer = RoomSerializer(room, context={'request': request})
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
def get_hotel_amenities(request, hotel_id):
    """Get hotel amenities and extras"""
    try:
        hotel = get_object_or_404(Hotel, id=hotel_id, is_active=True)
        
        # Get all extras grouped by category
        extras_by_category = {}
        for extra in hotel.extras.filter(is_active=True):
            category = extra.get_category_display()
            if category not in extras_by_category:
                extras_by_category[category] = []
            
            extras_by_category[category].append({
                'id': str(extra.id),
                'name': extra.name,
                'description': extra.description,
                'price': extra.price,
                'pricing_type': extra.get_pricing_type_display(),
                'max_quantity': extra.max_quantity
            })
        
        # Get room type amenities
        room_amenities = set()
        for room_type in RoomType.objects.filter(rooms__hotel=hotel).distinct():
            room_amenities.update(room_type.amenities_list)
        
        return Response({
            'hotel': {
                'id': str(hotel.id),
                'name': hotel.name
            },
            'room_amenities': list(room_amenities),
            'hotel_services': extras_by_category
        })
        
    except Exception as e:
        return Response(
            {'error': f'Failed to get hotel amenities: {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_hotel_policies(request, hotel_id):
    """Get hotel policies and information"""
    try:
        hotel = get_object_or_404(Hotel, id=hotel_id, is_active=True)
        
        return Response({
            'hotel': {
                'id': str(hotel.id),
                'name': hotel.name
            },
            'policies': {
                'cancellation_policy': hotel.cancellation_policy,
                'pet_policy': hotel.pet_policy,
                'smoking_policy': hotel.smoking_policy
            },
            'timing': {
                'check_in_time': hotel.check_in_time,
                'check_out_time': hotel.check_out_time
            },
            'contact': {
                'phone': hotel.phone_number,
                'email': hotel.email,
                'website': hotel.website
            },
            'address': hotel.full_address
        })
        
    except Exception as e:
        return Response(
            {'error': f'Failed to get hotel policies: {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST
        )


# ===== MISSING VIEWS IMPLEMENTATION =====

class HotelSearchAPIView(generics.ListAPIView):
    """Search hotels with filters"""
    serializer_class = HotelSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        queryset = Hotel.objects.filter(is_active=True)
        
        # Filter by location
        location = self.request.query_params.get('location')
        if location:
            queryset = queryset.filter(
                Q(city__icontains=location) |
                Q(state__icontains=location) |
                Q(country__icontains=location)
            )
        
        # Filter by star rating
        min_rating = self.request.query_params.get('min_rating')
        if min_rating:
            queryset = queryset.filter(star_rating__gte=min_rating)
        
        return queryset


class FeaturedHotelsAPIView(generics.ListAPIView):
    """Get featured hotels"""
    serializer_class = HotelSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        # Return hotels with high ratings or special designation
        return Hotel.objects.filter(
            is_active=True,
            star_rating__gte=4
        ).order_by('-star_rating')[:5]


class NearbyHotelsAPIView(generics.ListAPIView):
    """Find nearby hotels"""
    serializer_class = HotelSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        # In a real implementation, you'd use geolocation
        # For now, return all active hotels
        return Hotel.objects.filter(is_active=True)[:10]


class HotelGalleryAPIView(generics.RetrieveAPIView):
    """Get hotel image gallery"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, hotel_id):
        try:
            hotel = Hotel.objects.get(id=hotel_id, is_active=True)
            
            # In a real implementation, you'd have a HotelImage model
            gallery = {
                'hotel_id': str(hotel.id),
                'images': [
                    {
                        'id': 1,
                        'url': '/media/hotels/hotel_lobby.jpg',
                        'caption': 'Hotel Lobby',
                        'is_primary': True
                    },
                    {
                        'id': 2,
                        'url': '/media/hotels/hotel_room.jpg',
                        'caption': 'Deluxe Room',
                        'is_primary': False
                    }
                ]
            }
            
            return Response(gallery)
            
        except Hotel.DoesNotExist:
            return Response({'error': 'Hotel not found'}, status=status.HTTP_404_NOT_FOUND)


class HotelReviewsAPIView(generics.ListAPIView):
    """Get hotel reviews"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, hotel_id):
        try:
            hotel = Hotel.objects.get(id=hotel_id, is_active=True)
            
            # In a real implementation, you'd have a Review model
            reviews = {
                'hotel_id': str(hotel.id),
                'average_rating': 4.5,
                'total_reviews': 125,
                'reviews': [
                    {
                        'id': 1,
                        'guest_name': 'John D.',
                        'rating': 5,
                        'comment': 'Excellent service and beautiful rooms!',
                        'date': '2024-07-20',
                        'verified_stay': True
                    },
                    {
                        'id': 2,
                        'guest_name': 'Sarah M.',
                        'rating': 4,
                        'comment': 'Great location, friendly staff.',
                        'date': '2024-07-18',
                        'verified_stay': True
                    }
                ]
            }
            
            return Response(reviews)
            
        except Hotel.DoesNotExist:
            return Response({'error': 'Hotel not found'}, status=status.HTTP_404_NOT_FOUND)


class HotelPoliciesAPIView(generics.GenericAPIView):
    """Get hotel policies"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, hotel_id):
        try:
            hotel = get_object_or_404(Hotel, id=hotel_id, is_active=True)
            
            return Response({
                'hotel': {
                    'id': str(hotel.id),
                    'name': hotel.name
                },
                'policies': {
                    'cancellation_policy': hotel.cancellation_policy,
                    'pet_policy': hotel.pet_policy,
                    'smoking_policy': hotel.smoking_policy
                },
                'timing': {
                    'check_in_time': hotel.check_in_time,
                    'check_out_time': hotel.check_out_time
                },
                'contact': {
                    'phone': hotel.phone_number,
                    'email': hotel.email,
                    'website': hotel.website
                },
                'address': hotel.full_address
            })
            
        except Exception as e:
            return Response(
                {'error': f'Failed to get hotel policies: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )


class RoomDetailAPIView(generics.RetrieveAPIView):
    """Get detailed room information"""
    serializer_class = RoomSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_object(self):
        hotel_id = self.kwargs.get('hotel_id')
        room_id = self.kwargs.get('room_id')
        
        return get_object_or_404(
            Room,
            id=room_id,
            hotel_id=hotel_id,
            hotel__is_active=True
        )


class HotelAvailabilityAPIView(generics.GenericAPIView):
    """Check hotel availability"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, hotel_id):
        try:
            hotel = Hotel.objects.get(id=hotel_id, is_active=True)
            
            check_in = request.query_params.get('checkin')
            check_out = request.query_params.get('checkout')
            guests = int(request.query_params.get('guests', 1))
            
            if not check_in or not check_out:
                return Response(
                    {'error': 'checkin and checkout dates are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Use existing availability service
            available_rooms = RoomAvailabilityService.get_available_rooms(
                hotel_id=hotel_id,
                check_in_date=check_in,
                check_out_date=check_out,
                guests=guests
            )
            
            return Response({
                'hotel_id': str(hotel.id),
                'check_in': check_in,
                'check_out': check_out,
                'guests': guests,
                'available_rooms': available_rooms,
                'total_available': len(available_rooms)
            })
            
        except Hotel.DoesNotExist:
            return Response({'error': 'Hotel not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class AvailabilityCalendarAPIView(generics.GenericAPIView):
    """Get availability calendar for hotel"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, hotel_id):
        try:
            hotel = Hotel.objects.get(id=hotel_id, is_active=True)
            
            # Return 30-day availability calendar
            from datetime import datetime, timedelta
            start_date = datetime.now().date()
            calendar_data = []
            
            for i in range(30):
                date = start_date + timedelta(days=i)
                # In real implementation, check actual availability
                calendar_data.append({
                    'date': date.isoformat(),
                    'available_rooms': 10,  # Mock data
                    'min_price': 150.00,
                    'is_available': True
                })
            
            return Response({
                'hotel_id': str(hotel.id),
                'calendar': calendar_data
            })
            
        except Hotel.DoesNotExist:
            return Response({'error': 'Hotel not found'}, status=status.HTTP_404_NOT_FOUND)


class HotelPricingAPIView(generics.GenericAPIView):
    """Get hotel pricing information"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, hotel_id):
        try:
            hotel = Hotel.objects.get(id=hotel_id, is_active=True)
            
            # Get room types with pricing from actual rooms
            room_types_with_pricing = []
            room_types = RoomType.objects.filter(rooms__hotel=hotel).distinct()
            
            for room_type in room_types:
                # Get rooms of this type for this hotel
                rooms_of_type = Room.objects.filter(
                    hotel=hotel, 
                    room_type=room_type, 
                    is_active=True
                )
                
                if rooms_of_type.exists():
                    # Get average base price for this room type
                    avg_price = rooms_of_type.aggregate(
                        avg_price=Avg('base_price')
                    )['avg_price'] or Decimal('0.00')
                    
                    room_types_with_pricing.append({
                        'room_type_id': str(room_type.id),
                        'name': room_type.name,
                        'base_price': float(avg_price),
                        'weekend_price': float(avg_price * Decimal('1.2')),  # 20% markup
                        'holiday_price': float(avg_price * Decimal('1.5')),  # 50% markup
                        'max_capacity': room_type.max_capacity,
                        'bed_type': room_type.bed_type,
                    })
            
            return Response({
                'hotel_id': str(hotel.id),
                'pricing': room_types_with_pricing,
                'currency': 'USD',
                'taxes_included': False
            })
            
        except Hotel.DoesNotExist:
            return Response({'error': 'Hotel not found'}, status=status.HTTP_404_NOT_FOUND)


class RoomAvailabilityAPIView(generics.GenericAPIView):
    """Check specific room availability"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, hotel_id, room_id):
        try:
            room = Room.objects.get(
                id=room_id,
                hotel_id=hotel_id,
                hotel__is_active=True
            )
            
            check_in = request.query_params.get('checkin')
            check_out = request.query_params.get('checkout')
            
            if not check_in or not check_out:
                return Response(
                    {'error': 'checkin and checkout dates are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if room is available
            is_available = RoomAvailabilityService.is_room_available(
                room=room,
                check_in_date=check_in,
                check_out_date=check_out
            )
            
            return Response({
                'room_id': str(room.id),
                'hotel_id': str(room.hotel.id),
                'check_in': check_in,
                'check_out': check_out,
                'is_available': is_available,
                'room_details': RoomSerializer(room).data
            })
            
        except Room.DoesNotExist:
            return Response({'error': 'Room not found'}, status=status.HTTP_404_NOT_FOUND)


class HotelAmenitiesAPIView(generics.GenericAPIView):
    """Get hotel amenities and room features"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, hotel_id):
        try:
            hotel = get_object_or_404(Hotel, id=hotel_id, is_active=True)
            
            # Get all extras grouped by category
            extras_by_category = {}
            for extra in hotel.extras.filter(is_active=True):
                category = extra.get_category_display()
                if category not in extras_by_category:
                    extras_by_category[category] = []
                
                extras_by_category[category].append({
                    'id': str(extra.id),
                    'name': extra.name,
                    'description': extra.description,
                    'price': extra.price,
                    'pricing_type': extra.get_pricing_type_display(),
                    'max_quantity': extra.max_quantity
                })
            
            # Get room type amenities
            room_amenities = set()
            for room_type in RoomType.objects.filter(rooms__hotel=hotel).distinct():
                room_amenities.update(room_type.amenities_list)
            
            return Response({
                'hotel': {
                    'id': str(hotel.id),
                    'name': hotel.name
                },
                'room_amenities': list(room_amenities),
                'hotel_services': extras_by_category
            })
            
        except Exception as e:
            return Response(
                {'error': f'Failed to get hotel amenities: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )


class HotelServicesAPIView(generics.GenericAPIView):
    """Get hotel services"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, hotel_id):
        try:
            hotel = Hotel.objects.get(id=hotel_id, is_active=True)
            extras = hotel.extras.filter(is_active=True)
            
            return Response({
                'hotel_id': str(hotel.id),
                'services': ExtraSerializer(extras, many=True).data
            })
            
        except Hotel.DoesNotExist:
            return Response({'error': 'Hotel not found'}, status=status.HTTP_404_NOT_FOUND)


class HotelExtrasAPIView(HotelServicesAPIView):
    """Get hotel extras (alias for services)"""
    pass


class HotelDiningAPIView(generics.GenericAPIView):
    """Get hotel dining options"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, hotel_id):
        try:
            hotel = Hotel.objects.get(id=hotel_id, is_active=True)
            
            # Mock dining data - in real implementation, you'd have a Restaurant model
            dining_options = [
                {
                    'id': 1,
                    'name': 'Main Restaurant',
                    'cuisine_type': 'International',
                    'opening_hours': '06:00 - 22:00',
                    'description': 'Fine dining with international cuisine',
                    'dress_code': 'Smart casual'
                },
                {
                    'id': 2,
                    'name': 'Pool Bar',
                    'cuisine_type': 'Bar & Grill',
                    'opening_hours': '10:00 - 18:00',
                    'description': 'Casual dining by the pool',
                    'dress_code': 'Casual'
                }
            ]
            
            return Response({
                'hotel_id': str(hotel.id),
                'dining_options': dining_options
            })
            
        except Hotel.DoesNotExist:
            return Response({'error': 'Hotel not found'}, status=status.HTTP_404_NOT_FOUND)


class HotelLocationAPIView(generics.GenericAPIView):
    """Get hotel location information"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, hotel_id):
        try:
            hotel = Hotel.objects.get(id=hotel_id, is_active=True)
            
            return Response({
                'hotel_id': str(hotel.id),
                'location': {
                    'address': hotel.full_address,
                    'city': hotel.city,
                    'state': hotel.state,
                    'country': hotel.country,
                    'postal_code': hotel.postal_code,
                    'coordinates': {
                        'latitude': 25.7617,  # Mock coordinates for Miami
                        'longitude': -80.1918
                    }
                },
                'transportation': {
                    'airport_distance': '15 km',
                    'downtown_distance': '5 km',
                    'public_transport': 'Metro station 200m away'
                }
            })
            
        except Hotel.DoesNotExist:
            return Response({'error': 'Hotel not found'}, status=status.HTTP_404_NOT_FOUND)


class HotelDirectionsAPIView(generics.GenericAPIView):
    """Get directions to hotel"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, hotel_id):
        try:
            hotel = Hotel.objects.get(id=hotel_id, is_active=True)
            
            return Response({
                'hotel_id': str(hotel.id),
                'directions': {
                    'from_airport': 'Take highway I-95 south for 15 minutes',
                    'from_downtown': 'Take metro line to Ocean Drive station',
                    'parking': 'Valet parking available ($25/night)',
                    'public_transport': 'Metro, bus lines 120, 150'
                },
                'map_url': f'https://maps.google.com/search/{hotel.full_address}'
            })
            
        except Hotel.DoesNotExist:
            return Response({'error': 'Hotel not found'}, status=status.HTTP_404_NOT_FOUND)


class NearbyAttractionsAPIView(generics.GenericAPIView):
    """Get nearby attractions"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, hotel_id):
        try:
            hotel = Hotel.objects.get(id=hotel_id, is_active=True)
            
            # Mock attractions data
            attractions = [
                {
                    'name': 'South Beach',
                    'distance': '0.5 km',
                    'category': 'Beach',
                    'description': 'Famous white sand beach'
                },
                {
                    'name': 'Art Deco District',
                    'distance': '1.2 km',
                    'category': 'Historic',
                    'description': 'Historic art deco architecture'
                },
                {
                    'name': 'Bayside Marketplace',
                    'distance': '3.5 km',
                    'category': 'Shopping',
                    'description': 'Waterfront shopping and dining'
                }
            ]
            
            return Response({
                'hotel_id': str(hotel.id),
                'attractions': attractions
            })
            
        except Hotel.DoesNotExist:
            return Response({'error': 'Hotel not found'}, status=status.HTTP_404_NOT_FOUND)


class SearchHotelsByLocationAPIView(generics.ListAPIView):
    """Search hotels by location"""
    serializer_class = HotelSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        queryset = Hotel.objects.filter(is_active=True)
        
        # Location-based filtering
        city = self.request.query_params.get('city', None)
        state = self.request.query_params.get('state', None)
        country = self.request.query_params.get('country', None)
        
        if city:
            queryset = queryset.filter(city__icontains=city)
        if state:
            queryset = queryset.filter(state__icontains=state)
        if country:
            queryset = queryset.filter(country__icontains=country)
            
        return queryset
    
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return Response({
            'count': len(response.data),
            'results': response.data
        })


class SearchRoomAvailabilityAPIView(generics.GenericAPIView):
    """Search room availability"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        try:
            # Get search parameters
            check_in = request.query_params.get('check_in')
            check_out = request.query_params.get('check_out')
            guests = int(request.query_params.get('guests', 1))
            
            if not check_in or not check_out:
                return Response({
                    'error': 'check_in and check_out dates are required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Find available rooms
            available_rooms = Room.objects.filter(
                is_active=True,
                maintenance_status='operational',
                room_type__max_capacity__gte=guests
            ).select_related('room_type', 'hotel')
            
            # Serialize room data
            room_data = []
            for room in available_rooms:
                room_data.append({
                    'id': str(room.id),
                    'hotel': {
                        'id': str(room.hotel.id),
                        'name': room.hotel.name,
                        'star_rating': room.hotel.star_rating
                    },
                    'room_type': room.room_type.name,
                    'room_number': room.room_number,
                    'max_capacity': room.room_type.max_capacity,
                    'base_price': str(room.room_type.base_price),
                    'bed_type': room.room_type.bed_type,
                    'size_sqft': room.room_type.size_sqft
                })
            
            return Response({
                'search_params': {
                    'check_in': check_in,
                    'check_out': check_out,
                    'guests': guests
                },
                'count': len(room_data),
                'results': room_data
            })
            
        except ValueError:
            return Response({
                'error': 'Invalid guests parameter'
            }, status=status.HTTP_400_BAD_REQUEST)


class HotelFeaturesAPIView(generics.GenericAPIView):
    """Get hotel features and amenities"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, hotel_id):
        try:
            hotel = Hotel.objects.get(id=hotel_id, is_active=True)
            
            features = {
                'basic_amenities': [
                    'Free Wi-Fi',
                    'Air Conditioning',
                    'Parking',
                    '24/7 Front Desk',
                    'Room Service'
                ],
                'facilities': [
                    'Swimming Pool',
                    'Fitness Center',
                    'Spa',
                    'Restaurant',
                    'Business Center'
                ],
                'services': [
                    'Concierge',
                    'Laundry Service',
                    'Airport Shuttle',
                    'Valet Parking',
                    'Pet Friendly'
                ]
            }
            
            return Response({
                'hotel_id': str(hotel.id),
                'features': features
            })
            
        except Hotel.DoesNotExist:
            return Response({'error': 'Hotel not found'}, status=status.HTTP_404_NOT_FOUND)


class HotelPhotosAPIView(generics.GenericAPIView):
    """Get hotel photos"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, hotel_id):
        try:
            hotel = Hotel.objects.get(id=hotel_id, is_active=True)
            
            # Mock photo data
            photos = [
                {
                    'id': 1,
                    'url': f'/media/hotels/{hotel.id}/exterior.jpg',
                    'caption': 'Hotel Exterior',
                    'category': 'exterior'
                },
                {
                    'id': 2,
                    'url': f'/media/hotels/{hotel.id}/lobby.jpg',
                    'caption': 'Elegant Lobby',
                    'category': 'interior'
                },
                {
                    'id': 3,
                    'url': f'/media/hotels/{hotel.id}/pool.jpg',
                    'caption': 'Swimming Pool',
                    'category': 'amenities'
                }
            ]
            
            return Response({
                'hotel_id': str(hotel.id),
                'photos': photos
            })
            
        except Hotel.DoesNotExist:
            return Response({'error': 'Hotel not found'}, status=status.HTTP_404_NOT_FOUND)


class SeasonalPricingAPIView(generics.GenericAPIView):
    """Get seasonal pricing information"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, hotel_id):
        try:
            hotel = Hotel.objects.get(id=hotel_id, is_active=True)
            
            # Mock seasonal pricing data
            seasonal_rates = [
                {
                    'season': 'High Season',
                    'start_date': '2024-12-15',
                    'end_date': '2024-04-15',
                    'multiplier': 1.5,
                    'description': 'Peak tourist season'
                },
                {
                    'season': 'Regular Season',
                    'start_date': '2024-04-16',
                    'end_date': '2024-11-30',
                    'multiplier': 1.0,
                    'description': 'Standard rates'
                },
                {
                    'season': 'Low Season',
                    'start_date': '2024-12-01',
                    'end_date': '2024-12-14',
                    'multiplier': 0.8,
                    'description': 'Off-peak rates'
                }
            ]
            
            return Response({
                'hotel_id': str(hotel.id),
                'seasonal_pricing': seasonal_rates
            })
            
        except Hotel.DoesNotExist:
            return Response({'error': 'Hotel not found'}, status=status.HTTP_404_NOT_FOUND)


class RoomPhotosAPIView(generics.GenericAPIView):
    """Get room photos"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, hotel_id, room_id):
        try:
            room = Room.objects.get(
                id=room_id, 
                hotel_id=hotel_id, 
                is_active=True
            ).select_related('room_type', 'hotel')
            
            # Mock room photo data
            photos = [
                {
                    'id': 1,
                    'url': f'/media/rooms/{room.id}/bedroom.jpg',
                    'caption': f'{room.room_type.name} - Bedroom',
                    'category': 'bedroom'
                },
                {
                    'id': 2,
                    'url': f'/media/rooms/{room.id}/bathroom.jpg',
                    'caption': f'{room.room_type.name} - Bathroom',
                    'category': 'bathroom'
                },
                {
                    'id': 3,
                    'url': f'/media/rooms/{room.id}/view.jpg',
                    'caption': f'{room.room_type.name} - View',
                    'category': 'view'
                }
            ]
            
            return Response({
                'room_id': str(room.id),
                'room_type': room.room_type.name,
                'photos': photos
            })
            
        except Room.DoesNotExist:
            return Response({'error': 'Room not found'}, status=status.HTTP_404_NOT_FOUND)


class RoomAmenitiesAPIView(generics.GenericAPIView):
    """Get room amenities"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, hotel_id, room_id):
        try:
            room = Room.objects.get(
                id=room_id, 
                hotel_id=hotel_id, 
                is_active=True
            ).select_related('room_type')
            
            return Response({
                'room_id': str(room.id),
                'room_type': room.room_type.name,
                'amenities': room.room_type.amenities or []
            })
            
        except Room.DoesNotExist:
            return Response({'error': 'Room not found'}, status=status.HTTP_404_NOT_FOUND)


# Management views (require staff permissions)
class ManageRoomMaintenanceAPIView(generics.GenericAPIView):
    """Manage room maintenance status"""
    permission_classes = [permissions.IsAuthenticated]
    
    def patch(self, request, hotel_id, room_id):
        if not request.user.is_staff:
            return Response({
                'error': 'Staff access required'
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            room = Room.objects.get(id=room_id, hotel_id=hotel_id)
            
            new_status = request.data.get('maintenance_status')
            if new_status not in ['operational', 'maintenance', 'out_of_order']:
                return Response({
                    'error': 'Invalid maintenance status'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            room.maintenance_status = new_status
            room.save()
            
            return Response({
                'room_id': str(room.id),
                'maintenance_status': room.maintenance_status,
                'updated_at': room.updated_at
            })
            
        except Room.DoesNotExist:
            return Response({'error': 'Room not found'}, status=status.HTTP_404_NOT_FOUND)


class ManageRoomTypesAPIView(generics.ListCreateAPIView):
    """Manage room types"""
    serializer_class = RoomTypeSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if not self.request.user.is_staff:
            return RoomType.objects.none()
        return RoomType.objects.filter(is_active=True)


class ManageExtrasAPIView(generics.ListCreateAPIView):
    """Manage hotel extras"""
    serializer_class = ExtraSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if not self.request.user.is_staff:
            return Extra.objects.none()
        hotel_id = self.kwargs.get('hotel_id')
        return Extra.objects.filter(hotel_id=hotel_id, is_active=True)


class SearchHotelsByAmenitiesAPIView(generics.ListAPIView):
    """Search hotels by amenities"""
    serializer_class = HotelSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        queryset = Hotel.objects.filter(is_active=True)
        
        # Amenity-based filtering
        amenities = self.request.query_params.getlist('amenities')
        if amenities:
            # Filter hotels that have rooms with specified amenities
            for amenity in amenities:
                queryset = queryset.filter(
                    room_types__amenities__icontains=amenity
                ).distinct()
                
        return queryset
    
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return Response({
            'count': len(response.data),
            'results': response.data
        })


class HotelsByPriceRangeAPIView(generics.ListAPIView):
    """Search hotels by price range"""
    serializer_class = HotelSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        queryset = Hotel.objects.filter(is_active=True)
        
        # Price range filtering
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        
        if min_price:
            queryset = queryset.filter(room_types__base_price__gte=min_price).distinct()
        if max_price:
            queryset = queryset.filter(room_types__base_price__lte=max_price).distinct()
                
        return queryset
    
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return Response({
            'count': len(response.data),
            'results': response.data
        })


class SearchHotelsByPriceAPIView(HotelsByPriceRangeAPIView):
    """Alias for HotelsByPriceRangeAPIView for URL compatibility"""
    pass


class SearchHotelsByRatingAPIView(generics.ListAPIView):
    """Search hotels by star rating"""
    serializer_class = HotelSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        queryset = Hotel.objects.filter(is_active=True)
        
        # Rating filtering
        min_rating = self.request.query_params.get('min_rating')
        max_rating = self.request.query_params.get('max_rating')
        
        if min_rating:
            queryset = queryset.filter(star_rating__gte=min_rating)
        if max_rating:
            queryset = queryset.filter(star_rating__lte=max_rating)
                
        return queryset
    
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return Response({
            'count': len(response.data),
            'results': response.data
        })


class HotelRecommendationsAPIView(generics.GenericAPIView):
    """Get hotel recommendations"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        # Mock recommendation algorithm
        hotels = Hotel.objects.filter(is_active=True)[:6]
        
        recommended_hotels = []
        for hotel in hotels:
            recommended_hotels.append({
                'id': str(hotel.id),
                'name': hotel.name,
                'star_rating': hotel.star_rating,
                'city': hotel.city,
                'state': hotel.state,
                'recommendation_score': 85 + (hotel.star_rating * 3),
                'recommendation_reason': f'Popular {hotel.star_rating}-star hotel in {hotel.city}'
            })
        
        return Response({
            'count': len(recommended_hotels),
            'recommendations': recommended_hotels
        })


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def hotel_search(request):
    """
    Search hotels with availability filtering by dates and capacity
    
    Query Parameters:
    - check_in: Check-in date (YYYY-MM-DD)
    - check_out: Check-out date (YYYY-MM-DD) 
    - capacity: Number of guests (optional)
    - hotel_id: Specific hotel ID (optional)
    """
    from datetime import datetime
    from django.db.models import Count, Q, Exists, OuterRef
    from bookings.models import Booking
    
    try:
        # Get query parameters
        check_in = request.GET.get('check_in')
        check_out = request.GET.get('check_out')
        capacity = request.GET.get('capacity')
        hotel_id = request.GET.get('hotel_id')
        
        # Validate required parameters
        if not check_in or not check_out:
            return Response({
                'error': 'Both check_in and check_out dates are required',
                'format': 'YYYY-MM-DD'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Parse dates
        try:
            check_in_date = datetime.strptime(check_in, '%Y-%m-%d').date()
            check_out_date = datetime.strptime(check_out, '%Y-%m-%d').date()
        except ValueError:
            return Response({
                'error': 'Invalid date format. Use YYYY-MM-DD'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate dates
        if check_out_date <= check_in_date:
            return Response({
                'error': 'Check-out date must be after check-in date'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Parse capacity
        if capacity:
            try:
                capacity = int(capacity)
                if capacity < 1 or capacity > 10:
                    return Response({
                        'error': 'Capacity must be between 1 and 10'
                    }, status=status.HTTP_400_BAD_REQUEST)
            except ValueError:
                return Response({
                    'error': 'Capacity must be a valid number'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Start with active hotels
        hotels_query = Hotel.objects.filter(is_active=True)
        
        # Filter by specific hotel if provided
        if hotel_id:
            hotels_query = hotels_query.filter(id=hotel_id)
        
        # Get available hotels
        available_hotels = []
        
        for hotel in hotels_query:
            # Find room types that match capacity requirements
            room_types_query = RoomType.objects.filter(
                rooms__hotel=hotel
            ).distinct()
            
            # Filter by capacity if specified
            if capacity:
                room_types_query = room_types_query.filter(
                    max_capacity__gte=capacity
                )
            
            # Check availability for each room type
            available_room_types = []
            
            for room_type in room_types_query:
                # Get rooms of this type in this hotel
                hotel_rooms = Room.objects.filter(
                    hotel=hotel,
                    room_type=room_type,
                    is_active=True,
                    is_maintenance=False
                )
                
                # Check for conflicting bookings
                conflicting_bookings = Booking.objects.filter(
                    room__in=hotel_rooms,
                    status__in=['confirmed', 'checked_in'],
                    check_in__lt=check_out_date,
                    check_out__gt=check_in_date
                )
                
                # Get booked room IDs
                booked_room_ids = conflicting_bookings.values_list('room_id', flat=True)
                
                # Get available rooms
                available_rooms = hotel_rooms.exclude(id__in=booked_room_ids)
                available_count = available_rooms.count()
                
                if available_count > 0:
                    # Calculate pricing
                    base_price = available_rooms.first().base_price
                    
                    # Get detailed room information
                    room_details = []
                    for room in available_rooms:
                        room_details.append({
                            'room_id': str(room.id),
                            'room_number': room.room_number,
                            'floor': room.floor,
                            'capacity': room.capacity,
                            'base_price': str(room.base_price),
                            'view_type': room.view_type
                        })
                    
                    available_room_types.append({
                        'id': str(room_type.id),
                        'name': room_type.name,
                        'description': room_type.description,
                        'max_capacity': room_type.max_capacity,
                        'bed_type': room_type.bed_type,
                        'bed_count': room_type.bed_count,
                        'bathroom_count': room_type.bathroom_count,
                        'room_size_sqm': room_type.room_size_sqm,
                        'amenities': room_type.amenities_list,
                        'is_accessible': room_type.is_accessible,
                        'available_rooms': available_count,
                        'available_room_details': room_details,
                        'price_per_night': str(base_price),
                        'total_rooms': hotel_rooms.count()
                    })
            
            # If hotel has available room types, include it
            if available_room_types:
                # Calculate total nights
                nights = (check_out_date - check_in_date).days
                
                # Get min and max prices
                prices = [float(rt['price_per_night']) for rt in available_room_types]
                min_price = min(prices) if prices else 0
                max_price = max(prices) if prices else 0
                
                available_hotels.append({
                    'id': str(hotel.id),
                    'name': hotel.name,
                    'description': hotel.description,
                    'full_address': hotel.full_address,
                    'phone_number': hotel.phone_number,
                    'email': hotel.email,
                    'website': hotel.website,
                    'star_rating': hotel.star_rating,
                    'check_in_time': hotel.check_in_time.strftime('%H:%M'),
                    'check_out_time': hotel.check_out_time.strftime('%H:%M'),
                    'available_room_types': available_room_types,
                    'room_types_count': len(available_room_types),
                    'total_available_rooms': sum(rt['available_rooms'] for rt in available_room_types),
                    'price_range': {
                        'min_per_night': min_price,
                        'max_per_night': max_price,
                        'min_total': min_price * nights,
                        'max_total': max_price * nights,
                        'nights': nights
                    },
                    'search_params': {
                        'check_in': check_in,
                        'check_out': check_out,
                        'capacity': capacity,
                        'nights': nights
                    }
                })
        
        return Response({
            'count': len(available_hotels),
            'search_criteria': {
                'check_in': check_in,
                'check_out': check_out,
                'capacity': capacity,
                'hotel_id': hotel_id,
                'nights': (check_out_date - check_in_date).days
            },
            'hotels': available_hotels,
            'message': f'Found {len(available_hotels)} hotel(s) with availability' if available_hotels 
                      else 'No hotels available for the selected dates and criteria'
        })
        
    except Exception as e:
        return Response({
            'error': 'Internal server error',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Contact Form API Views
class ContactMessageView(generics.CreateAPIView):
    """API view to handle contact form submissions"""
    queryset = ContactMessage.objects.all()
    serializer_class = ContactMessageSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        contact_message = serializer.save()
        # Send email notification asynchronously or synchronously
        ContactEmailService.send_contact_email(contact_message)


@api_view(['GET'])
@permission_classes([AllowAny])
def hotel_search_by_capacity(request):
    """
    Search hotels by capacity only (without date requirements)
    
    Query Parameters:
    - capacity (required): Number of guests
    - hotel_id (optional): Specific hotel ID
    """
    try:
        # Get query parameters
        capacity = request.GET.get('capacity')
        hotel_id = request.GET.get('hotel_id')
        
        # Validate required parameters
        if not capacity:
            return Response({
                'error': 'Missing required parameter: capacity'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            capacity = int(capacity)
            if capacity <= 0:
                return Response({
                    'error': 'Capacity must be a positive integer'
                }, status=status.HTTP_400_BAD_REQUEST)
        except ValueError:
            return Response({
                'error': 'Capacity must be a valid integer'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Start with all hotels query
        hotels_query = Hotel.objects.all()
        
        # Filter by specific hotel if provided
        if hotel_id:
            try:
                hotel_id = int(hotel_id)
                hotels_query = hotels_query.filter(id=hotel_id)
            except ValueError:
                return Response({
                    'error': 'Hotel ID must be a valid integer'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get hotels that have room types with adequate capacity
        hotels_with_capacity = []
        for hotel in hotels_query:
            # Find room types that can accommodate the requested capacity
            # Get unique room types from hotel's rooms that have adequate capacity
            suitable_rooms = hotel.rooms.filter(
                capacity__gte=capacity,
                is_active=True
            ).select_related('room_type')
            
            # Get unique room types from these rooms
            room_type_ids = suitable_rooms.values_list('room_type_id', flat=True).distinct()
            suitable_room_types = RoomType.objects.filter(id__in=room_type_ids).order_by('max_capacity', 'name')
            
            if suitable_room_types.exists():
                # Serialize the hotel data
                hotel_data = HotelSerializer(hotel).data
                
                # Add room type information
                room_types_data = []
                for room_type in suitable_room_types:
                    room_type_data = RoomTypeSerializer(room_type).data
                    # Add total available rooms count for this room type at this hotel
                    rooms_of_type = suitable_rooms.filter(room_type=room_type)
                    room_type_data['available_rooms'] = rooms_of_type.count()
                    room_type_data['room_details'] = []
                    
                    # Add individual room details
                    for room in rooms_of_type:
                        room_type_data['room_details'].append({
                            'room_id': str(room.id),
                            'room_number': room.room_number,
                            'floor': room.floor,
                            'capacity': room.capacity,
                            'base_price': str(room.base_price),
                            'view_type': room.view_type
                        })
                    
                    room_types_data.append(room_type_data)
                
                hotel_data['suitable_room_types'] = room_types_data
                hotels_with_capacity.append(hotel_data)
        
        return Response({
            'count': len(hotels_with_capacity),
            'search_criteria': {
                'capacity': capacity,
                'hotel_id': hotel_id
            },
            'hotels': hotels_with_capacity,
            'message': f'Found {len(hotels_with_capacity)} hotel(s) with room types for {capacity} guests' if hotels_with_capacity 
                      else f'No hotels found with room types that can accommodate {capacity} guests'
        })
        
    except Exception as e:
        return Response({
            'error': 'Internal server error',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def hotel_search_flexible(request):
    """
    Flexible hotel search with adults and children support
    
    Query Parameters:
    - check_in: Check-in date (YYYY-MM-DD) - optional
    - check_out: Check-out date (YYYY-MM-DD) - optional  
    - adults: Number of adults (optional, default: 1)
    - children: Number of children (optional, default: 0)
    - capacity: Total number of guests (optional, alternative to adults/children)
    - hotel_id: Specific hotel ID (optional)
    """
    from datetime import datetime
    from django.db.models import Count, Q, Exists, OuterRef
    from bookings.models import Booking
    
    try:
        # Get query parameters
        check_in = request.GET.get('check_in')
        check_out = request.GET.get('check_out')
        adults = request.GET.get('adults')
        children = request.GET.get('children')
        capacity = request.GET.get('capacity')
        hotel_id = request.GET.get('hotel_id')
        
        # Parse adults and children
        adults_count = 1  # Default to 1 adult
        children_count = 0  # Default to 0 children
        
        if adults:
            try:
                adults_count = int(adults)
                if adults_count < 0 or adults_count > 10:
                    return Response({
                        'error': 'Adults must be between 0 and 10'
                    }, status=status.HTTP_400_BAD_REQUEST)
            except ValueError:
                return Response({
                    'error': 'Adults must be a valid number'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        if children:
            try:
                children_count = int(children)
                if children_count < 0 or children_count > 10:
                    return Response({
                        'error': 'Children must be between 0 and 10'
                    }, status=status.HTTP_400_BAD_REQUEST)
            except ValueError:
                return Response({
                    'error': 'Children must be a valid number'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Calculate total guests (adults + children, with capacity override)
        if capacity:
            try:
                total_guests = int(capacity)
                if total_guests < 1 or total_guests > 10:
                    return Response({
                        'error': 'Capacity must be between 1 and 10'
                    }, status=status.HTTP_400_BAD_REQUEST)
            except ValueError:
                return Response({
                    'error': 'Capacity must be a valid number'
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            total_guests = adults_count + children_count
            if total_guests < 1:
                return Response({
                    'error': 'Total guests (adults + children) must be at least 1'
                }, status=status.HTTP_400_BAD_REQUEST)
            if total_guests > 10:
                return Response({
                    'error': 'Total guests (adults + children) cannot exceed 10'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Parse and validate dates if provided
        check_in_date = None
        check_out_date = None
        dates_provided = bool(check_in and check_out)
        
        if check_in and check_out:
            try:
                check_in_date = datetime.strptime(check_in, '%Y-%m-%d').date()
                check_out_date = datetime.strptime(check_out, '%Y-%m-%d').date()
            except ValueError:
                return Response({
                    'error': 'Invalid date format. Use YYYY-MM-DD'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate dates
            if check_out_date <= check_in_date:
                return Response({
                    'error': 'Check-out date must be after check-in date'
                }, status=status.HTTP_400_BAD_REQUEST)
        elif check_in or check_out:
            return Response({
                'error': 'Both check_in and check_out dates are required when using date filtering'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Start with active hotels
        hotels_query = Hotel.objects.filter(is_active=True)
        
        # Filter by specific hotel if provided
        if hotel_id:
            hotels_query = hotels_query.filter(id=hotel_id)
        
        # Get available hotels
        available_hotels = []
        
        for hotel in hotels_query:
            # Find room types that match capacity requirements
            room_types_query = RoomType.objects.filter(
                rooms__hotel=hotel
            ).distinct()
            
            # Filter by total guest capacity
            room_types_query = room_types_query.filter(
                max_capacity__gte=total_guests
            )
            
            # Check availability for each room type
            available_room_types = []
            
            for room_type in room_types_query:
                # Get rooms of this type in this hotel
                hotel_rooms = Room.objects.filter(
                    hotel=hotel,
                    room_type=room_type,
                    is_active=True,
                    is_maintenance=False,
                    capacity__gte=total_guests
                )
                
                # If dates are provided, check for availability
                if dates_provided:
                    # Check for conflicting bookings
                    conflicting_bookings = Booking.objects.filter(
                        room__in=hotel_rooms,
                        status__in=['confirmed', 'checked_in'],
                        check_in__lt=check_out_date,
                        check_out__gt=check_in_date
                    ).values_list('room_id', flat=True)
                    
                    # Get available rooms (exclude conflicted ones)
                    available_rooms = hotel_rooms.exclude(id__in=conflicting_bookings)
                else:
                    # If no dates provided, all active rooms are considered available
                    available_rooms = hotel_rooms
                
                available_count = available_rooms.count()
                
                if available_count > 0:
                    # Get room details
                    room_details = []
                    for room in available_rooms[:5]:  # Limit to first 5 rooms for response size
                        base_price = room.base_price
                        room_details.append({
                            'room_id': str(room.id),
                            'room_number': room.room_number,
                            'floor': room.floor,
                            'capacity': room.capacity,
                            'base_price': str(base_price),
                            'view_type': room.view_type
                        })
                    
                    available_room_types.append({
                        'id': str(room_type.id),
                        'name': room_type.name,
                        'description': room_type.description,
                        'max_capacity': room_type.max_capacity,
                        'bed_type': room_type.bed_type,
                        'bed_count': room_type.bed_count,
                        'bathroom_count': room_type.bathroom_count,
                        'room_size_sqm': room_type.room_size_sqm,
                        'amenities': room_type.amenities_list,
                        'is_accessible': room_type.is_accessible,
                        'available_rooms': available_count,
                        'available_room_details': room_details,
                        'price_per_night': str(available_rooms.first().base_price) if available_rooms.exists() else '0.00',
                        'total_rooms': hotel_rooms.count()
                    })
            
            # If hotel has available room types, include it
            if available_room_types:
                # Calculate pricing if dates are provided
                nights = 0
                if dates_provided:
                    nights = (check_out_date - check_in_date).days
                
                # Get min and max prices
                prices = [float(rt['price_per_night']) for rt in available_room_types]
                min_price = min(prices) if prices else 0
                max_price = max(prices) if prices else 0
                
                # Calculate total price range if dates provided
                total_min_price = min_price * nights if dates_provided else min_price
                total_max_price = max_price * nights if dates_provided else max_price
                
                hotel_data = HotelSerializer(hotel).data
                hotel_data.update({
                    'available_room_types': available_room_types,
                    'total_available_rooms': sum(rt['available_rooms'] for rt in available_room_types),
                    'price_range': {
                        'min_price_per_night': min_price,
                        'max_price_per_night': max_price,
                        'total_min_price': total_min_price,
                        'total_max_price': total_max_price,
                        'currency': 'USD'
                    }
                })
                
                available_hotels.append(hotel_data)
        
        # Prepare response
        search_criteria = {
            'adults': adults_count,
            'children': children_count,
            'total_guests': total_guests,
            'dates_provided': dates_provided
        }
        
        if dates_provided:
            search_criteria.update({
                'check_in': check_in,
                'check_out': check_out,
                'nights': nights
            })
        
        if hotel_id:
            search_criteria['hotel_id'] = hotel_id
        
        return Response({
            'count': len(available_hotels),
            'search_criteria': search_criteria,
            'hotels': available_hotels,
            'message': f'Found {len(available_hotels)} hotel(s) for {adults_count} adult(s) and {children_count} child(ren)' if available_hotels 
                      else f'No hotels found for {adults_count} adult(s) and {children_count} child(ren)'
        })
        
    except Exception as e:
        return Response({
            'error': 'Internal server error',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
