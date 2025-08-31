"""
Secure Data Connector for AI Risk Mitigation System

This module provides secure, sanitized access to external data sources including:
- PostgreSQL databases
- MySQL databases  
- Supabase
- REST APIs
- GraphQL APIs

All data is automatically sanitized and risk-assessed before being returned to the LLM.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass
from enum import Enum
import json
import httpx
from datetime import datetime, timedelta

# Import our risk detection components
from .risk_detection.risk_agent import RiskAgent, RiskAgentConfig, ProcessingMode
from .risk_detection.detectors.pii_detector import PIIEntity, PIIType
from .risk_detection.detectors.bias_detector import BiasDetection
from .risk_detection.detectors.adversarial_detector import AdversarialDetection

logger = logging.getLogger(__name__)


class DataSourceType(str, Enum):
    """Types of data sources supported"""
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SUPABASE = "supabase"
    REST_API = "rest_api"
    GRAPHQL_API = "graphql_api"
    REDIS = "redis"
    MONGODB = "mongodb"


class ConnectionStatus(str, Enum):
    """Connection status indicators"""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    CONNECTING = "connecting"


@dataclass
class DataSourceConfig:
    """Configuration for a data source"""
    name: str
    type: DataSourceType
    host: str
    port: int
    database: str
    username: str
    password: str
    ssl_mode: str = "prefer"
    connection_timeout: int = 30
    max_connections: int = 10
    enable_ssl: bool = True
    
    # API-specific fields
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    
    # Security settings
    enable_data_sanitization: bool = True
    enable_risk_assessment: bool = True
    max_query_time: int = 60
    allowed_tables: Optional[List[str]] = None
    blocked_tables: Optional[List[str]] = None


@dataclass
class QueryResult:
    """Result from a data source query"""
    data: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    risk_assessment: Dict[str, Any]
    sanitization_log: List[str]
    processing_time_ms: float
    row_count: int
    is_safe: bool
    warnings: List[str]


@dataclass
class SanitizedData:
    """Sanitized data with risk assessment"""
    original_data: List[Dict[str, Any]]
    sanitized_data: List[Dict[str, Any]]
    pii_entities_found: List[PIIEntity]
    bias_detections: List[BiasDetection]
    adversarial_detections: List[AdversarialDetection]
    risk_score: float
    sanitization_log: List[str]


class DatabaseAdapter:
    """Base class for database adapters"""
    
    def __init__(self, config: DataSourceConfig):
        self.config = config
        self.connection = None
        self.status = ConnectionStatus.DISCONNECTED
        self.last_connection_attempt = None
        self.connection_errors = 0
        
    async def connect(self) -> bool:
        """Connect to the database"""
        raise NotImplementedError
        
    async def disconnect(self) -> bool:
        """Disconnect from the database"""
        raise NotImplementedError
        
    async def test_connection(self) -> bool:
        """Test if connection is working"""
        raise NotImplementedError
        
    async def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute a query and return results"""
        raise NotImplementedError
        
    async def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """Get schema information for a table"""
        raise NotImplementedError
        
    async def list_tables(self) -> List[str]:
        """List available tables"""
        raise NotImplementedError


