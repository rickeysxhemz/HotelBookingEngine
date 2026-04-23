"""
Complete booking-engine seed — Abha-only.

Populates every domain table exposed by the API:
  - Hotel (single Abha property)
  - RoomType + RoomAmenity + RoomTypeAmenity
  - Room + RoomImage
  - Extra
  - SeasonalPricing
  - OfferCategory + Offer + OfferHighlight + OfferImage
  - RefundPolicy

Idempotent — keyed on natural identifiers, safe to re-run.

Run:
    docker compose exec -T web bash -c "cd /app/hotel_booking && python manage.py shell < seed_demo.py"
"""
from datetime import date, timedelta
from decimal import Decimal

from core.models import (
    Hotel,
    Room,
    RoomType,
    RoomAmenity,
    RoomTypeAmenity,
    RoomImage,
    Extra,
    SeasonalPricing,
)
from offers.models import Offer, OfferCategory, OfferHighlight, OfferImage
from bookings.models import RefundPolicy


# ---------------------------------------------------------------------------
# 1. Single hotel — Mar Grand Abha
# ---------------------------------------------------------------------------
HOTEL_DEFAULTS = {
    "name": "Mar Grand Abha",
    "description": (
        "Nestled at 2,200m in the Asir highlands, Mar Grand Abha blends "
        "traditional Saudi architecture with five-star amenities. Panoramic "
        "mountain views, cloud-forest gardens, and a temperate climate "
        "year-round."
    ),
    "address_line_1": "King Fahd Road",
    "address_line_2": "Al Muruj District",
    "city": "Abha",
    "state": "Asir",
    "postal_code": "62523",
    "country": "Saudi Arabia",
    "phone_number": "+966-17-234-5001",
    "email": "reservations@marhotels.sa",
    "website": "https://marhotels.sa",
    "star_rating": 5,
    "cancellation_policy": "Free cancellation up to 48 hours before check-in.",
    "pet_policy": "Small pets (<15kg) permitted with SAR 75 nightly charge.",
    "smoking_policy": "Non-smoking property. Designated outdoor areas available.",
    "is_active": True,
}


# ---------------------------------------------------------------------------
# 2. Room amenities (registry) — attached to room types via RoomTypeAmenity
# ---------------------------------------------------------------------------
ROOM_AMENITIES = [
    ("High-Speed Wi-Fi", "connectivity", False),
    ("Smart TV (55\")", "entertainment", False),
    ("Nespresso Machine", "in_room", True),
    ("Rainfall Shower", "bathroom", True),
    ("Plush Robes & Slippers", "bathroom", False),
    ("Mini Bar", "in_room", False),
    ("Digital Safe", "in_room", False),
    ("Work Desk", "in_room", False),
    ("Mountain View Balcony", "views", True),
    ("Air Conditioning", "climate", False),
    ("Heated Floors", "climate", True),
    ("Blackout Curtains", "in_room", False),
    ("Daily Housekeeping", "service", False),
    ("Turndown Service", "service", True),
]


