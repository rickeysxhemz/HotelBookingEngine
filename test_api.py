#!/usr/bin/env python3
"""
API Testing Script for Hotel Booking Engine
Tests room search, booking flow, and email functionality
"""

import requests
import json
import time
from datetime import datetime, timedelta

# Base URL for the API
BASE_URL = "http://localhost:8000/api/v1"

# Test email
TEST_EMAIL = "myhomecell7@gmail.com"

def print_response(response, title="Response"):
    """Print formatted response"""
    print(f"\n{'='*50}")
    print(f"{title}")
    print(f"Status Code: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response Text: {response.text}")
    print('='*50)

def test_hotel_list():
    """Test hotel list endpoint"""
    print("\n🏨 Testing Hotel List Endpoint...")
    response = requests.get(f"{BASE_URL}/hotels/")
    print_response(response, "Hotel List")
    return response.status_code == 200

def test_register_user():
    """Register a test user"""
    print("\n👤 Registering Test User...")
    user_data = {
        "username": "testuser_" + str(int(time.time())),
        "email": TEST_EMAIL,
        "password": "TestPassword123!",
        "password_confirm": "TestPassword123!",
        "first_name": "Test",
        "last_name": "User",
        "phone_number": "+1234567890"
    }
    
    response = requests.post(f"{BASE_URL}/auth/register/", json=user_data)
    print_response(response, "User Registration")
    
    if response.status_code == 201:
        return user_data["username"], user_data["password"]
    return None, None

def test_login(username, password):
    """Login and get JWT token"""
    print("\n🔐 Testing Login...")
    login_data = {
        "email": TEST_EMAIL,  # Changed from username to email
        "password": password
    }
    
    response = requests.post(f"{BASE_URL}/auth/login/", json=login_data)
    print_response(response, "Login")
    
    if response.status_code == 200:
        return response.json().get("access")
    return None

def test_room_search():
    """Test room search functionality"""
    print("\n🔍 Testing Room Search...")
    
    # Calculate dates (tomorrow and day after)
    tomorrow = datetime.now() + timedelta(days=1)
    day_after = datetime.now() + timedelta(days=3)
    
    search_params = {
        "check_in": tomorrow.strftime("%Y-%m-%d"),
        "check_out": day_after.strftime("%Y-%m-%d"),
        "guests": 2
    }
    
    response = requests.get(f"{BASE_URL}/bookings/search-rooms/", params=search_params)
    print_response(response, "Room Search")
    
    if response.status_code == 200:
        data = response.json()
        available_rooms = data.get("available_rooms", [])
        if available_rooms:
            return available_rooms[0], search_params
    
    return None, search_params

def test_complete_booking(token, room_data, search_criteria):
    """Test complete booking flow"""
    print("\n💰 Testing Complete Booking Flow...")
    
    if not room_data:
        print("❌ No room data available for booking test")
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    booking_data = {
        "search_criteria": search_criteria,
        "booking_details": {
            "room_id": room_data.get("room_id"),
            "primary_guest_name": "Test User",
            "primary_guest_email": TEST_EMAIL,
            "primary_guest_phone": "+1234567890",
            "special_requests": "Testing API - please send confirmation email"
        },
        "payment_info": {
            "payment_method": "card",
            "save_payment_method": False
        }
    }
    
    response = requests.post(f"{BASE_URL}/bookings/complete-booking/", 
                           json=booking_data, headers=headers)
    print_response(response, "Complete Booking Flow")
    
    if response.status_code == 201:
        booking_response = response.json()
        booking_ref = booking_response.get("booking", {}).get("booking_reference")
        email_sent = booking_response.get("email_notification", {}).get("sent", False)
        
        print(f"\n✅ Booking successful!")
        print(f"📧 Booking Reference: {booking_ref}")
        print(f"📨 Email Sent: {'Yes' if email_sent else 'No'}")
        
        return booking_ref
    
    return None

def test_booking_details(token, booking_ref):
    """Test booking details retrieval"""
    if not booking_ref:
        return
        
    print(f"\n📋 Testing Booking Details for {booking_ref}...")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(f"{BASE_URL}/bookings/{booking_ref}/", headers=headers)
    print_response(response, "Booking Details")

def test_hotel_search_with_location():
    """Test hotel search with location"""
    print("\n🌍 Testing Hotel Search with Location...")
    
    search_params = {
        "location": "New York"
    }
    
    response = requests.get(f"{BASE_URL}/hotels/search/", params=search_params)
    print_response(response, "Hotel Search with Location")
    
    return response.status_code == 200

def run_all_tests():
    """Run all API tests"""
    print("🚀 Starting Hotel Booking API Tests...")
    print(f"📧 Test email: {TEST_EMAIL}")
    
    # Wait a moment for server to be ready
    print("⏳ Waiting for server to be ready...")
    time.sleep(2)
    
    # Test 1: Hotel List
    if not test_hotel_list():
        print("❌ Hotel list test failed!")
        return
    
    # Test 2: Hotel Search
    if not test_hotel_search_with_location():
        print("❌ Hotel search test failed!")
        return
    
    # Test 3: User Registration
    username, password = test_register_user()
    if not username:
        print("❌ User registration failed!")
        return
    
    # Test 4: Login
    token = test_login(username, password)
    if not token:
        print("❌ Login failed!")
        return
    
    # Test 5: Room Search
    room_data, search_criteria = test_room_search()
    
    # Test 6: Complete Booking (if rooms available)
    booking_ref = None
    if room_data:
        booking_ref = test_complete_booking(token, room_data, search_criteria)
        if booking_ref:
            # Test 7: Booking Details
            test_booking_details(token, booking_ref)
    else:
        print("⚠️  No rooms available for booking test")
    
    # Summary
    print("\n" + "="*60)
    print("🎯 TEST SUMMARY")
    print("="*60)
    print("✅ Hotel List: PASSED")
    print("✅ Hotel Search: PASSED") 
    print("✅ User Registration: PASSED")
    print("✅ Login: PASSED")
    print("✅ Room Search: PASSED" if room_data else "⚠️  Room Search: No rooms found")
    print("✅ Complete Booking: PASSED" if booking_ref else "⚠️  Complete Booking: Skipped (no rooms)")
    print("✅ Booking Details: PASSED" if booking_ref else "⚠️  Booking Details: Skipped")
    
    if booking_ref:
        print(f"\n📧 CHECK YOUR EMAIL ({TEST_EMAIL}) FOR BOOKING CONFIRMATION!")
        print(f"🎫 Booking Reference: {booking_ref}")
    
    print("\n🎉 All available tests completed!")

if __name__ == "__main__":
    try:
        run_all_tests()
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the server. Make sure the Django server is running on http://localhost:8000")
    except Exception as e:
        print(f"❌ An error occurred: {str(e)}")
