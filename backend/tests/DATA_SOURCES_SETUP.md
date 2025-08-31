# 🗄️ Secure Data Connector Setup Guide

This guide shows you how to set up and use the Secure Data Connector to access external data sources while maintaining full security and risk detection.

## 🚀 Quick Start

### 1. Install Database Dependencies

```bash
# Install required database drivers
pip install asyncpg aiomysql httpx

# Or install all requirements
pip install -r requirements.txt
```

### 2. Configure Your Data Sources

Edit `data_sources_config.json` with your actual database credentials:

```json
{
  "data_sources": {
    "production_db": {
      "name": "production_db",
      "type": "postgresql",
      "host": "your-postgres-host.com",
      "port": 5432,
      "database": "your_database_name",
      "username": "your_username",
      "password": "your_secure_password",
      "enable_data_sanitization": true,
      "enable_risk_assessment": true
    }
  }
}
```

### 3. Test the Connection

```python
import asyncio
from app.services.secure_data_connector import SecureDataConnector, DataSourceConfig, DataSourceType

async def test_connection():
    # Create connector
    connector = SecureDataConnector()
    
    # Add your data source
    config = DataSourceConfig(
        name="test_db",
        type=DataSourceType.POSTGRESQL,
        host="localhost",
        port=5432,
        database="test_db",
        username="test_user",
        password="test_password"
    )
    
    connector.add_data_source(config)
    
    # Test connection
    status = await connector.get_data_source_status()
    print(f"Connection status: {status}")

# Run the test
asyncio.run(test_connection())
```

## 🔌 Supported Data Sources

### PostgreSQL
- **Type**: `DataSourceType.POSTGRESQL`
- **Driver**: `asyncpg`
- **Features**: Full SQL support, connection pooling, SSL

### MySQL
- **Type**: `DataSourceType.MYSQL`
- **Driver**: `aiomysql`
- **Features**: Full SQL support, connection pooling

### Supabase
- **Type**: `DataSourceType.SUPABASE`
- **Driver**: `asyncpg` (PostgreSQL-based)
- **Features**: Same as PostgreSQL + Supabase-specific features

### REST APIs
- **Type**: `DataSourceType.REST_API`
- **Driver**: `httpx`
- **Features**: GET/POST requests, custom headers, API keys

## 🛡️ Security Features

### Automatic PII Detection
- All query results are automatically scanned for PII
- Sensitive data is automatically masked/replaced
- Configurable PII types and replacement strategies

### Risk Assessment
- Every data response is risk-assessed
- High-risk data can be blocked automatically
- Comprehensive logging of all security events

### Access Control
- Table-level access control (allow/block lists)
- Connection-level security (SSL, timeouts)
- Query-level restrictions and monitoring

## 📊 Usage Examples

### Basic Query Execution

```python
# Execute a secure query
result = await connector.execute_secure_query(
    data_source_name="production_db",
    query="SELECT id, name, email FROM users LIMIT 10",
    enable_sanitization=True,
    enable_risk_assessment=True
)

print(f"Risk Score: {result.risk_assessment['risk_score']}")
print(f"Is Safe: {result.is_safe}")
print(f"Data: {result.data}")
```

### Handling PII Data

```python
# Query that might contain PII
result = await connector.execute_secure_query(
    data_source_name="production_db",
    query="SELECT * FROM users WHERE id = 1",
    enable_sanitization=True,
    enable_risk_assessment=True
)

if result.risk_assessment['pii_entities_found'] > 0:
    print(f"⚠️  PII detected: {result.risk_assessment['pii_entities_found']} entities")
    print(f"🔒 Data has been sanitized for security")

# The returned data is automatically sanitized
print(f"Sanitized data: {result.data}")
```

### REST API Integration

```python
# GET request to external API
result = await connector.execute_secure_query(
    data_source_name="external_api",
    query="GET /users",
    params={"limit": 5, "status": "active"},
    enable_sanitization=True,
    enable_risk_assessment=True
)

# POST request to external API
result = await connector.execute_secure_query(
    data_source_name="external_api",
    query="POST /analytics",
    params={"event": "user_login", "user_id": 123},
    enable_sanitization=True,
    enable_risk_assessment=True
)
```

## 🔧 Configuration Options

### Data Source Configuration

```python
config = DataSourceConfig(
    name="my_db",
    type=DataSourceType.POSTGRESQL,
    host="localhost",
    port=5432,
    database="my_database",
    username="my_user",
    password="my_password",
    
    # Security settings
    enable_data_sanitization=True,
    enable_risk_assessment=True,
    enable_ssl=True,
    
    # Access control
    allowed_tables=["users", "orders", "products"],
    blocked_tables=["passwords", "secrets", "admin"],
    
    # Performance settings
    connection_timeout=30,
    max_connections=10,
    max_query_time=60
)
```

### Risk Agent Configuration

```python
from app.services.risk_detection.risk_agent import RiskAgent, RiskAgentConfig, ProcessingMode

# Strict mode for maximum security
risk_agent = RiskAgent(RiskAgentConfig(
    processing_mode=ProcessingMode.STRICT,
    pii_confidence_threshold=0.6,
    bias_confidence_threshold=0.7,
    enable_adversarial_detection=True
))

# Use with connector
connector = SecureDataConnector(risk_agent=risk_agent)
```