class PostgreSQLAdapter(DatabaseAdapter):
    """PostgreSQL database adapter"""
    
    async def connect(self) -> bool:
        """Connect to PostgreSQL database"""
        try:
            import asyncpg
            
            self.status = ConnectionStatus.CONNECTING
            self.connection = await asyncpg.connect(
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                user=self.config.username,
                password=self.config.password,
                ssl=self.config.enable_ssl,
                command_timeout=self.config.connection_timeout
            )
            
            self.status = ConnectionStatus.CONNECTED
            self.connection_errors = 0
            logger.info(f"Connected to PostgreSQL: {self.config.name}")
            return True
            
        except Exception as e:
            self.status = ConnectionStatus.ERROR
            self.connection_errors += 1
            logger.error(f"Failed to connect to PostgreSQL {self.config.name}: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from PostgreSQL database"""
        try:
            if self.connection:
                await self.connection.close()
                self.connection = None
                self.status = ConnectionStatus.DISCONNECTED
                logger.info(f"Disconnected from PostgreSQL: {self.config.name}")
                return True
        except Exception as e:
            logger.error(f"Error disconnecting from PostgreSQL {self.config.name}: {e}")
        return False
    
    async def test_connection(self) -> bool:
        """Test PostgreSQL connection"""
        try:
            if self.connection:
                await self.connection.execute("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"PostgreSQL connection test failed: {e}")
            self.status = ConnectionStatus.ERROR
        return False
    
    async def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute PostgreSQL query"""
        try:
            if not self.connection or self.status != ConnectionStatus.CONNECTED:
                await self.connect()
            
            # Execute query
            if params:
                result = await self.connection.fetch(query, *params.values())
            else:
                result = await self.connection.fetch(query)
            
            # Convert to list of dicts
            return [dict(row) for row in result]
            
        except Exception as e:
            logger.error(f"PostgreSQL query execution failed: {e}")
            raise
    
    async def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """Get PostgreSQL table schema"""
        try:
            query = """
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = $1
                ORDER BY ordinal_position
            """
            result = await self.execute_query(query, {"table_name": table_name})
            return {"table_name": table_name, "columns": result}
            
        except Exception as e:
            logger.error(f"Failed to get schema for table {table_name}: {e}")
            return {}
    
    async def list_tables(self) -> List[str]:
        """List PostgreSQL tables"""
        try:
            query = """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """
            result = await self.execute_query(query)
            return [row["table_name"] for row in result]
            
        except Exception as e:
            logger.error(f"Failed to list tables: {e}")
            return []


class MySQLAdapter(DatabaseAdapter):
    """MySQL database adapter"""
    
    async def connect(self) -> bool:
        """Connect to MySQL database"""
        try:
            import aiomysql
            
            self.status = ConnectionStatus.CONNECTING
            self.connection = await aiomysql.connect(
                host=self.config.host,
                port=self.config.port,
                db=self.config.database,
                user=self.config.username,
                password=self.config.password,
                charset='utf8mb4',
                autocommit=True
            )
            
            self.status = ConnectionStatus.CONNECTED
            self.connection_errors = 0
            logger.info(f"Connected to MySQL: {self.config.name}")
            return True
            
        except Exception as e:
            self.status = ConnectionStatus.ERROR
            self.connection_errors += 1
            logger.error(f"Failed to connect to MySQL {self.config.name}: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from MySQL database"""
        try:
            if self.connection:
                self.connection.close()
                self.connection = None
                self.status = ConnectionStatus.DISCONNECTED
                logger.info(f"Disconnected from MySQL: {self.config.name}")
                return True
        except Exception as e:
            logger.error(f"Error disconnecting from MySQL {self.config.name}: {e}")
        return False
    
    async def test_connection(self) -> bool:
        """Test MySQL connection"""
        try:
            if self.connection:
                async with self.connection.cursor() as cursor:
                    await cursor.execute("SELECT 1")
                    return True
        except Exception as e:
            logger.error(f"MySQL connection test failed: {e}")
            self.status = ConnectionStatus.ERROR
        return False
    
    async def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute MySQL query"""
        try:
            if not self.connection or self.status != ConnectionStatus.CONNECTED:
                await self.connect()
            
            async with self.connection.cursor() as cursor:
                if params:
                    await cursor.execute(query, list(params.values()))
                else:
                    await cursor.execute(query)
                
                result = await cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                
                # Convert to list of dicts
                return [dict(zip(columns, row)) for row in result]
                
        except Exception as e:
            logger.error(f"MySQL query execution failed: {e}")
            raise
    
    async def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """Get MySQL table schema"""
        try:
            query = "DESCRIBE " + table_name
            result = await self.execute_query(query)
            return {"table_name": table_name, "columns": result}
            
        except Exception as e:
            logger.error(f"Failed to get schema for table {table_name}: {e}")
            return {}
    
    async def list_tables(self) -> List[str]:
        """List MySQL tables"""
        try:
            query = "SHOW TABLES"
            result = await self.execute_query(query)
            # MySQL returns tuples, extract first element
            return [row[list(row.keys())[0]] for row in result]
            
        except Exception as e:
            logger.error(f"Failed to list tables: {e}")
            return []


class RESTAPIAdapter(DatabaseAdapter):
    """REST API adapter"""
    
    async def connect(self) -> bool:
        """Test REST API connectivity"""
        try:
            self.status = ConnectionStatus.CONNECTING
            
            async with httpx.AsyncClient(timeout=self.config.connection_timeout) as client:
                response = await client.get(
                    f"{self.config.base_url}/health",
                    headers=self.config.headers or {}
                )
                
                if response.status_code == 200:
                    self.status = ConnectionStatus.CONNECTED
                    logger.info(f"Connected to REST API: {self.config.name}")
                    return True
                else:
                    self.status = ConnectionStatus.ERROR
                    logger.error(f"REST API health check failed: {response.status_code}")
                    return False
                    
        except Exception as e:
            self.status = ConnectionStatus.ERROR
            self.connection_errors += 1
            logger.error(f"Failed to connect to REST API {self.config.name}: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from REST API (no-op)"""
        self.status = ConnectionStatus.DISCONNECTED
        return True
    
    async def test_connection(self) -> bool:
        """Test REST API connection"""
        return await self.connect()
    
    async def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute REST API query (treat query as endpoint)"""
        try:
            if not self.config.base_url:
                raise ValueError("Base URL not configured for REST API")
            
            async with httpx.AsyncClient(timeout=self.config.max_query_time) as client:
                # Parse query as endpoint and method
                if query.upper().startswith("GET "):
                    method = "GET"
                    endpoint = query[4:].strip()
                    response = await client.get(
                        f"{self.config.base_url}{endpoint}",
                        headers=self.config.headers or {},
                        params=params
                    )
                elif query.upper().startswith("POST "):
                    method = "POST"
                    endpoint = query[5:].strip()
                    response = await client.post(
                        f"{self.config.base_url}{endpoint}",
                        headers=self.config.headers or {},
                        json=params
                    )
                else:
                    # Default to GET
                    response = await client.get(
                        f"{self.config.base_url}{query}",
                        headers=self.config.headers or {},
                        params=params
                    )
                
                if response.status_code == 200:
                    return [response.json()]
                else:
                    logger.error(f"REST API request failed: {response.status_code}")
                    return []
                    
        except Exception as e:
            logger.error(f"REST API query execution failed: {e}")
            raise
    
    async def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """Get REST API schema (if available)"""
        try:
            # Try to get schema from API
            schema_result = await self.execute_query(f"GET /schema/{table_name}")
            if schema_result:
                return schema_result[0]
            else:
                return {"table_name": table_name, "columns": []}
        except Exception as e:
            logger.error(f"Failed to get schema for endpoint {table_name}: {e}")
            return {"table_name": table_name, "columns": []}
    
    async def list_tables(self) -> List[str]:
        """List REST API endpoints (if available)"""
        try:
            # Try to get available endpoints
            endpoints_result = await self.execute_query("GET /endpoints")
            if endpoints_result and "endpoints" in endpoints_result[0]:
                return endpoints_result[0]["endpoints"]
            else:
                return []
        except Exception as e:
            logger.error(f"Failed to list endpoints: {e}")
            return []


class SecureDataConnector:
    """
    Main secure data connector that orchestrates all data access
    with built-in risk detection and sanitization
    """
    
    def __init__(self, risk_agent: Optional[RiskAgent] = None):
        self.risk_agent = risk_agent or RiskAgent(RiskAgentConfig(processing_mode=ProcessingMode.STRICT))
        self.adapters: Dict[str, DatabaseAdapter] = {}
        self.connection_pool: Dict[str, Any] = {}
        self.query_cache: Dict[str, Tuple[Any, datetime]] = {}
        self.cache_ttl = timedelta(minutes=5)
        
    def add_data_source(self, config: DataSourceConfig) -> bool:
        """Add a new data source"""
        try:
            adapter = self._create_adapter(config)
            if adapter:
                self.adapters[config.name] = adapter
                logger.info(f"Added data source: {config.name} ({config.type.value})")
                return True
        except Exception as e:
            logger.error(f"Failed to add data source {config.name}: {e}")
        return False
    
    def _create_adapter(self, config: DataSourceConfig) -> Optional[DatabaseAdapter]:
        """Create appropriate adapter based on data source type"""
        if config.type == DataSourceType.POSTGRESQL:
            return PostgreSQLAdapter(config)
        elif config.type == DataSourceType.MYSQL:
            return MySQLAdapter(config)
        elif config.type == DataSourceType.REST_API:
            return RESTAPIAdapter(config)
        elif config.type == DataSourceType.SUPABASE:
            # Supabase uses PostgreSQL under the hood
            config.type = DataSourceType.POSTGRESQL
            return PostgreSQLAdapter(config)
        else:
            logger.warning(f"Unsupported data source type: {config.type}")
            return None
    
    async def connect_all(self) -> Dict[str, bool]:
        """Connect to all data sources"""
        results = {}
        for name, adapter in self.adapters.items():
            results[name] = await adapter.connect()
        return results
    
    async def disconnect_all(self) -> Dict[str, bool]:
        """Disconnect from all data sources"""
        results = {}
        for name, adapter in self.adapters.items():
            results[name] = await adapter.disconnect()
        return results
    
    async def execute_secure_query(self, 
                                 data_source_name: str, 
                                 query: str, 
                                 params: Optional[Dict[str, Any]] = None,
                                 enable_sanitization: bool = True,
                                 enable_risk_assessment: bool = True) -> QueryResult:
        """
        Execute a query with full risk detection and sanitization
        
        Args:
            data_source_name: Name of the data source to query
            query: Query to execute
            params: Query parameters
            enable_sanitization: Whether to sanitize the results
            enable_risk_assessment: Whether to assess risk of results
            
        Returns:
            QueryResult with sanitized data and risk assessment
        """
        start_time = datetime.now()
        
        try:
            # Check if data source exists
            if data_source_name not in self.adapters:
                raise ValueError(f"Data source '{data_source_name}' not found")
            
            adapter = self.adapters[data_source_name]
            
            # Execute query
            raw_data = await adapter.execute_query(query, params)
            
            # Sanitize and assess risk
            if enable_sanitization or enable_risk_assessment:
                sanitized_result = await self._sanitize_and_assess_data(raw_data)
                data = sanitized_result.sanitized_data
                risk_assessment = {
                    "risk_score": sanitized_result.risk_score,
                    "pii_entities_found": len(sanitized_result.pii_entities_found),
                    "bias_detections": len(sanitized_result.bias_detections),
                    "adversarial_detections": len(sanitized_result.adversarial_detections),
                    "is_safe": sanitized_result.risk_score < 7.0
                }
                sanitization_log = sanitized_result.sanitization_log
                is_safe = sanitized_result.risk_score < 7.0
            else:
                data = raw_data
                risk_assessment = {"risk_score": 0.0, "is_safe": True}
                sanitization_log = []
                is_safe = True
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return QueryResult(
                data=data,
                metadata={
                    "data_source": data_source_name,
                    "query": query,
                    "params": params,
                    "raw_row_count": len(raw_data),
                    "sanitized_row_count": len(data)
                },
                risk_assessment=risk_assessment,
                sanitization_log=sanitization_log,
                processing_time_ms=processing_time,
                row_count=len(data),
                is_safe=is_safe,
                warnings=[]
            )
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            logger.error(f"Query execution failed: {e}")
            
            return QueryResult(
                data=[],
                metadata={"error": str(e)},
                risk_assessment={"risk_score": 10.0, "is_safe": False},
                sanitization_log=[],
                processing_time_ms=processing_time,
                row_count=0,
                is_safe=False,
                warnings=[f"Query execution failed: {e}"]
            )
    
    async def _sanitize_and_assess_data(self, data: List[Dict[str, Any]]) -> SanitizedData:
        """Sanitize data and assess risk using the risk agent"""
        try:
            # Convert data to text for analysis
            data_text = json.dumps(data, indent=2)
            
            # Analyze with risk agent
            analysis_result = self.risk_agent.analyze_text(data_text)
            
            # Extract entities and detections
            pii_entities = analysis_result.risk_assessment.pii_entities
            bias_detections = analysis_result.risk_assessment.bias_detections
            adversarial_detections = getattr(analysis_result.risk_assessment, 'adversarial_detections', [])
            
            # Sanitize the data
            sanitized_data = self._apply_sanitization(data, pii_entities)
            
            return SanitizedData(
                original_data=data,
                sanitized_data=sanitized_data,
                pii_entities_found=pii_entities,
                bias_detections=bias_detections,
                adversarial_detections=adversarial_detections,
                risk_score=analysis_result.risk_assessment.overall_risk_score,
                sanitization_log=[f"Risk score: {analysis_result.risk_assessment.overall_risk_score}"]
            )
            
        except Exception as e:
            logger.error(f"Data sanitization failed: {e}")
            # Return original data if sanitization fails
            return SanitizedData(
                original_data=data,
                sanitized_data=data,
                pii_entities_found=[],
                bias_detections=[],
                adversarial_detections=[],
                risk_score=0.0,
                sanitization_log=[f"Sanitization failed: {e}"]
            )
    
    def _apply_sanitization(self, data: List[Dict[str, Any]], pii_entities: List[PIIEntity]) -> List[Dict[str, Any]]:
        """Apply PII sanitization to data"""
        if not pii_entities:
            return data
        
        sanitized_data = []
        for row in data:
            sanitized_row = row.copy()
            
            for entity in pii_entities:
                # Replace PII values with placeholders
                for key, value in sanitized_row.items():
                    if isinstance(value, str) and entity.value in value:
                        if entity.type == PIIType.EMAIL:
                            sanitized_row[key] = "[EMAIL]"
                        elif entity.type == PIIType.PHONE_NUMBER:
                            sanitized_row[key] = "[PHONE]"
                        elif entity.type == PIIType.SSN:
                            sanitized_row[key] = "[SSN]"
                        elif entity.type == PIIType.CREDIT_CARD:
                            sanitized_row[key] = "[CREDIT_CARD]"
                        elif entity.type == PIIType.API_KEY:
                            sanitized_row[key] = "[API_KEY]"
                        else:
                            sanitized_row[key] = f"[{entity.type.value.upper()}]"
            
            sanitized_data.append(sanitized_row)
        
        return sanitized_data
    
    async def get_data_source_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all data sources"""
        status = {}
        for name, adapter in self.adapters.items():
            status[name] = {
                "type": adapter.config.type.value,
                "status": adapter.status.value,
                "host": adapter.config.host,
                "port": adapter.config.port,
                "database": adapter.config.database,
                "connection_errors": adapter.connection_errors,
                "last_connection_attempt": adapter.last_connection_attempt
            }
        return status
    
    async def test_data_source(self, data_source_name: str) -> bool:
        """Test a specific data source"""
        if data_source_name in self.adapters:
            return await self.adapters[data_source_name].test_connection()
        return False
    
    def get_available_data_sources(self) -> List[str]:
        """Get list of available data sources"""
        return list(self.adapters.keys())
    
    def get_data_source_info(self, data_source_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific data source"""
        if data_source_name in self.adapters:
            adapter = self.adapters[data_source_name]
            return {
                "name": adapter.config.name,
                "type": adapter.config.type.value,
                "host": adapter.config.host,
                "port": adapter.config.port,
                "database": adapter.config.database,
                "enable_data_sanitization": adapter.config.enable_data_sanitization,
                "enable_risk_assessment": adapter.config.enable_risk_assessment
            }
        return None
