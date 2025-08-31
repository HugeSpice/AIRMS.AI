"""
Database connection and utilities for Supabase integration
"""

import os
from typing import Optional, Dict, Any, List
from supabase import create_client, Client
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class SupabaseClient:
    """Supabase client wrapper with utility methods"""
    
    def __init__(self):
        self.supabase: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_KEY
        )
        self.service_client: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_ROLE_KEY
        )
    
    async def health_check(self) -> bool:
        """Check if Supabase connection is healthy"""
        try:
            response = self.supabase.table("users").select("id").limit(1).execute()
            return True
        except Exception as e:
            logger.error(f"Supabase health check failed: {e}")
            return False
    
    # User operations
    async def create_user(self, email: str, hashed_password: str, full_name: Optional[str] = None) -> Dict[str, Any]:
        """Create a new user"""
        user_data = {
            "email": email,
            "hashed_password": hashed_password,
            "full_name": full_name,
            "is_active": True,
            "is_verified": False
        }
        
        response = self.service_client.table("users").insert(user_data).execute()
        if response.data:
            return response.data[0]
        raise Exception("Failed to create user")
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        response = self.service_client.table("users").select("*").eq("email", email).execute()
        return response.data[0] if response.data else None
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        response = self.service_client.table("users").select("*").eq("id", user_id).execute()
        return response.data[0] if response.data else None
    
    async def update_user(self, user_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user data"""
        response = self.service_client.table("users").update(update_data).eq("id", user_id).execute()
        if response.data:
            return response.data[0]
        raise Exception("Failed to update user")
    
    # API Key operations
    async def create_api_key(self, api_key_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new API key"""
        response = self.service_client.table("api_keys").insert(api_key_data).execute()
        if response.data:
            return response.data[0]
        raise Exception("Failed to create API key")
    
    async def get_api_key_by_hash(self, key_hash: str) -> Optional[Dict[str, Any]]:
        """Get API key by hash"""
        response = self.service_client.table("api_keys").select("*").eq("key_hash", key_hash).eq("is_active", True).execute()
        return response.data[0] if response.data else None
    
    async def get_user_api_keys(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all API keys for a user"""
        response = self.service_client.table("api_keys").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
        return response.data or []
    
    async def update_api_key(self, api_key_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update API key"""
        response = self.service_client.table("api_keys").update(update_data).eq("id", api_key_id).execute()
        if response.data:
            return response.data[0]
        raise Exception("Failed to update API key")
    
    async def increment_api_key_usage(self, api_key_id: str) -> None:
        """Increment API key usage count"""
        # Get current usage
        response = self.service_client.table("api_keys").select("usage_count, usage_limit").eq("id", api_key_id).execute()
        if not response.data:
            raise Exception("API key not found")
        
        current_usage = response.data[0]["usage_count"]
        usage_limit = response.data[0]["usage_limit"]
        
        # Check if limit exceeded
        if usage_limit and current_usage >= usage_limit:
            raise Exception("API key usage limit exceeded")
        
        # Increment usage
        update_data = {
            "usage_count": current_usage + 1,
            "last_used_at": "now()"
        }
        await self.update_api_key(api_key_id, update_data)
    
    async def delete_api_key(self, api_key_id: str, user_id: str) -> bool:
        """Delete API key (soft delete by deactivating)"""
        try:
            update_data = {"is_active": False}
            response = self.service_client.table("api_keys").update(update_data).eq("id", api_key_id).eq("user_id", user_id).execute()
            return bool(response.data)
        except Exception as e:
            logger.error(f"Failed to delete API key: {e}")
            return False
    
    # Risk Log operations
    async def create_risk_log(self, log_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a risk log entry"""
        response = self.service_client.table("risk_logs").insert(log_data).execute()
        if response.data:
            return response.data[0]
        raise Exception("Failed to create risk log")
    
    async def get_user_risk_logs(self, user_id: str, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get risk logs for a user"""
        response = (
            self.service_client.table("risk_logs")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )
        return response.data or []
    
    # User Settings operations
    async def create_user_settings(self, settings_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create user settings"""
        response = self.service_client.table("user_settings").insert(settings_data).execute()
        if response.data:
            return response.data[0]
        raise Exception("Failed to create user settings")
    
    async def get_user_settings(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user settings"""
        response = self.service_client.table("user_settings").select("*").eq("user_id", user_id).execute()
        return response.data[0] if response.data else None
    
    async def update_user_settings(self, user_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user settings"""
        response = self.service_client.table("user_settings").update(update_data).eq("user_id", user_id).execute()
        if response.data:
            return response.data[0]
        raise Exception("Failed to update user settings")
    
    # Database Connection operations
    async def create_database_connection(self, connection_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create database connection"""
        response = self.service_client.table("database_connections").insert(connection_data).execute()
        if response.data:
            return response.data[0]
        raise Exception("Failed to create database connection")
    
    async def get_user_database_connections(self, user_id: str) -> List[Dict[str, Any]]:
        """Get database connections for a user"""
        response = self.service_client.table("database_connections").select("*").eq("user_id", user_id).eq("is_active", True).execute()
        return response.data or []
    
    # Analytics operations
    async def get_risk_statistics(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get risk statistics for analytics dashboard"""
        try:
            # Get date range
            from datetime import datetime, timedelta
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Query risk logs with aggregation
            response = self.service_client.table("risk_logs")\
                .select("*")\
                .eq("user_id", user_id)\
                .gte("created_at", start_date.isoformat())\
                .lte("created_at", end_date.isoformat())\
                .execute()
            
            logs = response.data or []
            
            if not logs:
                return {
                    "total_requests": 0,
                    "avg_risk_score": 0.0,
                    "high_risk_percentage": 0.0,
                    "top_risk_types": [],
                    "requests_by_provider": {},
                    "mitigation_applied_count": 0
                }
            
            # Calculate statistics
            total_requests = len(logs)
            total_risk_score = sum(float(log.get("risk_score", 0)) for log in logs)
            avg_risk_score = total_risk_score / total_requests if total_requests > 0 else 0.0
            
            high_risk_count = sum(1 for log in logs if float(log.get("risk_score", 0)) >= 7.0)
            high_risk_percentage = (high_risk_count / total_requests * 100) if total_requests > 0 else 0.0
            
            # Count by provider
            provider_counts = {}
            mitigation_count = 0
            risk_type_counts = {}
            
            for log in logs:
                provider = log.get("llm_provider", "unknown")
                provider_counts[provider] = provider_counts.get(provider, 0) + 1
                
                # Check if mitigation was applied
                mitigation = log.get("mitigation_applied", {})
                if isinstance(mitigation, dict) and any(mitigation.values()):
                    mitigation_count += 1
                
                # Count risk types
                risks = log.get("risks_detected", [])
                if isinstance(risks, list):
                    for risk in risks:
                        if isinstance(risk, dict):
                            risk_type = risk.get("type", "unknown")
                            risk_type_counts[risk_type] = risk_type_counts.get(risk_type, 0) + 1
            
            # Top risk types
            top_risk_types = [
                {"type": risk_type, "count": count}
                for risk_type, count in sorted(risk_type_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            ]
            
            return {
                "total_requests": total_requests,
                "avg_risk_score": round(avg_risk_score, 2),
                "high_risk_percentage": round(high_risk_percentage, 2),
                "top_risk_types": top_risk_types,
                "requests_by_provider": provider_counts,
                "mitigation_applied_count": mitigation_count
            }
            
        except Exception as e:
            logger.error(f"Failed to get risk statistics: {e}")
            return {}
    
    async def get_risk_timeline(self, user_id: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get risk timeline data for charts"""
        try:
            from datetime import datetime, timedelta
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Query risk logs
            response = self.service_client.table("risk_logs")\
                .select("risk_score, created_at, mitigation_applied")\
                .eq("user_id", user_id)\
                .gte("created_at", start_date.isoformat())\
                .lte("created_at", end_date.isoformat())\
                .order("created_at")\
                .execute()
            
            logs = response.data or []
            
            # Group by date
            daily_stats = {}
            for log in logs:
                date_str = log["created_at"][:10]  # Extract YYYY-MM-DD
                risk_score = float(log.get("risk_score", 0))
                
                if date_str not in daily_stats:
                    daily_stats[date_str] = {
                        "total_requests": 0,
                        "total_risk": 0.0,
                        "high_risk_count": 0,
                        "blocked_count": 0
                    }
                
                daily_stats[date_str]["total_requests"] += 1
                daily_stats[date_str]["total_risk"] += risk_score
                
                if risk_score >= 7.0:
                    daily_stats[date_str]["high_risk_count"] += 1
                
                # Check if blocked (simplified check)
                mitigation = log.get("mitigation_applied", {})
                if isinstance(mitigation, dict) and mitigation.get("content_filtering"):
                    daily_stats[date_str]["blocked_count"] += 1
            
            # Convert to timeline format
            timeline = []
            for date_str, stats in sorted(daily_stats.items()):
                avg_risk = stats["total_risk"] / stats["total_requests"] if stats["total_requests"] > 0 else 0.0
                timeline.append({
                    "date": date_str,
                    "avg_risk_score": round(avg_risk, 2),
                    "total_requests": stats["total_requests"],
                    "high_risk_count": stats["high_risk_count"],
                    "blocked_count": stats["blocked_count"]
                })
            
            return timeline
            
        except Exception as e:
            logger.error(f"Failed to get risk timeline: {e}")
            return []
    
    async def get_top_risky_prompts(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top risky prompts for analysis"""
        try:
            response = self.service_client.table("risk_logs")\
                .select("original_input, risk_score, created_at, risks_detected")\
                .eq("user_id", user_id)\
                .gte("risk_score", 5.0)\
                .order("risk_score", desc=True)\
                .limit(limit)\
                .execute()
            
            logs = response.data or []
            
            risky_prompts = []
            for log in logs:
                # Truncate long prompts
                original_input = log.get("original_input", "")
                truncated_input = original_input[:200] + "..." if len(original_input) > 200 else original_input
                
                risky_prompts.append({
                    "input": truncated_input,
                    "risk_score": float(log.get("risk_score", 0)),
                    "created_at": log.get("created_at"),
                    "risk_types": [r.get("type") for r in log.get("risks_detected", []) if isinstance(r, dict)]
                })
            
            return risky_prompts
            
        except Exception as e:
            logger.error(f"Failed to get top risky prompts: {e}")
            return []


# Global database instance
db = SupabaseClient()
