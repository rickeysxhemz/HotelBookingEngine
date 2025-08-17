"""
Django management command to populate the hotel booking database with comprehensive sample data.

This command creates a complete hotel booking system with:
- Enhanced hotels with detailed information
- Comprehensive room types with 50+ amenity fields
- Individual rooms with condition tracking and images
- Additional amenities and seasonal pricing
- Sample bookings and user accounts

Usage:
    python manage.py populate_sample_data
    python manage.py populate_sample_data --clear  # Clear existing data first
    python manage.py populate_sample_data --minimal  # Create minimal data set
    python manage.py populate_sample_data --comprehensive  # Create full enhanced data
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from datetime import date, timedelta
import random
import logging

from core.models import (
    Hotel, RoomType, Room, Extra, SeasonalPricing,
    RoomImage, RoomAmenity, RoomTypeAmenity
)
from bookings.models import Booking

User = get_user_model()
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Populate database with comprehensive hotel booking data for API testing and development'

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
            '--comprehensive',
            action='store_true',
            help='Create comprehensive data with all enhanced features (default)',
        )
        parser.add_argument(
            '--hotels',
            type=int,
            default=1,
            help='Number of hotels to create (default: 1 for comprehensive, 3 for basic)',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting comprehensive database population...'))

        if options['clear']:
            self.clear_data()

        # Default to comprehensive unless minimal is specified
        if options['minimal']:
            self.create_minimal_data()
        else:
            # Use comprehensive data by default (includes all enhanced features)
            hotels_count = options['hotels'] if options['hotels'] != 1 else 1
            self.create_comprehensive_data(hotels_count)

        self.stdout.write(
            self.style.SUCCESS('Successfully populated database with sample data!')
        )

    def clear_data(self):
        """Clear existing data"""
        self.stdout.write('Clearing existing data...')
        
        with transaction.atomic():
            Booking.objects.all().delete()
            RoomImage.objects.all().delete()
            RoomTypeAmenity.objects.all().delete()
            SeasonalPricing.objects.all().delete()
            Extra.objects.all().delete()
            Room.objects.all().delete()
            RoomType.objects.all().delete()
            RoomAmenity.objects.all().delete()
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

    def create_comprehensive_data(self, num_hotels=1):
        """Create comprehensive sample data with all enhanced features"""
        self.stdout.write(f'Creating comprehensive sample data with {num_hotels} hotel(s)...')
        
        with transaction.atomic():
            # Create test users
            users = self.create_test_users(10)
            
            # Create sample amenities (enhanced feature)
            amenities = self.create_sample_amenities()
            
            # Create enhanced hotels
            hotels = self.create_enhanced_hotels(num_hotels)
            
            # Create comprehensive room types with all amenities
            room_types = self.create_comprehensive_room_types(amenities)
            
            # Create rooms and extras for each hotel
            all_rooms = []
            for hotel in hotels:
                rooms = self.create_comprehensive_rooms(hotel, room_types)
                all_rooms.extend(rooms)
                self.create_enhanced_extras(hotel)
                self.create_seasonal_pricing(hotel, room_types)
            
            # Create room images
            self.create_room_images(all_rooms, room_types)
            
            # Create sample bookings
            self.create_sample_bookings(users[0])
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Comprehensive data created:\n'
                    f'- {len(hotels)} Hotel(s)\n'
                    f'- {len(amenities)} Room Amenities\n'
                    f'- {len(room_types)} Room Types\n'
                    f'- {len(all_rooms)} Rooms\n'
                    f'- Room Images and Enhanced Features\n'
                    f'- Sample Bookings and Users'
                )
            )

    def create_full_data(self, num_hotels):
        """Legacy method - redirect to comprehensive data"""
        self.create_comprehensive_data(num_hotels)

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

    # Enhanced methods for comprehensive room data
    
    def create_sample_amenities(self):
        """Create sample room amenities for enhanced features"""
        self.stdout.write('Creating sample room amenities...')
        
        amenities_data = [
            # Technology
            {"name": "Smart Home Controls", "category": "technology", "description": "Voice-controlled room automation", "is_premium": True},
            {"name": "Gaming Console", "category": "entertainment", "description": "PlayStation 5 gaming system", "is_premium": True},
            {"name": "High-Speed Fiber Internet", "category": "technology", "description": "1Gbps fiber internet connection", "is_premium": False},
            
            # Luxury
            {"name": "Butler Service", "category": "luxury", "description": "24/7 personal butler service", "is_premium": True},
            {"name": "Premium Linens", "category": "luxury", "description": "Egyptian cotton sheets and towels", "is_premium": True},
            {"name": "Pillow Menu", "category": "comfort", "description": "Selection of specialty pillows", "is_premium": False},
            
            # Business
            {"name": "Executive Workspace", "category": "business", "description": "Dedicated work area with dual monitors", "is_premium": True},
            {"name": "Business Center Access", "category": "business", "description": "24/7 business center access", "is_premium": False},
            
            # Family
            {"name": "Child Safety Kit", "category": "family", "description": "Complete childproofing amenities", "is_premium": False},
            {"name": "Baby Amenities", "category": "family", "description": "Crib, high chair, and baby bath", "is_premium": False},
            
            # Wellness
            {"name": "In-Room Spa Services", "category": "luxury", "description": "Private spa treatments in room", "is_premium": True},
            {"name": "Yoga Equipment", "category": "comfort", "description": "Yoga mats and meditation cushions", "is_premium": False},
        ]
        
        amenities = []
        for amenity_data in amenities_data:
            amenity, created = RoomAmenity.objects.get_or_create(
                name=amenity_data['name'],
                defaults=amenity_data
            )
            amenities.append(amenity)
        
        self.stdout.write(f'Created {len(amenities)} room amenities.')
        return amenities

    def create_enhanced_hotels(self, count):
        """Create enhanced hotels with comprehensive information"""
        self.stdout.write(f'Creating {count} enhanced hotel(s)...')
        
        hotel_data = {
            'name': "Grand Plaza Hotel & Spa",
            'description': "A luxury 5-star hotel offering world-class amenities and exceptional service in the heart of the city.",
            'address_line_1': "123 Grand Avenue",
            'address_line_2': "Suite 100",
            'city': "New York",
            'state': "New York",
            'postal_code': "10001",
            'country': "United States",
            'phone_number': "+1-555-123-4567",
            'email': "reservations@grandplazahotel.com",
            'website': "https://www.grandplazahotel.com",
            'star_rating': 5,
            'cancellation_policy': "Free cancellation up to 24 hours before check-in. Late cancellations may incur charges.",
            'pet_policy': "Pets allowed with advance notice. Additional cleaning fee applies.",
            'smoking_policy': "Non-smoking property. Designated smoking areas available outdoors."
        }
        
        hotels = []
        for i in range(count):
            if i > 0:
                # Create variations for additional hotels
                data = hotel_data.copy()
                data['name'] = f"{hotel_data['name']} - Branch {i + 1}"
                data['email'] = f"hotel{i + 1}@grandplazahotel.com"
                data['phone_number'] = f"+1-555-123-{4567 + i}"
                data['address_line_1'] = f"{123 + i * 100} Grand Avenue"
            else:
                data = hotel_data
            
            hotel, created = Hotel.objects.get_or_create(
                name=data['name'],
                defaults=data
            )
            hotels.append(hotel)
        
        self.stdout.write(f'Created {len(hotels)} enhanced hotel(s).')
        return hotels

    def create_comprehensive_room_types(self, amenities):
        """Create comprehensive room types with all enhanced features"""
        self.stdout.write('Creating comprehensive room types...')
        
        room_types_data = [
            {
                "name": "Standard Queen Room",
                "category": "standard",
                "short_description": "Comfortable queen room with city views",
                "description": "Our Standard Queen Room offers comfortable accommodations with modern amenities and beautiful city views. Perfect for business travelers and couples.",
                "max_capacity": 2,
                "bed_type": "queen",
                "bed_count": 1,
                "bathroom_count": 1,
                "room_size_sqm": 28,
                "room_size_sqft": 301,
                # Basic amenities
                "has_wifi": True,
                "has_tv": True,
                "has_smart_tv": True,
                "has_air_conditioning": True,
                "has_heating": True,
                "has_desk": True,
                "has_safe": True,
                "has_shower": True,
                "has_hairdryer": True,
                "has_toiletries": True,
                "has_towels": True,
                "has_phone": True,
                "has_usb_charging": True,
                "has_coffee_maker": True,
                "has_blackout_curtains": True,
                # Policies
                "children_allowed": True,
                "max_children": 1,
                "extra_bed_available": True,
                "extra_bed_charge": Decimal("50.00"),
                "early_checkin_available": True,
                "early_checkin_charge": Decimal("25.00"),
                "late_checkout_available": True,
                "late_checkout_charge": Decimal("25.00"),
                "amenities": [0, 2, 5, 7, 11]  # Indices of amenities to add
            },
            {
                "name": "Deluxe King Room",
                "category": "deluxe",
                "short_description": "Spacious king room with premium amenities",
                "description": "Our Deluxe King Room features a spacious layout with premium amenities, a comfortable seating area, and stunning city or park views.",
                "max_capacity": 3,
                "bed_type": "king",
                "bed_count": 1,
                "bathroom_count": 1,
                "room_size_sqm": 35,
                "room_size_sqft": 377,
                # Enhanced amenities
                "has_wifi": True,
                "has_tv": True,
                "has_smart_tv": True,
                "has_streaming_service": True,
                "has_air_conditioning": True,
                "has_heating": True,
                "has_desk": True,
                "has_seating_area": True,
                "has_safe": True,
                "has_minibar": True,
                "has_shower": True,
                "has_hairdryer": True,
                "has_toiletries": True,
                "has_towels": True,
                "has_bathrobes": True,
                "has_slippers": True,
                "has_phone": True,
                "has_usb_charging": True,
                "has_bluetooth_speaker": True,
                "has_coffee_maker": True,
                "has_tea_kettle": True,
                "has_refrigerator": True,
                "has_iron": True,
                "has_ironing_board": True,
                "has_blackout_curtains": True,
                "has_soundproofing": True,
                # Policies
                "children_allowed": True,
                "max_children": 2,
                "extra_bed_available": True,
                "extra_bed_charge": Decimal("75.00"),
                "early_checkin_available": True,
                "early_checkin_charge": Decimal("0.00"),
                "late_checkout_available": True,
                "late_checkout_charge": Decimal("0.00"),
                "amenities": [0, 2, 4, 5, 6, 7, 11]
            },
            {
                "name": "Executive Suite",
                "category": "suite",
                "short_description": "Luxurious suite with separate living area",
                "description": "Our Executive Suite offers the ultimate in luxury with a separate living area, premium amenities, and personalized service for discerning guests.",
                "max_capacity": 4,
                "bed_type": "king",
                "bed_count": 1,
                "bathroom_count": 2,
                "room_size_sqm": 65,
                "room_size_sqft": 700,
                # Premium amenities
                "has_wifi": True,
                "has_tv": True,
                "has_smart_tv": True,
                "has_streaming_service": True,
                "has_air_conditioning": True,
                "has_heating": True,
                "has_balcony": True,
                "has_kitchenette": True,
                "has_desk": True,
                "has_seating_area": True,
                "has_safe": True,
                "has_minibar": True,
                "has_bathtub": True,
                "has_shower": True,
                "has_hairdryer": True,
                "has_toiletries": True,
                "has_towels": True,
                "has_bathrobes": True,
                "has_slippers": True,
                "has_phone": True,
                "has_usb_charging": True,
                "has_bluetooth_speaker": True,
                "has_coffee_maker": True,
                "has_tea_kettle": True,
                "has_refrigerator": True,
                "has_microwave": True,
                "has_iron": True,
                "has_ironing_board": True,
                "has_blackout_curtains": True,
                "has_soundproofing": True,
                # Policies
                "children_allowed": True,
                "max_children": 2,
                "infant_bed_available": True,
                "extra_bed_available": True,
                "extra_bed_charge": Decimal("100.00"),
                "early_checkin_available": True,
                "early_checkin_charge": Decimal("0.00"),
                "late_checkout_available": True,
                "late_checkout_charge": Decimal("0.00"),
                "virtual_tour_url": "https://example.com/virtual-tour/executive-suite",
                "amenities": [0, 1, 2, 3, 4, 5, 6, 10, 11]
            },
            {
                "name": "Accessible Standard Room",
                "category": "accessible",
                "short_description": "Fully accessible room with mobility aids",
                "description": "Our Accessible Standard Room is designed for guests with mobility needs, featuring wide doorways, accessible bathroom, and safety equipment.",
                "max_capacity": 2,
                "bed_type": "queen",
                "bed_count": 1,
                "bathroom_count": 1,
                "room_size_sqm": 32,
                "room_size_sqft": 344,
                # Accessibility features
                "is_accessible": True,
                "has_accessible_bathroom": True,
                "has_grab_bars": True,
                "has_roll_in_shower": True,
                "has_lowered_fixtures": True,
                "has_hearing_assistance": True,
                # Standard amenities
                "has_wifi": True,
                "has_tv": True,
                "has_smart_tv": True,
                "has_air_conditioning": True,
                "has_heating": True,
                "has_desk": True,
                "has_safe": True,
                "has_shower": True,
                "has_hairdryer": True,
                "has_toiletries": True,
                "has_towels": True,
                "has_phone": True,
                "has_usb_charging": True,
                "has_coffee_maker": True,
                "has_blackout_curtains": True,
                # Policies
                "children_allowed": True,
                "max_children": 1,
                "amenities": [2, 5, 7, 8, 11]
            },
            {
                "name": "Family Suite",
                "category": "family",
                "short_description": "Spacious family suite with connecting rooms",
                "description": "Our Family Suite is perfect for families, featuring separate areas for parents and children, plus family-friendly amenities and entertainment options.",
                "max_capacity": 6,
                "bed_type": "king",
                "bed_count": 2,
                "bathroom_count": 2,
                "room_size_sqm": 55,
                "room_size_sqft": 592,
                # Family amenities
                "has_wifi": True,
                "has_tv": True,
                "has_smart_tv": True,
                "has_streaming_service": True,
                "has_air_conditioning": True,
                "has_heating": True,
                "has_balcony": True,
                "has_kitchenette": True,
                "has_desk": True,
                "has_seating_area": True,
                "has_safe": True,
                "has_minibar": True,
                "has_shower": True,
                "has_hairdryer": True,
                "has_toiletries": True,
                "has_towels": True,
                "has_phone": True,
                "has_usb_charging": True,
                "has_bluetooth_speaker": True,
                "has_coffee_maker": True,
                "has_tea_kettle": True,
                "has_refrigerator": True,
                "has_microwave": True,
                "has_blackout_curtains": True,
                # Family policies
                "children_allowed": True,
                "max_children": 4,
                "infant_bed_available": True,
                "extra_bed_available": True,
                "extra_bed_charge": Decimal("30.00"),
                "amenities": [1, 2, 5, 8, 9, 11]
            }
        ]
        
        room_types = []
        for i, rt_data in enumerate(room_types_data):
            amenity_indices = rt_data.pop('amenities', [])
            room_type, created = RoomType.objects.get_or_create(
                name=rt_data['name'],
                defaults=rt_data
            )
            
            # Add amenities to room type
            if created:
                for amenity_index in amenity_indices:
                    if amenity_index < len(amenities):
                        RoomTypeAmenity.objects.create(
                            room_type=room_type,
                            amenity=amenities[amenity_index],
                            is_included=True,
                            additional_charge=Decimal("0.00") if not amenities[amenity_index].is_premium else Decimal("15.00")
                        )
            
            room_types.append(room_type)
        
        self.stdout.write(f'Created {len(room_types)} comprehensive room types.')
        return room_types

    def create_comprehensive_rooms(self, hotel, room_types):
        """Create comprehensive rooms with enhanced features"""
        self.stdout.write(f'Creating comprehensive rooms for {hotel.name}...')
        
        rooms = []
        
        # Room configurations for each type
        room_configs = [
            # Standard Queen Rooms (floors 2-5)
            {"room_type": room_types[0], "count": 20, "start_floor": 2, "base_price": Decimal("149.00"), "views": ["city", "courtyard"]},
            # Deluxe King Rooms (floors 6-10)
            {"room_type": room_types[1], "count": 15, "start_floor": 6, "base_price": Decimal("199.00"), "views": ["city", "park", "partial_sea"]},
            # Executive Suites (floors 11-12)
            {"room_type": room_types[2], "count": 8, "start_floor": 11, "base_price": Decimal("399.00"), "views": ["ocean", "mountain", "city"]},
            # Accessible Rooms (floor 1)
            {"room_type": room_types[3], "count": 4, "start_floor": 1, "base_price": Decimal("149.00"), "views": ["garden", "courtyard"]},
            # Family Suites (floors 3-4)
            {"room_type": room_types[4], "count": 6, "start_floor": 3, "base_price": Decimal("299.00"), "views": ["park", "city", "garden"]}
        ]
        
        room_number = 100
        
        for config in room_configs:
            room_type = config["room_type"]
            
            for i in range(config["count"]):
                floor = config["start_floor"] + (i // 10)
                room_num = str(room_number + i)
                
                # Determine special features
                is_corner = (i % 10) in [0, 9]  # First and last rooms on each floor
                is_connecting = (i % 10) in [1, 2, 7, 8]  # Some middle rooms
                
                # Assign view type
                view_type = config["views"][i % len(config["views"])]
                
                # Create room
                room, created = Room.objects.get_or_create(
                    hotel=hotel,
                    room_number=room_num,
                    defaults={
                        'room_type': room_type,
                        'floor': floor,
                        'capacity': room_type.max_capacity,
                        'base_price': config["base_price"],
                        'view_type': view_type,
                        'is_corner_room': is_corner,
                        'is_connecting_room': is_connecting,
                        'condition': "excellent" if i % 5 == 0 else "very_good",
                        'housekeeping_status': "clean",
                        'special_features': f"Corner room with panoramic {view_type} views" if is_corner else "",
                    }
                )
                
                if created:
                    rooms.append(room)
            
            room_number += config["count"]
        
        self.stdout.write(f'Created {len(rooms)} comprehensive rooms for {hotel.name}.')
        return rooms

    def create_enhanced_extras(self, hotel):
        """Create enhanced extra services"""
        self.stdout.write(f'Creating enhanced extras for {hotel.name}...')
        
        extras_data = [
            {
                'name': 'Gourmet Breakfast Buffet',
                'description': 'Premium breakfast buffet with international cuisine, fresh pastries, and barista coffee',
                'price': Decimal('25.00'),
                'pricing_type': 'per_person',
                'category': 'breakfast',
            },
            {
                'name': 'Premium Valet Parking',
                'description': 'Secure valet parking service with car detailing',
                'price': Decimal('45.00'),
                'pricing_type': 'per_night',
                'category': 'parking',
            },
            {
                'name': 'Luxury Airport Transfer',
                'description': 'Private luxury vehicle airport transfer service',
                'price': Decimal('75.00'),
                'pricing_type': 'per_person',
                'category': 'transport',
            },
            {
                'name': 'Full Spa Package',
                'description': 'Complete spa experience with massage, facial, and wellness treatments',
                'price': Decimal('300.00'),
                'pricing_type': 'per_stay',
                'category': 'spa',
            },
            {
                'name': 'Business Center Premium',
                'description': 'Full business center access with meeting rooms and secretarial services',
                'price': Decimal('50.00'),
                'pricing_type': 'per_night',
                'category': 'business',
            },
            {
                'name': 'Concierge Service',
                'description': 'Personal concierge for restaurant reservations, tours, and recommendations',
                'price': Decimal('100.00'),
                'pricing_type': 'per_stay',
                'category': 'other',
            },
        ]
        
        extras_count = 0
        for data in extras_data:
            extra, created = Extra.objects.get_or_create(
                hotel=hotel,
                name=data['name'],
                defaults=data
            )
            if created:
                extras_count += 1
        
        self.stdout.write(f'Created {extras_count} enhanced extras for {hotel.name}.')

    def create_room_images(self, rooms, room_types):
        """Create sample room images"""
        self.stdout.write('Creating sample room images...')
        
        # Sample image URLs (you would replace these with actual image URLs)
        sample_images = {
            "room_overview": "https://example.com/images/room-overview.jpg",
            "bed_area": "https://example.com/images/bed-area.jpg",
            "bathroom": "https://example.com/images/bathroom.jpg",
            "view": "https://example.com/images/room-view.jpg",
            "amenities": "https://example.com/images/amenities.jpg",
        }
        
        images_created = 0
        
        # Create images for room types
        for room_type in room_types:
            for i, (image_type, url) in enumerate(sample_images.items()):
                image, created = RoomImage.objects.get_or_create(
                    room_type=room_type,
                    image_type=image_type,
                    defaults={
                        'image_url': url,
                        'image_alt_text': f"{room_type.name} - {image_type.replace('_', ' ').title()}",
                        'caption': f"Beautiful {image_type.replace('_', ' ')} in our {room_type.name}",
                        'is_primary': (i == 0),
                        'display_order': i + 1,
                        'is_active': True
                    }
                )
                if created:
                    images_created += 1
        
        # Create specific images for some sample rooms
        for i, room in enumerate(rooms[:10]):  # First 10 rooms
            image, created = RoomImage.objects.get_or_create(
                room=room,
                image_type="room_overview",
                defaults={
                    'image_url': sample_images["room_overview"],
                    'image_alt_text': f"Room {room.room_number} overview",
                    'caption': f"Room {room.room_number} with {room.get_view_type_display()}",
                    'is_primary': True,
                    'display_order': 1,
                    'is_active': True
                }
            )
            if created:
                images_created += 1
        
        self.stdout.write(f'Created {images_created} room images.')

    def style_success(self, message):
        """Style success messages"""
        return f"\033[92m{message}\033[0m"
