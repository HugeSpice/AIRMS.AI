"""
Complete AIRMS Workflow Test

This test demonstrates the complete end-to-end workflow:
1. User Input → Risk Detection → Mitigation
2. LLM Query Generation → Data Access → Risk Detection on Data
3. LLM Response Generation → Output Post-Processing → Final Response
4. Complete Shipping Company Chatbot Example
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Import AIRMS components
from app.services.risk_detection.risk_agent import RiskAgent
from app.services.risk_detection.detectors.hallucination_detector import HallucinationDetector
from app.services.query_generator import QueryGenerator, QueryContext
from app.services.token_remapper import TokenRemapper, TokenType
from app.services.secure_data_connector import SecureDataConnector
from app.services.risk_detection.scorers.risk_scorer import RiskScorer

class CompleteWorkflowTest:
    """Test the complete AIRMS workflow end-to-end"""
    
    def __init__(self):
        self.risk_agent = RiskAgent()
        self.hallucination_detector = HallucinationDetector()
        self.query_generator = QueryGenerator()
        self.token_remapper = TokenRemapper()
        self.data_connector = SecureDataConnector()
        self.risk_scorer = RiskScorer()
        
        # Test data
        self.test_orders = self._create_test_orders()
        self.test_customers = self._create_test_customers()
        
    def _create_test_orders(self) -> List[Dict[str, Any]]:
        """Create test order data"""
        return [
            {
                "order_id": "ORD-2024-001",
                "customer_id": "CUST-001",
                "email": "john.doe@gmail.com",
                "status": "in_transit",
                "estimated_delivery": "2024-08-26",
                "tracking_number": "TRK-123456789",
                "current_location": "Distribution Center, Chicago",
                "created_at": "2024-08-20T10:00:00Z",
                "last_updated": "2024-08-22T15:30:00Z"
            },
            {
                "order_id": "ORD-2024-002", 
                "customer_id": "CUST-002",
                "email": "jane.smith@outlook.com",
                "status": "delivered",
                "estimated_delivery": "2024-08-24",
                "tracking_number": "TRK-987654321",
                "current_location": "Delivered to Customer",
                "created_at": "2024-08-18T14:00:00Z",
                "delivered_at": "2024-08-24T11:15:00Z",
                "last_updated": "2024-08-24T11:15:00Z"
            },
            {
                "order_id": "ORD-2024-003",
                "customer_id": "CUST-003", 
                "email": "bob.wilson@yahoo.com",
                "status": "pending",
                "estimated_delivery": "2024-08-28",
                "tracking_number": "TRK-456789123",
                "current_location": "Warehouse, Los Angeles",
                "created_at": "2024-08-21T09:00:00Z",
                "last_updated": "2024-08-21T09:00:00Z"
            }
        ]
    
    def _create_test_customers(self) -> List[Dict[str, Any]]:
        """Create test customer data"""
        return [
            {
                "customer_id": "CUST-001",
                "name": "John Doe",
                "email": "john.doe@gmail.com",
                "phone": "+1-555-123-4567",
                "address": "123 Main St, New York, NY 10001"
            },
            {
                "customer_id": "CUST-002",
                "name": "Jane Smith", 
                "email": "jane.smith@outlook.com",
                "phone": "+1-555-987-6543",
                "address": "456 Oak Ave, Los Angeles, CA 90210"
            },
            {
                "customer_id": "CUST-003",
                "name": "Bob Wilson",
                "email": "bob.wilson@yahoo.com", 
                "phone": "+1-555-456-7890",
                "address": "789 Pine Rd, Chicago, IL 60601"
            }
        ]
    
    async def test_complete_workflow(self):
        """Test the complete AIRMS workflow"""
        print("🚀 Starting Complete AIRMS Workflow Test")
        print("=" * 60)
        
        # Test Case 1: Shipping Company Chatbot Example
        await self._test_shipping_chatbot_workflow()
        
        # Test Case 2: High-Risk Input Detection
        await self._test_high_risk_input()
        
        # Test Case 3: Data Access with Risk Detection
        await self._test_data_access_workflow()
        
        # Test Case 4: Output Hallucination Detection
        await self._test_hallucination_detection()
        
        print("\n✅ Complete AIRMS Workflow Test Completed Successfully!")
    
    async def _test_shipping_chatbot_workflow(self):
        """Test the complete shipping chatbot workflow"""
        print("\n📦 Test Case 1: Shipping Company Chatbot Workflow")
        print("-" * 50)
        
        # Step 1: Customer asks question
        customer_question = "My email is dev23@gmail.com, where is my package?"
        print(f"👤 Customer Question: {customer_question}")
        
        # Step 2: Input Risk Detection & Sanitization
        print("\n🔒 Step 2: Input Risk Detection & Sanitization")
        input_analysis = self.risk_agent.analyze_text(customer_question)
        print(f"   Input Risk Score: {input_analysis.risk_assessment.overall_risk_score}/10")
        print(f"   PII Detected: {len(input_analysis.risk_assessment.pii_entities)} entities")
        print(f"   Should Block: {input_analysis.should_block}")
        
        # Step 3: Token Storage & Masking
        print("\n🔐 Step 3: Token Storage & Masking")
        email = "dev23@gmail.com"
        masked_email = self.token_remapper.store_token(email, TokenType.EMAIL, 24)
        print(f"   Original Email: {email}")
        print(f"   Masked Token: {masked_email}")
        
        # Step 4: Query Generation via LLM
        print("\n🤖 Step 4: Query Generation via LLM")
        query_context = QueryContext(
            user_question=customer_question,
            data_source_name="shipping_db",
            table_schema={"orders": ["order_id", "email", "status", "estimated_delivery"]},
            available_tables=["orders", "customers", "packages"],
            user_permissions=["read_orders"],
            risk_threshold=5.0
        )
        
        generated_query = await self.query_generator.generate_query(query_context)
        print(f"   Generated SQL: {generated_query.sql_query}")
        print(f"   Query Type: {generated_query.query_type.value}")
        print(f"   Complexity: {generated_query.complexity.value}")
        print(f"   Risk Score: {generated_query.risk_score}/10")
        
        # Step 5: Query Execution (Trusted Zone)
        print("\n🛡️ Step 5: Query Execution (Trusted Zone)")
        # Simulate query execution with test data
        query_result = self._execute_test_query(generated_query.sql_query, email)
        print(f"   Query Result: {query_result}")
        
        # Step 6: Risk Detection on Fetched Data
        print("\n🔍 Step 6: Risk Detection on Fetched Data")
        data_text = json.dumps(query_result, indent=2)
        data_analysis = self.risk_agent.analyze_text(data_text)
        print(f"   Data Risk Score: {data_analysis.risk_assessment.overall_risk_score}/10")
        print(f"   Data PII Count: {len(data_analysis.risk_assessment.pii_entities)}")
        
        # Step 7: LLM Response Generation
        print("\n🤖 Step 7: LLM Response Generation")
        llm_response = self._generate_llm_response(query_result, customer_question)
        print(f"   LLM Response: {llm_response}")
        
        # Step 8: Output Risk Detection & Post-Processing
        print("\n🔒 Step 8: Output Risk Detection & Post-Processing")
        output_analysis = self.risk_agent.analyze_text(llm_response)
        print(f"   Output Risk Score: {output_analysis.risk_assessment.overall_risk_score}/10")
        
        # Hallucination Detection
        hallucination_assessment = self.hallucination_detector.detect_hallucinations(
            llm_response, query_result, customer_question
        )
        print(f"   Hallucination Score: {hallucination_assessment.overall_hallucination_score}/10")
        print(f"   Factual Accuracy: {hallucination_assessment.factual_accuracy}")
        
        # Step 9: Final Response to Customer
        print("\n📤 Step 9: Final Response to Customer")
        final_response = self._generate_final_response(llm_response, output_analysis, hallucination_assessment)
        print(f"   Final Response: {final_response}")
        
        # Step 10: Risk Report & Dashboard Logs
        print("\n📊 Step 10: Risk Report & Dashboard Logs")
        risk_report = self._generate_risk_report(
            input_analysis, data_analysis, output_analysis, hallucination_assessment
        )
        print(f"   Overall Risk Level: {risk_report['overall_risk_level']}")
        print(f"   Total Risk Score: {risk_report['total_risk_score']}/10")
        print(f"   Mitigation Actions: {', '.join(risk_report['mitigation_actions'])}")
    
    async def _test_high_risk_input(self):
        """Test high-risk input detection and blocking"""
        print("\n⚠️ Test Case 2: High-Risk Input Detection")
        print("-" * 50)
        
        high_risk_inputs = [
            "My SSN is 123-45-6789 and credit card is 1234-5678-9012-3456",
            "I want to hack the system and get admin access",
            "DROP TABLE orders; SELECT * FROM customers WHERE 1=1"
        ]
        
        for i, input_text in enumerate(high_risk_inputs, 1):
            print(f"\n   Test {i}: {input_text[:50]}...")
            
            analysis = self.risk_agent.analyze_text(input_text)
            print(f"      Risk Score: {analysis.risk_assessment.overall_risk_score}/10")
            print(f"      Should Block: {analysis.should_block}")
            print(f"      Risk Level: {analysis.risk_assessment.risk_level.value}")
            
            if analysis.should_block:
                print(f"      🚫 INPUT BLOCKED - High Risk Detected")
            else:
                print(f"      ✅ Input Allowed - Risk Acceptable")
    
    async def _test_data_access_workflow(self):
        """Test data access with risk detection"""
        print("\n🛡️ Test Case 3: Data Access with Risk Detection")
        print("-" * 50)
        
        # Test secure data connector
        test_query = "SELECT * FROM orders WHERE email = 'test@example.com'"
        print(f"   Test Query: {test_query}")
        
        # Simulate secure query execution
        try:
            # In real implementation, this would use the actual data connector
            result = {
                "is_safe": True,
                "data": [{"order_id": "TEST-001", "status": "pending"}],
                "risk_score": 2.5,
                "sanitization_log": ["PII removed", "Data sanitized"]
            }
            
            print(f"   Query Result: Safe={result['is_safe']}, Risk={result['risk_score']}/10")
            print(f"   Sanitization: {', '.join(result['sanitization_log'])}")
            
        except Exception as e:
            print(f"   ❌ Data Access Failed: {e}")
    
    async def _test_hallucination_detection(self):
        """Test hallucination detection on LLM outputs"""
        print("\n🧠 Test Case 4: Hallucination Detection")
        print("-" * 50)
        
        test_responses = [
            # Accurate response
            "Your order ORD-2024-001 is in transit and should arrive on August 26, 2024.",
            
            # Hallucinated response (wrong order number)
            "Your order ORD-9999-999 is in transit and should arrive on August 26, 2024.",
            
            # Hallucinated response (wrong date)
            "Your order ORD-2024-001 is in transit and should arrive on September 15, 2024.",
            
            # Unverifiable claim
            "Your order is definitely the fastest shipping option available and will arrive soon."
        ]
        
        source_data = {
            "order_id": "ORD-2024-001",
            "status": "in_transit",
            "estimated_delivery": "2024-08-26"
        }
        
        for i, response in enumerate(test_responses, 1):
            print(f"\n   Test Response {i}: {response[:60]}...")
            
            assessment = self.hallucination_detector.detect_hallucinations(
                response, source_data, "Where is my package?"
            )
            
            print(f"      Hallucination Score: {assessment.overall_hallucination_score}/10")
            print(f"      Factual Accuracy: {assessment.factual_accuracy}")
            print(f"      Level: {assessment.hallucination_level}")
            
            if assessment.detections:
                for detection in assessment.detections[:2]:  # Show first 2 detections
                    print(f"      Detection: {detection.description}")
    
    def _execute_test_query(self, sql_query: str, email: str) -> Dict[str, Any]:
        """Simulate query execution with test data"""
        # Find matching order for the email
        matching_order = None
        for order in self.test_orders:
            if order["email"] == email:
                matching_order = order
                break
        
        if matching_order:
            return {
                "order_id": matching_order["order_id"],
                "status": matching_order["status"],
                "estimated_delivery": matching_order["estimated_delivery"],
                "tracking_number": matching_order["tracking_number"],
                "current_location": matching_order["current_location"]
            }
        else:
            return {"error": "No order found for this email"}
    
    def _generate_llm_response(self, query_result: Dict[str, Any], question: str) -> str:
        """Simulate LLM response generation"""
        if "error" in query_result:
            return "I'm sorry, I couldn't find any orders associated with that email address."
        
        status = query_result["status"]
        order_id = query_result["order_id"]
        delivery_date = query_result["estimated_delivery"]
        
        if status == "in_transit":
            return f"Your order {order_id} is currently in transit and should arrive on {delivery_date}. You can track it using tracking number {query_result['tracking_number']}."
        elif status == "delivered":
            return f"Your order {order_id} has been delivered! It was completed on {delivery_date}."
        elif status == "pending":
            return f"Your order {order_id} is currently being processed and is expected to ship soon. Estimated delivery is {delivery_date}."
        else:
            return f"Your order {order_id} has status: {status}. Estimated delivery is {delivery_date}."
    
    def _generate_final_response(self, llm_response: str, output_analysis: Any, hallucination_assessment: Any) -> str:
        """Generate final response based on risk assessment"""
        # Check if output should be blocked
        if output_analysis.should_block:
            return "[RESPONSE_BLOCKED_DUE_TO_HIGH_RISK]"
        
        # Check for hallucinations
        if hallucination_assessment.overall_hallucination_score > 5.0:
            return f"[RESPONSE_MODIFIED_DUE_TO_HALLUCINATIONS] {llm_response}"
        
        # Return sanitized response if needed
        if output_analysis.sanitization_result:
            return output_analysis.sanitized_text
        
        return llm_response
    
    def _generate_risk_report(self, input_analysis: Any, data_analysis: Any, 
                             output_analysis: Any, hallucination_assessment: Any) -> Dict[str, Any]:
        """Generate comprehensive risk report"""
        # Calculate overall risk
        total_risk = max(
            input_analysis.risk_assessment.overall_risk_score,
            data_analysis.risk_assessment.overall_risk_score,
            output_analysis.risk_assessment.overall_risk_score,
            hallucination_assessment.overall_hallucination_score
        )
        
        # Determine overall risk level
        if total_risk >= 8.0:
            risk_level = "CRITICAL"
        elif total_risk >= 6.0:
            risk_level = "HIGH"
        elif total_risk >= 4.0:
            risk_level = "MEDIUM"
        elif total_risk >= 2.0:
            risk_level = "LOW"
        else:
            risk_level = "SAFE"
        
        # Collect mitigation actions
        mitigation_actions = []
        if input_analysis.should_block:
            mitigation_actions.append("Input blocked")
        if input_analysis.sanitization_result:
            mitigation_actions.append("Input sanitized")
        if output_analysis.should_block:
            mitigation_actions.append("Output blocked")
        if output_analysis.sanitization_result:
            mitigation_actions.append("Output sanitized")
        if hallucination_assessment.overall_hallucination_score > 3.0:
            mitigation_actions.append("Hallucination detected")
        
        return {
            "overall_risk_level": risk_level,
            "total_risk_score": total_risk,
            "input_risk_score": input_analysis.risk_assessment.overall_risk_score,
            "data_risk_score": data_analysis.risk_assessment.overall_risk_score,
            "output_risk_score": output_analysis.risk_assessment.overall_risk_score,
            "hallucination_score": hallucination_assessment.overall_hallucination_score,
            "mitigation_actions": mitigation_actions,
            "timestamp": datetime.now().isoformat()
        }

async def main():
    """Run the complete workflow test"""
    test = CompleteWorkflowTest()
    await test.test_complete_workflow()
    
    # Cleanup
    test.token_remapper.close()

if __name__ == "__main__":
    asyncio.run(main())
