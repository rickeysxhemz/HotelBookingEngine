# Django imports
from django.shortcuts import get_object_or_404
from django.db.models import Q, Prefetch
from django.utils import timezone
from django.core.exceptions import ValidationError as DjangoValidationError

# Django REST Framework imports
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination

# Third-party imports
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from decimal import Decimal

# Local imports
from .models import Offer, OfferCategory, OfferHighlight, OfferImage
from .serializers import (
    OfferCategorySerializer, OfferCategoryListSerializer,
    OfferListSerializer, OfferDetailSerializer, OfferCreateUpdateSerializer,
    OfferSearchSerializer, OfferCalculationSerializer, OfferCalculationResponseSerializer,
    OfferHighlightSerializer, OfferImageSerializer
)
from .permissions import IsAdminOrManagerOrReadOnly, IsAdminOrManagerPermission
from core.models import Hotel, RoomType


class OfferPagination(PageNumberPagination):
    """Custom pagination for offers"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class OfferListCreateView(generics.ListCreateAPIView):
    """
    List all offers or create a new offer
    
    GET: Returns a paginated list of offers with optional filtering
    POST: Creates a new offer (requires admin or manager permissions)
    """
    
    serializer_class = OfferListSerializer
    pagination_class = OfferPagination
    permission_classes = [IsAdminOrManagerOrReadOnly]
    
    def get_queryset(self):
        """Get offers with optional filtering"""
        queryset = Offer.objects.select_related('hotel', 'category').prefetch_related(
            'images', 'highlights'
        )
        
        # Apply filters from query parameters
        hotel_id = self.request.query_params.get('hotel_id')
        if hotel_id:
            queryset = queryset.filter(hotel_id=hotel_id)
        
        # Filter by category
        category_id = self.request.query_params.get('category_id')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        category_slug = self.request.query_params.get('category_slug')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        
        offer_type = self.request.query_params.get('offer_type')
        if offer_type:
            queryset = queryset.filter(offer_type=offer_type)
        
        is_featured = self.request.query_params.get('is_featured')
        if is_featured is not None:
            is_featured_bool = is_featured.lower() in ('true', '1', 'yes')
            queryset = queryset.filter(is_featured=is_featured_bool)
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active', 'true')
        if is_active.lower() in ('true', '1', 'yes'):
            queryset = queryset.filter(is_active=True)
        
        # Filter by validity (current date)
        show_expired = self.request.query_params.get('show_expired', 'false')
        if show_expired.lower() not in ('true', '1', 'yes'):
            today = timezone.now().date()
            queryset = queryset.filter(
                valid_from__lte=today,
                valid_to__gte=today
            )
        
        # Filter by date range if provided
        check_in = self.request.query_params.get('check_in')
        check_out = self.request.query_params.get('check_out')
        if check_in and check_out:
            try:
                check_in_date = timezone.datetime.strptime(check_in, '%Y-%m-%d').date()
                check_out_date = timezone.datetime.strptime(check_out, '%Y-%m-%d').date()
                queryset = queryset.filter(
                    valid_from__lte=check_out_date,
                    valid_to__gte=check_in_date
                )
            except ValueError:
                pass  # Invalid date format, ignore filter
        
        # Removed room type filtering as applicable_room_types field is removed
        # room_type_id = self.request.query_params.get('room_type_id')
        # if room_type_id:
        #     queryset = queryset.filter(
        #         Q(applicable_room_types__isnull=True) |
        #         Q(applicable_room_types__id=room_type_id)
        #     ).distinct()
        
        return queryset.order_by('-is_featured', '-created_at')
    
    def get_serializer_class(self):
        """Use different serializers for list and create"""
        if self.request.method == 'POST':
            return OfferCreateUpdateSerializer
        return OfferListSerializer
    
    @extend_schema(
        summary="List offers",
        description="Get a paginated list of offers with optional filtering",
        parameters=[
            OpenApiParameter(
                name='hotel_id',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.QUERY,
                description='Filter offers by hotel ID'
            ),
            OpenApiParameter(
                name='offer_type',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter by offer type',
                enum=['percentage', 'fixed_amount', 'package', 'seasonal', 'early_bird', 'last_minute', 'loyalty', 'group']
            ),
            OpenApiParameter(
                name='is_featured',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description='Filter featured offers only'
            ),
            OpenApiParameter(
                name='is_active',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description='Filter by active status (default: true)'
            ),
            OpenApiParameter(
                name='show_expired',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description='Include expired offers (default: false)'
            ),
            OpenApiParameter(
                name='check_in',
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description='Check-in date to filter applicable offers (YYYY-MM-DD)'
            ),
            OpenApiParameter(
                name='check_out',
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description='Check-out date to filter applicable offers (YYYY-MM-DD)'
            ),
            OpenApiParameter(
                name='room_type_id',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.QUERY,
                description='Filter offers applicable to specific room type'
            ),
        ],
        responses={200: OfferListSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @extend_schema(
        summary="Create offer",
        description="Create a new offer (requires admin or manager permissions)",
        request=OfferCreateUpdateSerializer,
        responses={201: OfferDetailSerializer}
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
    
    def perform_create(self, serializer):
        """Set additional fields when creating an offer"""
        serializer.save()


class OfferDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete an offer
    
    GET: Returns detailed offer information
    PUT/PATCH: Updates the offer (requires admin or manager permissions)
    DELETE: Deletes the offer (requires admin or manager permissions)
    """
    
    serializer_class = OfferDetailSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]
    lookup_field = 'slug'
    
    def get_queryset(self):
        """Get offers with related data prefetched for performance"""
        return Offer.objects.select_related(
            'hotel', 'category'
        ).prefetch_related(
            'highlights',
            'images'
        )
    
    def get_serializer_class(self):
        """Use different serializers for different actions"""
        if self.request.method in ['PUT', 'PATCH']:
            return OfferCreateUpdateSerializer
        return OfferDetailSerializer
    
    @extend_schema(
        summary="Get offer details",
        description="Get detailed information about a specific offer",
        responses={200: OfferDetailSerializer}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @extend_schema(
        summary="Update offer",
        description="Update an existing offer (requires admin or manager permissions)",
        request=OfferCreateUpdateSerializer,
        responses={200: OfferDetailSerializer}
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)
    
    @extend_schema(
        summary="Partially update offer",
        description="Partially update an existing offer (requires admin or manager permissions)",
        request=OfferCreateUpdateSerializer,
        responses={200: OfferDetailSerializer}
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)
    
    @extend_schema(
        summary="Delete offer",
        description="Delete an offer (requires authentication)",
        responses={204: None}
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)


class FeaturedOffersView(generics.ListAPIView):
    """Get featured offers"""
    
    serializer_class = OfferListSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        """Get featured offers that are currently valid with optimized query"""
        return Offer.objects.featured_offers().select_related(
            'hotel', 'category'
        ).prefetch_related(
            'images', 'highlights'
        )[:10]  # Limit to 10 featured offers
    
    @extend_schema(
        summary="Get featured offers",
        description="Get a list of featured offers that are currently valid",
        responses={200: OfferListSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class OfferSearchView(APIView):
    """Advanced offer search with multiple criteria"""
    
    permission_classes = [permissions.AllowAny]
    
    @extend_schema(
        summary="Search offers",
        description="Search offers with advanced filtering criteria",
        request=OfferSearchSerializer,
        responses={200: OfferListSerializer(many=True)}
    )
    def post(self, request):
        """Search offers based on criteria"""
        serializer = OfferSearchSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        data = serializer.validated_data
        queryset = Offer.objects.active_offers().select_related('hotel', 'category').prefetch_related(
            'images', 'highlights'
        )
        
        # Apply filters
        if data.get('hotel_id'):
            queryset = queryset.filter(hotel_id=data['hotel_id'])
        
        # Category filters
        if data.get('category_id'):
            queryset = queryset.filter(category_id=data['category_id'])
        
        if data.get('category_slug'):
            queryset = queryset.filter(category__slug=data['category_slug'])
        
        if data.get('offer_type'):
            queryset = queryset.filter(offer_type=data['offer_type'])
        
        if data.get('is_featured'):
            queryset = queryset.filter(is_featured=True)
        
        # Removed room type filtering as applicable_room_types field is removed
        # if data.get('room_type_id'):
        #     queryset = queryset.filter(
        #         Q(applicable_room_types__isnull=True) |
        #         Q(applicable_room_types__id=data['room_type_id'])
        #     ).distinct()
        
        if data.get('min_discount'):
            queryset = queryset.filter(
                discount_percentage__gte=data['min_discount']
            )
        
        if data.get('max_nights'):
            queryset = queryset.filter(
                minimum_stay__lte=data['max_nights']
            )
        
        # Date range filter
        check_in = data.get('check_in')
        check_out = data.get('check_out')
        if check_in and check_out:
            queryset = queryset.filter(
                valid_from__lte=check_out,
                valid_to__gte=check_in
            )
            
            # Filter by day of week applicability
            nights = (check_out - check_in).days
            for i in range(nights):
                current_date = check_in + timezone.timedelta(days=i)
                weekday = current_date.weekday()
                
                # Create a mapping for day applicability
                day_fields = [
                    'applies_monday', 'applies_tuesday', 'applies_wednesday',
                    'applies_thursday', 'applies_friday', 'applies_saturday', 'applies_sunday'
                ]
                
                if weekday < len(day_fields):
                    day_filter = {day_fields[weekday]: True}
                    queryset = queryset.filter(**day_filter)
        
        # Paginate results
        paginator = OfferPagination()
        page = paginator.paginate_queryset(queryset, request)
        if page is not None:
            serializer = OfferListSerializer(page, many=True, context={'request': request})
            return paginator.get_paginated_response(serializer.data)
        
        serializer = OfferListSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)


class OfferCalculationView(APIView):
    """Calculate offer discount for specific booking parameters"""
    
    permission_classes = [permissions.AllowAny]
    
    @extend_schema(
        summary="Calculate offer discount",
        description="Calculate the discount amount for a specific offer and booking parameters",
        request=OfferCalculationSerializer,
        responses={200: OfferCalculationResponseSerializer}
    )
    def post(self, request):
        """Calculate offer discount"""
        serializer = OfferCalculationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        data = serializer.validated_data
        
        try:
            offer = Offer.objects.get(id=data['offer_id'])
        except Offer.DoesNotExist:
            return Response(
                {'error': 'Offer not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        base_price = data['base_price']
        nights = data['nights']
        check_in = data['check_in']
        check_out = data['check_out']
        
        # Check if offer is applicable
        is_applicable = True
        message = ""
        
        # Check if offer is valid and available
        if not offer.is_available:
            is_applicable = False
            message = "Offer is not currently available"
        
        # Check date range
        elif not (offer.valid_from <= check_in <= offer.valid_to and 
                 offer.valid_from <= check_out <= offer.valid_to):
            is_applicable = False
            message = "Offer is not valid for the selected dates"
        
        # Check minimum stay
        elif nights < offer.minimum_stay:
            is_applicable = False
            message = f"Minimum stay of {offer.minimum_stay} nights required"
        
        # Check maximum stay
        elif offer.maximum_stay and nights > offer.maximum_stay:
            is_applicable = False
            message = f"Maximum stay of {offer.maximum_stay} nights exceeded"
        
        # Check day of week applicability
        else:
            for i in range(nights):
                current_date = check_in + timezone.timedelta(days=i)
                if not offer.applies_to_date(current_date):
                    is_applicable = False
                    message = "Offer does not apply to one or more selected dates"
                    break
        
        # Calculate discount if applicable
        if is_applicable:
            discount_amount = offer.calculate_discount(base_price, nights)
            original_price = base_price * nights
            discounted_price = max(Decimal('0.00'), original_price - discount_amount)
            savings = discount_amount
            message = "Offer successfully applied"
        else:
            discount_amount = Decimal('0.00')
            original_price = base_price * nights
            discounted_price = original_price
            savings = Decimal('0.00')
        
        response_data = {
            'offer_id': offer.id,
            'offer_name': offer.name,
            'is_applicable': is_applicable,
            'discount_amount': discount_amount,
            'discounted_price': discounted_price,
            'original_price': original_price,
            'savings': savings,
            'message': message
        }
        
        response_serializer = OfferCalculationResponseSerializer(data=response_data)
        response_serializer.is_valid(raise_exception=True)
        
        return Response(response_serializer.data)


# Offer Highlights Views
class OfferHighlightListCreateView(generics.ListCreateAPIView):
    """List or create offer highlights"""
    
    serializer_class = OfferHighlightSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]
    
    def get_queryset(self):
        """Get highlights for a specific offer"""
        offer_id = self.kwargs.get('offer_id')
        return OfferHighlight.objects.filter(offer_id=offer_id)
    
    def perform_create(self, serializer):
        """Set the offer when creating a highlight"""
        offer_id = self.kwargs.get('offer_id')
        offer = get_object_or_404(Offer, id=offer_id)
        serializer.save(offer=offer)


class OfferHighlightDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete an offer highlight"""
    
    serializer_class = OfferHighlightSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]
    
    def get_queryset(self):
        """Get highlights for a specific offer"""
        offer_id = self.kwargs.get('offer_id')
        return OfferHighlight.objects.filter(offer_id=offer_id)


# Offer Images Views
class OfferImageListCreateView(generics.ListCreateAPIView):
    """List or create offer images"""
    
    serializer_class = OfferImageSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]
    
    def get_queryset(self):
        """Get images for a specific offer"""
        offer_id = self.kwargs.get('offer_id')
        return OfferImage.objects.filter(offer_id=offer_id)
    
    def perform_create(self, serializer):
        """Set the offer when creating an image"""
        offer_id = self.kwargs.get('offer_id')
        offer = get_object_or_404(Offer, id=offer_id)
        serializer.save(offer=offer)


class OfferImageDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete an offer image"""
    
    serializer_class = OfferImageSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]
    
    def get_queryset(self):
        """Get images for a specific offer"""
        offer_id = self.kwargs.get('offer_id')
        return OfferImage.objects.filter(offer_id=offer_id)


# Offer Category Views
class OfferCategoryListCreateView(generics.ListCreateAPIView):
    """
    List all offer categories or create a new category
    
    GET: Returns a list of offer categories
    POST: Creates a new offer category (requires admin or manager permissions)
    """
    
    serializer_class = OfferCategoryListSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]
    
    def get_queryset(self):
        """Get active categories ordered by order and name"""
        return OfferCategory.objects.filter(is_active=True).order_by('order', 'name')
    
    def get_serializer_class(self):
        """Use different serializers for list and create"""
        if self.request.method == 'POST':
            return OfferCategorySerializer
        return OfferCategoryListSerializer
    
    @extend_schema(
        summary="List offer categories",
        description="Get a list of active offer categories",
        responses={200: OfferCategoryListSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @extend_schema(
        summary="Create offer category",
        description="Create a new offer category (requires authentication)",
        request=OfferCategorySerializer,
        responses={201: OfferCategorySerializer}
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class OfferCategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete an offer category
    
    GET: Returns detailed category information with offer count
    PUT/PATCH: Updates the category (requires admin or manager permissions)
    DELETE: Deletes the category (requires admin or manager permissions)
    """
    
    serializer_class = OfferCategorySerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]
    lookup_field = 'slug'
    
    def get_queryset(self):
        """Get categories"""
        return OfferCategory.objects.all()
    
    @extend_schema(
        summary="Get category details",
        description="Get detailed information about a specific offer category",
        responses={200: OfferCategorySerializer}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @extend_schema(
        summary="Update category",
        description="Update an existing offer category (requires authentication)",
        request=OfferCategorySerializer,
        responses={200: OfferCategorySerializer}
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)
    
    @extend_schema(
        summary="Partially update category",
        description="Partially update an existing offer category (requires authentication)",
        request=OfferCategorySerializer,
        responses={200: OfferCategorySerializer}
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)
    
    @extend_schema(
        summary="Delete category",
        description="Delete an offer category (requires authentication)",
        responses={204: None}
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)


class OffersByCategoryView(APIView):
    """Get offers grouped by categories"""
    
    permission_classes = [permissions.AllowAny]
    
    @extend_schema(
        summary="Get offers by category",
        description="Get offers grouped by categories with category information",
        responses={200: dict}
    )
    def get(self, request):
        """Get offers grouped by categories"""
        categories = OfferCategory.objects.filter(is_active=True).order_by('order', 'name')
        
        result = []
        for category in categories:
            category_offers = Offer.objects.active_offers().filter(
                category=category
            ).select_related('hotel').prefetch_related('images', 'highlights')[:5]  # Limit to 5 offers per category
            
            if category_offers.exists():
                category_data = OfferCategoryListSerializer(category).data
                offers_data = OfferListSerializer(category_offers, many=True, context={'request': request}).data
                
                result.append({
                    'category': category_data,
                    'offers': offers_data,
                    'total_offers': category.offer_count
                })
        
        return Response(result)