## 📈 Monitoring and Health Checks

### Check Data Source Status

```python
# Get status of all data sources
status = await connector.get_data_source_status()
for name, info in status.items():
    print(f"{name}: {info['status']} ({info['type']})")

# Test specific data source
is_working = await connector.test_data_source("production_db")
print(f"Production DB working: {is_working}")
```

### Performance Monitoring

```python
# Execute query with timing
result = await connector.execute_secure_query(
    data_source_name="production_db",
    query="SELECT COUNT(*) FROM users"
)

print(f"Query executed in {result.processing_time_ms:.2f}ms")
print(f"Rows returned: {result.row_count}")
```

## 🚨 Error Handling

### Connection Errors

```python
try:
    result = await connector.execute_secure_query(
        data_source_name="production_db",
        query="SELECT * FROM users"
    )
except Exception as e:
    print(f"Query failed: {e}")
    
    # Check connection status
    status = await connector.get_data_source_status()
    print(f"Database status: {status['production_db']['status']}")
```

### Security Violations

```python
result = await connector.execute_secure_query(
    data_source_name="production_db",
    query="SELECT * FROM users"
)

if not result.is_safe:
    print(f"⚠️  High-risk data detected!")
    print(f"Risk score: {result.risk_assessment['risk_score']}")
    print(f"Warnings: {result.warnings}")
    
    # Handle high-risk data appropriately
    if result.risk_assessment['risk_score'] > 8.0:
        print("🚫 Data blocked due to high risk")
        return None
```

## 🔒 Best Practices

### 1. **Always Enable Sanitization**
```python
# Good: Sanitization enabled
result = await connector.execute_secure_query(
    data_source_name="db",
    query="SELECT * FROM users",
    enable_sanitization=True,  # ✅
    enable_risk_assessment=True
)

# Bad: Sanitization disabled
result = await connector.execute_secure_query(
    data_source_name="db",
    query="SELECT * FROM users",
    enable_sanitization=False,  # ❌
    enable_risk_assessment=False
)
```

### 2. **Use Strict Processing Mode**
```python
# Good: Strict mode for production
risk_agent = RiskAgent(RiskAgentConfig(
    processing_mode=ProcessingMode.STRICT  # ✅
))

# Bad: Permissive mode in production
risk_agent = RiskAgent(RiskAgentConfig(
    processing_mode=ProcessingMode.PERMISSIVE  # ❌
))
```

### 3. **Implement Proper Access Control**
```python
# Good: Restrict table access
config = DataSourceConfig(
    # ... other settings ...
    allowed_tables=["public_data", "user_profiles"],  # ✅
    blocked_tables=["passwords", "admin", "secrets"]   # ✅
)

# Bad: No access restrictions
config = DataSourceConfig(
    # ... other settings ...
    allowed_tables=None,  # ❌
    blocked_tables=None   # ❌
)
```

### 4. **Monitor and Log Everything**
```python
# Good: Comprehensive logging
import logging
logging.basicConfig(level=logging.INFO)

# The connector automatically logs:
# - All queries executed
# - Security violations detected
# - Performance metrics
# - Connection status changes
```

## 🧪 Testing

### Run the Example

```bash
# Run the comprehensive example
python example_data_usage.py

# This will show you:
# - How to set up data sources
# - How to execute secure queries
# - How risk detection works
# - How data is sanitized
```

### Test with Your Database

1. Update `data_sources_config.json` with your credentials
2. Run the example script
3. Check the logs for any connection issues
4. Verify that PII detection is working
5. Test with queries that contain sensitive data

## 🆘 Troubleshooting

### Common Issues

#### 1. **Connection Failed**
```bash
# Check if database is running
# Verify credentials
# Check firewall settings
# Ensure database accepts connections from your IP
```

#### 2. **Import Errors**
```bash
# Install missing dependencies
pip install asyncpg aiomysql httpx

# Check Python path
python -c "import sys; print(sys.path)"
```

#### 3. **PII Not Detected**
```python
# Check confidence thresholds
risk_agent = RiskAgent(RiskAgentConfig(
    pii_confidence_threshold=0.6,  # Lower = more sensitive
    processing_mode=ProcessingMode.STRICT
))
```

#### 4. **Performance Issues**
```python
# Reduce connection pool size
config = DataSourceConfig(
    max_connections=5,  # Reduce from default 10
    connection_timeout=15  # Reduce from default 30
)
```

## 📚 Next Steps

1. **Set up your databases** using the configuration examples
2. **Test the connections** with simple queries
3. **Integrate with your application** using the provided examples
4. **Monitor and tune** the security settings for your needs
5. **Scale up** by adding more data sources as needed

## 🎯 What You've Built

With the Secure Data Connector, you now have:

✅ **Enterprise-grade security** for all data access  
✅ **Automatic PII detection and sanitization**  
✅ **Multi-database support** (PostgreSQL, MySQL, REST APIs)  
✅ **Real-time risk assessment** of all data  
✅ **Comprehensive monitoring and logging**  
✅ **Easy integration** with existing systems  

Your AI Risk Mitigation System is now **production-ready** and can securely access external data while maintaining the highest security standards! 🚀
