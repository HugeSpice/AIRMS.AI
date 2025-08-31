#!/usr/bin/env python3
"""
Frontend-Backend Integration Test Script
Tests the connection between frontend and backend APIs
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"

def test_backend_health():
    """Test backend health endpoint"""
    print("🔍 Testing Backend Health...")
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Backend is healthy!")
            print(f"   Status: {data.get('status')}")
            print(f"   Database: {data.get('database_status')}")
            print(f"   Version: {data.get('version')}")
            return True
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Backend connection failed: {e}")
        return False

def test_frontend_access():
    """Test frontend accessibility"""
    print("\n🔍 Testing Frontend Access...")
    try:
        response = requests.get(FRONTEND_URL, timeout=5)
        if response.status_code == 200:
            print(f"✅ Frontend is accessible!")
            print(f"   Status: {response.status_code}")
            print(f"   Content Length: {len(response.content)} bytes")
            return True
        else:
            print(f"❌ Frontend access failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Frontend connection failed: {e}")
        return False

def test_backend_apis():
    """Test backend API endpoints (without authentication)"""
    print("\n🔍 Testing Backend APIs...")
    
    # Test endpoints that should require authentication
    endpoints = [
        "/api/v1/analytics/statistics?days=7",
        "/api/v1/analytics/dashboard",
        "/api/v1/api-keys",
        "/api/v1/risk/analyze"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{BACKEND_URL}{endpoint}", timeout=5)
            if response.status_code in [401, 403]:
                print(f"✅ {endpoint}: Authentication required (expected) - Status: {response.status_code}")
            elif response.status_code == 422:
                print(f"✅ {endpoint}: Validation error (expected for GET)")
            elif response.status_code == 405:
                print(f"✅ {endpoint}: Method not allowed (expected for GET)")
            else:
                print(f"⚠️  {endpoint}: Unexpected status {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ {endpoint}: Connection failed - {e}")

def test_cors_configuration():
    """Test CORS configuration"""
    print("\n🔍 Testing CORS Configuration...")
    try:
        # Test preflight request
        headers = {
            'Origin': 'http://localhost:3000',
            'Access-Control-Request-Method': 'GET',
            'Access-Control-Request-Headers': 'Content-Type'
        }
        response = requests.options(f"{BACKEND_URL}/health", headers=headers, timeout=5)
        
        if response.status_code == 200:
            cors_headers = response.headers
            print("✅ CORS preflight successful!")
            print(f"   Access-Control-Allow-Origin: {cors_headers.get('Access-Control-Allow-Origin', 'Not set')}")
            print(f"   Access-Control-Allow-Methods: {cors_headers.get('Access-Control-Allow-Methods', 'Not set')}")
        else:
            print(f"⚠️  CORS preflight status: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ CORS test failed: {e}")

def test_database_connection():
    """Test database connection through backend"""
    print("\n🔍 Testing Database Connection...")
    try:
        # The health endpoint should show database status
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            db_status = data.get('database_status', 'unknown')
            if db_status == 'connected':
                print("✅ Database connection successful!")
            else:
                print(f"⚠️  Database status: {db_status}")
        else:
            print(f"❌ Cannot check database status: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Database connection test failed: {e}")

def main():
    """Run all integration tests"""
    print("🚀 Frontend-Backend Integration Test")
    print("=" * 50)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Frontend URL: {FRONTEND_URL}")
    print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # Run tests
    backend_ok = test_backend_health()
    frontend_ok = test_frontend_access()
    
    if backend_ok:
        test_backend_apis()
        test_cors_configuration()
        test_database_connection()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    print(f"Backend Status: {'✅ RUNNING' if backend_ok else '❌ FAILED'}")
    print(f"Frontend Status: {'✅ RUNNING' if frontend_ok else '❌ FAILED'}")
    
    if backend_ok and frontend_ok:
        print("\n🎉 Integration Test PASSED!")
        print("Both frontend and backend are running and accessible.")
        print("\nNext steps:")
        print("1. Open http://localhost:3000 in your browser")
        print("2. Navigate to /dashboard to see real data")
        print("3. Check /dashboard/api-keys for API key management")
        print("4. Test /dashboard/risk-detection for risk analysis")
    else:
        print("\n❌ Integration Test FAILED!")
        if not backend_ok:
            print("- Backend is not running or accessible")
        if not frontend_ok:
            print("- Frontend is not running or accessible")
        print("\nTroubleshooting:")
        print("1. Check if backend is running: python -m uvicorn app.main:app --reload")
        print("2. Check if frontend is running: npm run dev")
        print("3. Verify ports 8000 and 3000 are available")

if __name__ == "__main__":
    main()