# ---------------------------------------------------------------------------
# 3. Room types — detailed amenities flags + pricing scaffolding
# ---------------------------------------------------------------------------
ROOM_TYPES = [
    {
        "name": "Deluxe King",
        "category": "deluxe",
        "short_description": "King bed with mountain-view balcony and marble bath.",
        "description": (
            "Generous 35m² room featuring a king bed, blackout curtains, "
            "private balcony overlooking the Asir range, and a rainfall shower."
        ),
        "max_capacity": 2,
        "bed_type": "king",
        "bed_count": 1,
        "bathroom_count": 1,
        "room_size_sqm": 35,
        "room_size_sqft": 377,
        "has_wifi": True,
        "has_tv": True,
        "has_smart_tv": True,
        "has_streaming_service": True,
        "has_air_conditioning": True,
        "has_heating": True,
        "has_balcony": True,
        "has_minibar": True,
        "has_safe": True,
        "has_desk": True,
        "has_bathtub": False,
        "has_shower": True,
        "has_hairdryer": True,
        "has_toiletries": True,
        "has_towels": True,
        "has_bathrobes": True,
        "has_slippers": True,
        "has_coffee_maker": True,
        "has_tea_kettle": True,
        "has_refrigerator": True,
        "has_blackout_curtains": True,
        "has_soundproofing": True,
        "children_allowed": True,
        "max_children": 1,
        "extra_bed_available": True,
        "extra_bed_charge": Decimal("150.00"),
        "early_checkin_available": True,
        "late_checkout_available": True,
        "early_checkin_charge": Decimal("100.00"),
        "late_checkout_charge": Decimal("100.00"),
        "cancellation_policy": "Free cancellation up to 48 hours before check-in.",
    },
    {
        "name": "Family Suite",
        "category": "suite",
        "short_description": "Two bedrooms, lounge, kitchenette — perfect for families.",
        "description": (
            "Spacious 60m² suite with two queen bedrooms, separate living "
            "area, kitchenette, and dual bathrooms. Includes complimentary "
            "breakfast for up to four guests."
        ),
        "max_capacity": 4,
        "bed_type": "queen",
        "bed_count": 2,
        "bathroom_count": 2,
        "room_size_sqm": 60,
        "room_size_sqft": 645,
        "has_wifi": True,
        "has_tv": True,
        "has_smart_tv": True,
        "has_streaming_service": True,
        "has_air_conditioning": True,
        "has_heating": True,
        "has_kitchenette": True,
        "has_minibar": True,
        "has_safe": True,
        "has_desk": True,
        "has_seating_area": True,
        "has_shower": True,
        "has_bathtub": True,
        "has_hairdryer": True,
        "has_toiletries": True,
        "has_towels": True,
        "has_bathrobes": True,
        "has_slippers": True,
        "has_coffee_maker": True,
        "has_tea_kettle": True,
        "has_refrigerator": True,
        "has_microwave": True,
        "has_iron": True,
        "has_ironing_board": True,
        "has_blackout_curtains": True,
        "children_allowed": True,
        "max_children": 2,
        "infant_bed_available": True,
        "extra_bed_available": True,
        "extra_bed_charge": Decimal("150.00"),
        "early_checkin_available": True,
        "late_checkout_available": True,
        "early_checkin_charge": Decimal("100.00"),
        "late_checkout_charge": Decimal("150.00"),
        "cancellation_policy": "Free cancellation up to 72 hours before check-in.",
    },
    {
        "name": "Executive Twin",
        "category": "standard",
        "short_description": "Two twin beds and a dedicated work station.",
        "description": (
            "Business-traveller favourite: two twin beds, ergonomic work "
            "station, high-speed Wi-Fi, and access to the executive lounge."
        ),
        "max_capacity": 2,
        "bed_type": "twin",
        "bed_count": 2,
        "bathroom_count": 1,
        "room_size_sqm": 28,
        "room_size_sqft": 301,
        "has_wifi": True,
        "has_tv": True,
        "has_air_conditioning": True,
        "has_heating": True,
        "has_desk": True,
        "has_safe": True,
        "has_shower": True,
        "has_hairdryer": True,
        "has_toiletries": True,
        "has_towels": True,
        "has_coffee_maker": True,
        "has_tea_kettle": True,
        "has_blackout_curtains": True,
        "children_allowed": False,
        "early_checkin_available": True,
        "late_checkout_available": True,
        "early_checkin_charge": Decimal("75.00"),
        "late_checkout_charge": Decimal("75.00"),
        "cancellation_policy": "Free cancellation up to 24 hours before check-in.",
    },
    {
        "name": "Accessible Room",
        "category": "standard",
        "short_description": "Wheelchair-accessible room with roll-in shower.",
        "description": (
            "Fully accessible 32m² room with roll-in shower, grab bars, "
            "lowered fixtures, and hearing-assistance kit available on request."
        ),
        "max_capacity": 2,
        "bed_type": "queen",
        "bed_count": 1,
        "bathroom_count": 1,
        "room_size_sqm": 32,
        "room_size_sqft": 344,
        "has_wifi": True,
        "has_tv": True,
        "has_air_conditioning": True,
        "has_heating": True,
        "has_safe": True,
        "has_desk": True,
        "has_shower": True,
        "has_hairdryer": True,
        "has_toiletries": True,
        "has_towels": True,
        "has_bathrobes": True,
        "has_slippers": True,
        "has_coffee_maker": True,
        "has_tea_kettle": True,
        "has_refrigerator": True,
        "has_blackout_curtains": True,
        "is_accessible": True,
        "has_accessible_bathroom": True,
        "has_grab_bars": True,
        "has_roll_in_shower": True,
        "has_lowered_fixtures": True,
        "has_hearing_assistance": True,
        "children_allowed": True,
        "max_children": 1,
        "cancellation_policy": "Free cancellation up to 48 hours before check-in.",
    },
]


