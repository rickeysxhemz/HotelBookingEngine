"""
Comprehensive test suite for the booking app.
Tests all models, views, serializers, and email functionality.
"""

# Django imports
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from django.core import mail
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import date, timedelta
import json

# Django REST Framework imports
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

# Local imports
from .models import Booking
from core.models import Hotel, Room, RoomType

User = get_user_model()


class BookingModelTestCase(TestCase):
    """Test cases for the Booking model functionality"""
    
    def setUp(self):
        """Set up test data"""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        # Create test hotel
        self.hotel = Hotel.objects.create(
            name='Grand Test Hotel',
            address='123 Test Avenue',
            city='Test City',
            country='Test Country',
            phone='+1-555-123-4567',
            email='info@grandtesthotel.com',
            description='A luxurious test hotel for testing purposes'
        )
        
        # Create room type
        self.room_type = RoomType.objects.create(
            name='Deluxe Suite',
            description='A spacious deluxe suite with city view',
            base_price=Decimal('250.00')
        )
        
        # Create test room
        self.room = Room.objects.create(
            hotel=self.hotel,
            room_type=self.room_type,
            room_number='501',
            capacity=4,
            base_price=Decimal('250.00'),
            is_active=True
        )
    
    def test_booking_creation_with_all_fields(self):
        """Test creating a booking with all required and optional fields"""
        booking = Booking.objects.create(
            # Guest information
            guest_first_name='John',
            guest_last_name='Doe',
            guest_email='john.doe@example.com',
            guest_phone='+1-555-987-6543',
            guest_passport_number='AB123456789',
            
            # Address information
            guest_country='United States',
            guest_address='456 Main Street, Apt 2B',
            guest_city='New York',
            guest_postal_code='10001',
            
            # Booking details
            hotel=self.hotel,
            room=self.room,
            check_in_date=date.today() + timedelta(days=7),
            check_out_date=date.today() + timedelta(days=10),
            
            # Guest count
            adults=2,
            children=1,
            
            # Pricing
            room_rate=Decimal('250.00'),
            tax_amount=Decimal('75.00'),
            discount_amount=Decimal('25.00'),
            discount_type='Early Bird Discount',
            
            # Status
            status='confirmed',
            payment_status='paid',
            
            # Optional fields
            special_requests='Late check-in requested, extra towels',
            user=self.user
        )
        
        # Test auto-generated fields
        self.assertTrue(booking.booking_id.startswith('BK'))
        self.assertEqual(len(booking.booking_id), 10)
        self.assertEqual(booking.nights, 3)
        self.assertEqual(booking.subtotal, Decimal('750.00'))  # 250 * 3 nights
        self.assertEqual(booking.total_amount, Decimal('800.00'))  # 750 - 25 + 75
        
        # Test string representation
        self.assertEqual(str(booking), f"{booking.booking_id} - John Doe (Grand Test Hotel)")
        
        # Test timestamps
        self.assertIsNotNone(booking.created_at)
        self.assertIsNotNone(booking.updated_at)
    
    def test_booking_id_uniqueness(self):
        """Test that booking IDs are unique"""
        booking1 = Booking.objects.create(
            guest_first_name='Jane',
            guest_last_name='Smith',
            guest_email='jane@example.com',
            guest_phone='+1-555-111-2222',
            guest_country='Canada',
            guest_address='789 Oak Street',
            guest_city='Toronto',
            guest_postal_code='M5V 3L9',
            hotel=self.hotel,
            room=self.room,
            check_in_date=date.today() + timedelta(days=1),
            check_out_date=date.today() + timedelta(days=3),
            adults=1,
            room_rate=Decimal('250.00')
        )
        
        booking2 = Booking.objects.create(
            guest_first_name='Bob',
            guest_last_name='Wilson',
            guest_email='bob@example.com',
            guest_phone='+1-555-333-4444',
            guest_country='Australia',
            guest_address='321 Pine Road',
            guest_city='Sydney',
            guest_postal_code='2000',
            hotel=self.hotel,
            room=self.room,
            check_in_date=date.today() + timedelta(days=5),
            check_out_date=date.today() + timedelta(days=8),
            adults=2,
            room_rate=Decimal('250.00')
        )
        
        self.assertNotEqual(booking1.booking_id, booking2.booking_id)
    
    def test_booking_validation_check_dates(self):
        """Test booking validation for check-in/check-out dates"""
        # Test check-out before check-in
        booking = Booking(
            guest_first_name='Invalid',
            guest_last_name='Dates',
            guest_email='invalid@example.com',
            guest_phone='+1-555-000-0000',
            guest_country='USA',
            guest_address='123 Error St',
            guest_city='Test City',
            guest_postal_code='12345',
            hotel=self.hotel,
            room=self.room,
            check_in_date=date.today() + timedelta(days=5),
            check_out_date=date.today() + timedelta(days=3),  # Before check-in
            adults=1,
            room_rate=Decimal('250.00')
        )
        
        with self.assertRaises(ValidationError) as context:
            booking.clean()
        
        self.assertIn('check_out_date', context.exception.message_dict)
    
    def test_booking_validation_past_dates(self):
        """Test booking validation for past check-in dates"""
        booking = Booking(
            guest_first_name='Past',
            guest_last_name='Date',
            guest_email='past@example.com',
            guest_phone='+1-555-555-5555',
            guest_country='UK',
            guest_address='999 Past Lane',
            guest_city='London',
            guest_postal_code='SW1A 1AA',
            hotel=self.hotel,
            room=self.room,
            check_in_date=date.today() - timedelta(days=1),  # Past date
            check_out_date=date.today() + timedelta(days=1),
            adults=1,
            room_rate=Decimal('250.00')
        )
        
        with self.assertRaises(ValidationError) as context:
            booking.clean()
        
        self.assertIn('check_in_date', context.exception.message_dict)
    
    def test_calculated_methods(self):
        """Test all calculated methods and properties"""
        booking = Booking.objects.create(
            guest_first_name='Calculate',
            guest_last_name='Methods',
            guest_email='calculate@example.com',
            guest_phone='+1-555-777-8888',
            guest_country='Germany',
            guest_address='100 Math Street',
            guest_city='Berlin',
            guest_postal_code='10115',
            hotel=self.hotel,
            room=self.room,
            check_in_date=date.today() + timedelta(days=10),
            check_out_date=date.today() + timedelta(days=15),
            adults=2,
            children=2,
            room_rate=Decimal('200.00'),
            tax_amount=Decimal('150.00'),
            discount_amount=Decimal('100.00'),
            discount_type='Family Discount'
        )
        
        # Test calculated methods
        self.assertEqual(booking.guest_full_name(), 'Calculate Methods')
        self.assertEqual(booking.guest_address_formatted(), 
                        '100 Math Street, Berlin, 10115, Germany')
        self.assertEqual(booking.total_guests(), 4)
        self.assertEqual(booking.tax_percentage(), 15.0)  # 150/1000 * 100
        self.assertEqual(booking.discount_percentage(), 10.0)  # 100/1000 * 100
        
        # Test can_be_cancelled (future booking, not cancelled/completed)
        self.assertTrue(booking.can_be_cancelled())
        
        # Test can_be_cancelled for cancelled booking
        booking.status = 'cancelled'
        self.assertFalse(booking.can_be_cancelled())
    
    def test_pricing_calculations(self):
        """Test automatic pricing calculations"""
        booking = Booking.objects.create(
            guest_first_name='Price',
            guest_last_name='Test',
            guest_email='price@example.com',
            guest_phone='+1-555-999-0000',
            guest_country='France',
            guest_address='50 Price Avenue',
            guest_city='Paris',
            guest_postal_code='75001',
            hotel=self.hotel,
            room=self.room,
            check_in_date=date.today() + timedelta(days=20),
            check_out_date=date.today() + timedelta(days=25),  # 5 nights
            adults=1,
            room_rate=Decimal('300.00'),
            tax_amount=Decimal('225.00'),  # 15% tax
            discount_amount=Decimal('150.00')  # 10% discount
        )
        
        # Verify calculations
        self.assertEqual(booking.nights, 5)
        self.assertEqual(booking.subtotal, Decimal('1500.00'))  # 300 * 5
        # total = (subtotal - discount) + tax = (1500 - 150) + 225 = 1575
        self.assertEqual(booking.total_amount, Decimal('1575.00'))


