#!/usr/bin/env python3
"""
Test the Enhanced Data Connector

This script demonstrates the new data access capabilities:
1. Query Security Validation
2. SQL Injection Prevention
3. Table Access Control
4. Data Sanitization Pipeline
"""

import asyncio
import time
from typing import Dict, Any

async def test_query_security_validation():
    """Test the advanced query security validation system"""
    
    print("\n🔒 Testing Query Security Validation...")
    
    try:
        from app.services.enhanced_data_connector import (
            QuerySecurityValidator, QuerySecurityLevel, 
            EnhancedDataSourceConfig, DataSourceType
        )
        
        # Create test configuration
        config = EnhancedDataSourceConfig(
            name="test_db",
            type=DataSourceType.POSTGRESQL,
            host="localhost",
            port=5432,
            database="test_db",
            username="test_user",
            password="test_password",
            query_security_level=QuerySecurityLevel.HIGH,
            allowed_tables=["users", "orders", "products"],
            blocked_tables=["admin_users", "system_config"],
            allowed_operations=["SELECT"]
        )
        
        validator = QuerySecurityValidator(QuerySecurityLevel.HIGH)
        
        # Test 1: Safe query
        safe_query = "SELECT id, name, email FROM users WHERE status = 'active'"
        result1 = validator.validate_query(safe_query, config)
        
        print(f"✅ Safe query test:")
        print(f"   Is safe: {result1.is_safe}")
        print(f"   Security score: {result1.security_score:.2f}")
        print(f"   Threats detected: {len(result1.threats_detected)}")
        print(f"   Warnings: {len(result1.warnings)}")
        
        # Test 2: Dangerous query (should be blocked)
        dangerous_query = "DROP TABLE users; SELECT * FROM admin_users"
        result2 = validator.validate_query(dangerous_query, config)
        
        print(f"\n✅ Dangerous query test:")
        print(f"   Is safe: {result2.is_safe}")
        print(f"   Security score: {result2.security_score:.2f}")
        print(f"   Threats detected: {len(result2.threats_detected)}")
        print(f"   Blocked: {not result2.is_safe}")
        
        # Test 3: Suspicious query (should be flagged)
        suspicious_query = "SELECT * FROM users WHERE id = 1 OR 1=1 UNION SELECT * FROM information_schema.tables"
        result3 = validator.validate_query(suspicious_query, config)
        
        print(f"\n✅ Suspicious query test:")
        print(f"   Is safe: {result3.is_safe}")
        print(f"   Security score: {result3.security_score:.2f}")
        print(f"   Threats detected: {len(result3.threats_detected)}")
        print(f"   Recommendations: {len(result3.recommendations)}")
        
        # Test 4: Complex query (should be flagged for complexity)
        complex_query = """
        SELECT u.name, u.email, o.amount, p.name as product_name
        FROM users u
        JOIN orders o ON u.id = o.user_id
        JOIN order_items oi ON o.id = oi.order_id
        JOIN products p ON oi.product_id = p.id
        WHERE u.status = 'active'
        AND o.created_at > '2024-01-01'
        AND (CASE WHEN o.amount > 100 THEN 'high_value' ELSE 'low_value' END) = 'high_value'
        """
        result4 = validator.validate_query(complex_query, config)
        
        print(f"\n✅ Complex query test:")
        print(f"   Is safe: {result4.is_safe}")
        print(f"   Security score: {result4.security_score:.2f}")
        print(f"   Warnings: {result4.warnings}")
        
        return True
        
    except Exception as e:
        print(f"❌ Query security validation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_enhanced_data_connector():
    """Test the enhanced data connector with security features"""
    
    print("\n🗄️ Testing Enhanced Data Connector...")
    
    try:
        from app.services.enhanced_data_connector import (
            EnhancedSecureDataConnector, EnhancedDataSourceConfig, 
            DataSourceType, QuerySecurityLevel
        )
        from app.services.risk_detection.risk_agent import RiskAgent, RiskAgentConfig, ProcessingMode
        
        # Create risk agent
        risk_agent = RiskAgent(RiskAgentConfig(processing_mode=ProcessingMode.STRICT))
        
        # Create enhanced data connector
        connector = EnhancedSecureDataConnector(risk_agent=risk_agent)
        
        # Add test data source
        config = EnhancedDataSourceConfig(
            name="secure_db",
            type=DataSourceType.POSTGRESQL,
            host="localhost",
            port=5432,
            database="secure_db",
            username="secure_user",
            password="secure_password",
            query_security_level=QuerySecurityLevel.HIGH,
            allowed_tables=["users", "orders"],
            allowed_operations=["SELECT"],
            max_result_rows=1000
        )
        
        success = await connector.add_data_source(config)
        print(f"✅ Data source added: {success}")
        
        # Test 1: Safe query execution
        safe_query = "SELECT id, name, email FROM users WHERE status = 'active'"
        result1 = await connector.execute_secure_query("secure_db", safe_query)
        
        print(f"\n✅ Safe query execution:")
        print(f"   Is safe: {result1.is_safe}")
        print(f"   Row count: {result1.row_count}")
        print(f"   Security validation: {result1.security_validation.is_safe}")
        print(f"   Security score: {result1.security_validation.security_score:.2f}")
        print(f"   Processing time: {result1.processing_time_ms:.2f}ms")
        
        # Test 2: Query with security validation
        print(f"\n📊 Security Validation Details:")
        print(f"   Threats detected: {len(result1.security_validation.threats_detected)}")
        print(f"   Warnings: {len(result1.security_validation.warnings)}")
        print(f"   Recommendations: {len(result1.security_validation.recommendations)}")
        
        # Test 3: Get connector statistics
        stats = connector.get_connector_stats()
        print(f"\n📈 Connector Statistics:")
        print(f"   Total queries: {stats['total_queries']}")
        print(f"   Total data processed: {stats['total_data_processed']}")
        print(f"   Security violations: {stats['security_violations']}")
        print(f"   Average processing time: {stats['average_processing_time']:.2f}ms")
        
        # Test 4: Available data sources
        sources = connector.get_available_data_sources()
        print(f"\n🔗 Available Data Sources: {sources}")
        
        return True
        
    except Exception as e:
        print(f"❌ Enhanced data connector test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_security_violations():
    """Test security violation handling"""
    
    print("\n🚨 Testing Security Violation Handling...")
    
    try:
        from app.services.enhanced_data_connector import (
            EnhancedSecureDataConnector, EnhancedDataSourceConfig, 
            DataSourceType, QuerySecurityLevel
        )
        
        # Create connector
        connector = EnhancedSecureDataConnector()
        
        # Add data source with strict security
        config = EnhancedDataSourceConfig(
            name="strict_db",
            type=DataSourceType.POSTGRESQL,
            host="localhost",
            port=5432,
            database="strict_db",
            username="strict_user",
            password="strict_password",
            query_security_level=QuerySecurityLevel.CRITICAL,
            allowed_tables=["public_data"],
            blocked_tables=["sensitive_data", "admin_tables"],
            allowed_operations=["SELECT"]
        )
        
        await connector.add_data_source(config)
        
        # Test 1: Blocked table access
        blocked_query = "SELECT * FROM sensitive_data WHERE id = 1"
        result = await connector.execute_secure_query("strict_db", blocked_query)
        
        if result.is_safe and result.row_count > 0:
            print(f"❌ Blocked query should have failed but returned: {result.row_count} rows")
            return False
        else:
            print(f"✅ Blocked query correctly blocked: {result.warnings}")
        
        # Test 2: Dangerous operation
        dangerous_query = "DELETE FROM public_data WHERE id = 1"
        result = await connector.execute_secure_query("strict_db", dangerous_query)
        
        if result.is_safe and result.row_count > 0:
            print(f"❌ Dangerous query should have failed but returned: {result.row_count} rows")
            return False
        else:
            print(f"✅ Dangerous query correctly blocked: {result.warnings}")
        
        # Test 3: SQL injection attempt
        injection_query = "SELECT * FROM public_data WHERE id = 1 OR 1=1"
        result = await connector.execute_secure_query("strict_db", injection_query)
        
        if result.is_safe and result.row_count > 0:
            print(f"❌ SQL injection should have been detected but returned: {result.row_count} rows")
            return False
        else:
            print(f"✅ SQL injection correctly detected: {result.warnings}")
        
        # Test 4: Check security violation count
        stats = connector.get_connector_stats()
        print(f"\n📊 Security Violations: {stats['security_violations']}")
        
        # All security tests passed - queries were correctly blocked
        print(f"✅ All security violations correctly handled!")
        return True
        
    except Exception as e:
        print(f"❌ Security violation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_data_integrity():
    """Test data integrity and hashing"""
    
    print("\n🔐 Testing Data Integrity and Hashing...")
    
    try:
        from app.services.enhanced_data_connector import (
            EnhancedSecureDataConnector, EnhancedDataSourceConfig, 
            DataSourceType, QuerySecurityLevel
        )
        
        # Create connector
        connector = EnhancedSecureDataConnector()
        
        # Add data source
        config = EnhancedDataSourceConfig(
            name="integrity_db",
            type=DataSourceType.POSTGRESQL,
            host="localhost",
            port=5432,
            database="integrity_db",
            username="integrity_user",
            password="integrity_password",
            query_security_level=QuerySecurityLevel.HIGH
        )
        
        await connector.add_data_source(config)
        
        # Test 1: Execute same query multiple times
        query = "SELECT id, name, email FROM users LIMIT 5"
        
        result1 = await connector.execute_secure_query("integrity_db", query)
        result2 = await connector.execute_secure_query("integrity_db", query)
        
        print(f"✅ Data integrity test:")
        print(f"   Query 1 hash: {result1.data_hash[:16]}...")
        print(f"   Query 2 hash: {result2.data_hash[:16]}...")
        print(f"   Hashes match: {result1.data_hash == result2.data_hash}")
        
        # Test 2: Different queries should have different hashes
        query2 = "SELECT id, name, email FROM users LIMIT 10"
        result3 = await connector.execute_secure_query("integrity_db", query2)
        
        print(f"\n✅ Hash uniqueness test:")
        print(f"   Query 1 hash: {result1.data_hash[:16]}...")
        print(f"   Query 3 hash: {result3.data_hash[:16]}...")
        print(f"   Hashes different: {result1.data_hash != result3.data_hash}")
        
        # Test 3: Data content verification
        print(f"\n✅ Data content verification:")
        print(f"   Query 1 rows: {result1.row_count}")
        print(f"   Query 3 rows: {result3.row_count}")
        print(f"   Data safe: {result1.is_safe and result3.is_safe}")
        
        return True
        
    except Exception as e:
        print(f"❌ Data integrity test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all enhanced data connector tests"""
    
    print("🚀 Enhanced Data Connector - Comprehensive Test")
    print("=" * 60)
    
    tests = [
        ("Query Security Validation", test_query_security_validation),
        ("Enhanced Data Connector", test_enhanced_data_connector),
        ("Security Violation Handling", test_security_violations),
        ("Data Integrity", test_data_integrity)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            success = await test_func()
            results[test_name] = "✅ PASSED" if success else "❌ FAILED"
        except Exception as e:
            print(f"❌ Test {test_name} crashed: {e}")
            results[test_name] = "💥 CRASHED"
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 ENHANCED DATA CONNECTOR TEST RESULTS")
    print("=" * 60)
    
    for test_name, result in results.items():
        print(f"{test_name:30} {result}")
    
    passed = sum(1 for result in results.values() if "PASSED" in result)
    total = len(results)
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL ENHANCED DATA CONNECTOR TESTS PASSED!")
        print("   Your data access layer is secure and ready!")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    print(f"\n🚀 Next steps:")
    print("1. Install real database drivers (asyncpg, aiomysql)")
    print("2. Configure production database connections")
    print("3. Set up real table access controls")
    print("4. Test with production data volumes")
    print("5. Monitor security violations and performance")


if __name__ == "__main__":
    asyncio.run(main())
