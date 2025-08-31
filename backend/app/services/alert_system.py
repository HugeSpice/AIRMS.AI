"""
Alert System for Risk Detection Events

Monitors risk events and sends notifications via email/webhook when thresholds are exceeded.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, EmailStr
import httpx
from app.core.config import settings
from app.core.database import db

logger = logging.getLogger(__name__)


class AlertConfig(BaseModel):
    """Configuration for alert rules"""
    alert_type: str  # "high_risk", "blocked_request", "usage_limit", "anomaly"
    threshold: float
    notification_method: str  # "email", "webhook", "both"
    notification_target: str  # email address or webhook URL
    cooldown_minutes: int = 60  # Minimum time between same alerts
    is_active: bool = True


class AlertEvent(BaseModel):
    """Alert event data"""
    alert_type: str
    user_id: str
    severity: str  # "low", "medium", "high", "critical"
    message: str
    details: Dict[str, Any]
    triggered_at: datetime
    threshold: float
    actual_value: float


class AlertManager:
    """Manages alert rules and notifications"""
    
    def __init__(self):
        self.alert_history: Dict[str, datetime] = {}
        
    async def check_risk_alerts(self, user_id: str, risk_score: float, 
                               risk_log: Dict[str, Any]) -> List[AlertEvent]:
        """Check if risk events trigger any alerts"""
        alerts = []
        
        try:
            # Get user alert rules (for now, use default rules)
            alert_rules = await self._get_user_alert_rules(user_id)
            
            for rule in alert_rules:
                if not rule.get("is_active", True):
                    continue
                    
                alert_event = None
                
                if rule["alert_type"] == "high_risk" and risk_score >= rule["threshold"]:
                    alert_event = AlertEvent(
                        alert_type="high_risk",
                        user_id=user_id,
                        severity=self._get_severity_from_risk_score(risk_score),
                        message=f"High risk detected: {risk_score:.2f}/10",
                        details={
                            "risk_score": risk_score,
                            "request_id": risk_log.get("request_id"),
                            "risks_detected": risk_log.get("risks_detected", []),
                            "llm_provider": risk_log.get("llm_provider")
                        },
                        triggered_at=datetime.now(),
                        threshold=rule["threshold"],
                        actual_value=risk_score
                    )
                
                elif rule["alert_type"] == "blocked_request" and self._is_blocked_request(risk_log):
                    alert_event = AlertEvent(
                        alert_type="blocked_request",
                        user_id=user_id,
                        severity="medium",
                        message="Request blocked due to high risk content",
                        details={
                            "risk_score": risk_score,
                            "request_id": risk_log.get("request_id"),
                            "mitigation_applied": risk_log.get("mitigation_applied", {})
                        },
                        triggered_at=datetime.now(),
                        threshold=rule["threshold"],
                        actual_value=1.0  # Boolean converted to numeric
                    )
                
                if alert_event and self._should_send_alert(alert_event, rule):
                    alerts.append(alert_event)
                    await self._send_alert_notification(alert_event, rule)
                    
        except Exception as e:
            logger.error(f"Failed to check risk alerts for user {user_id}: {e}")
            
        return alerts
    
    async def check_usage_alerts(self, user_id: str, api_key_id: str, 
                               current_usage: int, usage_limit: Optional[int]) -> List[AlertEvent]:
        """Check for API key usage limit alerts"""
        alerts = []
        
        if not usage_limit:
            return alerts
            
        try:
            alert_rules = await self._get_user_alert_rules(user_id)
            
            for rule in alert_rules:
                if rule["alert_type"] == "usage_limit" and rule.get("is_active", True):
                    usage_percentage = (current_usage / usage_limit) * 100
                    
                    if usage_percentage >= rule["threshold"]:
                        alert_event = AlertEvent(
                            alert_type="usage_limit",
                            user_id=user_id,
                            severity="medium" if usage_percentage < 95 else "high",
                            message=f"API key usage at {usage_percentage:.1f}%",
                            details={
                                "api_key_id": api_key_id,
                                "current_usage": current_usage,
                                "usage_limit": usage_limit,
                                "usage_percentage": usage_percentage
                            },
                            triggered_at=datetime.now(),
                            threshold=rule["threshold"],
                            actual_value=usage_percentage
                        )
                        
                        if self._should_send_alert(alert_event, rule):
                            alerts.append(alert_event)
                            await self._send_alert_notification(alert_event, rule)
                            
        except Exception as e:
            logger.error(f"Failed to check usage alerts for user {user_id}: {e}")
            
        return alerts
    
    async def check_anomaly_alerts(self, user_id: str) -> List[AlertEvent]:
        """Check for anomalous patterns in user behavior"""
        alerts = []
        
        try:
            # Get recent risk statistics
            recent_stats = await db.get_risk_statistics(user_id, days=1)
            historical_stats = await db.get_risk_statistics(user_id, days=30)
            
            if not recent_stats or not historical_stats:
                return alerts
                
            # Check for anomalies
            recent_avg_risk = recent_stats.get("avg_risk_score", 0)
            historical_avg_risk = historical_stats.get("avg_risk_score", 0)
            
            # Alert if recent risk is significantly higher than historical
            if historical_avg_risk > 0 and recent_avg_risk > historical_avg_risk * 2:
                alert_event = AlertEvent(
                    alert_type="anomaly",
                    user_id=user_id,
                    severity="medium",
                    message=f"Anomalous risk spike detected",
                    details={
                        "recent_avg_risk": recent_avg_risk,
                        "historical_avg_risk": historical_avg_risk,
                        "spike_multiplier": recent_avg_risk / historical_avg_risk
                    },
                    triggered_at=datetime.now(),
                    threshold=2.0,  # 2x historical average
                    actual_value=recent_avg_risk / historical_avg_risk
                )
                
                alert_rules = await self._get_user_alert_rules(user_id)
                anomaly_rule = next((r for r in alert_rules if r["alert_type"] == "anomaly"), None)
                
                if anomaly_rule and self._should_send_alert(alert_event, anomaly_rule):
                    alerts.append(alert_event)
                    await self._send_alert_notification(alert_event, anomaly_rule)
                    
        except Exception as e:
            logger.error(f"Failed to check anomaly alerts for user {user_id}: {e}")
            
        return alerts
    
    async def _get_user_alert_rules(self, user_id: str) -> List[Dict[str, Any]]:
        """Get alert rules for a user (with fallback to defaults)"""
        try:
            # For now, return default rules. In production, store in database
            return [
                {
                    "alert_type": "high_risk",
                    "threshold": 7.0,
                    "notification_method": "email",
                    "notification_target": "admin@example.com",  # Would be user's email
                    "cooldown_minutes": 60,
                    "is_active": True
                },
                {
                    "alert_type": "blocked_request",
                    "threshold": 1.0,
                    "notification_method": "webhook",
                    "notification_target": settings.ALERT_WEBHOOK_URL if hasattr(settings, 'ALERT_WEBHOOK_URL') else "",
                    "cooldown_minutes": 30,
                    "is_active": True
                },
                {
                    "alert_type": "usage_limit",
                    "threshold": 90.0,  # 90% of limit
                    "notification_method": "email",
                    "notification_target": "admin@example.com",
                    "cooldown_minutes": 360,  # 6 hours
                    "is_active": True
                },
                {
                    "alert_type": "anomaly",
                    "threshold": 2.0,
                    "notification_method": "both",
                    "notification_target": "admin@example.com",
                    "cooldown_minutes": 720,  # 12 hours
                    "is_active": True
                }
            ]
        except Exception as e:
            logger.error(f"Failed to get alert rules for user {user_id}: {e}")
            return []
    
    def _get_severity_from_risk_score(self, risk_score: float) -> str:
        """Convert risk score to severity level"""
        if risk_score >= 9.0:
            return "critical"
        elif risk_score >= 7.0:
            return "high"
        elif risk_score >= 5.0:
            return "medium"
        else:
            return "low"
    
    def _is_blocked_request(self, risk_log: Dict[str, Any]) -> bool:
        """Check if request was blocked based on mitigation"""
        mitigation = risk_log.get("mitigation_applied", {})
        if isinstance(mitigation, dict):
            return mitigation.get("content_filtering", False) or mitigation.get("rate_limiting", False)
        return False
    
    def _should_send_alert(self, alert_event: AlertEvent, rule: Dict[str, Any]) -> bool:
        """Check if alert should be sent based on cooldown rules"""
        alert_key = f"{alert_event.user_id}:{alert_event.alert_type}"
        last_sent = self.alert_history.get(alert_key)
        
        if last_sent:
            cooldown = timedelta(minutes=rule.get("cooldown_minutes", 60))
            if datetime.now() - last_sent < cooldown:
                return False
        
        self.alert_history[alert_key] = datetime.now()
        return True
    
    async def _send_alert_notification(self, alert_event: AlertEvent, rule: Dict[str, Any]):
        """Send alert notification via configured method"""
        try:
            notification_method = rule.get("notification_method", "email")
            target = rule.get("notification_target", "")
            
            if not target:
                logger.warning(f"No notification target configured for alert: {alert_event.alert_type}")
                return
            
            if notification_method in ["email", "both"]:
                await self._send_email_alert(alert_event, target)
                
            if notification_method in ["webhook", "both"]:
                await self._send_webhook_alert(alert_event, target)
                
        except Exception as e:
            logger.error(f"Failed to send alert notification: {e}")
    
    async def _send_email_alert(self, alert_event: AlertEvent, email: str):
        """Send email alert (mock implementation)"""
        try:
            # In production, integrate with email service (SendGrid, AWS SES, etc.)
            logger.info(f"EMAIL ALERT to {email}: {alert_event.message}")
            logger.info(f"Details: {alert_event.details}")
            
            # Mock email sending
            print(f"""
            📧 EMAIL ALERT
            To: {email}
            Subject: Risk Agent Alert - {alert_event.alert_type.replace('_', ' ').title()}
            
            Alert: {alert_event.message}
            Severity: {alert_event.severity.upper()}
            User ID: {alert_event.user_id}
            Triggered: {alert_event.triggered_at}
            Threshold: {alert_event.threshold}
            Actual Value: {alert_event.actual_value}
            
            Details: {alert_event.details}
            """)
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
    
    async def _send_webhook_alert(self, alert_event: AlertEvent, webhook_url: str):
        """Send webhook alert"""
        try:
            if not webhook_url:
                return
                
            payload = {
                "alert_type": alert_event.alert_type,
                "user_id": alert_event.user_id,
                "severity": alert_event.severity,
                "message": alert_event.message,
                "details": alert_event.details,
                "triggered_at": alert_event.triggered_at.isoformat(),
                "threshold": alert_event.threshold,
                "actual_value": alert_event.actual_value
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    webhook_url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code >= 400:
                    logger.error(f"Webhook alert failed: {response.status_code} {response.text}")
                else:
                    logger.info(f"Webhook alert sent successfully to {webhook_url}")
                    
        except Exception as e:
            logger.error(f"Failed to send webhook alert: {e}")


# Global alert manager instance
alert_manager = AlertManager()


# Background task functions
async def process_risk_alert(user_id: str, risk_score: float, risk_log: Dict[str, Any]):
    """Background task to process risk alerts"""
    try:
        alerts = await alert_manager.check_risk_alerts(user_id, risk_score, risk_log)
        if alerts:
            logger.info(f"Processed {len(alerts)} risk alerts for user {user_id}")
    except Exception as e:
        logger.error(f"Failed to process risk alert: {e}")


async def process_usage_alert(user_id: str, api_key_id: str, current_usage: int, usage_limit: Optional[int]):
    """Background task to process usage alerts"""
    try:
        if usage_limit:
            alerts = await alert_manager.check_usage_alerts(user_id, api_key_id, current_usage, usage_limit)
            if alerts:
                logger.info(f"Processed {len(alerts)} usage alerts for user {user_id}")
    except Exception as e:
        logger.error(f"Failed to process usage alert: {e}")


async def process_anomaly_alerts():
    """Background task to check for anomalies across all users"""
    try:
        # Get all active users (simplified query)
        # In production, this would be more efficient
        logger.info("Running anomaly detection check...")
        
        # For now, just log that the check ran
        # In production, would iterate through users and check anomalies
        
    except Exception as e:
        logger.error(f"Failed to process anomaly alerts: {e}")
