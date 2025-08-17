"""
Django management command to populate the hotel booking database with sample data.

Usage:
    python manage.py populate_sample_data
    python manage.py populate_sample_data --clear  # Clear existing data first
    python manage.py populate_sample_data --minimal  # Create minimal data set
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from datetime import date, timedelta
import random

from core.models import Hotel, RoomType, Room, Extra, SeasonalPricing
from bookings.models import Booking

User = get_user_model()


class Command(BaseCommand):
    help = 'Populate database with sample hotel booking data for API testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before populating',
        )
        parser.add_argument(
            '--minimal',
            action='store_true',
            help='Create minimal data set (fewer records)',
        )
        parser.add_argument(
            '--hotels',
            type=int,
            default=5,
            help='Number of hotels to create (default: 5)',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting database population...'))

        if options['clear']:
            self.clear_data()

        if options['minimal']:
            self.create_minimal_data()
        else:
            self.create_full_data(options['hotels'])

        self.stdout.write(
            self.style.SUCCESS('Successfully populated database with sample data!')
        )

    def clear_data(self):
        """Clear existing data"""
        self.stdout.write('Clearing existing data...')
        
        with transaction.atomic():
            Booking.objects.all().delete()
            SeasonalPricing.objects.all().delete()
            Extra.objects.all().delete()
            Room.objects.all().delete()
            RoomType.objects.all().delete()
            Hotel.objects.all().delete()
            # Keep users for authentication testing
            
        self.stdout.write(self.style.SUCCESS('Existing data cleared.'))

    def create_minimal_data(self):
        """Create minimal sample data"""
        self.stdout.write('Creating minimal sample data...')
        
        with transaction.atomic():
            # Create 1 test user
            user = self.create_test_users(1)[0]
            
            # Create 2 hotels
            hotels = self.create_hotels(2)
            
            # Create room types
            room_types = self.create_room_types()
            
            # Create rooms for each hotel
            for hotel in hotels:
                self.create_rooms_for_hotel(hotel, room_types, minimal=True)
                self.create_extras_for_hotel(hotel, minimal=True)
            
            # Create some bookings
            self.create_sample_bookings(user, minimal=True)

    def create_full_data(self, num_hotels):
        """Create full sample data"""
        self.stdout.write(f'Creating full sample data with {num_hotels} hotels...')
        
        with transaction.atomic():
            # Create test users
            users = self.create_test_users(10)
            
            # Create hotels
            hotels = self.create_hotels(num_hotels)
            
            # Create room types
            room_types = self.create_room_types()
            
            # Create rooms and extras for each hotel
            for hotel in hotels:
                self.create_rooms_for_hotel(hotel, room_types)
                self.create_extras_for_hotel(hotel)
                self.create_seasonal_pricing(hotel, room_types)
            
            # Create sample bookings
            self.create_sample_bookings(users[0])

    def create_test_users(self, count):
        """Create test users"""
        self.stdout.write(f'Creating {count} test users...')
        
        users = []
        
        # Create admin user
        admin_user, created = User.objects.get_or_create(
            email='admin@hotel.com',
            username='admin',
            defaults={
                'first_name': 'Admin',
                'last_name': 'User',
                'user_type': 'admin',
                'is_staff': True,
                'is_superuser': True,
                'is_verified': True,
                'phone_number': '+1234567890',
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
        users.append(admin_user)
        
        # Create guest users
        for i in range(1, count):
            user, created = User.objects.get_or_create(
                email=f'guest{i}@example.com',
                username=f'guest{i}',
                defaults={
                    'first_name': f'Guest',
                    'last_name': f'User{i}',
                    'user_type': 'guest',
                    'is_verified': True,
                    'phone_number': f'+123456789{i}',
                    'address_line_1': f'{i}00 Test Street',
                    'city': 'Test City',
                    'state': 'Test State',
                    'postal_code': f'1000{i}',
                    'country': 'United States',
                }
            )
            if created:
                user.set_password('guest123')
                user.save()
            users.append(user)
        
        self.stdout.write(f'Created {len(users)} users.')
        return users

    def create_hotels(self, count):
        """Create sample hotels"""
        self.stdout.write(f'Creating {count} hotels...')
        
        hotel_data = [
            {
                'name': 'Grand Plaza Hotel',
                'description': 'Luxury hotel in the heart of downtown with stunning city views and world-class amenities.',
                'address_line_1': '123 Main Street',
                'city': 'New York',
                'state': 'NY',
                'postal_code': '10001',
                'phone_number': '+1-555-0101',
                'email': 'info@grandplaza.com',
                'website': 'https://grandplaza.com',
                'star_rating': 5,
            },
            {
                'name': 'Oceanview Resort',
                'description': 'Beachfront resort with private beach access, spa services, and oceanfront dining.',
                'address_line_1': '456 Ocean Drive',
                'city': 'Miami Beach',
                'state': 'FL',
                'postal_code': '33139',
                'phone_number': '+1-555-0202',
                'email': 'reservations@oceanview.com',
                'website': 'https://oceanviewresort.com',
                'star_rating': 4,
            },
            {
                'name': 'Mountain Lodge',
                'description': 'Rustic mountain lodge with hiking trails, cozy fireplaces, and scenic mountain views.',
                'address_line_1': '789 Mountain Road',
                'city': 'Aspen',
                'state': 'CO',
                'postal_code': '81611',
                'phone_number': '+1-555-0303',
                'email': 'bookings@mountainlodge.com',
                'website': 'https://mountainlodge.com',
                'star_rating': 4,
            },
            {
                'name': 'Business Center Hotel',
                'description': 'Modern business hotel with conference facilities, high-speed internet, and executive services.',
                'address_line_1': '321 Business Boulevard',
                'city': 'Chicago',
                'state': 'IL',
                'postal_code': '60601',
                'phone_number': '+1-555-0404',
                'email': 'corporate@bizcenter.com',
                'website': 'https://businesscenter.com',
                'star_rating': 3,
            },
            {
                'name': 'Historic Inn',
                'description': 'Charming historic inn with antique furnishings, garden courtyard, and traditional hospitality.',
                'address_line_1': '654 Heritage Lane',
                'city': 'Charleston',
                'state': 'SC',
                'postal_code': '29401',
                'phone_number': '+1-555-0505',
                'email': 'welcome@historicinn.com',
                'website': 'https://historicinn.com',
                'star_rating': 3,
            },
        ]
        
        hotels = []
        for i in range(count):
            data = hotel_data[i % len(hotel_data)]
            if i >= len(hotel_data):
                # Create variations for additional hotels
                data = data.copy()
                data['name'] = f"{data['name']} {i + 1}"
                data['email'] = f"hotel{i + 1}@example.com"
                data['phone_number'] = f"+1-555-{1000 + i:04d}"
            
            hotel, created = Hotel.objects.get_or_create(
                name=data['name'],
                defaults=data
            )
            hotels.append(hotel)
        
        self.stdout.write(f'Created {len(hotels)} hotels.')
        return hotels

    def create_room_types(self):
        """Create room types"""
        self.stdout.write('Creating room types...')
        
        room_type_data = [
            {
                'name': 'Standard Single',
                'description': 'Comfortable single room with essential amenities',
                'max_capacity': 1,
                'bed_type': 'Single Bed',
                'bed_count': 1,
                'room_size_sqm': 20,
                'has_balcony': False,
                'has_kitchenette': False,
                'has_minibar': False,
            },
            {
                'name': 'Standard Double',
                'description': 'Spacious double room with modern amenities',
                'max_capacity': 2,
                'bed_type': 'Queen Bed',
                'bed_count': 1,
                'room_size_sqm': 25,
                'has_balcony': False,
                'has_kitchenette': False,
                'has_minibar': True,
            },
            {
                'name': 'Family Room',
                'description': 'Large family room with multiple beds',
                'max_capacity': 4,
                'bed_type': 'Queen Bed',
                'bed_count': 2,
                'room_size_sqm': 35,
                'has_balcony': True,
                'has_kitchenette': False,
                'has_minibar': True,
            },
            {
                'name': 'Suite',
                'description': 'Luxurious suite with separate living area',
                'max_capacity': 4,
                'bed_type': 'King Bed',
                'bed_count': 1,
                'bathroom_count': 2,
                'room_size_sqm': 50,
                'has_balcony': True,
                'has_kitchenette': True,
                'has_minibar': True,
            },
            {
                'name': 'Executive Suite',
                'description': 'Premium executive suite with luxury amenities',
                'max_capacity': 6,
                'bed_type': 'King Bed',
                'bed_count': 2,
                'bathroom_count': 2,
                'room_size_sqm': 70,
                'has_balcony': True,
                'has_kitchenette': True,
                'has_minibar': True,
                'is_accessible': True,
            },
            {
                'name': 'Presidential Suite',
                'description': 'Ultimate luxury suite with panoramic views',
                'max_capacity': 8,
                'bed_type': 'King Bed',
                'bed_count': 3,
                'bathroom_count': 3,
                'room_size_sqm': 100,
                'has_balcony': True,
                'has_kitchenette': True,
                'has_minibar': True,
                'is_accessible': True,
            },
        ]
        
        room_types = []
        for data in room_type_data:
            room_type, created = RoomType.objects.get_or_create(
                name=data['name'],
                defaults=data
            )
            room_types.append(room_type)
        
        self.stdout.write(f'Created {len(room_types)} room types.')
        return room_types

    def create_rooms_for_hotel(self, hotel, room_types, minimal=False):
        """Create rooms for a hotel"""
        self.stdout.write(f'Creating rooms for {hotel.name}...')
        
        view_types = ['city', 'sea', 'mountain', 'garden', 'pool', 'courtyard']
        floors = [1, 2, 3, 4, 5] if not minimal else [1, 2]
        rooms_per_floor = 3 if minimal else 6
        
        room_count = 0
        for floor in floors:
            for room_num in range(1, rooms_per_floor + 1):
                room_number = f"{floor}{room_num:02d}"
                
                # Select room type based on room number (distribution)
                if room_num <= 2:
                    room_type = room_types[0]  # Standard Single
                    capacity = 1
                    base_price = Decimal('80.00')
                elif room_num <= 4:
                    room_type = room_types[1]  # Standard Double
                    capacity = 2
                    base_price = Decimal('120.00')
                elif room_num <= 5:
                    room_type = room_types[2]  # Family Room
                    capacity = 4
                    base_price = Decimal('180.00')
                else:
                    room_type = random.choice(room_types[3:])  # Suites
                    capacity = room_type.max_capacity
                    base_price = Decimal(str(200.00 + (room_type.max_capacity * 20)))
                
                # Vary prices by hotel star rating
                price_multiplier = hotel.star_rating / 3.0
                base_price = base_price * Decimal(str(price_multiplier))
                
                room, created = Room.objects.get_or_create(
                    hotel=hotel,
                    room_number=room_number,
                    defaults={
                        'room_type': room_type,
                        'floor': floor,
                        'capacity': capacity,
                        'base_price': base_price,
                        'view_type': random.choice(view_types),
                        'is_active': True,
                        'is_maintenance': False,
                    }
                )
                if created:
                    room_count += 1
        
        self.stdout.write(f'Created {room_count} rooms for {hotel.name}.')

    def create_extras_for_hotel(self, hotel, minimal=False):
        """Create extra services for a hotel"""
        self.stdout.write(f'Creating extras for {hotel.name}...')
        
        extras_data = [
            {
                'name': 'Continental Breakfast',
                'description': 'Fresh breakfast buffet with pastries, fruits, and beverages',
                'price': Decimal('15.00'),
                'pricing_type': 'per_person',
                'category': 'breakfast',
            },
            {
                'name': 'Valet Parking',
                'description': 'Convenient valet parking service',
                'price': Decimal('25.00'),
                'pricing_type': 'per_night',
                'category': 'parking',
            },
            {
                'name': 'Airport Shuttle',
                'description': 'Complimentary shuttle service to/from airport',
                'price': Decimal('20.00'),
                'pricing_type': 'per_person',
                'category': 'transport',
            },
            {
                'name': 'Spa Package',
                'description': 'Relaxing spa treatment package',
                'price': Decimal('150.00'),
                'pricing_type': 'per_stay',
                'category': 'spa',
            },
            {
                'name': 'Premium WiFi',
                'description': 'High-speed premium internet access',
                'price': Decimal('10.00'),
                'pricing_type': 'per_night',
                'category': 'wifi',
            },
            {
                'name': 'Room Service',
                'description': '24/7 in-room dining service',
                'price': Decimal('5.00'),
                'pricing_type': 'per_stay',
                'category': 'dining',
            },
        ]
        
        if minimal:
            extras_data = extras_data[:3]  # Only first 3 for minimal
        
        extras_count = 0
        for data in extras_data:
            extra, created = Extra.objects.get_or_create(
                hotel=hotel,
                name=data['name'],
                defaults=data
            )
            if created:
                extras_count += 1
        
        self.stdout.write(f'Created {extras_count} extras for {hotel.name}.')

    def create_seasonal_pricing(self, hotel, room_types):
        """Create seasonal pricing for hotel"""
        self.stdout.write(f'Creating seasonal pricing for {hotel.name}...')
        
        current_year = timezone.now().year
        
        seasonal_data = [
            {
                'name': 'Summer Peak Season',
                'start_date': date(current_year, 6, 1),
                'end_date': date(current_year, 8, 31),
                'price_multiplier': Decimal('1.5'),
            },
            {
                'name': 'Holiday Season',
                'start_date': date(current_year, 12, 20),
                'end_date': date(current_year + 1, 1, 5),
                'price_multiplier': Decimal('2.0'),
            },
            {
                'name': 'Weekend Premium',
                'start_date': date(current_year, 1, 1),
                'end_date': date(current_year, 12, 31),
                'price_multiplier': Decimal('1.2'),
                'apply_monday': False,
                'apply_tuesday': False,
                'apply_wednesday': False,
                'apply_thursday': False,
                'apply_friday': True,
                'apply_saturday': True,
                'apply_sunday': True,
            },
        ]
        
        pricing_count = 0
        for room_type in room_types[:3]:  # Apply to first 3 room types
            for data in seasonal_data:
                pricing, created = SeasonalPricing.objects.get_or_create(
                    hotel=hotel,
                    room_type=room_type,
                    name=data['name'],
                    defaults=data
                )
                if created:
                    pricing_count += 1
        
        self.stdout.write(f'Created {pricing_count} seasonal pricing rules for {hotel.name}.')

    def create_sample_bookings(self, user, minimal=False):
        """Create sample bookings"""
        self.stdout.write('Creating sample bookings...')
        
        rooms = Room.objects.all()
        if not rooms:
            self.stdout.write(self.style.WARNING('No rooms available for bookings.'))
            return
        
        today = timezone.now().date()
        booking_count = 0
        
        # Create some past bookings (checked out)
        for i in range(2 if minimal else 5):
            room = random.choice(rooms)
            check_in = today - timedelta(days=random.randint(30, 90))
            check_out = check_in + timedelta(days=random.randint(1, 5))
            
            nights = (check_out - check_in).days
            room_price = room.base_price * nights
            
            # Create booking without validation for past dates
            booking = Booking(
                user=user,
                room=room,
                check_in=check_in,
                check_out=check_out,
                guests=random.randint(1, min(room.capacity, 4)),
                status='checked_out',
                payment_status='paid',
                room_price=room_price,
                extras_price=Decimal('0.00'),
                tax_amount=room_price * Decimal('0.10'),
                total_price=room_price * Decimal('1.10'),
                primary_guest_name=f"{user.first_name} {user.last_name}",
                primary_guest_email=user.email,
                primary_guest_phone=user.phone_number or '+1234567890',
                booking_source='api',
            )
            # Generate booking reference manually
            if not booking.booking_reference:
                booking.booking_reference = booking._generate_booking_reference()
            # Save without calling clean() to bypass date validation
            booking.save_base()
            booking_count += 1
        
        # Create some future bookings (confirmed)
        for i in range(2 if minimal else 5):
            room = random.choice(rooms)
            check_in = today + timedelta(days=random.randint(10, 60))
            check_out = check_in + timedelta(days=random.randint(1, 7))
            
            nights = (check_out - check_in).days
            room_price = room.base_price * nights
            
            booking = Booking.objects.create(
                user=user,
                room=room,
                check_in=check_in,
                check_out=check_out,
                guests=random.randint(1, min(room.capacity, 4)),
                status='confirmed',
                payment_status='paid',
                room_price=room_price,
                extras_price=Decimal('0.00'),
                tax_amount=room_price * Decimal('0.10'),
                total_price=room_price * Decimal('1.10'),
                primary_guest_name=f"{user.first_name} {user.last_name}",
                primary_guest_email=user.email,
                primary_guest_phone=user.phone_number or '+1234567890',
                booking_source='api',
            )
            booking_count += 1
        
        # Create a current booking (checked in)
        if not minimal:
            room = random.choice(rooms)
            check_in = today - timedelta(days=1)
            check_out = today + timedelta(days=2)
            
            nights = (check_out - check_in).days
            room_price = room.base_price * nights
            
            # Create booking without validation for past check-in date
            booking = Booking(
                user=user,
                room=room,
                check_in=check_in,
                check_out=check_out,
                guests=random.randint(1, min(room.capacity, 4)),
                status='checked_in',
                payment_status='paid',
                room_price=room_price,
                extras_price=Decimal('0.00'),
                tax_amount=room_price * Decimal('0.10'),
                total_price=room_price * Decimal('1.10'),
                primary_guest_name=f"{user.first_name} {user.last_name}",
                primary_guest_email=user.email,
                primary_guest_phone=user.phone_number or '+1234567890',
                booking_source='api',
            )
            # Generate booking reference manually
            if not booking.booking_reference:
                booking.booking_reference = booking._generate_booking_reference()
            # Save without calling clean() to bypass date validation
            booking.save_base()
            booking_count += 1
        
        self.stdout.write(f'Created {booking_count} sample bookings.')

    def style_success(self, message):
        """Style success messages"""
        return f"\033[92m{message}\033[0m"
