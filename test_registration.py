#!/usr/bin/env python3
"""
Test script for user registration functionality
"""

import requests
import json

# API base URL
BASE_URL = "http://localhost:8000"

def test_registration():
    """Test user registration"""
    
    # Test data
    test_user = {
        "username": "testuser123",
        "email": "test@example.com",
        "password": "TestPass123",
        "name": "Test User"
    }
    
    print("🧪 Testing user registration...")
    
    try:
        # Make registration request
        response = requests.post(
            f"{BASE_URL}/auth/register",
            json=test_user,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Registration successful!")
            print(f"📝 User ID: {data['user']['id']}")
            print(f"👤 Username: {data['user']['username']}")
            print(f"📧 Email: {data['user']['email']}")
            print(f"🔑 Token: {data['access_token'][:20]}...")
            print(f"💬 Message: {data['message']}")
            return True
        else:
            print(f"❌ Registration failed: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the API. Make sure the server is running on http://localhost:8000")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_duplicate_registration():
    """Test duplicate registration (should fail)"""
    
    test_user = {
        "username": "testuser123",
        "email": "test@example.com",
        "password": "TestPass123",
        "name": "Test User"
    }
    
    print("\n🧪 Testing duplicate registration...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/auth/register",
            json=test_user,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 400:
            print("✅ Correctly rejected duplicate registration!")
            print(f"📝 Error: {response.json()['detail']}")
            return True
        else:
            print(f"❌ Unexpected response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_invalid_registration():
    """Test registration with invalid data"""
    
    invalid_users = [
        {
            "username": "ab",  # Too short
            "email": "test2@example.com",
            "password": "TestPass123",
            "name": "Test User 2"
        },
        {
            "username": "testuser2",
            "email": "invalid-email",  # Invalid email
            "password": "TestPass123",
            "name": "Test User 2"
        },
        {
            "username": "testuser2",
            "email": "test2@example.com",
            "password": "weak",  # Weak password
            "name": "Test User 2"
        }
    ]
    
    print("\n🧪 Testing invalid registration data...")
    
    for i, user in enumerate(invalid_users, 1):
        print(f"\n📝 Test {i}: Invalid data")
        try:
            response = requests.post(
                f"{BASE_URL}/auth/register",
                json=user,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"📊 Status Code: {response.status_code}")
            
            if response.status_code == 422:
                print("✅ Correctly rejected invalid data!")
                errors = response.json()['detail']
                for error in errors:
                    print(f"   - {error['loc'][-1]}: {error['msg']}")
            else:
                print(f"❌ Unexpected response: {response.text}")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    print("🚀 Starting registration tests...\n")
    
    # Test valid registration
    success = test_registration()
    
    if success:
        # Test duplicate registration
        test_duplicate_registration()
        
        # Test invalid registration
        test_invalid_registration()
    
    print("\n✨ Registration tests completed!") 