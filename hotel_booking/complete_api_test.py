#!/usr/bin/env python3
"""
Hotel Booking Engine - Complete API Test Suite
==============================================

This script tests all API endpoints of the Hotel Booking Engine with actual HTTP requests.
It verifies the complete booking flow from user registration to booking completion.

Requirements:
- Hotel Booking Engine server running on http://127.0.0.1:8000/
- requests library: pip install requests

Usage:
    python complete_api_test.py

Author: Hotel Maar Development Team
Date: July 26, 2025
"""

import requests
import json
import time
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

class Colors:
    """Terminal colors for output formatting"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class HotelBookingAPITester:
    """Complete API test suite for Hotel Booking Engine"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.access_token = None
        self.refresh_token = None
        self.user_data = {}
        self.hotel_id = None
        self.booking_reference = None
        self.test_results = []
        
    def log(self, message: str, color: str = Colors.OKBLUE):
        """Log message with color"""
        print(f"{color}{message}{Colors.ENDC}")
        
    def log_success(self, message: str):
        """Log success message"""
        self.log(f"✅ {message}", Colors.OKGREEN)
        
    def log_error(self, message: str):
        """Log error message"""
        self.log(f"❌ {message}", Colors.FAIL)
        
    def log_warning(self, message: str):
        """Log warning message"""
        self.log(f"⚠️  {message}", Colors.WARNING)
        
    def log_info(self, message: str):
        """Log info message"""
        self.log(f"ℹ️  {message}", Colors.OKCYAN)
        
    def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                    authenticated: bool = False, expected_status: int = 200) -> Dict[str, Any]:
        """Make HTTP request and return response"""
        url = f"{self.base_url}{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if authenticated and self.access_token:
            headers['Authorization'] = f'Bearer {self.access_token}'
            
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, headers=headers)
            elif method.upper() == 'POST':
                response = self.session.post(url, headers=headers, json=data)
            elif method.upper() == 'PATCH':
                response = self.session.patch(url, headers=headers, json=data)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
                
            # Log request details
            self.log_info(f"{method.upper()} {endpoint} -> {response.status_code}")
            
            if response.status_code == expected_status:
                self.test_results.append({'endpoint': endpoint, 'status': 'PASS'})
                return response.json() if response.content else {}
            else:
                error_msg = f"Expected {expected_status}, got {response.status_code}"
                if response.content:
                    try:
                        error_data = response.json()
                        error_msg += f" - {error_data}"
                    except:
                        error_msg += f" - {response.text}"
                self.log_error(f"{endpoint}: {error_msg}")
                self.test_results.append({'endpoint': endpoint, 'status': 'FAIL', 'error': error_msg})
                return {}
                
        except Exception as e:
            error_msg = f"Request failed: {str(e)}"
            self.log_error(f"{endpoint}: {error_msg}")
            self.test_results.append({'endpoint': endpoint, 'status': 'ERROR', 'error': error_msg})
            return {}
    
    def test_user_registration(self):
        """Test user registration endpoint"""
        self.log(f"\n{Colors.HEADER}{'='*60}")
        self.log("🏨 TESTING USER REGISTRATION", Colors.HEADER)
        self.log(f"{'='*60}{Colors.ENDC}")
        
        # Generate unique email and username for testing
        import random
        random_suffix = random.randint(1000, 9999)
        
        registration_data = {
            "email": f"john.doe.{random_suffix}@example.com",
            "username": f"johndoe{random_suffix}",
            "first_name": "John",
            "last_name": "Doe",
            "phone_number": "+1234567890",
            "password": "TestPass123!",
            "password_confirm": "TestPass123!"
        }
        
        response = self.make_request('POST', '/api/accounts/register/', 
                                   registration_data, expected_status=201)
        
        if response:
            self.user_data = response.get('user', {})
            self.registration_email = registration_data["email"]
            self.log_success(f"User registered: {self.user_data.get('full_name')}")
            self.log_info(f"User ID: {self.user_data.get('id')}")
            self.log_info(f"Email: {self.registration_email}")
        else:
            self.log_error("Failed to register user")
            
    def test_user_login(self):
        """Test user login endpoint"""
        self.log(f"\n{Colors.HEADER}{'='*60}")
        self.log("🔐 TESTING USER LOGIN", Colors.HEADER)
        self.log(f"{'='*60}{Colors.ENDC}")
        
        login_data = {
            "email": getattr(self, 'registration_email', "john.doe@example.com"),
            "password": "TestPass123!"
        }
        
        response = self.make_request('POST', '/api/accounts/login/', login_data)
        
        if response:
            tokens = response.get('tokens', {})
            self.access_token = tokens.get('access')
            self.refresh_token = tokens.get('refresh')
            user_info = response.get('user', {})
            
            self.log_success(f"Login successful: {user_info.get('full_name')}")
            self.log_info(f"Access token received: {self.access_token[:20]}...")
            self.log_info(f"Refresh token received: {self.refresh_token[:20]}...")
        else:
            self.log_error("Failed to login")
            
    def test_user_profile(self):
        """Test user profile endpoint"""
        self.log(f"\n{Colors.HEADER}{'='*60}")
        self.log("👤 TESTING USER PROFILE", Colors.HEADER)
        self.log(f"{'='*60}{Colors.ENDC}")
        
        response = self.make_request('GET', '/api/accounts/profile/', authenticated=True)
        
        if response:
            self.log_success(f"Profile retrieved: {response.get('full_name')}")
            self.log_info(f"Email: {response.get('email')}")
            self.log_info(f"Member since: {response.get('date_joined')}")
        else:
            self.log_error("Failed to get user profile")
            
    def test_hotels_list(self):
        """Test hotels list endpoint"""
        self.log(f"\n{Colors.HEADER}{'='*60}")
        self.log("🏨 TESTING HOTELS LIST", Colors.HEADER)
        self.log(f"{'='*60}{Colors.ENDC}")
        
        response = self.make_request('GET', '/api/core/hotels/')
        
        if response and 'results' in response and len(response['results']) > 0:
            hotels = response['results']
            hotel = hotels[0]
            self.hotel_id = hotel.get('id')
            self.log_success(f"Hotels retrieved: {len(hotels)} hotels found")
            self.log_info(f"Hotel: {hotel.get('name')}")
            self.log_info(f"Rating: {hotel.get('star_rating')} stars")
            self.log_info(f"Address: {hotel.get('full_address')}")
        else:
            self.log_error("Failed to get hotels list or no hotels found")
            
    def test_hotel_details(self):
        """Test hotel details endpoint"""
        if not self.hotel_id:
            self.log_warning("Skipping hotel details test - no hotel ID available")
            return
            
        self.log(f"\n{Colors.HEADER}{'='*60}")
        self.log("🏨 TESTING HOTEL DETAILS", Colors.HEADER)
        self.log(f"{'='*60}{Colors.ENDC}")
        
        response = self.make_request('GET', f'/api/core/hotels/{self.hotel_id}/')
        
        if response:
            self.log_success(f"Hotel details retrieved: {response.get('name')}")
            self.log_info(f"Total rooms: {response.get('total_rooms')}")
            self.log_info(f"Check-in time: {response.get('check_in_time')}")
            self.log_info(f"Check-out time: {response.get('check_out_time')}")
            
            room_types = response.get('room_types', [])
            self.log_info(f"Room types available: {len(room_types)}")
            for rt in room_types:
                self.log_info(f"  - {rt.get('name')}: {rt.get('max_capacity')} guests")
        else:
            self.log_error("Failed to get hotel details")
            
    def test_hotel_room_types(self):
        """Test hotel room types endpoint"""
        if not self.hotel_id:
            self.log_warning("Skipping room types test - no hotel ID available")
            return
            
        self.log(f"\n{Colors.HEADER}{'='*60}")
        self.log("🛏️  TESTING HOTEL ROOM TYPES", Colors.HEADER)
        self.log(f"{'='*60}{Colors.ENDC}")
        
        response = self.make_request('GET', f'/api/core/hotels/{self.hotel_id}/room-types/')
        
        if response:
            room_types = response.get('room_types', [])
            self.log_success(f"Room types retrieved: {len(room_types)} types")
            for rt in room_types:
                self.log_info(f"  - {rt.get('name')}: ${rt.get('price_range', {}).get('min_price')}-${rt.get('price_range', {}).get('max_price')}")
                self.log_info(f"    Capacity: {rt.get('max_capacity')} guests, Available: {rt.get('available_rooms')} rooms")
        else:
            self.log_error("Failed to get hotel room types")
            
    def test_hotel_amenities(self):
        """Test hotel amenities endpoint"""
        if not self.hotel_id:
            self.log_warning("Skipping amenities test - no hotel ID available")
            return
            
        self.log(f"\n{Colors.HEADER}{'='*60}")
        self.log("🎯 TESTING HOTEL AMENITIES", Colors.HEADER)
        self.log(f"{'='*60}{Colors.ENDC}")
        
        response = self.make_request('GET', f'/api/core/hotels/{self.hotel_id}/amenities/')
        
        if response:
            room_amenities = response.get('room_amenities', [])
            hotel_services = response.get('hotel_services', {})
            
            self.log_success(f"Amenities retrieved")
            self.log_info(f"Room amenities: {', '.join(room_amenities)}")
            
            for category, services in hotel_services.items():
                self.log_info(f"{category} services: {len(services)} available")
                for service in services:
                    self.log_info(f"  - {service.get('name')}: ${service.get('price')} {service.get('pricing_type')}")
        else:
            self.log_error("Failed to get hotel amenities")
            
    def test_room_search(self):
        """Test room search endpoint"""
        if not self.hotel_id:
            self.log_warning("Skipping room search test - no hotel ID available")
            return
            
        self.log(f"\n{Colors.HEADER}{'='*60}")
        self.log("🔍 TESTING ROOM SEARCH", Colors.HEADER)
        self.log(f"{'='*60}{Colors.ENDC}")
        
        # Search for 3 guests to test multi-room solutions
        search_data = {
            "check_in": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
            "check_out": (datetime.now() + timedelta(days=9)).strftime("%Y-%m-%d"),
            "guests": 3,
            "hotel_id": self.hotel_id,
            "max_price": "1000.00"
        }
        
        response = self.make_request('POST', '/api/bookings/search/', search_data)
        
        if response:
            results = response.get('results', [])
            search_params = response.get('search_params', {})
            
            self.log_success(f"Room search completed")
            self.log_info(f"Search for {search_params.get('guests')} guests, {search_params.get('nights')} nights")
            self.log_info(f"Dates: {search_params.get('check_in')} to {search_params.get('check_out')}")
            
            if results:
                hotel_result = results[0]
                room_combinations = hotel_result.get('room_combinations', [])
                available_extras = hotel_result.get('available_extras', [])
                
                self.log_info(f"Available room combinations: {len(room_combinations)}")
                for i, combo in enumerate(room_combinations):
                    combo_type = combo.get('type')
                    total_price = combo.get('total_price')
                    room_count = combo.get('room_count')
                    
                    self.log_info(f"  Option {i+1}: {combo_type} - {room_count} room(s) - ${total_price}")
                    
                self.log_info(f"Available extras: {len(available_extras)}")
                for extra in available_extras:
                    self.log_info(f"  - {extra.get('name')}: ${extra.get('price')} {extra.get('pricing_type')}")
                    
                # Store first room for booking test
                if room_combinations:
                    first_combo = room_combinations[0]
                    if first_combo.get('rooms'):
                        self.test_room_id = first_combo['rooms'][0].get('id')
                        self.log_info(f"Selected room for booking: {first_combo['rooms'][0].get('room_number')}")
            else:
                self.log_warning("No rooms available for the search criteria")
        else:
            self.log_error("Failed to search rooms")
            
    def test_create_booking(self):
        """Test create booking endpoint"""
        if not hasattr(self, 'test_room_id') or not self.test_room_id:
            self.log_warning("Skipping booking creation test - no room ID available")
            return
            
        self.log(f"\n{Colors.HEADER}{'='*60}")
        self.log("📝 TESTING BOOKING CREATION", Colors.HEADER)
        self.log(f"{'='*60}{Colors.ENDC}")
        
        booking_data = {
            "room_id": self.test_room_id,
            "check_in": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
            "check_out": (datetime.now() + timedelta(days=9)).strftime("%Y-%m-%d"),
            "guests": 2,
            "primary_guest_name": "John Doe",
            "primary_guest_email": "john.doe@example.com",
            "primary_guest_phone": "+1234567890",
            "special_requests": "Ground floor room preferred",
            "extras_data": [],
            "additional_guests_data": [
                {
                    "first_name": "Jane",
                    "last_name": "Doe",
                    "age_group": "adult"
                }
            ]
        }
        
        response = self.make_request('POST', '/api/bookings/create/', 
                                   booking_data, authenticated=True, expected_status=201)
        
        if response:
            booking = response.get('booking', {})
            self.booking_reference = booking.get('booking_reference')
            
            self.log_success(f"Booking created successfully")
            self.log_info(f"Booking reference: {self.booking_reference}")
            self.log_info(f"Status: {booking.get('status')}")
            self.log_info(f"Total price: ${booking.get('total_price')}")
            self.log_info(f"Room: {booking.get('room', {}).get('room_number')}")
            
            # Display price breakdown
            price_breakdown = booking.get('price_breakdown', {})
            if price_breakdown:
                self.log_info("Price breakdown:")
                self.log_info(f"  Room: ${price_breakdown.get('room_price')}")
                self.log_info(f"  Extras: ${price_breakdown.get('extras_price')}")
                self.log_info(f"  Tax: ${price_breakdown.get('tax_amount')}")
                self.log_info(f"  Total: ${price_breakdown.get('total_price')}")
        else:
            self.log_error("Failed to create booking")
            
    def test_list_user_bookings(self):
        """Test list user bookings endpoint"""
        self.log(f"\n{Colors.HEADER}{'='*60}")
        self.log("📋 TESTING USER BOOKINGS LIST", Colors.HEADER)
        self.log(f"{'='*60}{Colors.ENDC}")
        
        response = self.make_request('GET', '/api/bookings/', authenticated=True)
        
        if response:
            results = response.get('results', [])
            count = response.get('count', 0)
            
            self.log_success(f"User bookings retrieved: {count} total bookings")
            
            for booking in results:
                self.log_info(f"  - {booking.get('booking_reference')}: {booking.get('status')}")
                self.log_info(f"    {booking.get('check_in')} to {booking.get('check_out')} - ${booking.get('total_price')}")
        else:
            self.log_error("Failed to get user bookings")
            
    def test_booking_details(self):
        """Test booking details endpoint"""
        if not self.booking_reference:
            self.log_warning("Skipping booking details test - no booking reference available")
            return
            
        self.log(f"\n{Colors.HEADER}{'='*60}")
        self.log("📄 TESTING BOOKING DETAILS", Colors.HEADER)
        self.log(f"{'='*60}{Colors.ENDC}")
        
        response = self.make_request('GET', f'/api/bookings/{self.booking_reference}/', authenticated=True)
        
        if response:
            self.log_success(f"Booking details retrieved: {response.get('booking_reference')}")
            self.log_info(f"Status: {response.get('status')}")
            self.log_info(f"Guests: {response.get('guests')}")
            self.log_info(f"Room: {response.get('room', {}).get('room_number')}")
            self.log_info(f"Check-in: {response.get('check_in')}")
            self.log_info(f"Check-out: {response.get('check_out')}")
            
            # Show additional guests
            additional_guests = response.get('additional_guests', [])
            if additional_guests:
                self.log_info(f"Additional guests: {len(additional_guests)}")
                for guest in additional_guests:
                    self.log_info(f"  - {guest.get('first_name')} {guest.get('last_name')} ({guest.get('age_group')})")
                    
            # Show booking history
            history = response.get('history', [])
            if history:
                self.log_info(f"Booking history: {len(history)} events")
                for event in history[-3:]:  # Show last 3 events
                    self.log_info(f"  - {event.get('action')}: {event.get('description')}")
        else:
            self.log_error("Failed to get booking details")
            
    def test_booking_history(self):
        """Test booking history endpoint"""
        if not self.booking_reference:
            self.log_warning("Skipping booking history test - no booking reference available")
            return
            
        self.log(f"\n{Colors.HEADER}{'='*60}")
        self.log("📜 TESTING BOOKING HISTORY", Colors.HEADER)
        self.log(f"{'='*60}{Colors.ENDC}")
        
        response = self.make_request('GET', f'/api/bookings/{self.booking_reference}/history/', authenticated=True)
        
        if response:
            history = response.get('history', [])
            self.log_success(f"Booking history retrieved: {len(history)} events")
            
            for event in history:
                self.log_info(f"  - {event.get('timestamp')}: {event.get('action')}")
                self.log_info(f"    {event.get('description')} (by {event.get('performed_by')})")
        else:
            self.log_error("Failed to get booking history")
            
    def test_update_booking(self):
        """Test update booking endpoint"""
        if not self.booking_reference:
            self.log_warning("Skipping booking update test - no booking reference available")
            return
            
        self.log(f"\n{Colors.HEADER}{'='*60}")
        self.log("✏️  TESTING BOOKING UPDATE", Colors.HEADER)
        self.log(f"{'='*60}{Colors.ENDC}")
        
        update_data = {
            "special_requests": "Updated: Please provide extra towels and late check-in"
        }
        
        response = self.make_request('PATCH', f'/api/bookings/{self.booking_reference}/update/', 
                                   update_data, authenticated=True)
        
        if response:
            booking = response.get('booking', {})
            self.log_success(f"Booking updated successfully")
            self.log_info(f"New special requests: {booking.get('special_requests')}")
        else:
            self.log_error("Failed to update booking")
            
    def test_token_refresh(self):
        """Test token refresh endpoint"""
        if not self.refresh_token:
            self.log_warning("Skipping token refresh test - no refresh token available")
            return
            
        self.log(f"\n{Colors.HEADER}{'='*60}")
        self.log("🔄 TESTING TOKEN REFRESH", Colors.HEADER)
        self.log(f"{'='*60}{Colors.ENDC}")
        
        refresh_data = {
            "refresh": self.refresh_token
        }
        
        response = self.make_request('POST', '/api/accounts/token/refresh/', refresh_data)
        
        if response:
            new_access_token = response.get('access')
            self.access_token = new_access_token
            self.log_success(f"Token refreshed successfully")
            self.log_info(f"New access token: {new_access_token[:20]}...")
        else:
            self.log_error("Failed to refresh token")
            
    def test_logout(self):
        """Test user logout endpoint"""
        if not self.refresh_token:
            self.log_warning("Skipping logout test - no refresh token available")
            return
            
        self.log(f"\n{Colors.HEADER}{'='*60}")
        self.log("🚪 TESTING USER LOGOUT", Colors.HEADER)
        self.log(f"{'='*60}{Colors.ENDC}")
        
        logout_data = {
            "refresh": self.refresh_token
        }
        
        response = self.make_request('POST', '/api/accounts/logout/', 
                                   logout_data, authenticated=True)
        
        if response:
            self.log_success("User logged out successfully")
            self.access_token = None
            self.refresh_token = None
        else:
            self.log_error("Failed to logout user")
            
    def run_all_tests(self):
        """Run all API tests"""
        self.log(f"{Colors.BOLD}{Colors.HEADER}")
        self.log("🏨 HOTEL BOOKING ENGINE - COMPLETE API TEST SUITE")
        self.log("=" * 80)
        self.log(f"Testing API at: {self.base_url}")
        self.log(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.log(f"{'=' * 80}{Colors.ENDC}")
        
        # Test sequence
        test_methods = [
            self.test_user_registration,
            self.test_user_login,
            self.test_user_profile,
            self.test_hotels_list,
            self.test_hotel_details,
            self.test_hotel_room_types,
            self.test_hotel_amenities,
            self.test_room_search,
            self.test_create_booking,
            self.test_list_user_bookings,
            self.test_booking_details,
            self.test_booking_history,
            self.test_update_booking,
            self.test_token_refresh,
            self.test_logout
        ]
        
        # Run tests
        for test_method in test_methods:
            try:
                test_method()
                time.sleep(0.5)  # Small delay between tests
            except Exception as e:
                self.log_error(f"Test {test_method.__name__} failed with exception: {str(e)}")
                
        # Test summary
        self.print_test_summary()
        
    def print_test_summary(self):
        """Print test results summary"""
        self.log(f"\n{Colors.BOLD}{Colors.HEADER}")
        self.log("📊 TEST RESULTS SUMMARY")
        self.log("=" * 80)
        
        passed = len([r for r in self.test_results if r['status'] == 'PASS'])
        failed = len([r for r in self.test_results if r['status'] == 'FAIL'])
        errors = len([r for r in self.test_results if r['status'] == 'ERROR'])
        total = len(self.test_results)
        
        self.log(f"Total Tests: {total}")
        self.log(f"Passed: {passed}", Colors.OKGREEN)
        self.log(f"Failed: {failed}", Colors.FAIL if failed > 0 else Colors.OKGREEN)
        self.log(f"Errors: {errors}", Colors.FAIL if errors > 0 else Colors.OKGREEN)
        
        success_rate = (passed / total * 100) if total > 0 else 0
        self.log(f"Success Rate: {success_rate:.1f}%")
        
        # Show failed tests
        failed_tests = [r for r in self.test_results if r['status'] in ['FAIL', 'ERROR']]
        if failed_tests:
            self.log(f"\n{Colors.FAIL}Failed Tests:")
            for test in failed_tests:
                self.log(f"  ❌ {test['endpoint']}: {test.get('error', 'Unknown error')}")
                
        self.log(f"\n{'=' * 80}")
        self.log(f"Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if success_rate >= 90:
            self.log("🎉 EXCELLENT! Hotel Booking Engine API is working great!", Colors.OKGREEN)
        elif success_rate >= 70:
            self.log("✅ GOOD! Most API endpoints are working correctly.", Colors.WARNING)
        else:
            self.log("⚠️  NEEDS ATTENTION! Several API endpoints have issues.", Colors.FAIL)
            
        self.log(f"{'=' * 80}{Colors.ENDC}")

def main():
    """Main function to run API tests"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Hotel Booking Engine API Test Suite')
    parser.add_argument('--url', default='http://127.0.0.1:8000', 
                       help='Base URL of the API (default: http://127.0.0.1:8000)')
    parser.add_argument('--check-server', action='store_true',
                       help='Check if server is running before tests')
    
    args = parser.parse_args()
    
    tester = HotelBookingAPITester(args.url)
    
    # Check if server is running
    if args.check_server:
        try:
            response = requests.get(f"{args.url}/api/core/hotels/", timeout=5)
            tester.log_success(f"Server is running at {args.url}")
        except requests.exceptions.RequestException:
            tester.log_error(f"Server is not running at {args.url}")
            tester.log_info("Please start the Django development server:")
            tester.log_info("cd hotel_booking && python manage.py runserver")
            sys.exit(1)
    
    # Run all tests
    tester.run_all_tests()

if __name__ == "__main__":
    main()
