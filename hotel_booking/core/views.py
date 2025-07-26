# Django imports
from django.shortcuts import get_object_or_404
from django.db.models import Q, Prefetch

# Django REST Framework imports
from rest_framework import generics, status, permissions, serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

# Local imports
from .models import Hotel, Room, RoomType, Extra
from .services import HotelSearchService, RoomAvailabilityService
from bookings.serializers import (
    RoomSerializer, ExtraSerializer, RoomAvailabilitySerializer
)


class HotelSerializer(serializers.ModelSerializer):
    """Serializer for hotel information"""
    room_types = serializers.SerializerMethodField()
    amenities_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Hotel
        fields = [
            'id', 'name', 'description', 'full_address', 'phone_number',
            'email', 'website', 'star_rating', 'check_in_time', 'check_out_time',
            'room_types', 'amenities_count'
        ]
    
    def get_room_types(self, obj):
        """Get available room types for this hotel"""
        room_types = RoomType.objects.filter(
            rooms__hotel=obj
        ).distinct()
        return RoomTypeSerializer(room_types, many=True).data
    
    def get_amenities_count(self, obj):
        """Get count of available amenities/extras"""
        return obj.extras.filter(is_active=True).count()


class RoomTypeSerializer(serializers.ModelSerializer):
    """Serializer for room type information"""
    amenities = serializers.SerializerMethodField()
    
    class Meta:
        model = RoomType
        fields = [
            'id', 'name', 'description', 'max_capacity', 'bed_type', 'bed_count',
            'bathroom_count', 'room_size_sqm', 'amenities', 'is_accessible'
        ]
    
    def get_amenities(self, obj):
        return obj.amenities_list


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