# Which registry amenities attach to which room type (by name):
ROOM_TYPE_AMENITY_MAP = {
    "Deluxe King": [
        ("High-Speed Wi-Fi", True, 0),
        ("Smart TV (55\")", True, 0),
        ("Nespresso Machine", True, 0),
        ("Rainfall Shower", True, 0),
        ("Plush Robes & Slippers", True, 0),
        ("Mini Bar", True, 0),
        ("Digital Safe", True, 0),
        ("Mountain View Balcony", True, 0),
        ("Air Conditioning", True, 0),
        ("Daily Housekeeping", True, 0),
        ("Turndown Service", True, 0),
    ],
    "Family Suite": [
        ("High-Speed Wi-Fi", True, 0),
        ("Smart TV (55\")", True, 0),
        ("Nespresso Machine", True, 0),
        ("Rainfall Shower", True, 0),
        ("Plush Robes & Slippers", True, 0),
        ("Mini Bar", True, 0),
        ("Digital Safe", True, 0),
        ("Work Desk", True, 0),
        ("Air Conditioning", True, 0),
        ("Heated Floors", True, 0),
        ("Daily Housekeeping", True, 0),
        ("Turndown Service", True, 0),
    ],
    "Executive Twin": [
        ("High-Speed Wi-Fi", True, 0),
        ("Smart TV (55\")", True, 0),
        ("Work Desk", True, 0),
        ("Digital Safe", True, 0),
        ("Air Conditioning", True, 0),
        ("Daily Housekeeping", True, 0),
    ],
    "Accessible Room": [
        ("High-Speed Wi-Fi", True, 0),
        ("Smart TV (55\")", True, 0),
        ("Air Conditioning", True, 0),
        ("Daily Housekeeping", True, 0),
        ("Digital Safe", True, 0),
    ],
}


# ---------------------------------------------------------------------------
# 4. Rooms — multiple units per room type
# ---------------------------------------------------------------------------
ROOM_LAYOUT = {
    "Accessible Room": {
        "floors": [1],
        "rooms_per_floor": 2,
        "base_price": Decimal("600.00"),
        "view_types": ["garden"],
    },
    "Executive Twin": {
        "floors": [2, 3],
        "rooms_per_floor": 3,
        "base_price": Decimal("520.00"),
        "view_types": ["city"],
    },
    "Deluxe King": {
        "floors": [4, 5, 6],
        "rooms_per_floor": 3,
        "base_price": Decimal("650.00"),
        "view_types": ["mountain", "city", "garden"],
    },
    "Family Suite": {
        "floors": [7, 8],
        "rooms_per_floor": 2,
        "base_price": Decimal("1100.00"),
        "view_types": ["mountain", "mountain"],
    },
}


