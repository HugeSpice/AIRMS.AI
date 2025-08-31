#!/usr/bin/env python3
"""
Debug Login Process
Tests the login process step by step to identify the issue
"""

import requests
import json
import time

# Configuration
BACKEND_URL = "http://localhost:8000"

def debug_login():
    print("🔍 Debugging Login Process")
    print("=" * 40)
    
    # Step 1: Create a test user
    timestamp = int(time.time())
    test_email = f"debuguser{timestamp}@example.com"
    test_password = "DebugPass123!"
    
    print(f"📝 Creating test user: {test_email}")
    
    registration_data = {
        "email": test_email,
        "password": test_password,
        "full_name": "Debug Test User"
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/v1/auth/register",
            json=registration_data
        )
        
        print(f"Registration Status: {response.status_code}")
        if response.status_code in [200, 201]:
            user_data = response.json()
            print(f"✅ User created: {user_data.get('id')}")
            print(f"User data: {json.dumps(user_data, indent=2)}")
        else:
            print(f"❌ Registration failed: {response.text}")
            return
            
    except Exception as e:
        print(f"❌ Registration error: {e}")
        return
    
    # Step 2: Try to login
    print(f"\n🔐 Attempting login for: {test_email}")
    
    login_data = {
        "email": test_email,
        "password": test_password
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/v1/auth/login",
            json=login_data
        )
        
        print(f"Login Status: {response.status_code}")
        print(f"Login Response: {response.text}")
        
        if response.status_code == 200:
            login_response = response.json()
            print(f"✅ Login successful!")
            print(f"Token: {login_response.get('access_token', '')[:20]}...")
            print(f"Token type: {login_response.get('token_type')}")
            print(f"Expires in: {login_response.get('expires_in')} seconds")
        else:
            print(f"❌ Login failed")
            
    except Exception as e:
        print(f"❌ Login error: {e}")
    
    # Step 3: Check user in database
    print(f"\n🔍 Checking user in database...")
    
    try:
        # Try to get user by email (this might not work without auth)
        response = requests.get(f"{BACKEND_URL}/api/v1/auth/me")
        print(f"Me endpoint status: {response.status_code}")
        print(f"Me endpoint response: {response.text}")
        
    except Exception as e:
        print(f"❌ Me endpoint error: {e}")

if __name__ == "__main__":
    debug_login()