class BookingSerializerTestCase(TestCase):
    """Test cases for booking serializers"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='serializeruser',
            email='serializer@example.com',
            password='serializerpass123'
        )
        
        self.hotel = Hotel.objects.create(
            name='Serializer Hotel',
            address='456 Serializer St',
            city='Serializer City',
            country='Serializer Country',
            phone='+1-555-222-3333',
            email='info@serializerhotel.com'
        )
        
        self.room_type = RoomType.objects.create(
            name='Standard Room',
            description='A comfortable standard room'
        )
        
        self.room = Room.objects.create(
            hotel=self.hotel,
            room_type=self.room_type,
            room_number='101',
            capacity=2,
            base_price=Decimal('150.00')
        )
    
    def test_booking_serializer_read(self):
        """Test BookingSerializer for read operations"""
        from .serializers import BookingSerializer
        
        booking = Booking.objects.create(
            guest_first_name='Serialize',
            guest_last_name='Read',
            guest_email='serialize@example.com',
            guest_phone='+1-555-444-5555',
            guest_country='Italy',
            guest_address='77 Serialize Road',
            guest_city='Rome',
            guest_postal_code='00118',
            hotel=self.hotel,
            room=self.room,
            check_in_date=date.today() + timedelta(days=30),
            check_out_date=date.today() + timedelta(days=33),
            adults=2,
            room_rate=Decimal('150.00'),
            user=self.user
        )
        
        serializer = BookingSerializer(booking)
        data = serializer.data
        
        # Test that all expected fields are present
        expected_fields = [
            'id', 'booking_id', 'status', 'guest_first_name', 'guest_last_name',
            'guest_full_name', 'guest_email', 'total_guests', 'hotel_name',
            'room_number', 'check_in_date', 'check_out_date', 'nights',
            'total_amount', 'can_be_cancelled'
        ]
        
        for field in expected_fields:
            self.assertIn(field, data)
        
        # Test calculated fields
        self.assertEqual(data['guest_full_name'], 'Serialize Read')
        self.assertEqual(data['total_guests'], 2)
        self.assertEqual(data['hotel_name'], 'Serializer Hotel')
        self.assertEqual(data['nights'], 3)
    
    def test_booking_create_serializer(self):
        """Test BookingCreateSerializer for creating bookings"""
        from .serializers import BookingCreateSerializer
        
        booking_data = {
            'guest_first_name': 'Create',
            'guest_last_name': 'Test',
            'guest_email': 'create@example.com',
            'guest_phone': '+1-555-666-7777',
            'guest_country': 'Spain',
            'guest_address': '88 Create Street',
            'guest_city': 'Madrid',
            'guest_postal_code': '28001',
            'hotel': self.hotel.id,
            'room': self.room.id,
            'check_in_date': (date.today() + timedelta(days=40)).isoformat(),
            'check_out_date': (date.today() + timedelta(days=43)).isoformat(),
            'adults': 1,
            'room_rate': '150.00',
            'tax_amount': '33.75',
            'user': self.user.id
        }
        
        serializer = BookingCreateSerializer(data=booking_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        
        booking = serializer.save()
        self.assertEqual(booking.guest_first_name, 'Create')
        self.assertEqual(booking.nights, 3)
        self.assertEqual(booking.subtotal, Decimal('450.00'))  # 150 * 3


class BookingAPITestCase(APITestCase):
    """Test cases for Booking API endpoints"""
    
    def setUp(self):
        """Set up test data and authentication"""
        # Create test user
        self.user = User.objects.create_user(
            username='apiuser',
            email='api@example.com',
            password='apipass123',
            first_name='API',
            last_name='User'
        )
        
        # Create test hotel and room
        self.hotel = Hotel.objects.create(
            name='API Test Hotel',
            address='123 API Boulevard',
            city='API City',
            country='API Country',
            phone='+1-555-API-TEST',
            email='api@testhotel.com'
        )
        
        self.room_type = RoomType.objects.create(
            name='API Test Room',
            description='Room for API testing'
        )
        
        self.room = Room.objects.create(
            hotel=self.hotel,
            room_type=self.room_type,
            room_number='API-101',
            capacity=4,
            base_price=Decimal('180.00')
        )
        
        # Set up API client with authentication
        self.client = APIClient()
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    
    def test_create_booking_endpoint(self):
        """Test POST /bookings/create/ endpoint"""
        booking_data = {
            'guest_first_name': 'API',
            'guest_last_name': 'Create',
            'guest_email': 'apicreate@example.com',
            'guest_phone': '+1-555-CREATE-1',
            'guest_country': 'Netherlands',
            'guest_address': '123 API Create Lane',
            'guest_city': 'Amsterdam',
            'guest_postal_code': '1012',
            'hotel': self.hotel.id,
            'room': self.room.id,
            'check_in_date': (date.today() + timedelta(days=50)).isoformat(),
            'check_out_date': (date.today() + timedelta(days=53)).isoformat(),
            'adults': 2,
            'children': 1,
            'room_rate': '180.00',
            'tax_amount': '40.50',
            'discount_amount': '10.00',
            'discount_type': 'API Discount',
            'special_requests': 'API testing booking',
            'user': self.user.id
        }
        
        url = reverse('bookings:booking-create')
        response = self.client.post(url, booking_data, format='json')
        
        # Verify response
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertIn('booking', response.data)
        self.assertIn('email_confirmation', response.data)
        
        # Verify booking was created in database
        booking_id = response.data['booking']['id']
        booking = Booking.objects.get(id=booking_id)
        self.assertEqual(booking.guest_first_name, 'API')
        self.assertEqual(booking.guest_last_name, 'Create')
        self.assertEqual(booking.nights, 3)
        self.assertEqual(booking.total_guests(), 3)
    
    def test_list_bookings_endpoint(self):
        """Test GET /bookings/ endpoint"""
        # Create multiple test bookings
        for i in range(3):
            Booking.objects.create(
                guest_first_name=f'List{i}',
                guest_last_name='Test',
                guest_email=f'list{i}@example.com',
                guest_phone=f'+1-555-LIST-{i}',
                guest_country='Belgium',
                guest_address=f'{i} List Street',
                guest_city='Brussels',
                guest_postal_code='1000',
                hotel=self.hotel,
                room=self.room,
                check_in_date=date.today() + timedelta(days=60 + i),
                check_out_date=date.today() + timedelta(days=63 + i),
                adults=i + 1,
                room_rate=Decimal('180.00'),
                user=self.user
            )
        
        url = reverse('bookings:booking-list')
        response = self.client.get(url)
        
        # Verify response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)
        self.assertEqual(len(response.data['results']), 3)
        
        # Test filtering
        response = self.client.get(url, {'guest_name': 'List1'})
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['guest_first_name'], 'List1')
    
    def test_get_booking_detail_endpoint(self):
        """Test GET /bookings/<id>/ endpoint"""
        booking = Booking.objects.create(
            guest_first_name='Detail',
            guest_last_name='Test',
            guest_email='detail@example.com',
            guest_phone='+1-555-DETAIL-1',
            guest_country='Sweden',
            guest_address='99 Detail Avenue',
            guest_city='Stockholm',
            guest_postal_code='10001',
            hotel=self.hotel,
            room=self.room,
            check_in_date=date.today() + timedelta(days=70),
            check_out_date=date.today() + timedelta(days=73),
            adults=2,
            room_rate=Decimal('180.00'),
            user=self.user
        )
        
        url = reverse('bookings:booking-detail', kwargs={'pk': booking.id})
        response = self.client.get(url)
        
        # Verify response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['guest_first_name'], 'Detail')
        self.assertEqual(response.data['booking_id'], booking.booking_id)
        self.assertIn('hotel_name', response.data)
        self.assertIn('guest_full_name', response.data)
    
    def test_update_booking_endpoint(self):
        """Test PUT/PATCH /bookings/<id>/update/ endpoint"""
        booking = Booking.objects.create(
            guest_first_name='Update',
            guest_last_name='Test',
            guest_email='update@example.com',
            guest_phone='+1-555-UPDATE-1',
            guest_country='Norway',
            guest_address='88 Update Road',
            guest_city='Oslo',
            guest_postal_code='0001',
            hotel=self.hotel,
            room=self.room,
            check_in_date=date.today() + timedelta(days=80),
            check_out_date=date.today() + timedelta(days=83),
            adults=1,
            room_rate=Decimal('180.00'),
            status='confirmed',
            user=self.user
        )
        
        # Test partial update
        update_data = {
            'special_requests': 'Updated: Please provide extra pillows',
            'adults': 2
        }
        
        url = reverse('bookings:booking-update', kwargs={'pk': booking.id})
        response = self.client.patch(url, update_data, format='json')
        
        # Verify response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Verify changes in database
        booking.refresh_from_db()
        self.assertEqual(booking.special_requests, 'Updated: Please provide extra pillows')
        self.assertEqual(booking.adults, 2)
        
        # Test status change to cancelled (should trigger email)
        status_update = {'status': 'cancelled'}
        response = self.client.patch(url, status_update, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('email_confirmation', response.data)
        self.assertEqual(response.data['email_confirmation']['type'], 'cancellation')
    
    def test_delete_booking_endpoint(self):
        """Test DELETE /bookings/<id>/delete/ endpoint"""
        booking = Booking.objects.create(
            guest_first_name='Delete',
            guest_last_name='Test',
            guest_email='delete@example.com',
            guest_phone='+1-555-DELETE-1',
            guest_country='Denmark',
            guest_address='77 Delete Street',
            guest_city='Copenhagen',
            guest_postal_code='1001',
            hotel=self.hotel,
            room=self.room,
            check_in_date=date.today() + timedelta(days=90),
            check_out_date=date.today() + timedelta(days=93),
            adults=1,
            room_rate=Decimal('180.00'),
            status='confirmed',
            user=self.user
        )
        
        url = reverse('bookings:booking-delete', kwargs={'pk': booking.id})
        response = self.client.delete(url)
        
        # Verify response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('email_confirmation', response.data)
        self.assertTrue(response.data['email_confirmation']['sent'])
        
        # Verify booking is marked as cancelled (soft delete)
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'cancelled')
        
        # Test deleting already cancelled booking
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
    
    def test_user_bookings_endpoint(self):
        """Test GET /bookings/user/<user_id>/ endpoint"""
        # Create bookings for the user
        for i in range(2):
            Booking.objects.create(
                guest_first_name=f'User{i}',
                guest_last_name='Booking',
                guest_email=f'user{i}@example.com',
                guest_phone=f'+1-555-USER-{i}',
                guest_country='Finland',
                guest_address=f'{i} User Lane',
                guest_city='Helsinki',
                guest_postal_code='00100',
                hotel=self.hotel,
                room=self.room,
                check_in_date=date.today() + timedelta(days=100 + i),
                check_out_date=date.today() + timedelta(days=103 + i),
                adults=1,
                room_rate=Decimal('180.00'),
                user=self.user
            )
        
        url = reverse('bookings:user-bookings', kwargs={'user_id': self.user.id})
        response = self.client.get(url)
        
        # Verify response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        self.assertIn('user_info', response.data)
        self.assertEqual(response.data['user_info']['email'], self.user.email)
    
    def test_room_bookings_endpoint(self):
        """Test GET /bookings/room/<room_id>/ endpoint"""
        # Create bookings for the room
        for i in range(2):
            Booking.objects.create(
                guest_first_name=f'Room{i}',
                guest_last_name='Guest',
                guest_email=f'room{i}@example.com',
                guest_phone=f'+1-555-ROOM-{i}',
                guest_country='Iceland',
                guest_address=f'{i} Room Street',
                guest_city='Reykjavik',
                guest_postal_code='101',
                hotel=self.hotel,
                room=self.room,
                check_in_date=date.today() + timedelta(days=110 + i),
                check_out_date=date.today() + timedelta(days=113 + i),
                adults=1,
                room_rate=Decimal('180.00'),
                user=self.user
            )
        
        url = reverse('bookings:room-bookings', kwargs={'room_id': self.room.id})
        response = self.client.get(url)
        
        # Verify response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        self.assertIn('room_info', response.data)
        self.assertIn('stats', response.data)
        self.assertEqual(response.data['room_info']['room_number'], 'API-101')


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class BookingEmailTestCase(TestCase):
    """Test email functionality for bookings"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='emailuser',
            email='email@example.com',
            password='emailpass123'
        )
        
        self.hotel = Hotel.objects.create(
            name='Email Test Hotel',
            address='123 Email Street',
            city='Email City',
            country='Email Country',
            phone='+1-555-EMAIL-1',
            email='email@hotel.com'
        )
        
        self.room_type = RoomType.objects.create(
            name='Email Test Room',
            description='Room for email testing'
        )
        
        self.room = Room.objects.create(
            hotel=self.hotel,
            room_type=self.room_type,
            room_number='EMAIL-101',
            capacity=2,
            base_price=Decimal('200.00')
        )
    
    def test_booking_confirmation_email_content(self):
        """Test booking confirmation email content and sending"""
        from .views import send_booking_confirmation_email
        
        booking = Booking.objects.create(
            guest_first_name='Email',
            guest_last_name='Confirmation',
            guest_email='confirmation@example.com',
            guest_phone='+1-555-CONFIRM-1',
            guest_country='Portugal',
            guest_address='123 Confirm Street',
            guest_city='Lisbon',
            guest_postal_code='1000-001',
            hotel=self.hotel,
            room=self.room,
            check_in_date=date.today() + timedelta(days=120),
            check_out_date=date.today() + timedelta(days=123),
            adults=2,
            room_rate=Decimal('200.00'),
            tax_amount=Decimal('60.00'),
            user=self.user
        )
        
        # Clear any existing emails
        mail.outbox = []
        
        # Send confirmation email
        result = send_booking_confirmation_email(booking)
        
        # Verify email was sent successfully
        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)
        
        # Check email content
        email = mail.outbox[0]
        self.assertIn(booking.booking_id, email.subject)
        self.assertIn('Confirmation', email.subject)
        self.assertEqual(email.to, [booking.guest_email])
        self.assertIn('Email Test Hotel', email.body)
        self.assertIn('Email Confirmation', email.body)
        self.assertIn(str(booking.total_amount), email.body)
        
        # Check HTML content if available
        if hasattr(email, 'alternatives') and email.alternatives:
            html_content = email.alternatives[0][0]
            self.assertIn(booking.booking_id, html_content)
            self.assertIn('Booking Confirmation', html_content)
    
    def test_booking_cancellation_email_content(self):
        """Test booking cancellation email content and sending"""
        from .views import send_booking_cancellation_email
        
        booking = Booking.objects.create(
            guest_first_name='Email',
            guest_last_name='Cancellation',
            guest_email='cancellation@example.com',
            guest_phone='+1-555-CANCEL-1',
            guest_country='Greece',
            guest_address='456 Cancel Avenue',
            guest_city='Athens',
            guest_postal_code='10431',
            hotel=self.hotel,
            room=self.room,
            check_in_date=date.today() + timedelta(days=130),
            check_out_date=date.today() + timedelta(days=133),
            adults=1,
            room_rate=Decimal('200.00'),
            status='cancelled',
            user=self.user
        )
        
        # Clear any existing emails
        mail.outbox = []
        
        # Send cancellation email
        result = send_booking_cancellation_email(booking)
        
        # Verify email was sent successfully
        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)
        
        # Check email content
        email = mail.outbox[0]
        self.assertIn(booking.booking_id, email.subject)
        self.assertIn('Cancellation', email.subject)
        self.assertEqual(email.to, [booking.guest_email])
        self.assertIn('cancelled', email.body)
        self.assertIn('Email Cancellation', email.body)
        self.assertIn('CANCELLED', email.body)
        
        # Check HTML content if available
        if hasattr(email, 'alternatives') and email.alternatives:
            html_content = email.alternatives[0][0]
            self.assertIn('Cancellation Confirmation', html_content)
            self.assertIn('CANCELLED', html_content)
    
    def test_email_failure_handling(self):
        """Test email failure handling"""
        from .views import send_booking_confirmation_email
        
        booking = Booking.objects.create(
            guest_first_name='Email',
            guest_last_name='Failure',
            guest_email='invalid-email',  # Invalid email format
            guest_phone='+1-555-FAIL-1',
            guest_country='Ireland',
            guest_address='789 Fail Road',
            guest_city='Dublin',
            guest_postal_code='D01',
            hotel=self.hotel,
            room=self.room,
            check_in_date=date.today() + timedelta(days=140),
            check_out_date=date.today() + timedelta(days=143),
            adults=1,
            room_rate=Decimal('200.00'),
            user=self.user
        )
        
        # This should handle the email failure gracefully
        result = send_booking_confirmation_email(booking)
        
        # The function should return False for failed emails but not raise exception
        self.assertFalse(result)


