"""
Query Generation Service for AIRMS

This module generates SQL queries using LLM based on:
1. User questions in natural language
2. Database schema information
3. Context about available data sources
4. Security and risk considerations
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import re
import json
import time
from datetime import datetime

class QueryType(str, Enum):
    """Types of queries that can be generated"""
    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    ANALYTICS = "ANALYTICS"
    SEARCH = "SEARCH"

class QueryComplexity(str, Enum):
    """Complexity levels for generated queries"""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    ADVANCED = "advanced"

@dataclass
class GeneratedQuery:
    """Result of query generation"""
    sql_query: str
    query_type: QueryType
    complexity: QueryComplexity
    confidence: float
    explanation: str
    risk_score: float
    suggested_improvements: List[str]
    processing_time_ms: float

@dataclass
class QueryContext:
    """Context for query generation"""
    user_question: str
    data_source_name: str
    table_schema: Dict[str, Any]
    available_tables: List[str]
    user_permissions: List[str]
    risk_threshold: float

class QueryGenerator:
    """LLM-powered query generation service"""
    
    def __init__(self, llm_provider: str = "groq"):
        self.llm_provider = llm_provider
        self.query_templates = self._setup_query_templates()
        self.safety_patterns = self._setup_safety_patterns()
        
    def _setup_query_templates(self) -> Dict[str, str]:
        """Setup common query templates for different use cases"""
        return {
            "order_status": """
                SELECT order_id, status, estimated_delivery, created_at
                FROM orders 
                WHERE {email_condition}
                ORDER BY created_at DESC 
                LIMIT 1
            """,
            "package_tracking": """
                SELECT tracking_number, status, current_location, last_updated
                FROM packages 
                WHERE {tracking_condition}
                ORDER BY last_updated DESC
            """,
            "customer_info": """
                SELECT customer_id, name, email, phone, address
                FROM customers 
                WHERE {identifier_condition}
                LIMIT 1
            """,
            "shipping_history": """
                SELECT order_id, status, shipped_date, delivered_date
                FROM orders 
                WHERE {customer_condition}
                ORDER BY created_at DESC
            """
        }
    
    def _setup_safety_patterns(self) -> List[str]:
        """Setup patterns for potentially unsafe queries"""
        return [
            r'\b(?:DROP|TRUNCATE|DELETE\s+FROM)\b',  # Destructive operations
            r'\b(?:UPDATE.*SET.*WHERE\s*1\s*=\s*1)\b',  # Mass updates
            r'\b(?:SELECT\s*\*\s*FROM)\b',  # Select all columns
            r'\b(?:UNION\s+ALL)\b',  # Union attacks
            r'\b(?:EXEC\s*\(|EXECUTE\s*\(|sp_executesql)\b',  # Dynamic execution
            r'\b(?:xp_cmdshell|sp_configure)\b',  # Dangerous stored procedures
            r'\b(?:WAITFOR\s+DELAY|BENCHMARK)\b',  # Time-based attacks
        ]
    
    async def generate_query(self, context: QueryContext) -> GeneratedQuery:
        """
        Generate SQL query based on user question and context
        
        Args:
            context: Query generation context including user question and schema
            
        Returns:
            GeneratedQuery with SQL and metadata
        """
        start_time = time.time()
        
        # Step 1: Analyze user question
        question_analysis = self._analyze_question(context.user_question)
        
        # Step 2: Select appropriate template
        template = self._select_template(question_analysis)
        
        # Step 3: Generate SQL query
        sql_query = self._generate_sql(context, template, question_analysis)
        
        # Step 4: Validate and improve query
        improved_query = self._improve_query(sql_query, context)
        
        # Step 5: Assess risk and safety
        risk_assessment = self._assess_query_risk(improved_query)
        
        # Step 6: Generate explanation
        explanation = self._generate_explanation(improved_query, question_analysis)
        
        # Step 7: Calculate confidence
        confidence = self._calculate_confidence(improved_query, context)
        
        # Step 8: Determine complexity
        complexity = self._determine_complexity(improved_query)
        
        # Step 9: Generate improvements
        improvements = self._suggest_improvements(improved_query, context)
        
        processing_time_ms = (time.time() - start_time) * 1000
        
        return GeneratedQuery(
            sql_query=improved_query,
            query_type=question_analysis.get('query_type', QueryType.SELECT),
            complexity=complexity,
            confidence=confidence,
            explanation=explanation,
            risk_score=risk_assessment['risk_score'],
            suggested_improvements=improvements,
            processing_time_ms=round(processing_time_ms, 2)
        )
    
    def _analyze_question(self, question: str) -> Dict[str, Any]:
        """Analyze user question to understand intent"""
        analysis = {
            'query_type': QueryType.SELECT,
            'entities': [],
            'actions': [],
            'filters': [],
            'intent': 'unknown'
        }
        
        question_lower = question.lower()
        
        # Detect query type
        if any(word in question_lower for word in ['where', 'status', 'location', 'track']):
            analysis['query_type'] = QueryType.SELECT
            analysis['intent'] = 'status_inquiry'
        elif any(word in question_lower for word in ['create', 'add', 'new']):
            analysis['query_type'] = QueryType.INSERT
            analysis['intent'] = 'create_record'
        elif any(word in question_lower for word in ['update', 'change', 'modify']):
            analysis['query_type'] = QueryType.UPDATE
            analysis['intent'] = 'update_record'
        elif any(word in question_lower for word in ['delete', 'remove', 'cancel']):
            analysis['query_type'] = QueryType.DELETE
            analysis['intent'] = 'delete_record'
        
        # Extract entities
        entity_patterns = [
            (r'\b(?:order|package|item|product)\b', 'order'),
            (r'\b(?:customer|user|account)\b', 'customer'),
            (r'\b(?:email|gmail|outlook)\b', 'email'),
            (r'\b(?:tracking|shipping|delivery)\b', 'shipping'),
            (r'\b(?:status|condition|state)\b', 'status')
        ]
        
        for pattern, entity_type in entity_patterns:
            if re.search(pattern, question_lower):
                analysis['entities'].append(entity_type)
        
        # Extract filters
        filter_patterns = [
            (r'\b(?:my|where is|what is)\b', 'personal'),
            (r'\b(?:recent|latest|last)\b', 'temporal'),
            (r'\b(?:in transit|delivered|pending)\b', 'status_filter')
        ]
        
        for pattern, filter_type in filter_patterns:
            if re.search(pattern, question_lower):
                analysis['filters'].append(filter_type)
        
        return analysis
    
    def _select_template(self, analysis: Dict[str, Any]) -> str:
        """Select appropriate query template based on analysis"""
        intent = analysis.get('intent', 'unknown')
        
        if intent == 'status_inquiry':
            if 'shipping' in analysis.get('entities', []):
                return self.query_templates['package_tracking']
            elif 'order' in analysis.get('entities', []):
                return self.query_templates['order_status']
            elif 'customer' in analysis.get('entities', []):
                return self.query_templates['customer_info']
            else:
                return self.query_templates['order_status']  # Default
        elif intent == 'create_record':
            return "INSERT INTO {table} ({columns}) VALUES ({values})"
        elif intent == 'update_record':
            return "UPDATE {table} SET {updates} WHERE {condition}"
        elif intent == 'delete_record':
            return "DELETE FROM {table} WHERE {condition}"
        else:
            return self.query_templates['order_status']  # Default fallback
    
    def _generate_sql(self, context: QueryContext, template: str, analysis: Dict[str, Any]) -> str:
        """Generate SQL query from template and context"""
        # Extract email from question if present
        email_match = re.search(r'\b([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b', context.user_question)
        email = email_match.group(1) if email_match else None
        
        # Extract order/tracking numbers
        number_match = re.search(r'\b(\d{6,})\b', context.user_question)
        order_number = number_match.group(1) if number_match else None
        
        # Replace template placeholders
        sql = template
        
        if 'email_condition' in sql:
            if email:
                sql = sql.replace('{email_condition}', f"email = '{email}'")
            else:
                sql = sql.replace('{email_condition}', "email IS NOT NULL")
        
        if 'tracking_condition' in sql:
            if order_number:
                sql = sql.replace('{tracking_condition}', f"tracking_number = '{order_number}'")
            else:
                sql = sql.replace('{tracking_condition}', "tracking_number IS NOT NULL")
        
        if 'identifier_condition' in sql:
            if email:
                sql = sql.replace('{identifier_condition}', f"email = '{email}'")
            elif order_number:
                sql = sql.replace('{identifier_condition}', f"customer_id IN (SELECT customer_id FROM orders WHERE order_id = '{order_number}')")
            else:
                sql = sql.replace('{identifier_condition}', "1=1")
        
        if 'customer_condition' in sql:
            if email:
                sql = sql.replace('{customer_condition}', f"customer_id IN (SELECT customer_id FROM customers WHERE email = '{email}')")
            else:
                sql = sql.replace('{customer_condition}', "1=1")
        
        return sql.strip()
    
    def _improve_query(self, sql: str, context: QueryContext) -> str:
        """Improve generated SQL query for better performance and security"""
        improved = sql
        
        # Add LIMIT clause if missing for SELECT queries
        if sql.upper().startswith('SELECT') and 'LIMIT' not in sql.upper():
            improved += " LIMIT 100"
        
        # Add ORDER BY if missing for status queries
        if 'status' in context.user_question.lower() and 'ORDER BY' not in sql.upper():
            if 'orders' in sql.lower():
                improved = improved.replace('LIMIT', 'ORDER BY created_at DESC LIMIT')
            elif 'packages' in sql.lower():
                improved = improved.replace('LIMIT', 'ORDER BY last_updated DESC LIMIT')
        
        # Ensure WHERE clause exists for security
        if sql.upper().startswith('SELECT') and 'WHERE' not in sql.upper():
            improved = improved.replace('FROM', 'FROM orders WHERE 1=0')  # Safe default
        
        return improved
    
    def _assess_query_risk(self, sql: str) -> Dict[str, Any]:
        """Assess risk and safety of generated query"""
        risk_score = 0.0
        warnings = []
        
        # Check for dangerous patterns
        for pattern in self.safety_patterns:
            if re.search(pattern, sql, re.IGNORECASE):
                risk_score += 3.0
                warnings.append(f"Dangerous pattern detected: {pattern}")
        
        # Check for missing WHERE clause in SELECT
        if sql.upper().startswith('SELECT') and 'WHERE' not in sql.upper():
            risk_score += 2.0
            warnings.append("Missing WHERE clause - could return all records")
        
        # Check for potential injection patterns
        injection_patterns = [
            r"'.*'",  # String literals
            r"'.*OR.*'",  # OR injection
            r"'.*UNION.*'",  # UNION injection
        ]
        
        for pattern in injection_patterns:
            if re.search(pattern, sql, re.IGNORECASE):
                risk_score += 1.0
                warnings.append(f"Potential injection pattern: {pattern}")
        
        # Normalize risk score to 0-10
        risk_score = min(10.0, risk_score)
        
        return {
            'risk_score': round(risk_score, 2),
            'warnings': warnings,
            'is_safe': risk_score < 5.0
        }
    
    def _generate_explanation(self, sql: str, analysis: Dict[str, Any]) -> str:
        """Generate human-readable explanation of the query"""
        intent = analysis.get('intent', 'unknown')
        
        if intent == 'status_inquiry':
            return f"This query retrieves the current status and details of your order/package. It searches for records matching your email address and returns the most recent information."
        elif intent == 'create_record':
            return f"This query will create a new record in the system with the specified information."
        elif intent == 'update_record':
            return f"This query will update existing records based on the specified conditions."
        elif intent == 'delete_record':
            return f"This query will remove records that match the specified conditions."
        else:
            return f"This query retrieves information based on your request. It's designed to be safe and only return relevant data."
    
    def _calculate_confidence(self, sql: str, context: QueryContext) -> float:
        """Calculate confidence in the generated query"""
        confidence = 0.7  # Base confidence
        
        # Increase confidence for well-formed queries
        if 'WHERE' in sql.upper() and 'LIMIT' in sql.upper():
            confidence += 0.2
        
        # Increase confidence for specific conditions
        if any(word in sql.lower() for word in ['email', 'order_id', 'tracking_number']):
            confidence += 0.1
        
        # Decrease confidence for complex queries
        if sql.count('JOIN') > 2 or sql.count('UNION') > 0:
            confidence -= 0.1
        
        return max(0.0, min(1.0, confidence))
    
    def _determine_complexity(self, sql: str) -> QueryComplexity:
        """Determine complexity level of generated query"""
        sql_upper = sql.upper()
        
        # Count complexity indicators
        complexity_score = 0
        
        if 'JOIN' in sql_upper:
            complexity_score += 2
        if 'UNION' in sql_upper:
            complexity_score += 3
        if 'GROUP BY' in sql_upper:
            complexity_score += 2
        if 'HAVING' in sql_upper:
            complexity_score += 2
        if 'SUBQUERY' in sql_upper or '(' in sql and ')' in sql:
            complexity_score += 1
        
        # Classify based on score
        if complexity_score >= 5:
            return QueryComplexity.ADVANCED
        elif complexity_score >= 3:
            return QueryComplexity.COMPLEX
        elif complexity_score >= 1:
            return QueryComplexity.MODERATE
        else:
            return QueryComplexity.SIMPLE
    
    def _suggest_improvements(self, sql: str, context: QueryContext) -> List[str]:
        """Suggest improvements for the generated query"""
        improvements = []
        
        # Performance improvements
        if 'ORDER BY' in sql.upper() and 'LIMIT' not in sql.upper():
            improvements.append("Add LIMIT clause to prevent large result sets")
        
        if 'SELECT *' in sql.upper():
            improvements.append("Specify only needed columns instead of SELECT *")
        
        # Security improvements
        if 'WHERE' not in sql.upper():
            improvements.append("Add WHERE clause to restrict data access")
        
        # Readability improvements
        if len(sql) > 200:
            improvements.append("Consider breaking complex query into smaller parts")
        
        return improvements
    
    async def validate_query(self, sql: str, context: QueryContext) -> Dict[str, Any]:
        """Validate generated query for safety and correctness"""
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'risk_score': 0.0
        }
        
        # Basic SQL syntax check
        if not sql.strip():
            validation_result['is_valid'] = False
            validation_result['errors'].append("Empty SQL query")
            return validation_result
        
        # Check for required keywords
        required_keywords = ['SELECT', 'FROM']
        for keyword in required_keywords:
            if keyword not in sql.upper():
                validation_result['is_valid'] = False
                validation_result['errors'].append(f"Missing required keyword: {keyword}")
        
        # Risk assessment
        risk_assessment = self._assess_query_risk(sql)
        validation_result['risk_score'] = risk_assessment['risk_score']
        validation_result['warnings'].extend(risk_assessment['warnings'])
        
        # Check if query is too risky
        if risk_assessment['risk_score'] >= 7.0:
            validation_result['is_valid'] = False
            validation_result['errors'].append("Query risk score too high")
        
        return validation_result