# ---------------------------------------------------------------------------
# 5. Extras — hotel services (bookable add-ons)
# ---------------------------------------------------------------------------
EXTRAS = [
    {
        "name": "Breakfast Buffet",
        "description": "International breakfast buffet at Al Sarawat restaurant.",
        "price": Decimal("85.00"),
        "pricing_type": "per_person_per_night",
        "category": "dining",
        "max_quantity": 4,
    },
    {
        "name": "Airport Transfer (Private Sedan)",
        "description": "One-way private transfer between Abha Regional Airport and hotel.",
        "price": Decimal("180.00"),
        "pricing_type": "per_booking",
        "category": "transport",
        "max_quantity": 2,
    },
    {
        "name": "Executive Lounge Access",
        "description": "All-day lounge access with light food and beverages.",
        "price": Decimal("120.00"),
        "pricing_type": "per_person_per_night",
        "category": "experience",
        "max_quantity": 2,
    },
    {
        "name": "Spa Voucher (60 min)",
        "description": "60-minute signature massage at the Asir Spa.",
        "price": Decimal("350.00"),
        "pricing_type": "per_person",
        "category": "wellness",
        "max_quantity": 2,
    },
    {
        "name": "In-Room Dining Credit",
        "description": "SAR 200 credit toward room-service menu.",
        "price": Decimal("180.00"),
        "pricing_type": "per_booking",
        "category": "dining",
        "max_quantity": 1,
    },
    {
        "name": "Parking (Valet)",
        "description": "Valet parking with unlimited access.",
        "price": Decimal("50.00"),
        "pricing_type": "per_night",
        "category": "transport",
        "max_quantity": 1,
    },
]


# ---------------------------------------------------------------------------
# 6. Seasonal pricing — summer peak, winter low
# ---------------------------------------------------------------------------
TODAY = date.today()
SEASONS = [
    {
        "name": "Summer Peak (June-August)",
        "start_date": date(TODAY.year, 6, 1),
        "end_date": date(TODAY.year, 8, 31),
        "price_multiplier": Decimal("1.25"),
    },
    {
        "name": "Eid Al-Adha Holiday",
        "start_date": date(TODAY.year, 6, 15),
        "end_date": date(TODAY.year, 6, 22),
        "price_multiplier": Decimal("1.40"),
    },
    {
        "name": "Winter Low Season",
        "start_date": date(TODAY.year, 12, 1),
        "end_date": date(TODAY.year + 1, 2, 28),
        "price_multiplier": Decimal("0.85"),
    },
]


# ---------------------------------------------------------------------------
# 7. Offer categories + offers
# ---------------------------------------------------------------------------
OFFER_CATEGORIES = [
    {
        "name": "Seasonal",
        "slug": "seasonal",
        "description": "Limited-time seasonal packages tied to holidays and weather.",
        "color": "#B2571B",
        "is_active": True,
        "order": 1,
    },
    {
        "name": "Family",
        "slug": "family",
        "description": "Deals designed for families travelling with children.",
        "color": "#6B7A2F",
        "is_active": True,
        "order": 2,
    },
    {
        "name": "Business",
        "slug": "business",
        "description": "Corporate and executive-traveller savings.",
        "color": "#2F4A6B",
        "is_active": True,
        "order": 3,
    },
    {
        "name": "Wellness",
        "slug": "wellness",
        "description": "Spa, wellness, and longevity experiences.",
        "color": "#7B5EA7",
        "is_active": True,
        "order": 4,
    },
]


