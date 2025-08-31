#!/usr/bin/env python3
"""
End-to-End Frontend-Backend Integration Test
Tests the complete user journey from login to data fetching
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"

class EndToEndTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.user_id = None
        self.test_results = {}
        
    def log_test(self, test_name, success, details=""):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   {details}")
        self.test_results[test_name] = {"success": success, "details": details}
        return success
    
    def test_backend_health(self):
        """Test backend health endpoint"""
        print("🔍 Testing Backend Health...")
        try:
            response = self.session.get(f"{BACKEND_URL}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return self.log_test("Backend Health", True, 
                    f"Status: {data.get('status')}, Database: {data.get('database_status')}")
            else:
                return self.log_test("Backend Health", False, f"Status: {response.status_code}")
        except Exception as e:
            return self.log_test("Backend Health", False, f"Error: {e}")
    
    def test_frontend_access(self):
        """Test frontend accessibility"""
        print("\n🔍 Testing Frontend Access...")
        try:
            response = self.session.get(FRONTEND_URL, timeout=5)
            if response.status_code == 200:
                return self.log_test("Frontend Access", True, 
                    f"Status: {response.status_code}, Content: {len(response.content)} bytes")
            else:
                return self.log_test("Frontend Access", False, f"Status: {response.status_code}")
        except Exception as e:
            return self.log_test("Frontend Access", False, f"Error: {e}")
    
    def test_user_registration(self):
        """Test user registration"""
        print("\n🔍 Testing User Registration...")
        try:
            # Generate unique email
            timestamp = int(time.time())
            test_email = f"testuser{timestamp}@example.com"
            
            registration_data = {
                "email": test_email,
                "password": "TestPassword123!",
                "full_name": "Test User"
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/api/v1/auth/register",
                json=registration_data,
                timeout=10
            )
            
            if response.status_code == 201:
                data = response.json()
                self.user_id = data.get("id")
                return self.log_test("User Registration", True, 
                    f"User ID: {self.user_id}, Email: {test_email}")
            else:
                data = response.json()
                return self.log_test("User Registration", False, 
                    f"Status: {response.status_code}, Error: {data.get('detail', 'Unknown')}")
        except Exception as e:
            return self.log_test("User Registration", False, f"Error: {e}")
    
    def test_user_login(self):
        """Test user login"""
        print("\n🔍 Testing User Login...")
        try:
            # Generate unique email (same as registration)
            timestamp = int(time.time())
            test_email = f"testuser{timestamp}@example.com"
            
            login_data = {
                "email": test_email,
                "password": "TestPassword123!"
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/api/v1/auth/login",
                json=login_data,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                if self.auth_token:
                    # Set authorization header for future requests
                    self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                    return self.log_test("User Login", True, 
                        f"Token received: {self.auth_token[:20]}...")
                else:
                    return self.log_test("User Login", False, "No access token received")
            else:
                data = response.json()
                return self.log_test("User Login", False, 
                    f"Status: {response.status_code}, Error: {data.get('detail', 'Unknown')}")
        except Exception as e:
            return self.log_test("User Login", False, f"Error: {e}")
    
    def test_authenticated_endpoints(self):
        """Test authenticated endpoints with valid token"""
        print("\n🔍 Testing Authenticated Endpoints...")
        
        if not self.auth_token:
            return self.log_test("Authenticated Endpoints", False, "No auth token available")
        
        endpoints_to_test = [
            ("/api/v1/auth/me", "GET", "User Profile"),
            ("/api/v1/api-keys", "GET", "API Keys List"),
            ("/api/v1/analytics/statistics?days=7", "GET", "Analytics Statistics"),
            ("/api/v1/analytics/dashboard", "GET", "Dashboard Overview"),
            ("/api/v1/analytics/logs?limit=10&offset=0&days=7", "GET", "Risk Logs")
        ]
        
        success_count = 0
        total_count = len(endpoints_to_test)
        
        for endpoint, method, description in endpoints_to_test:
            try:
                if method == "GET":
                    response = self.session.get(f"{BACKEND_URL}{endpoint}", timeout=10)
                elif method == "POST":
                    response = self.session.post(f"{BACKEND_URL}{endpoint}", timeout=10)
                
                if response.status_code == 200:
                    success_count += 1
                    print(f"   ✅ {description}: {response.status_code}")
                else:
                    print(f"   ❌ {description}: {response.status_code} - {response.text[:100]}")
                    
            except Exception as e:
                print(f"   ❌ {description}: Error - {e}")
        
        success_rate = success_count / total_count
        return self.log_test("Authenticated Endpoints", success_rate > 0.5, 
            f"{success_count}/{total_count} endpoints working ({success_rate:.1%})")
    
    def test_api_key_creation(self):
        """Test API key creation"""
        print("\n🔍 Testing API Key Creation...")
        
        if not self.auth_token:
            return self.log_test("API Key Creation", False, "No auth token available")
        
        try:
            api_key_data = {
                "key_name": "Test API Key",
                "permissions": ["chat.completions", "risk.analyze"],
                "usage_limit": 1000,
                "expires_at": None
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/api/v1/api-keys",
                json=api_key_data,
                timeout=10
            )
            
            if response.status_code == 201:
                data = response.json()
                api_key_id = data.get("id")
                return self.log_test("API Key Creation", True, 
                    f"API Key ID: {api_key_id}")
            else:
                data = response.json()
                return self.log_test("API Key Creation", False, 
                    f"Status: {response.status_code}, Error: {data.get('detail', 'Unknown')}")
        except Exception as e:
            return self.log_test("API Key Creation", False, f"Error: {e}")
    
    def test_risk_analysis(self):
        """Test risk analysis endpoint"""
        print("\n🔍 Testing Risk Analysis...")
        
        if not self.auth_token:
            return self.log_test("Risk Analysis", False, "No auth token available")
        
        try:
            risk_data = {
                "text": "This is a test message for risk analysis. It contains some potentially sensitive information like email@example.com and phone number 123-456-7890.",
                "enable_sanitization": True
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/api/v1/risk/analyze",
                json=risk_data,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                risk_score = data.get("overall_risk_score", "Unknown")
                return self.log_test("Risk Analysis", True, 
                    f"Risk Score: {risk_score}")
            else:
                data = response.json()
                return self.log_test("Risk Analysis", False, 
                    f"Status: {response.status_code}, Error: {data.get('detail', 'Unknown')}")
        except Exception as e:
            return self.log_test("Risk Analysis", False, f"Error: {e}")
    
    def test_chat_completion(self):
        """Test chat completion with risk detection"""
        print("\n🔍 Testing Chat Completion...")
        
        if not self.auth_token:
            return self.log_test("Chat Completion", False, "No auth token available")
        
        try:
            chat_data = {
                "messages": [
                    {"role": "user", "content": "Hello, this is a test message."}
                ],
                "model": "llama3-8b-8192",
                "max_tokens": 100,
                "temperature": 0.7
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/v1/chat/completions",
                json=chat_data,
                timeout=20
            )
            
            if response.status_code == 200:
                data = response.json()
                choices = data.get("choices", [])
                if choices:
                    return self.log_test("Chat Completion", True, 
                        f"Response received: {len(choices)} choices")
                else:
                    return self.log_test("Chat Completion", False, "No choices in response")
            else:
                data = response.json()
                return self.log_test("Chat Completion", False, 
                    f"Status: {response.status_code}, Error: {data.get('detail', 'Unknown')}")
        except Exception as e:
            return self.log_test("Chat Completion", False, f"Error: {e}")
    
    def test_data_consistency(self):
        """Test data consistency across endpoints"""
        print("\n🔍 Testing Data Consistency...")
        
        if not self.auth_token:
            return self.log_test("Data Consistency", False, "No auth token available")
        
        try:
            # Test that analytics data is consistent
            stats_response = self.session.get(
                f"{BACKEND_URL}/api/v1/analytics/statistics?days=7",
                timeout=10
            )
            
            if stats_response.status_code == 200:
                stats_data = stats_response.json()
                
                # Check if data structure is correct
                required_fields = ["total_requests", "avg_risk_score", "high_risk_count"]
                missing_fields = [field for field in required_fields if field not in stats_data]
                
                if not missing_fields:
                    return self.log_test("Data Consistency", True, 
                        f"Analytics data structure correct: {list(stats_data.keys())}")
                else:
                    return self.log_test("Data Consistency", False, 
                        f"Missing fields: {missing_fields}")
            else:
                return self.log_test("Data Consistency", False, 
                    f"Could not fetch analytics data: {stats_response.status_code}")
        except Exception as e:
            return self.log_test("Data Consistency", False, f"Error: {e}")
    
    def test_error_handling(self):
        """Test error handling for invalid requests"""
        print("\n🔍 Testing Error Handling...")
        
        if not self.auth_token:
            return self.log_test("Error Handling", False, "No auth token available")
        
        try:
            # Test invalid endpoint
            response = self.session.get(f"{BACKEND_URL}/api/v1/invalid-endpoint", timeout=5)
            
            if response.status_code == 404:
                return self.log_test("Error Handling", True, "404 for invalid endpoint (expected)")
            else:
                return self.log_test("Error Handling", False, 
                    f"Unexpected status for invalid endpoint: {response.status_code}")
        except Exception as e:
            return self.log_test("Error Handling", False, f"Error: {e}")
    
    def run_all_tests(self):
        """Run all end-to-end tests"""
        print("🚀 End-to-End Frontend-Backend Integration Test")
        print("=" * 60)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Frontend URL: {FRONTEND_URL}")
        print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # Run tests in sequence
        tests = [
            self.test_backend_health,
            self.test_frontend_access,
            self.test_user_registration,
            self.test_user_login,
            self.test_authenticated_endpoints,
            self.test_api_key_creation,
            self.test_risk_analysis,
            self.test_chat_completion,
            self.test_data_consistency,
            self.test_error_handling
        ]
        
        for test in tests:
            test()
            time.sleep(1)  # Small delay between tests
        
        # Generate summary
        self.generate_summary()
    
    def generate_summary(self):
        """Generate test summary"""
        print("\n" + "=" * 60)
        print("📊 END-TO-END TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        print("\nDetailed Results:")
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            print(f"{status} {test_name}")
            if result["details"]:
                print(f"   {result['details']}")
        
        if passed_tests == total_tests:
            print("\n🎉 ALL TESTS PASSED!")
            print("Complete end-to-end integration is working correctly.")
        elif passed_tests > total_tests * 0.7:
            print("\n⚠️  MOST TESTS PASSED")
            print("Integration is mostly working, but some issues need attention.")
        else:
            print("\n❌ MANY TESTS FAILED")
            print("Integration has significant issues that need to be resolved.")
        
        print("\n🎯 Next Steps:")
        print("1. Open http://localhost:3000 in your browser")
        print("2. Login with the test account created during testing")
        print("3. Navigate through all dashboard features")
        print("4. Verify real data is displayed correctly")

def main():
    """Main function"""
    tester = EndToEndTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()
