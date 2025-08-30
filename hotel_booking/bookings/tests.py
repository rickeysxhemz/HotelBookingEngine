# Django imports
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal
from datetime import date, timedelta

# Django REST Framework imports
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

# Local imports
from .models import Booking, BookingExtra, BookingGuest, BookingHistory
from core.models import Hotel, Room, RoomType, Extra
from core.services import PricingService, RoomAvailabilityService

User = get_user_model()


class BookingModelTest(TestCase):
    """Test cases for Booking model"""
    
    def setUp(self):
        """Set up test data"""
        # Create user
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        
        # Create hotel
        self.hotel = Hotel.objects.create(
            name='Hotel Maar',
            address_line_1='123 Main St',
            city='Test City',
            state='Test State',
            postal_code='12345',
            phone_number='+1234567890',
            email='hotel@example.com'
        )
        
        # Create room type
        self.room_type = RoomType.objects.create(
            name='Standard Room',
            description='A comfortable standard room',
            max_capacity=2
        )
        
        # Create room
        self.room = Room.objects.create(
            hotel=self.hotel,
            room_type=self.room_type,
            room_number='101',
            floor=1,
            capacity=2,
            base_price=Decimal('100.00')
        )
        
        # Create extra
        self.extra = Extra.objects.create(
            hotel=self.hotel,
            name='Breakfast',
            description='Continental breakfast',
            price=Decimal('25.00'),
            category='breakfast'
        )
    
    def test_booking_creation(self):
        """Test booking creation"""
        booking = Booking.objects.create(
            user=self.user,
            room=self.room,
            check_in=date.today() + timedelta(days=1),
            check_out=date.today() + timedelta(days=3),
            guests=2,
            room_price=Decimal('200.00'),
            total_price=Decimal('220.00'),
            primary_guest_name='Test Guest',
            primary_guest_email='guest@example.com',
            primary_guest_phone='+1234567890'
        )
        
        self.assertEqual(booking.nights, 2)
        self.assertTrue(booking.booking_reference.startswith('BK'))
        self.assertEqual(booking.status, 'pending')
    
    def test_booking_price_calculation(self):
        """Test booking price calculation"""
        booking = Booking.objects.create(
            user=self.user,
            room=self.room,
            check_in=date.today() + timedelta(days=1),
            check_out=date.today() + timedelta(days=3),
            guests=2,
            room_price=Decimal('200.00'),
            total_price=Decimal('220.00'),
            primary_guest_name='Test Guest',
            primary_guest_email='guest@example.com'
        )
        
        # Add booking extra
        BookingExtra.objects.create(
            booking=booking,
            extra=self.extra,
            quantity=2,
            unit_price=self.extra.price
        )
        
        price_breakdown = booking.calculate_total_price()
        self.assertIsInstance(price_breakdown, dict)
        self.assertIn('room_price', price_breakdown)
        self.assertIn('extras_price', price_breakdown)
        self.assertIn('total_price', price_breakdown)
    
    def test_booking_confirmation(self):
        """Test booking confirmation"""
        booking = Booking.objects.create(
            user=self.user,
            room=self.room,
            check_in=date.today() + timedelta(days=1),
            check_out=date.today() + timedelta(days=3),
            guests=2,
            room_price=Decimal('200.00'),
            total_price=Decimal('220.00'),
            primary_guest_name='Test Guest',
            primary_guest_email='guest@example.com'
        )
        
        booking.confirm_booking()
        booking.refresh_from_db()
        
        self.assertEqual(booking.status, 'confirmed')
        self.assertIsNotNone(booking.confirmation_date)
    
    def test_booking_cancellation(self):
        """Test booking cancellation"""
        # Create future booking
        booking = Booking.objects.create(
            user=self.user,
            room=self.room,
            check_in=date.today() + timedelta(days=5),  # Far enough in future to allow cancellation
            check_out=date.today() + timedelta(days=7),
            guests=2,
            room_price=Decimal('200.00'),
            total_price=Decimal('220.00'),
            primary_guest_name='Test Guest',
            primary_guest_email='guest@example.com',
            status='confirmed'
        )
        
        self.assertTrue(booking.can_be_cancelled)
        
        booking.cancel_booking(reason='guest_request', notes='Change of plans')
        booking.refresh_from_db()
        
        self.assertEqual(booking.status, 'cancelled')
        self.assertEqual(booking.cancellation_reason, 'guest_request')
        self.assertIsNotNone(booking.cancellation_date)