OFFERS = [
    {
        "name": "Abha Summer Mountain Escape",
        "slug": "abha-summer-mountain-escape",
        "category_slug": "seasonal",
        "short_description": "Beat the heat with 20% off in the cool Asir highlands.",
        "description": (
            "Escape the summer heat and enjoy 20% off room rates at Mar Grand "
            "Abha. Package includes daily breakfast, complimentary late "
            "check-out, and a scenic Al Soudah cable-car voucher for two."
        ),
        "offer_type": "percentage",
        "discount_type": "room_rate",
        "discount_percentage": Decimal("20.00"),
        "valid_from": date(TODAY.year, 6, 1),
        "valid_to": date(TODAY.year, 8, 31),
        "minimum_stay": 2,
        "is_featured": True,
        "is_combinable": False,
        "terms_and_conditions": (
            "Valid for stays between 1 June and 31 August. Not combinable with "
            "other promotions. Blackout dates apply during Eid Al-Adha."
        ),
        "highlights": [
            ("Daily breakfast included", "Full buffet at Al Sarawat restaurant.", 1),
            ("Complimentary late check-out", "Until 2:00 PM, subject to availability.", 2),
            ("Al Soudah cable-car voucher", "Two adult tickets included per stay.", 3),
            ("Free upgrade when available", "Room upgrade at check-in if inventory permits.", 4),
        ],
        "images": [
            ("https://images.unsplash.com/photo-1566073771259-6a8506099945?q=80&w=1600", True, "Hotel exterior"),
            ("https://images.unsplash.com/photo-1551882547-ff40c63fe5fa?q=80&w=1600", False, "Lounge"),
        ],
    },
    {
        "name": "Family Adventure Package",
        "slug": "family-adventure-package",
        "category_slug": "family",
        "short_description": "Suite stay with breakfast and kids' activities for two nights.",
        "description": (
            "Book our Family Suite for two nights or more and kids stay free. "
            "Includes breakfast for four, a guided hike to Habala Village, "
            "and unlimited access to the family pool and arcade."
        ),
        "offer_type": "package",
        "discount_type": "package_price",
        "package_price": Decimal("2499.00"),
        "valid_from": TODAY,
        "valid_to": TODAY + timedelta(days=180),
        "minimum_stay": 2,
        "is_featured": True,
        "is_combinable": False,
        "terms_and_conditions": (
            "Package rate is for up to 2 adults and 2 children under 12. "
            "Guided hike is weather-dependent; alternative indoor activity "
            "provided otherwise."
        ),
        "highlights": [
            ("Family Suite accommodation", "Two bedrooms, lounge, kitchenette.", 1),
            ("Breakfast for four", "Daily buffet breakfast for two adults and two children.", 2),
            ("Guided Habala Village hike", "Half-day guided nature excursion.", 3),
            ("Arcade credit SAR 100", "Per stay, redeemable at the kids' club arcade.", 4),
        ],
        "images": [
            ("https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?q=80&w=1600", True, "Family suite"),
        ],
    },
    {
        "name": "Executive Business Stay",
        "slug": "executive-business-stay",
        "category_slug": "business",
        "short_description": "Work away with airport transfer, lounge access, and early check-in.",
        "description": (
            "Designed for business travellers: Executive Twin room with "
            "executive-lounge access, complimentary airport transfer, and "
            "guaranteed early check-in/late check-out."
        ),
        "offer_type": "fixed_amount",
        "discount_type": "total_booking",
        "discount_amount": Decimal("200.00"),
        "valid_from": TODAY,
        "valid_to": TODAY + timedelta(days=365),
        "minimum_stay": 1,
        "is_featured": False,
        "is_combinable": True,
        "applies_friday": False,
        "applies_saturday": False,
        "terms_and_conditions": (
            "Weekdays only (Sunday-Thursday). Airport transfer subject to "
            "24-hour advance notice."
        ),
        "highlights": [
            ("Executive lounge access", "Full-day lounge with food & beverages.", 1),
            ("Complimentary airport transfer", "One-way private sedan.", 2),
            ("Guaranteed early check-in", "Check in from 11:00 AM.", 3),
            ("Late check-out", "Until 4:00 PM upon request.", 4),
        ],
        "images": [
            ("https://images.unsplash.com/photo-1590490360182-c33d57733427?q=80&w=1600", True, "Executive suite"),
        ],
    },
    {
        "name": "Asir Wellness Retreat",
        "slug": "asir-wellness-retreat",
        "category_slug": "wellness",
        "short_description": "Three-night spa-focused retreat with daily treatments.",
        "description": (
            "A three-night wellness escape with daily 60-minute spa treatments, "
            "yoga at sunrise, and a custom wellness menu at Al Sarawat."
        ),
        "offer_type": "package",
        "discount_type": "package_price",
        "package_price": Decimal("4999.00"),
        "valid_from": TODAY,
        "valid_to": TODAY + timedelta(days=365),
        "minimum_stay": 3,
        "is_featured": True,
        "is_combinable": False,
        "terms_and_conditions": (
            "Three-night minimum. Spa treatments are non-transferable and "
            "non-refundable. Wellness menu is available at Al Sarawat only."
        ),
        "highlights": [
            ("Daily 60-min spa treatment", "Choose from signature massage, facial, or body ritual.", 1),
            ("Sunrise yoga", "Daily class on the mountain terrace.", 2),
            ("Wellness dining", "Three meals a day from the custom wellness menu.", 3),
            ("Private hiking guide", "One guided mountain hike per stay.", 4),
        ],
        "images": [
            ("https://images.unsplash.com/photo-1540555700478-4be289fbecef?q=80&w=1600", True, "Spa"),
        ],
    },
    {
        "name": "Last-Minute Weekend",
        "slug": "last-minute-weekend",
        "category_slug": "seasonal",
        "short_description": "15% off when you book within 7 days of arrival.",
        "description": (
            "Spontaneous traveller? Book within 7 days of your arrival date "
            "and save 15% on any room type. Minimum one-night stay."
        ),
        "offer_type": "last_minute",
        "discount_type": "room_rate",
        "discount_percentage": Decimal("15.00"),
        "valid_from": TODAY,
        "valid_to": TODAY + timedelta(days=365),
        "minimum_stay": 1,
        "minimum_advance_booking": 0,
        "maximum_advance_booking": 7,
        "is_featured": False,
        "is_combinable": False,
        "terms_and_conditions": (
            "Must be booked within 7 days of arrival. Non-refundable; "
            "cancellation forfeits the full booking amount."
        ),
        "highlights": [
            ("15% off any room", "Applies to all room types.", 1),
            ("Flexible arrival", "Same-day bookings welcome.", 2),
        ],
        "images": [
            ("https://images.unsplash.com/photo-1571896349842-33c89424de2d?q=80&w=1600", True, "Last-minute"),
        ],
    },
]


