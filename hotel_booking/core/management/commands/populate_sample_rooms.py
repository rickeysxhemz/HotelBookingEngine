from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal
from core.models import Hotel, RoomType, Room, RoomAmenity, RoomTypeAmenity, RoomImage
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Populate database with sample room data showcasing all new fields'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing room data before populating',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing room data...')
            RoomImage.objects.all().delete()
            RoomTypeAmenity.objects.all().delete()
            Room.objects.all().delete()
            RoomType.objects.all().delete()
            RoomAmenity.objects.all().delete()
            Hotel.objects.all().delete()

        self.stdout.write('Creating sample hotel and room data...')
        
        with transaction.atomic():
            # Create sample hotel
            hotel = self.create_sample_hotel()
            
            # Create sample amenities
            amenities = self.create_sample_amenities()
            
            # Create sample room types with comprehensive data
            room_types = self.create_sample_room_types(amenities)
            
            # Create sample rooms
            rooms = self.create_sample_rooms(hotel, room_types)
            
            # Create sample room images
            self.create_sample_room_images(rooms, room_types)

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created:\n'
                f'- 1 Hotel\n'
                f'- {len(amenities)} Amenities\n'
                f'- {len(room_types)} Room Types\n'
                f'- {len(rooms)} Rooms\n'
                f'- Sample room images'
            )
        )

    def create_sample_hotel(self):
        """Create a sample hotel"""
        hotel = Hotel.objects.create(
            name="Grand Plaza Hotel & Spa",
            description="A luxury 5-star hotel offering world-class amenities and exceptional service in the heart of the city.",
            address_line_1="123 Grand Avenue",
            address_line_2="Suite 100",
            city="New York",
            state="New York",
            postal_code="10001",
            country="United States",
            phone_number="+1-555-123-4567",
            email="reservations@grandplazahotel.com",
            website="https://www.grandplazahotel.com",
            star_rating=5,
            cancellation_policy="Free cancellation up to 24 hours before check-in. Late cancellations may incur charges.",
            pet_policy="Pets allowed with advance notice. Additional cleaning fee applies.",
            smoking_policy="Non-smoking property. Designated smoking areas available outdoors."
        )
        return hotel

    def create_sample_amenities(self):
        """Create sample room amenities"""
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
            amenity = RoomAmenity.objects.create(**amenity_data)
            amenities.append(amenity)
        
        return amenities

    def create_sample_room_types(self, amenities):
        """Create sample room types with comprehensive amenity configurations"""
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
            room_type = RoomType.objects.create(**rt_data)
            
            # Add amenities to room type
            for amenity_index in amenity_indices:
                if amenity_index < len(amenities):
                    RoomTypeAmenity.objects.create(
                        room_type=room_type,
                        amenity=amenities[amenity_index],
                        is_included=True,
                        additional_charge=Decimal("0.00") if not amenities[amenity_index].is_premium else Decimal("15.00")
                    )
            
            room_types.append(room_type)
        
        return room_types

    def create_sample_rooms(self, hotel, room_types):
        """Create sample rooms for each room type"""
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
            floors_needed = (config["count"] + 9) // 10  # Calculate floors needed
            
            for i in range(config["count"]):
                floor = config["start_floor"] + (i // 10)
                room_num = str(room_number + i)
                
                # Determine special features
                is_corner = (i % 10) in [0, 9]  # First and last rooms on each floor
                is_connecting = (i % 10) in [1, 2, 7, 8]  # Some middle rooms
                
                # Assign view type
                view_type = config["views"][i % len(config["views"])]
                
                # Create room
                room = Room.objects.create(
                    hotel=hotel,
                    room_type=room_type,
                    room_number=room_num,
                    floor=floor,
                    capacity=room_type.max_capacity,
                    base_price=config["base_price"],
                    view_type=view_type,
                    is_corner_room=is_corner,
                    is_connecting_room=is_connecting,
                    condition="excellent" if i % 5 == 0 else "very_good",
                    housekeeping_status="clean",
                    special_features=f"Corner room with panoramic {view_type} views" if is_corner else "",
                )
                
                rooms.append(room)
            
            room_number += config["count"]
        
        return rooms

    def create_sample_room_images(self, rooms, room_types):
        """Create sample room images"""
        # Sample image URLs (you would replace these with actual image URLs)
        sample_images = {
            "room_overview": "https://example.com/images/room-overview.jpg",
            "bed_area": "https://example.com/images/bed-area.jpg",
            "bathroom": "https://example.com/images/bathroom.jpg",
            "view": "https://example.com/images/room-view.jpg",
            "amenities": "https://example.com/images/amenities.jpg",
        }
        
        # Create images for room types
        for room_type in room_types:
            for i, (image_type, url) in enumerate(sample_images.items()):
                RoomImage.objects.create(
                    room_type=room_type,
                    image_url=url,
                    image_alt_text=f"{room_type.name} - {image_type.replace('_', ' ').title()}",
                    caption=f"Beautiful {image_type.replace('_', ' ')} in our {room_type.name}",
                    image_type=image_type,
                    is_primary=(i == 0),
                    display_order=i + 1,
                    is_active=True
                )
        
        # Create specific images for some sample rooms
        for i, room in enumerate(rooms[:10]):  # First 10 rooms
            RoomImage.objects.create(
                room=room,
                image_url=sample_images["room_overview"],
                image_alt_text=f"Room {room.room_number} overview",
                caption=f"Room {room.room_number} with {room.get_view_type_display()}",
                image_type="room_overview",
                is_primary=True,
                display_order=1,
                is_active=True
            )
