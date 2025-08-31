#!/usr/bin/env python3
"""
Comprehensive Risk Logging Test
Tests the complete risk detection and logging flow to ensure data is properly saved
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"

class RiskLoggingTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.user_id = None
        self.api_key = None
        self.test_results = {}
        self.test_email = None
        self.test_password = None

    def log_test(self, test_name, success, details=""):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   {details}")
        self.test_results[test_name] = {"success": success, "details": details}

    def test_backend_health(self):
        """Test backend health"""
        try:
            response = self.session.get(f"{BACKEND_URL}/health")
            if response.status_code == 200:
                self.log_test("Backend Health", True, f"Status: {response.status_code}")
                return True
            else:
                self.log_test("Backend Health", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Backend Health", False, f"Error: {e}")
            return False

    def test_user_registration(self):
        """Test user registration"""
        try:
            timestamp = int(time.time())
            self.test_email = f"riskuser{timestamp}@example.com"
            self.test_password = "RiskTest123!"

            registration_data = {
                "email": self.test_email,
                "password": self.test_password,
                "full_name": "Risk Test User"
            }

            response = self.session.post(
                f"{BACKEND_URL}/api/v1/auth/register",
                json=registration_data
            )

            if response.status_code in [200, 201]:
                user_data = response.json()
                self.user_id = user_data.get("id")
                self.log_test("User Registration", True, f"User ID: {self.user_id}")
                return True
            else:
                self.log_test("User Registration", False, f"Status: {response.status_code}")
                return False

        except Exception as e:
            self.log_test("User Registration", False, f"Error: {e}")
            return False

    def test_user_login(self):
        """Test user login"""
        try:
            if not self.test_email or not self.test_password:
                self.log_test("User Login", False, "No test credentials available")
                return False

            login_data = {
                "email": self.test_email,
                "password": self.test_password
            }

            response = self.session.post(
                f"{BACKEND_URL}/api/v1/auth/login",
                json=login_data
            )

            if response.status_code == 200:
                login_data = response.json()
                self.auth_token = login_data.get("access_token")
                self.log_test("User Login", True, f"Token: {self.auth_token[:20]}...")
                return True
            else:
                self.log_test("User Login", False, f"Status: {response.status_code}, Response: {response.text}")
                return False

        except Exception as e:
            self.log_test("User Login", False, f"Error: {e}")
            return False

    def test_create_api_key(self):
        """Test API key creation"""
        try:
            if not self.auth_token:
                self.log_test("API Key Creation", False, "No auth token")
                return False

            headers = {
                "Authorization": f"Bearer {self.auth_token}",
                "Content-Type": "application/json"
            }

            api_key_data = {
                "key_name": "Test API Key",
                "permissions": ["chat.completions", "risk.analyze"],
                "usage_limit": 1000,
                "expires_at": None
            }

            response = self.session.post(
                f"{BACKEND_URL}/api/v1/api-keys",
                json=api_key_data,
                headers=headers
            )

            if response.status_code == 200:
                key_response = response.json()
                self.api_key = key_response.get("api_key")
                self.log_test("API Key Creation", True, f"API Key: {self.api_key[:20]}...")
                return True
            else:
                self.log_test("API Key Creation", False, f"Status: {response.status_code}, Response: {response.text}")
                return False

        except Exception as e:
            self.log_test("API Key Creation", False, f"Error: {e}")
            return False

    def test_chat_with_risk_detection(self):
        """Test chat completion with risk detection"""
        try:
            if not self.api_key:
                self.log_test("Chat with Risk Detection", False, "No API key")
                return False

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            # Test 1: Low risk message
            low_risk_data = {
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": "Hello, how are you?"}],
                "enable_risk_detection": True,
                "max_risk_score": 6.0
            }

            response = self.session.post(
                f"{BACKEND_URL}/v1/chat/completions",
                json=low_risk_data,
                headers=headers
            )

            if response.status_code == 200:
                self.log_test("Low Risk Chat", True, "Low risk message processed")
            else:
                self.log_test("Low Risk Chat", False, f"Status: {response.status_code}")

            # Test 2: High risk message (should trigger risk detection)
            high_risk_data = {
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": "My SSN is 123-45-6789 and credit card is 1234-5678-9012-3456"}],
                "enable_risk_detection": True,
                "max_risk_score": 6.0
            }

            response = self.session.post(
                f"{BACKEND_URL}/v1/chat/completions",
                json=high_risk_data,
                headers=headers
            )

            if response.status_code == 200:
                self.log_test("High Risk Chat", True, "High risk message processed")
            else:
                self.log_test("High Risk Chat", False, f"Status: {response.status_code}")

            # Test 3: Data access request
            data_request_data = {
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": "Show me user data from database"}],
                "enable_risk_detection": True,
                "enable_data_access": True,
                "data_source_name": "test_db",
                "data_query": "SELECT * FROM users LIMIT 5"
            }

            response = self.session.post(
                f"{BACKEND_URL}/v1/chat/completions",
                json=data_request_data,
                headers=headers
            )

            if response.status_code == 200:
                self.log_test("Data Access Request", True, "Data access request processed")
            else:
                self.log_test("Data Access Request", False, f"Status: {response.status_code}")

            return True

        except Exception as e:
            self.log_test("Chat with Risk Detection", False, f"Error: {e}")
            return False

    def test_risk_logs_creation(self):
        """Test that risk logs are being created"""
        try:
            if not self.auth_token:
                self.log_test("Risk Logs Creation", False, "No auth token")
                return False

            # Wait for logs to be processed
            time.sleep(3)

            headers = {
                "Authorization": f"Bearer {self.auth_token}"
            }

            # Check risk logs
            response = self.session.get(
                f"{BACKEND_URL}/api/v1/analytics/logs?limit=10",
                headers=headers
            )

            if response.status_code == 200:
                logs = response.json()
                if logs and len(logs) > 0:
                    self.log_test("Risk Logs Creation", True, f"Found {len(logs)} risk logs")
                    
                    # Check log structure
                    first_log = logs[0]
                    required_fields = ["id", "user_id", "request_id", "risk_score", "created_at"]
                    missing_fields = [field for field in required_fields if field not in first_log]
                    
                    if not missing_fields:
                        self.log_test("Risk Log Structure", True, "All required fields present")
                    else:
                        self.log_test("Risk Log Structure", False, f"Missing fields: {missing_fields}")
                    
                    return True
                else:
                    self.log_test("Risk Logs Creation", False, "No risk logs found")
                    return False
            else:
                self.log_test("Risk Logs Creation", False, f"Status: {response.status_code}")
                return False

        except Exception as e:
            self.log_test("Risk Logs Creation", False, f"Error: {e}")
            return False

    def test_analytics_data(self):
        """Test that analytics data is updated"""
        try:
            if not self.auth_token:
                self.log_test("Analytics Data", False, "No auth token")
                return False

            headers = {
                "Authorization": f"Bearer {self.auth_token}"
            }

            # Check statistics
            response = self.session.get(
                f"{BACKEND_URL}/api/v1/analytics/statistics?days=1",
                headers=headers
            )

            if response.status_code == 200:
                stats = response.json()
                if stats.get("total_requests", 0) > 0:
                    self.log_test("Analytics Statistics", True, f"Total requests: {stats.get('total_requests')}")
                else:
                    self.log_test("Analytics Statistics", False, "No requests found in statistics")
                
                return True
            else:
                self.log_test("Analytics Data", False, f"Status: {response.status_code}")
                return False

        except Exception as e:
            self.log_test("Analytics Data", False, f"Error: {e}")
            return False

    def test_real_time_stats(self):
        """Test real-time statistics"""
        try:
            if not self.auth_token:
                self.log_test("Real-time Stats", False, "No auth token")
                return False

            headers = {
                "Authorization": f"Bearer {self.auth_token}"
            }

            response = self.session.get(
                f"{BACKEND_URL}/api/v1/analytics/real-time-stats",
                headers=headers
            )

            if response.status_code == 200:
                stats = response.json()
                if "last_hour" in stats:
                    self.log_test("Real-time Stats", True, "Real-time stats retrieved")
                    return True
                else:
                    self.log_test("Real-time Stats", False, "Invalid real-time stats format")
                    return False
            else:
                self.log_test("Real-time Stats", False, f"Status: {response.status_code}")
                return False

        except Exception as e:
            self.log_test("Real-time Stats", False, f"Error: {e}")
            return False

    def run_complete_test(self):
        """Run all tests"""
        print("🚀 Comprehensive Risk Logging Test")
        print("=" * 50)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Frontend URL: {FRONTEND_URL}")
        print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 50)

        # Run tests in sequence
        if not self.test_backend_health():
            print("❌ Backend health check failed. Stopping tests.")
            return

        if not self.test_user_registration():
            print("❌ User registration failed. Stopping tests.")
            return

        if not self.test_user_login():
            print("❌ User login failed. Stopping tests.")
            return

        if not self.test_create_api_key():
            print("❌ API key creation failed. Stopping tests.")
            return

        if not self.test_chat_with_risk_detection():
            print("❌ Chat with risk detection failed. Stopping tests.")
            return

        if not self.test_risk_logs_creation():
            print("❌ Risk logs creation failed. Stopping tests.")
            return

        if not self.test_analytics_data():
            print("❌ Analytics data test failed. Stopping tests.")
            return

        if not self.test_real_time_stats():
            print("❌ Real-time stats test failed. Stopping tests.")
            return

        self.generate_summary()

    def generate_summary(self):
        """Generate test summary"""
        print("\n" + "=" * 50)
        print("📊 RISK LOGGING TEST SUMMARY")
        print("=" * 50)

        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result["success"])
        failed_tests = total_tests - passed_tests

        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")

        if failed_tests == 0:
            print("\n🎉 All tests passed! Risk logging is working correctly.")
            print("\n🔍 Next Steps:")
            print("1. Open the frontend dashboard to see real data")
            print("2. Check risk detection page for detailed logs")
            print("3. Verify analytics are showing real-time updates")
        else:
            print(f"\n⚠️ {failed_tests} test(s) failed. Check the details above.")
            print("\n🔧 Troubleshooting:")
            print("1. Ensure backend is running on localhost:8000")
            print("2. Check database connection and schema")
            print("3. Verify environment variables are set correctly")

def main():
    tester = RiskLoggingTester()
    tester.run_complete_test()

if __name__ == "__main__":
    main()