class BookingIntegrationTestCase(APITestCase):
    """Integration tests for complete booking workflows"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='integrationuser',
            email='integration@example.com',
            password='integrationpass123'
        )
        
        self.hotel = Hotel.objects.create(
            name='Integration Hotel',
            address='123 Integration Blvd',
            city='Integration City',
            country='Integration Country',
            phone='+1-555-INT-TEST',
            email='integration@hotel.com'
        )
        
        self.room_type = RoomType.objects.create(
            name='Integration Suite',
            description='Suite for integration testing'
        )
        
        self.room = Room.objects.create(
            hotel=self.hotel,
            room_type=self.room_type,
            room_number='INT-501',
            capacity=3,
            base_price=Decimal('300.00')
        )
        
        # Set up authenticated client
        self.client = APIClient()
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    
    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_complete_booking_lifecycle(self):
        """Test complete booking lifecycle: create -> update -> cancel"""
        # 1. Create booking
        booking_data = {
            'guest_first_name': 'Integration',
            'guest_last_name': 'Lifecycle',
            'guest_email': 'lifecycle@example.com',
            'guest_phone': '+1-555-LIFE-CYCLE',
            'guest_country': 'Switzerland',
            'guest_address': '999 Lifecycle Street',
            'guest_city': 'Zurich',
            'guest_postal_code': '8001',
            'hotel': self.hotel.id,
            'room': self.room.id,
            'check_in_date': (date.today() + timedelta(days=150)).isoformat(),
            'check_out_date': (date.today() + timedelta(days=153)).isoformat(),
            'adults': 2,
            'children': 1,
            'room_rate': '300.00',
            'tax_amount': '90.00',
            'special_requests': 'Integration test booking',
            'user': self.user.id
        }
        
        # Clear email outbox
        mail.outbox = []
        
        # Create booking
        create_url = reverse('bookings:booking-create')
        create_response = self.client.post(create_url, booking_data, format='json')
        
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(create_response.data['success'])
        self.assertTrue(create_response.data['email_confirmation']['sent'])
        
        booking_id = create_response.data['booking']['id']
        
        # Verify confirmation email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Confirmation', mail.outbox[0].subject)
        
        # 2. Update booking
        update_data = {
            'special_requests': 'Updated: Need early check-in',
            'adults': 3
        }
        
        update_url = reverse('bookings:booking-update', kwargs={'pk': booking_id})
        update_response = self.client.patch(update_url, update_data, format='json')
        
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        self.assertTrue(update_response.data['success'])
        
        # 3. Get booking details
        detail_url = reverse('bookings:booking-detail', kwargs={'pk': booking_id})
        detail_response = self.client.get(detail_url)
        
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_response.data['special_requests'], 'Updated: Need early check-in')
        self.assertEqual(detail_response.data['adults'], 3)
        
        # 4. Cancel booking
        delete_url = reverse('bookings:booking-delete', kwargs={'pk': booking_id})
        delete_response = self.client.delete(delete_url)
        
        self.assertEqual(delete_response.status_code, status.HTTP_200_OK)
        self.assertTrue(delete_response.data['success'])
        self.assertTrue(delete_response.data['email_confirmation']['sent'])
        
        # Verify cancellation email was sent
        self.assertEqual(len(mail.outbox), 2)
        self.assertIn('Cancellation', mail.outbox[1].subject)
        
        # 5. Verify booking is cancelled in database
        booking = Booking.objects.get(id=booking_id)
        self.assertEqual(booking.status, 'cancelled')
        self.assertEqual(booking.total_guests(), 3)  # Should still have updated values
