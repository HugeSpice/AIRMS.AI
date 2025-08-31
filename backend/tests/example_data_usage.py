#!/usr/bin/env python3
"""
Example: Using the Secure Data Connector

This example demonstrates how to:
1. Configure and connect to multiple data sources
2. Execute secure queries with automatic sanitization
3. Handle different database types (PostgreSQL, MySQL, REST APIs)
4. Monitor data source health and status
5. Integrate with the enhanced risk detection system

Run this example to see the full system in action!
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any

# Import our secure data connector
from app.services.secure_data_connector import (
    SecureDataConnector, 
    DataSourceConfig, 
    DataSourceType
)

# Import risk detection components
from app.services.risk_detection.risk_agent import RiskAgent, RiskAgentConfig, ProcessingMode

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def setup_data_sources() -> SecureDataConnector:
    """Setup and configure data sources"""
    
    # Initialize the secure data connector with strict risk detection
    risk_agent = RiskAgent(RiskAgentConfig(processing_mode=ProcessingMode.STRICT))
    connector = SecureDataConnector(risk_agent=risk_agent)
    
    # Example 1: PostgreSQL Database
    postgres_config = DataSourceConfig(
        name="production_db",
        type=DataSourceType.POSTGRESQL,
        host="localhost",  # Change to your PostgreSQL host
        port=5432,
        database="airms_production",
        username="airms_user",  # Change to your username
        password="secure_password",  # Change to your password
        enable_data_sanitization=True,
        enable_risk_assessment=True,
        allowed_tables=["users", "orders", "products"],
        blocked_tables=["passwords", "api_keys", "secrets"]
    )
    
    # Example 2: MySQL Database
    mysql_config = DataSourceConfig(
        name="analytics_db",
        type=DataSourceType.MYSQL,
        host="localhost",  # Change to your MySQL host
        port=3306,
        database="airms_analytics",
        username="analytics_user",  # Change to your username
        password="analytics_password",  # Change to your password
        enable_data_sanitization=True,
        enable_risk_assessment=True,
        allowed_tables=["metrics", "logs", "reports"]
    )
    
    # Example 3: REST API
    rest_api_config = DataSourceConfig(
        name="external_api",
        type=DataSourceType.REST_API,
        base_url="https://api.example.com",  # Change to your API URL
        api_key="your_api_key_here",  # Change to your API key
        headers={
            "Authorization": "Bearer your_api_key_here",
            "Content-Type": "application/json"
        },
        enable_data_sanitization=True,
        enable_risk_assessment=True,
        max_query_time=30
    )
    
    # Example 4: Supabase (PostgreSQL-based)
    supabase_config = DataSourceConfig(
        name="supabase_db",
        type=DataSourceType.SUPABASE,
        host="your-project.supabase.co",  # Change to your Supabase host
        port=5432,
        database="postgres",
        username="postgres",  # Change to your Supabase username
        password="your_supabase_password",  # Change to your Supabase password
        enable_data_sanitization=True,
        enable_risk_assessment=True
    )
    
    # Add data sources to connector
    logger.info("Adding data sources...")
    connector.add_data_source(postgres_config)
    connector.add_data_source(mysql_config)
    connector.add_data_source(rest_api_config)
    connector.add_data_source(supabase_config)
    
    return connector


async def demonstrate_postgresql_queries(connector: SecureDataConnector):
    """Demonstrate PostgreSQL queries with risk detection"""
    
    logger.info("\n🔍 Demonstrating PostgreSQL Queries...")
    
    try:
        # Example 1: Safe query - user information
        logger.info("Query 1: Safe user data query")
        result = await connector.execute_secure_query(
            data_source_name="production_db",
            query="SELECT id, name, email, created_at FROM users LIMIT 5",
            enable_sanitization=True,
            enable_risk_assessment=True
        )
        
        print(f"✅ Query executed successfully!")
        print(f"   Risk Score: {result.risk_assessment['risk_score']}")
        print(f"   Is Safe: {result.is_safe}")
        print(f"   Rows Returned: {result.row_count}")
        print(f"   Processing Time: {result.processing_time_ms:.2f}ms")
        
        if result.data:
            print(f"   Sample Data: {json.dumps(result.data[0], indent=2)}")
        
        # Example 2: Query with potential PII
        logger.info("\nQuery 2: Query with potential PII data")
        result = await connector.execute_secure_query(
            data_source_name="production_db",
            query="SELECT id, name, email, phone, ssn FROM users WHERE id = 1",
            enable_sanitization=True,
            enable_risk_assessment=True
        )
        
        print(f"✅ PII Query executed!")
        print(f"   Risk Score: {result.risk_assessment['risk_score']}")
        print(f"   PII Entities Found: {result.risk_assessment['pii_entities_found']}")
        print(f"   Is Safe: {result.is_safe}")
        
        if result.data:
            print(f"   Sanitized Data: {json.dumps(result.data[0], indent=2)}")
        
        # Example 3: Schema exploration
        logger.info("\nQuery 3: Exploring table schema")
        tables = await connector.adapters["production_db"].list_tables()
        print(f"   Available Tables: {tables}")
        
        if tables:
            schema = await connector.adapters["production_db"].get_table_schema(tables[0])
            print(f"   Schema for {tables[0]}: {json.dumps(schema, indent=2)}")
            
    except Exception as e:
        logger.error(f"PostgreSQL demonstration failed: {e}")
        print(f"❌ PostgreSQL demo failed: {e}")


async def demonstrate_mysql_queries(connector: SecureDataConnector):
    """Demonstrate MySQL queries with risk detection"""
    
    logger.info("\n🔍 Demonstrating MySQL Queries...")
    
    try:
        # Example 1: Analytics data query
        logger.info("Query 1: Analytics data query")
        result = await connector.execute_secure_query(
            data_source_name="analytics_db",
            query="SELECT date, metric_name, value FROM metrics WHERE date >= '2024-01-01' LIMIT 5",
            enable_sanitization=True,
            enable_risk_assessment=True
        )
        
        print(f"✅ Analytics query executed!")
        print(f"   Risk Score: {result.risk_assessment['risk_score']}")
        print(f"   Is Safe: {result.is_safe}")
        print(f"   Rows Returned: {result.row_count}")
        
        if result.data:
            print(f"   Sample Data: {json.dumps(result.data[0], indent=2)}")
            
    except Exception as e:
        logger.error(f"MySQL demonstration failed: {e}")
        print(f"❌ MySQL demo failed: {e}")


async def demonstrate_rest_api_queries(connector: SecureDataConnector):
    """Demonstrate REST API queries with risk detection"""
    
    logger.info("\n🔍 Demonstrating REST API Queries...")
    
    try:
        # Example 1: GET request
        logger.info("Query 1: GET request to external API")
        result = await connector.execute_secure_query(
            data_source_name="external_api",
            query="GET /users",
            params={"limit": 5, "status": "active"},
            enable_sanitization=True,
            enable_risk_assessment=True
        )
        
        print(f"✅ REST API GET query executed!")
        print(f"   Risk Score: {result.risk_assessment['risk_score']}")
        print(f"   Is Safe: {result.is_safe}")
        print(f"   Data Received: {result.row_count > 0}")
        
        if result.data:
            print(f"   API Response: {json.dumps(result.data[0], indent=2)}")
            
        # Example 2: POST request
        logger.info("\nQuery 2: POST request to external API")
        result = await connector.execute_secure_query(
            data_source_name="external_api",
            query="POST /analytics",
            params={"event": "user_login", "user_id": 123, "timestamp": datetime.now().isoformat()},
            enable_sanitization=True,
            enable_risk_assessment=True
        )
        
        print(f"✅ REST API POST query executed!")
        print(f"   Risk Score: {result.risk_assessment['risk_score']}")
        print(f"   Is Safe: {result.is_safe}")
        
    except Exception as e:
        logger.error(f"REST API demonstration failed: {e}")
        print(f"❌ REST API demo failed: {e}")


async def demonstrate_data_source_management(connector: SecureDataConnector):
    """Demonstrate data source management features"""
    
    logger.info("\n🔍 Demonstrating Data Source Management...")
    
    try:
        # Get status of all data sources
        status = await connector.get_data_source_status()
        print(f"✅ Data Source Status:")
        for name, info in status.items():
            print(f"   {name}: {info['status']} ({info['type']})")
        
        # Test connections
        print(f"\n🔍 Testing Data Source Connections...")
        for name in connector.get_available_data_sources():
            is_working = await connector.test_data_source(name)
            status_icon = "✅" if is_working else "❌"
            print(f"   {status_icon} {name}: {'Connected' if is_working else 'Failed'}")
        
        # Get data source information
        print(f"\n📊 Data Source Information:")
        for name in connector.get_available_data_sources():
            info = connector.get_data_source_info(name)
            if info:
                print(f"   {name}: {info['type']} at {info['host']}:{info['port']}")
                
    except Exception as e:
        logger.error(f"Data source management demonstration failed: {e}")
        print(f"❌ Management demo failed: {e}")


async def demonstrate_risk_detection_integration(connector: SecureDataConnector):
    """Demonstrate how risk detection integrates with data access"""
    
    logger.info("\n🔍 Demonstrating Risk Detection Integration...")
    
    try:
        # Example: Query that might contain sensitive data
        logger.info("Query: Data that might contain PII or bias")
        
        # Simulate data with potential risks
        test_data = [
            {
                "user_id": 1,
                "name": "John Doe",
                "email": "john.doe@example.com",
                "phone": "+1-555-123-4567",
                "ssn": "123-45-6789",
                "salary": 75000,
                "department": "Engineering",
                "gender": "Male",
                "age": 35
            },
            {
                "user_id": 2,
                "name": "Jane Smith",
                "email": "jane.smith@example.com",
                "phone": "+1-555-987-6543",
                "ssn": "987-65-4321",
                "salary": 65000,
                "department": "Marketing",
                "gender": "Female",
                "age": 28
            }
        ]
        
        # Analyze this data with our risk agent
        risk_agent = connector.risk_agent
        analysis_result = risk_agent.analyze_text(json.dumps(test_data, indent=2))
        
        print(f"✅ Risk Analysis Completed!")
        print(f"   Overall Risk Score: {analysis_result.risk_assessment.overall_risk_score}")
        print(f"   Is Safe: {analysis_result.is_safe}")
        print(f"   Should Block: {analysis_result.should_block}")
        print(f"   PII Entities Found: {len(analysis_result.risk_assessment.pii_entities)}")
        print(f"   Bias Detections: {len(analysis_result.risk_assessment.bias_detections)}")
        print(f"   Adversarial Detections: {len(analysis_result.risk_assessment.adversarial_detections)}")
        
        # Show sanitized version
        if hasattr(analysis_result, 'sanitized_text'):
            print(f"\n📝 Sanitized Data Preview:")
            print(f"   {analysis_result.sanitized_text[:200]}...")
            
    except Exception as e:
        logger.error(f"Risk detection integration demonstration failed: {e}")
        print(f"❌ Risk detection demo failed: {e}")


async def main():
    """Main demonstration function"""
    
    logger.info("🚀 AI Risk Mitigation System - Secure Data Connector Demo")
    logger.info("=" * 70)
    
    try:
        # Setup data sources
        logger.info("📡 Setting up data sources...")
        connector = await setup_data_sources()
        
        # Note: In a real scenario, you would connect to actual databases
        # For this demo, we'll show the setup and explain what would happen
        
        logger.info("⚠️  Note: This demo shows the setup and configuration.")
        logger.info("   To test with real databases, update the connection details above.")
        logger.info("   The system will automatically detect and block any risky data.")
        
        # Show data source management
        await demonstrate_data_source_management(connector)
        
        # Show risk detection integration
        await demonstrate_risk_detection_integration(connector)
        
        # Show what would happen with real connections
        logger.info("\n🔮 What Would Happen With Real Connections:")
        logger.info("   1. PostgreSQL: Safe queries would return sanitized data")
        logger.info("   2. MySQL: PII would be automatically detected and masked")
        logger.info("   3. REST APIs: Responses would be risk-assessed")
        logger.info("   4. All data would be logged and monitored")
        
        logger.info("\n✅ Demo completed successfully!")
        logger.info("   Your AI Risk Mitigation System is ready for production use!")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"❌ Demo failed: {e}")


if __name__ == "__main__":
    # Run the async demo
    asyncio.run(main())
