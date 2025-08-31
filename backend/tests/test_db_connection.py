image.png

#!/usr/bin/env python3
"""
Test Database Connection
Simple test to check if database connection is working
"""

import requests
import json

# Configuration
BACKEND_URL = "http://localhost:8000"

def test_db_connection():
    print("🔍 Testing Database Connection")
    print("=" * 40)
    
    # Test 1: Backend health
    try:
        response = requests.get(f"{BACKEND_URL}/health")
        print(f"Backend Health: {response.status_code}")
        if response.status_code == 200:
            health_data = response.json()
            print(f"Database Status: {health_data.get('database_status')}")
        else:
            print(f"Health check failed: {response.text}")
            return
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return
    
    # Test 2: Create a test user
    print(f"\n📝 Creating test user...")
    
    registration_data = {
        "email": "dbtest@example.com",
        "password": "TestPass123!",
        "full_name": "DB Test User"
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
        else:
            print(f"❌ Registration failed: {response.text}")
            return
            
    except Exception as e:
        print(f"❌ Registration error: {e}")
        return
    
    # Test 3: Try to create a risk log directly
    print(f"\n💾 Testing direct risk log creation...")
    
    try:
        # This should fail since we're not authenticated, but it will test the endpoint
        test_log_data = {
            "user_id": user_data.get('id'),
            "api_key_id": "test-key",
            "request_id": "test-request-123",
            "original_input": "Test input",
            "sanitized_input": "Test input",
            "llm_response": "Test response",
            "sanitized_response": "Test response",
            "risk_score": 5.0,
            "risks_detected": [{"type": "test", "score": 5.0}],
            "mitigation_applied": {"test": True},
            "processing_time_ms": 100,
            "llm_provider": "test",
            "model_used": "test-model",
            "tokens_used": 50
        }
        
        response = requests.post(
            f"{BACKEND_URL}/api/v1/analytics/logs",
            json=test_log_data
        )
        
        print(f"Direct log creation attempt: {response.status_code}")
        print(f"Response: {response.text}")
        
    except Exception as e:
        print(f"❌ Direct log creation error: {e}")

if __name__ == "__main__":
    test_db_connection()