# ---------------------------------------------------------------------------
# 8. Refund policy
# ---------------------------------------------------------------------------
REFUND_POLICY = {
    "free_cancellation_days": 2,
    "refund_schedule": {
        "2": 100,
        "1": 50,
        "0": 0,
    },
    "non_refundable_deposit_percentage": Decimal("10.00"),
    "policy_description": (
        "Free cancellation up to 48 hours before check-in. Between 48h and "
        "24h prior, 50% refund. Within 24h or no-show: no refund. A 10% "
        "service fee is non-refundable in all cases."
    ),
}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run():
    counts = {}

    # 1. Prune other hotels so search stays Abha-only.
    removed = Hotel.objects.exclude(name=HOTEL_DEFAULTS["name"]).delete()
    counts["pruned_hotels"] = removed[0] if removed else 0

    # 2. Hotel
    hotel, _ = Hotel.objects.update_or_create(
        name=HOTEL_DEFAULTS["name"],
        defaults=HOTEL_DEFAULTS,
    )
    counts["hotel"] = 1

    # 3. Room amenities registry
    amenity_map = {}
    for amenity_name, category, is_premium in ROOM_AMENITIES:
        obj, _ = RoomAmenity.objects.update_or_create(
            name=amenity_name,
            defaults={"category": category, "is_premium": is_premium},
        )
        amenity_map[amenity_name] = obj
    counts["room_amenities"] = len(amenity_map)

    # 4. Room types + their amenity links
    room_type_objs = {}
    for rt_spec in ROOM_TYPES:
        obj, _ = RoomType.objects.update_or_create(
            name=rt_spec["name"],
            defaults=rt_spec,
        )
        room_type_objs[rt_spec["name"]] = obj

        # Reset + recreate the M2M-through rows for this room type
        RoomTypeAmenity.objects.filter(room_type=obj).delete()
        for amenity_name, included, charge in ROOM_TYPE_AMENITY_MAP.get(rt_spec["name"], []):
            amenity = amenity_map.get(amenity_name)
            if not amenity:
                continue
            RoomTypeAmenity.objects.create(
                room_type=obj,
                amenity=amenity,
                is_included=included,
                additional_charge=Decimal(charge or 0),
            )
    counts["room_types"] = len(room_type_objs)

    # 5. Rooms — wipe existing rows first to avoid stale room-number collisions
    Room.objects.filter(hotel=hotel).delete()
    room_count = 0
    for rt_name, layout in ROOM_LAYOUT.items():
        rt = room_type_objs.get(rt_name)
        if not rt:
            continue
        for floor in layout["floors"]:
            for idx in range(layout["rooms_per_floor"]):
                view = layout["view_types"][idx % len(layout["view_types"])]
                room_number = f"{floor}{idx + 1:02d}"
                Room.objects.update_or_create(
                    hotel=hotel,
                    room_number=room_number,
                    defaults={
                        "room_type": rt,
                        "floor": floor,
                        "capacity": rt.max_capacity,
                        "base_price": layout["base_price"],
                        "view_type": view,
                        "is_active": True,
                        "condition": "excellent",
                        "housekeeping_status": "clean",
                    },
                )
                room_count += 1
    counts["rooms"] = room_count

    # 6. Room-type images (URL-based; image field expects a file, so we
    #    store display_order + caption. Skip if schema requires ImageField.)
    # RoomImage expects an actual image upload, so we simply skip it here.

    # 7. Extras
    for extra_spec in EXTRAS:
        Extra.objects.update_or_create(
            hotel=hotel,
            name=extra_spec["name"],
            defaults={**extra_spec, "is_active": True},
        )
    counts["extras"] = len(EXTRAS)

    # 8. Seasonal pricing (each season × each room type)
    seasonal_count = 0
    for rt in room_type_objs.values():
        for season in SEASONS:
            SeasonalPricing.objects.update_or_create(
                hotel=hotel,
                room_type=rt,
                name=season["name"],
                defaults={
                    "start_date": season["start_date"],
                    "end_date": season["end_date"],
                    "price_multiplier": season["price_multiplier"],
                    "is_active": True,
                },
            )
            seasonal_count += 1
    counts["seasonal_pricing"] = seasonal_count

    # 9. Offer categories
    category_map = {}
    for cat_spec in OFFER_CATEGORIES:
        obj, _ = OfferCategory.objects.update_or_create(
            slug=cat_spec["slug"],
            defaults=cat_spec,
        )
        category_map[cat_spec["slug"]] = obj
    counts["offer_categories"] = len(category_map)

    # 10. Offers + highlights (images skipped — ImageField requires real uploads)
    offer_count = 0
    highlight_count = 0
    for offer_spec in OFFERS:
        category = category_map.get(offer_spec["category_slug"])
        highlights = offer_spec.pop("highlights", [])
        images = offer_spec.pop("images", [])
        offer_spec.pop("category_slug", None)

        offer, _ = Offer.objects.update_or_create(
            slug=offer_spec["slug"],
            defaults={**offer_spec, "hotel": hotel, "category": category, "is_active": True},
        )
        offer_count += 1

        OfferHighlight.objects.filter(offer=offer).delete()
        for idx, (title, description, order) in enumerate(highlights, start=1):
            OfferHighlight.objects.create(
                offer=offer,
                title=title,
                description=description,
                order=order or idx,
            )
            highlight_count += 1

        # Skip OfferImage — requires real ImageField uploads, serializer
        # errors on empty .url. Wipe any existing rows from prior runs.
        OfferImage.objects.filter(offer=offer).delete()
        _ = images  # references suppressed; keep spec above for future uploads
    counts["offers"] = offer_count
    counts["offer_highlights"] = highlight_count

    # 11. Refund policy
    RefundPolicy.objects.update_or_create(
        hotel=hotel,
        defaults=REFUND_POLICY,
    )
    counts["refund_policy"] = 1

    print("\n=== Seed complete ===")
    for key, value in counts.items():
        print(f"  {key:<24} {value}")
    print()


run()
