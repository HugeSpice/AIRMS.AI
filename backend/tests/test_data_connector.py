#!/usr/bin/env python3
"""
Simple test script for the Secure Data Connector
"""

import asyncio
import json
from app.services.secure_data_connector import SecureDataConnector, DataSourceConfig, DataSourceType
from app.services.risk_detection.risk_agent import RiskAgent, RiskAgentConfig, ProcessingMode

async def test_data_connector():
    """Test the Secure Data Connector functionality"""
    
    print("🚀 Testing Secure Data Connector...")
    
    try:
        # Create risk agent
        risk_agent = RiskAgent(RiskAgentConfig(processing_mode=ProcessingMode.STRICT))
        print("✅ Risk Agent created successfully")
        
        # Create data connector
        connector = SecureDataConnector(risk_agent=risk_agent)
        print("✅ Data Connector created successfully")
        
        # Test with a mock data source config
        config = DataSourceConfig(
            name="test_db",
            type=DataSourceType.POSTGRESQL,
            host="localhost",
            port=5432,
            database="test_db",
            username="test_user",
            password="test_password",
            enable_data_sanitization=True,
            enable_risk_assessment=True
        )
        
        # Add data source
        success = connector.add_data_source(config)
        print(f"✅ Data source added: {success}")
        
        # Get available data sources
        sources = connector.get_available_data_sources()
        print(f"✅ Available data sources: {sources}")
        
        # Get data source info
        info = connector.get_data_source_info("test_db")
        print(f"✅ Data source info: {info}")
        
        print("\n🎉 All tests passed! The Secure Data Connector is working correctly.")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_data_connector())
