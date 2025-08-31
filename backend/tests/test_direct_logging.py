#!/usr/bin/env python3
"""
Test Direct Logging
Tests the logging function directly to see if it works
"""

import requests
import json
import time

# Configuration
BACKEND_URL = "http://localhost:8000"

def test_direct_logging():
    print("🔍 Testing Direct Logging")
    print("=" * 40)
    
    # Step 1: Create a test user
    timestamp = int(time.time())
    test_email = f"logtestuser{timestamp}@example.com"
    test_password = "LogTest123!"
    
    print(f"📝 Creating test user: {test_email}")
    
    registration_data = {
        "email": test_email,
        "password": test_password,
        "full_name": "Log Test User"
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/v1/auth/register",
            json=registration_data
        )
        
        if response.status_code in [200, 201]:
            user_data = response.json()
            user_id = user_data.get('id')
            print(f"✅ User created: {user_id}")
        else:
            print(f"❌ Registration failed: {response.text}")
            return
            
    except Exception as e:
        print(f"❌ Registration error: {e}")
        return
    
    # Step 2: Login to get JWT token
    print(f"\n🔐 Logging in...")
    
    login_data = {
        "email": test_email,
        "password": test_password
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/v1/auth/login",
            json=login_data
        )
        
        if response.status_code == 200:
            login_response = response.json()
            auth_token = login_response.get('access_token')
            print(f"✅ Login successful!")
        else:
            print(f"❌ Login failed: {response.text}")
            return
            
    except Exception as e:
        print(f"❌ Login error: {e}")
        return
    
    # Step 3: Create API key
    print(f"\n🔑 Creating API key...")
    
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }
    
    api_key_data = {
        "key_name": "Test Logging Key",
        "permissions": ["chat.completions"],
        "usage_limit": 1000,
        "expires_at": None
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/v1/api-keys",
            json=api_key_data,
            headers=headers
        )
        
        if response.status_code == 200:
            key_response = response.json()
            api_key = key_response.get("api_key")
            print(f"✅ API key created: {api_key[:20]}...")
        else:
            print(f"❌ API key creation failed: {response.text}")
            return
            
    except Exception as e:
        print(f"❌ API key creation error: {e}")
        return
    
    # Step 4: Test chat completion
    print(f"\n💬 Testing chat completion...")
    
    chat_headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    chat_data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": "Hello, this is a test message"}],
        "enable_risk_detection": True,
        "max_risk_score": 6.0
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/v1/chat/completions",
            json=chat_data,
            headers=chat_headers
        )
        
        if response.status_code == 200:
            print(f"✅ Chat completion successful!")
            chat_response = response.json()
            print(f"Response: {chat_response.get('choices', [{}])[0].get('message', {}).get('content', '')[:100]}...")
        else:
            print(f"❌ Chat completion failed: {response.status_code}, {response.text}")
            return
            
    except Exception as e:
        print(f"❌ Chat completion error: {e}")
        return
    
    # Step 5: Wait and check logs
    print(f"\n⏳ Waiting for logs to be processed...")
    time.sleep(5)
    
    print(f"\n📊 Checking risk logs...")
    
    try:
        response = requests.get(
            f"{BACKEND_URL}/api/v1/analytics/logs?limit=5",
            headers=headers
        )
        
        if response.status_code == 200:
            logs = response.json()
            if logs and len(logs) > 0:
                print(f"✅ Found {len(logs)} risk logs!")
                for i, log in enumerate(logs[:3]):
                    print(f"   Log {i+1}: Risk Score {log.get('risk_score', 'N/A')}, Created: {log.get('created_at', 'N/A')}")
            else:
                print(f"❌ No risk logs found")
                print(f"Response: {response.text}")
        else:
            print(f"❌ Failed to get logs: {response.status_code}, {response.text}")
            
    except Exception as e:
        print(f"❌ Log retrieval error: {e}")

if __name__ == "__main__":
    test_direct_logging()