class BookingAPITest(APITestCase):
    """Test cases for booking API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        # Create user
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123',
            first_name='Test',
            last_name='User',
            phone_number='+1234567890'
        )
        
        # Create hotel
        self.hotel = Hotel.objects.create(
            name='Hotel Maar',
            address_line_1='123 Main St',
            city='Test City',
            state='Test State',
            postal_code='12345',
            phone_number='+1234567890',
            email='hotel@example.com'
        )
        
        # Create room type
        self.room_type = RoomType.objects.create(
            name='Standard Room',
            description='A comfortable standard room',
            max_capacity=3
        )
        
        # Create rooms
        self.room1 = Room.objects.create(
            hotel=self.hotel,
            room_type=self.room_type,
            room_number='101',
            floor=1,
            capacity=2,
            base_price=Decimal('100.00')
        )
        
        self.room2 = Room.objects.create(
            hotel=self.hotel,
            room_type=self.room_type,
            room_number='102',
            floor=1,
            capacity=3,
            base_price=Decimal('150.00')
        )
        
        # Create extra
        self.extra = Extra.objects.create(
            hotel=self.hotel,
            name='Breakfast',
            description='Continental breakfast',
            price=Decimal('25.00'),
            category='breakfast',
            max_quantity=5  # Allow multiple breakfast bookings
        )
        
        # Set up API client
        self.client = APIClient()
        
        # Get JWT token
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
    
    def authenticate(self):
        """Authenticate the client"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
    
    def test_room_search(self):
        """Test room availability search"""
        url = reverse('bookings:search_rooms_only')
        params = {
            'check_in': (date.today() + timedelta(days=1)).isoformat(),
            'check_out': (date.today() + timedelta(days=3)).isoformat(),
            'guests': 2
        }
        
        response = self.client.get(url, params)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('available_rooms', response.data)
        self.assertIn('search_criteria', response.data)
    
    def test_create_booking(self):
        """Test booking creation"""
        self.authenticate()
        
        url = reverse('bookings:booking_create')
        data = {
            'room_id': str(self.room1.id),
            'check_in': (date.today() + timedelta(days=1)).isoformat(),
            'check_out': (date.today() + timedelta(days=3)).isoformat(),
            'guests': 2,
            'special_requests': 'Late check-in please',
            'extras_data': [
                {
                    'extra_id': str(self.extra.id),
                    'quantity': 2
                }
            ]
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('booking', response.data)
        self.assertIn('message', response.data)
        
        # Check booking was created
        booking = Booking.objects.get(user=self.user)
        self.assertEqual(booking.room, self.room1)
        self.assertEqual(booking.guests, 2)
        self.assertEqual(booking.special_requests, 'Late check-in please')
    
    def test_list_user_bookings(self):
        """Test listing user bookings"""
        self.authenticate()
        
        # Create a booking
        booking = Booking.objects.create(
            user=self.user,
            room=self.room1,
            check_in=date.today() + timedelta(days=1),
            check_out=date.today() + timedelta(days=3),
            guests=2,
            room_price=Decimal('200.00'),
            total_price=Decimal('220.00'),
            primary_guest_name='Test Guest',
            primary_guest_email='guest@example.com'
        )
        
        url = reverse('bookings:booking_list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['booking_reference'], booking.booking_reference)
    
    def test_get_booking_detail(self):
        """Test getting booking details"""
        self.authenticate()
        
        booking = Booking.objects.create(
            user=self.user,
            room=self.room1,
            check_in=date.today() + timedelta(days=1),
            check_out=date.today() + timedelta(days=3),
            guests=2,
            room_price=Decimal('200.00'),
            total_price=Decimal('220.00'),
            primary_guest_name='Test Guest',
            primary_guest_email='guest@example.com'
        )
        
        url = reverse('bookings:booking_detail', kwargs={'booking_reference': booking.booking_reference})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['booking_reference'], booking.booking_reference)
        self.assertIn('room', response.data)
        self.assertIn('can_cancel', response.data)
    
    def test_cancel_booking(self):
        """Test booking cancellation"""
        self.authenticate()
        
        # Create future booking
        booking = Booking.objects.create(
            user=self.user,
            room=self.room1,
            check_in=date.today() + timedelta(days=5),
            check_out=date.today() + timedelta(days=7),
            guests=2,
            room_price=Decimal('200.00'),
            total_price=Decimal('220.00'),
            primary_guest_name='Test Guest',
            primary_guest_email='guest@example.com',
            status='confirmed'
        )
        
        url = reverse('bookings:booking_cancel', kwargs={'booking_reference': booking.booking_reference})
        data = {
            'reason': 'guest_request',
            'notes': 'Change of plans'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'cancelled')
    
    def test_unauthorized_access(self):
        """Test unauthorized access to booking endpoints"""
        # Don't authenticate
        
        # Try to create booking
        url = reverse('bookings:booking_create')
        data = {'room_id': str(self.room1.id)}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Try to list bookings
        url = reverse('bookings:booking_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class BookingServiceTest(TestCase):
    """Test cases for booking services"""
    
    def setUp(self):
        """Set up test data"""
        # Create hotel
        self.hotel = Hotel.objects.create(
            name='Hotel Maar',
            address_line_1='123 Main St',
            city='Test City',
            state='Test State',
            postal_code='12345',
            phone_number='+1234567890',
            email='hotel@example.com'
        )
        
        # Create room type
        self.room_type = RoomType.objects.create(
            name='Standard Room',
            description='A comfortable standard room',
            max_capacity=3
        )
        
        # Create rooms with different capacities
        self.room1 = Room.objects.create(
            hotel=self.hotel,
            room_type=self.room_type,
            room_number='101',
            floor=1,
            capacity=1,
            base_price=Decimal('80.00')
        )
        
        self.room2 = Room.objects.create(
            hotel=self.hotel,
            room_type=self.room_type,
            room_number='102',
            floor=1,
            capacity=2,
            base_price=Decimal('100.00')
        )
        
        self.room3 = Room.objects.create(
            hotel=self.hotel,
            room_type=self.room_type,
            room_number='103',
            floor=1,
            capacity=3,
            base_price=Decimal('150.00')
        )
    
    def test_room_availability_service(self):
        """Test room availability service"""
        check_in = date.today() + timedelta(days=1)
        check_out = date.today() + timedelta(days=3)
        
        # Test for 3 guests - should return combinations
        combinations = RoomAvailabilityService.get_room_combinations_for_guests(
            hotel=self.hotel,
            check_in=check_in,
            check_out=check_out,
            guests=3
        )
        
        self.assertGreater(len(combinations), 0)
        
        # Should have single room solution (room3 with capacity 3)
        single_room_solutions = [c for c in combinations if c['type'] == 'single_room']
        self.assertGreater(len(single_room_solutions), 0)
        
        # Should have multi-room solutions (room1+room2, etc.)
        multi_room_solutions = [c for c in combinations if c['type'] == 'multi_room']
        self.assertGreater(len(multi_room_solutions), 0)
    
    def test_pricing_service(self):
        """Test pricing service"""
        check_in = date.today() + timedelta(days=1)
        check_out = date.today() + timedelta(days=3)
        
        # Test room price calculation
        total_price = PricingService.calculate_room_price(
            room=self.room2,
            check_in=check_in,
            check_out=check_out
        )
        
        # Should be base_price * nights
        expected_price = self.room2.base_price * 2  # 2 nights
        self.assertEqual(total_price, expected_price)
    
    def test_room_capacity_matching(self):
        """Test room capacity matching for different guest counts"""
        check_in = date.today() + timedelta(days=1)
        check_out = date.today() + timedelta(days=3)
        
        # Test 1 guest - should get all rooms
        available_rooms = RoomAvailabilityService.get_available_rooms(
            hotel=self.hotel,
            check_in=check_in,
            check_out=check_out,
            guests=1
        )
        self.assertEqual(available_rooms.count(), 3)
        
        # Test 2 guests - should get room2 and room3
        available_rooms = RoomAvailabilityService.get_available_rooms(
            hotel=self.hotel,
            check_in=check_in,
            check_out=check_out,
            guests=2
        )
        self.assertEqual(available_rooms.count(), 2)
        
        # Test 3 guests - should get only room3
        available_rooms = RoomAvailabilityService.get_available_rooms(
            hotel=self.hotel,
            check_in=check_in,
            check_out=check_out,
            guests=3
        )
        self.assertEqual(available_rooms.count(), 1)
        self.assertEqual(available_rooms.first(), self.room3)
