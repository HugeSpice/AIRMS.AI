"""
SQLite Adapter for Local Testing

This module provides a SQLite adapter that integrates with the enhanced data connector
for local testing and workflow demonstration.
"""

import sqlite3
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import os

logger = logging.getLogger(__name__)


class SQLiteAdapter:
    """SQLite database adapter for local testing"""
    
    def __init__(self, db_path: str):
        """Initialize SQLite adapter"""
        self.db_path = db_path
        self.connection = None
        self.status = "disconnected"
    
    def connect(self) -> bool:
        """Connect to SQLite database"""
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row  # Enable dict-like access
            self.status = "connected"
            logger.info(f"Connected to SQLite database: {self.db_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to SQLite database: {e}")
            self.status = "error"
            return False
    
    def disconnect(self) -> bool:
        """Disconnect from SQLite database"""
        try:
            if self.connection:
                self.connection.close()
                self.connection = None
                self.status = "disconnected"
                logger.info("Disconnected from SQLite database")
                return True
        except Exception as e:
            logger.error(f"Error disconnecting from SQLite database: {e}")
        return False
    
    def test_connection(self) -> bool:
        """Test SQLite connection"""
        try:
            if self.connection:
                cursor = self.connection.cursor()
                cursor.execute("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"SQLite connection test failed: {e}")
            self.status = "error"
        return False
    
    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute SQLite query"""
        try:
            if not self.connection or self.status != "connected":
                self.connect()
            
            cursor = self.connection.cursor()
            
            if params:
                cursor.execute(query, list(params.values()))
            else:
                cursor.execute(query)
            
            result = cursor.fetchall()
            
            # Convert to list of dicts
            if result:
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in result]
            else:
                return []
                
        except Exception as e:
            logger.error(f"SQLite query execution failed: {e}")
            raise
    
    def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """Get SQLite table schema"""
        try:
            query = "PRAGMA table_info(" + table_name + ")"
            result = self.execute_query(query)
            return {"table_name": table_name, "columns": result}
        except Exception as e:
            logger.error(f"Failed to get schema for table {table_name}: {e}")
            return {}
    
    def list_tables(self) -> List[str]:
        """List SQLite tables"""
        try:
            query = "SELECT name FROM sqlite_master WHERE type='table'"
            result = self.execute_query(query)
            return [row["name"] for row in result]
        except Exception as e:
            logger.error(f"Failed to list tables: {e}")
            return []
    
    def get_sample_data(self, table_name: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get sample data from a table"""
        try:
            query = f"SELECT * FROM {table_name} LIMIT {limit}"
            return self.execute_query(query)
        except Exception as e:
            logger.error(f"Failed to get sample data from {table_name}: {e}")
            return []
    
    def search_data(self, table_name: str, search_term: str, columns: List[str] = None) -> List[Dict[str, Any]]:
        """Search data in a table"""
        try:
            if not columns:
                # Get all columns if none specified
                schema = self.get_table_schema(table_name)
                columns = [col["name"] for col in schema.get("columns", [])]
            
            # Build search query
            search_conditions = []
            for col in columns:
                search_conditions.append(f"{col} LIKE '%{search_term}%'")
            
            where_clause = " OR ".join(search_conditions)
            query = f"SELECT * FROM {table_name} WHERE {where_clause}"
            
            return self.execute_query(query)
            
        except Exception as e:
            logger.error(f"Search failed in {table_name}: {e}")
            return []
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        return {
            "status": self.status,
            "database_path": self.db_path,
            "tables": self.list_tables()
        }


class LocalTestDataConnector:
    """Local test data connector using SQLite"""
    
    def __init__(self, db_path: str):
        """Initialize local test connector"""
        self.db_path = db_path
        self.adapter = SQLiteAdapter(db_path)
        self.connector_stats = {
            "total_queries": 0,
            "total_data_processed": 0,
            "pii_detections": 0,
            "data_sanitizations": 0
        }
    
    def connect(self) -> bool:
        """Connect to local database"""
        return self.adapter.connect()
    
    def disconnect(self) -> bool:
        """Disconnect from local database"""
        return self.adapter.disconnect()
    
    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute query on local database"""
        try:
            result = self.adapter.execute_query(query, params)
            
            # Update statistics
            self.connector_stats["total_queries"] += 1
            self.connector_stats["total_data_processed"] += len(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise
    
    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """Get information about a table"""
        try:
            schema = self.adapter.get_table_schema(table_name)
            sample_data = self.adapter.get_sample_data(table_name, 3)
            
            return {
                "table_name": table_name,
                "schema": schema,
                "sample_data": sample_data,
                "row_count": len(self.adapter.execute_query(f"SELECT COUNT(*) as count FROM {table_name}"))
            }
        except Exception as e:
            logger.error(f"Failed to get table info for {table_name}: {e}")
            return {}
    
    def get_database_overview(self) -> Dict[str, Any]:
        """Get overview of the entire database"""
        try:
            tables = self.adapter.list_tables()
            overview = {
                "database_path": self.db_path,
                "total_tables": len(tables),
                "tables": {}
            }
            
            for table in tables:
                overview["tables"][table] = self.get_table_info(table)
            
            return overview
            
        except Exception as e:
            logger.error(f"Failed to get database overview: {e}")
            return {}
    
    def get_connector_stats(self) -> Dict[str, Any]:
        """Get connector statistics"""
        stats = self.connector_stats.copy()
        stats["database_info"] = self.adapter.get_connection_stats()
        return stats


# Test function
def test_local_connector():
    """Test the local connector"""
    
    print("🧪 Testing Local SQLite Connector...")
    
    # Create test database if it doesn't exist
    db_path = "test_workflow.db"
    if not os.path.exists(db_path):
        print("❌ Test database not found. Please run create_local_db.py first.")
        return False
    
    try:
        # Initialize connector
        connector = LocalTestDataConnector(db_path)
        
        # Connect
        if not connector.connect():
            print("❌ Failed to connect to database")
            return False
        
        print("✅ Connected to local database")
        
        # Test basic operations
        print("\n📊 Testing Basic Operations...")
        
        # List tables
        tables = connector.adapter.list_tables()
        print(f"   Tables found: {tables}")
        
        # Get sample data
        users = connector.execute_query("SELECT * FROM users LIMIT 3")
        print(f"   Sample users: {len(users)}")
        
        # Get database overview
        overview = connector.get_database_overview()
        print(f"   Database overview: {overview['total_tables']} tables")
        
        # Test search
        search_results = connector.adapter.search_data("users", "john")
        print(f"   Search results for 'john': {len(search_results)}")
        
        # Get statistics
        stats = connector.get_connector_stats()
        print(f"   Statistics: {stats['total_queries']} queries, {stats['total_data_processed']} rows")
        
        connector.disconnect()
        print("✅ Local connector test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Local connector test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_local_connector()
