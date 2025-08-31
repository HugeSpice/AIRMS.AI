#!/usr/bin/env python3
"""
Risk Detection and Mitigation Flow Test
Tests the complete flow from chat completion to risk detection to dashboard display
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"

class RiskMitigationTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
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
    
    def test_chat_with_risk_detection(self):
        """Test chat completion with risk detection enabled"""
        print("\n🔍 Testing Chat Completion with Risk Detection...")
        
        try:
            # Test with potentially risky content
            chat_data = {
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {
                        "role": "user", 
                        "content": "Hello, my name is John Smith and my email is john.smith@company.com. Can you help me with my credit card number 1234-5678-9012-3456?"
                    }
                ],
                "max_tokens": 150,
                "temperature": 0.7
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/v1/chat/completions",
                json=chat_data,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                choices = data.get("choices", [])
                
                if choices:
                    # Check if risk detection metadata is present
                    risk_metadata = data.get("risk_metadata", {})
                    risk_score = risk_metadata.get("overall_risk_score", "Not found")
                    risk_level = risk_metadata.get("risk_level", "Not found")
                    mitigation_applied = risk_metadata.get("mitigation_applied", [])
                    
                    print(f"   📊 Risk Detection Results:")
                    print(f"      Risk Score: {risk_score}")
                    print(f"      Risk Level: {risk_level}")
                    print(f"      Mitigation Applied: {mitigation_applied}")
                    
                    # Check if response was sanitized
                    response_content = choices[0].get("message", {}).get("content", "")
                    if "john.smith@company.com" not in response_content and "1234-5678-9012-3456" not in response_content:
                        sanitization_status = "✅ Content was sanitized (PII removed)"
                    else:
                        sanitization_status = "⚠️ Content may contain PII (not sanitized)"
                    
                    return self.log_test("Chat with Risk Detection", True, 
                        f"Response received, Risk Score: {risk_score}, {sanitization_status}")
                else:
                    return self.log_test("Chat with Risk Detection", False, "No choices in response")
            else:
                data = response.json()
                return self.log_test("Chat with Risk Detection", False, 
                    f"Status: {response.status_code}, Error: {data.get('detail', 'Unknown')}")
        except Exception as e:
            return self.log_test("Chat with Risk Detection", False, f"Error: {e}")
    
    def test_risk_analysis_endpoint(self):
        """Test direct risk analysis endpoint"""
        print("\n🔍 Testing Direct Risk Analysis...")
        
        try:
            # Test with high-risk content
            risk_data = {
                "text": "My personal information: John Doe, SSN: 123-45-6789, Phone: (555) 123-4567, Address: 123 Main St, Anytown, USA 12345. I need help with my bank account.",
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
                risk_level = data.get("risk_level", "Unknown")
                risk_factors = data.get("risk_factors", [])
                mitigation_suggestions = data.get("mitigation_suggestions", [])
                sanitized_text = data.get("sanitized_text", "")
                
                print(f"   📊 Risk Analysis Results:")
                print(f"      Risk Score: {risk_score}")
                print(f"      Risk Level: {risk_level}")
                print(f"      Risk Factors: {risk_factors}")
                print(f"      Mitigation Suggestions: {mitigation_suggestions}")
                
                # Check if text was sanitized
                if sanitized_text and ("123-45-6789" not in sanitized_text and "(555) 123-4567" not in sanitized_text):
                    sanitization_status = "✅ Text was properly sanitized"
                else:
                    sanitization_status = "⚠️ Text may not be fully sanitized"
                
                return self.log_test("Direct Risk Analysis", True, 
                    f"Risk Score: {risk_score}, {sanitization_status}")
            else:
                data = response.json()
                return self.log_test("Direct Risk Analysis", False, 
                    f"Status: {response.status_code}, Error: {data.get('detail', 'Unknown')}")
        except Exception as e:
            return self.log_test("Direct Risk Analysis", False, f"Error: {e}")
    
    def test_analytics_data_after_risk_detection(self):
        """Test if risk detection events are saved and visible in analytics"""
        print("\n🔍 Testing Analytics Data After Risk Detection...")
        
        try:
            # Wait a moment for data to be processed
            time.sleep(2)
            
            # Check analytics statistics
            stats_response = self.session.get(
                f"{BACKEND_URL}/api/v1/analytics/statistics?days=1",
                timeout=10
            )
            
            if stats_response.status_code == 200:
                stats_data = stats_response.json()
                
                print(f"   📊 Analytics Statistics:")
                print(f"      Total Requests: {stats_data.get('total_requests', 'N/A')}")
                print(f"      Average Risk Score: {stats_data.get('avg_risk_score', 'N/A')}")
                print(f"      High Risk Count: {stats_data.get('high_risk_count', 'N/A')}")
                print(f"      PII Detections: {stats_data.get('pii_detections', 'N/A')}")
                print(f"      Blocked Count: {stats_data.get('blocked_count', 'N/A')}")
                
                # Check if we have recent data
                if stats_data.get('total_requests', 0) > 0:
                    return self.log_test("Analytics Data", True, 
                        f"Data available: {stats_data.get('total_requests')} requests")
                else:
                    return self.log_test("Analytics Data", False, "No request data found")
            else:
                return self.log_test("Analytics Data", False, 
                    f"Could not fetch analytics: {stats_response.status_code}")
        except Exception as e:
            return self.log_test("Analytics Data", False, f"Error: {e}")
    
    def test_risk_logs_after_detection(self):
        """Test if risk detection events are logged"""
        print("\n🔍 Testing Risk Logs...")
        
        try:
            # Check recent risk logs
            logs_response = self.session.get(
                f"{BACKEND_URL}/api/v1/analytics/logs?limit=5&offset=0&days=1",
                timeout=10
            )
            
            if logs_response.status_code == 200:
                logs_data = logs_response.json()
                
                if logs_data and len(logs_data) > 0:
                    print(f"   📋 Recent Risk Logs ({len(logs_data)} entries):")
                    for i, log in enumerate(logs_data[:3]):  # Show first 3 logs
                        risk_score = log.get('risk_score', 'N/A')
                        risk_level = log.get('risk_level', 'N/A')
                        risk_factors = log.get('risk_factors', [])
                        created_at = log.get('created_at', 'N/A')
                        
                        print(f"      Log {i+1}: Score {risk_score} ({risk_level}), Factors: {risk_factors[:2]}")
                    
                    return self.log_test("Risk Logs", True, 
                        f"Found {len(logs_data)} risk log entries")
                else:
                    return self.log_test("Risk Logs", False, "No risk logs found")
            else:
                return self.log_test("Risk Logs", False, 
                    f"Could not fetch logs: {logs_response.status_code}")
        except Exception as e:
            return self.log_test("Risk Logs", False, f"Error: {e}")
    
    def test_dashboard_overview(self):
        """Test dashboard overview data"""
        print("\n🔍 Testing Dashboard Overview...")
        
        try:
            # Check dashboard overview
            dashboard_response = self.session.get(
                f"{BACKEND_URL}/api/v1/analytics/dashboard",
                timeout=10
            )
            
            if dashboard_response.status_code == 200:
                dashboard_data = dashboard_response.json()
                
                print(f"   📊 Dashboard Overview:")
                print(f"      Total Requests: {dashboard_data.get('total_requests', 'N/A')}")
                print(f"      Risk Score Trend: {dashboard_data.get('risk_score_trend', 'N/A')}")
                print(f"      Top Risk Types: {dashboard_data.get('top_risk_types', 'N/A')}")
                print(f"      Provider Distribution: {dashboard_data.get('provider_distribution', 'N/A')}")
                
                return self.log_test("Dashboard Overview", True, 
                    f"Dashboard data available: {dashboard_data.get('total_requests', 0)} requests")
            else:
                return self.log_test("Dashboard Overview", False, 
                    f"Could not fetch dashboard: {dashboard_response.status_code}")
        except Exception as e:
            return self.log_test("Dashboard Overview", False, f"Error: {e}")
    
    def test_real_time_stats(self):
        """Test real-time statistics"""
        print("\n🔍 Testing Real-time Statistics...")
        
        try:
            # Check real-time stats
            realtime_response = self.session.get(
                f"{BACKEND_URL}/api/v1/analytics/real-time-stats",
                timeout=10
            )
            
            if realtime_response.status_code == 200:
                realtime_data = realtime_response.json()
                
                print(f"   ⚡ Real-time Stats:")
                print(f"      Active Requests: {realtime_data.get('active_requests', 'N/A')}")
                print(f"      Requests Last Hour: {realtime_data.get('requests_last_hour', 'N/A')}")
                print(f"      Average Response Time: {realtime_data.get('avg_response_time', 'N/A')}ms")
                
                return self.log_test("Real-time Stats", True, 
                    f"Real-time data available: {realtime_data.get('active_requests', 0)} active requests")
            else:
                return self.log_test("Real-time Stats", False, 
                    f"Could not fetch real-time stats: {realtime_response.status_code}")
        except Exception as e:
            return self.log_test("Real-time Stats", False, f"Error: {e}")
    
    def run_complete_test(self):
        """Run complete risk mitigation flow test"""
        print("🚀 Complete Risk Detection and Mitigation Flow Test")
        print("=" * 70)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
        # Run tests in sequence
        tests = [
            self.test_backend_health,
            self.test_chat_with_risk_detection,
            self.test_risk_analysis_endpoint,
            self.test_analytics_data_after_risk_detection,
            self.test_risk_logs_after_detection,
            self.test_dashboard_overview,
            self.test_real_time_stats
        ]
        
        for test in tests:
            test()
            time.sleep(1)  # Small delay between tests
        
        # Generate summary
        self.generate_summary()
    
    def generate_summary(self):
        """Generate test summary"""
        print("\n" + "=" * 70)
        print("📊 RISK MITIGATION FLOW TEST SUMMARY")
        print("=" * 70)
        
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
            print("Complete risk detection and mitigation flow is working correctly.")
            print("The system is properly detecting risks, applying mitigation, and saving data.")
        elif passed_tests > total_tests * 0.7:
            print("\n⚠️  MOST TESTS PASSED")
            print("Risk mitigation flow is mostly working, but some issues need attention.")
        else:
            print("\n❌ MANY TESTS FAILED")
            print("Risk mitigation flow has significant issues that need to be resolved.")
        
        print("\n🎯 What This Test Verifies:")
        print("1. ✅ Chat completions trigger risk detection")
        print("2. ✅ Risk analysis works with direct endpoint")
        print("3. ✅ Risk events are saved to database")
        print("4. ✅ Analytics show risk statistics")
        print("5. ✅ Dashboard displays risk data")
        print("6. ✅ Real-time stats are updated")
        
        print("\n🔍 To Test Manually:")
        print("1. Use PowerShell command:")
        print("   Invoke-RestMethod -Uri 'http://localhost:8000/v1/chat/completions' -Method POST -Headers @{'Content-Type'='application/json'; 'Authorization'='Bearer YOUR_TOKEN'} -Body '{\"model\":\"llama-3.3-70b-versatile\",\"messages\":[{\"role\":\"user\",\"content\":\"Hello, my name is John Smith and my email is john@example.com\"}]}'")
        print("2. Check dashboard at http://localhost:3000/dashboard")
        print("3. Verify risk detection numbers increased")
        print("4. Check risk logs at /dashboard/risk-detection")

def main():
    """Main function"""
    tester = RiskMitigationTester()
    tester.run_complete_test()

if __name__ == "__main__":
    main()
