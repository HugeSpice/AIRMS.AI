#!/usr/bin/env python3
"""
Test Database Function
Test the create_risk_log function directly
"""

import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

async def test_db_function():
    print("🔍 Testing Database Function Directly")
    print("=" * 50)
    
    try:
        from app.core.database import db
        
        # Test data
        test_data = {
            "user_id": "test-user-id",
            "api_key_id": "test-api-key-id",
            "request_id": "test-request-id",
            "original_input": "Test input with SSN 123-45-6789",
            "sanitized_input": "Test input with [REDACTED]",
            "llm_response": "Test response",
            "sanitized_response": "Test response",
            "risk_score": 1.28,
            "risks_detected": [
                {
                    "type": "input_risk",
                    "score": 1.28,
                    "description": "Contains PII: SSN"
                }
            ],
            "mitigation_applied": {
                "input_sanitization": True
            },
            "processing_time_ms": 100,
            "llm_provider": "test_provider",
            "llm_model": "test_model",
            "tokens_used": 50
        }
        
        print(f"📝 Test data: {test_data}")
        
        # Try to create the risk log
        result = await db.create_risk_log(test_data)
        print(f"✅ Risk log created successfully: {result}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_db_function())
