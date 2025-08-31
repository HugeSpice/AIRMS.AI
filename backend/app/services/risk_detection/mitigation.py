"""
Advanced Mitigation System for AI Risk Mitigation

This module provides comprehensive mitigation capabilities including:
- Intelligent token replacement and masking
- Dynamic blocking and allowlisting
- Escalation and reporting systems
- Real-time risk monitoring and alerting
"""

import time
import json
import logging
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta
import hashlib
import re

from .detectors.pii_detector import PIIEntity, PIIType
from .detectors.bias_detector import BiasDetection, BiasType
from .detectors.adversarial_detector import AdversarialDetection, AdversarialType
from .scorers.risk_scorer import RiskLevel

logger = logging.getLogger(__name__)


class MitigationAction(str, Enum):
    """Available mitigation actions"""
    ALLOW = "allow"
    BLOCK = "block"
    SANITIZE = "sanitize"
    ESCALATE = "escalate"
    QUARANTINE = "quarantine"
    REDACT = "redact"
    MASK = "mask"
    LOG_ONLY = "log_only"


class EscalationLevel(str, Enum):
    """Escalation levels for risk management"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


@dataclass
class MitigationRule:
    """Rule for automatic mitigation"""
    rule_id: str
    name: str
    description: str
    conditions: Dict[str, Any]
    actions: List[MitigationAction]
    priority: int
    enabled: bool = True
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            **asdict(self),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


@dataclass
class MitigationResult:
    """Result of mitigation processing"""
    original_content: str
    mitigated_content: str
    actions_taken: List[MitigationAction]
    risk_reduction: float
    processing_time_ms: float
    warnings: List[str]
    escalation_required: bool
    escalation_level: Optional[EscalationLevel]
    audit_trail: List[Dict[str, Any]]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "original_length": len(self.original_content),
            "mitigated_length": len(self.mitigated_content),
            "actions_taken": [action.value for action in self.actions_taken],
            "risk_reduction": self.risk_reduction,
            "processing_time_ms": self.processing_time_ms,
            "warnings": self.warnings,
            "escalation_required": self.escalation_required,
            "escalation_level": self.escalation_level.value if self.escalation_level else None,
            "audit_trail": self.audit_trail
        }


class TokenReplacer:
    """Advanced token replacement system with context awareness"""
    
    def __init__(self):
        """Initialize token replacer with default patterns"""
        self.replacement_patterns = self._get_default_patterns()
        self.context_preservation = True
        self.audit_mode = True
    
    def _get_default_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Get default replacement patterns for different PII types"""
        return {
            "email": {
                "pattern": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                "replacement": "[EMAIL]",
                "preserve_domain": True,
                "hash_sensitive": False
            },
            "phone": {
                "pattern": r'(\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})',
                "replacement": "[PHONE]",
                "preserve_country_code": True,
                "hash_sensitive": False
            },
            "ssn": {
                "pattern": r'\b\d{3}-\d{2}-\d{4}\b',
                "replacement": "[SSN]",
                "preserve_format": True,
                "hash_sensitive": True
            },
            "credit_card": {
                "pattern": r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
                "replacement": "[CREDIT_CARD]",
                "preserve_last_four": True,
                "hash_sensitive": True
            },
            "ip_address": {
                "pattern": r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
                "replacement": "[IP_ADDRESS]",
                "preserve_subnet": True,
                "hash_sensitive": False
            }
        }
    
    def replace_tokens(self, text: str, entities: List[PIIEntity]) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Replace detected PII entities with safe placeholders
        
        Args:
            text: Original text content
            entities: List of detected PII entities
            
        Returns:
            Tuple of (sanitized_text, audit_trail)
        """
        sanitized_text = text
        audit_trail = []
        
        for entity in entities:
            try:
                # Get replacement pattern for this entity type
                pattern_info = self.replacement_patterns.get(entity.type.value.lower(), {})
                
                if not pattern_info:
                    # Use generic replacement
                    replacement = f"[{entity.type.value.upper()}]"
                else:
                    replacement = self._create_smart_replacement(
                        entity, text, pattern_info
                    )
                
                # Perform replacement
                original_value = text[entity.start:entity.end]
                sanitized_text = sanitized_text.replace(original_value, replacement)
                
                # Log the replacement
                audit_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "entity_type": entity.type.value,
                    "original_value": original_value,
                    "replacement": replacement,
                    "confidence": entity.confidence,
                    "position": (entity.start, entity.end)
                }
                audit_trail.append(audit_entry)
                
            except Exception as e:
                logger.error(f"Error replacing token for entity {entity}: {e}")
                audit_trail.append({
                    "timestamp": datetime.now().isoformat(),
                    "error": f"Token replacement failed: {str(e)}",
                    "entity": str(entity)
                })
        
        return sanitized_text, audit_trail
    
    def _create_smart_replacement(self, entity: PIIEntity, text: str, pattern_info: Dict[str, Any]) -> str:
        """Create context-aware replacement for PII entity"""
        original_value = text[entity.start:entity.end]
        
        if pattern_info.get("hash_sensitive", False):
            # Create hash-based replacement
            hash_value = hashlib.sha256(original_value.encode()).hexdigest()[:8]
            return f"[{entity.type.value.upper()}_{hash_value}]"
        
        elif pattern_info.get("preserve_last_four", False) and len(original_value) >= 4:
            # Preserve last 4 characters (common for credit cards)
            return f"[{entity.type.value.upper()}_****{original_value[-4:]}]"
        
        elif pattern_info.get("preserve_domain", False) and "@" in original_value:
            # Preserve domain for emails
            username, domain = original_value.split("@", 1)
            return f"[USER]@{domain}"
        
        else:
            # Use standard replacement
            return pattern_info.get("replacement", f"[{entity.type.value.upper()}]")


class RiskMitigator:
    """Main risk mitigation orchestrator"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize risk mitigator"""
        self.config = config or {}
        self.token_replacer = TokenReplacer()
        self.mitigation_rules = self._load_default_rules()
        self.risk_thresholds = self._get_default_thresholds()
        self.escalation_config = self._get_default_escalation_config()
        self.audit_log = []
        self.mitigation_stats = {
            "total_processed": 0,
            "total_blocked": 0,
            "total_sanitized": 0,
            "total_escalated": 0,
            "average_risk_reduction": 0.0
        }
    
    def _load_default_rules(self) -> List[MitigationRule]:
        """Load default mitigation rules"""
        return [
            MitigationRule(
                rule_id="critical_adversarial",
                name="Block Critical Adversarial Content",
                description="Automatically block any content with critical adversarial risk",
                conditions={
                    "adversarial_risk": RiskLevel.CRITICAL,
                    "confidence_threshold": 0.8
                },
                actions=[MitigationAction.BLOCK, MitigationAction.ESCALATE],
                priority=1
            ),
            MitigationRule(
                rule_id="high_pii_risk",
                name="Sanitize High PII Risk",
                description="Sanitize content with high PII risk scores",
                conditions={
                    "pii_risk_score": 7.0,
                    "pii_entities_count": 3
                },
                actions=[MitigationAction.SANITIZE, MitigationAction.LOG_ONLY],
                priority=2
            ),
            MitigationRule(
                rule_id="bias_detection",
                name="Handle Bias Detection",
                description="Escalate and log bias detection findings",
                conditions={
                    "bias_detected": True,
                    "bias_confidence": 0.7
                },
                actions=[MitigationAction.ESCALATE, MitigationAction.LOG_ONLY],
                priority=3
            )
        ]
    
    def _get_default_thresholds(self) -> Dict[str, float]:
        """Get default risk thresholds"""
        return {
            "block_threshold": 8.0,
            "sanitize_threshold": 5.0,
            "escalate_threshold": 6.0,
            "quarantine_threshold": 9.0
        }
    
    def _get_default_escalation_config(self) -> Dict[str, Any]:
        """Get default escalation configuration"""
        return {
            "enable_escalation": True,
            "escalation_delay_minutes": 5,
            "auto_escalate_critical": True,
            "escalation_channels": ["log", "alert", "email"],
            "escalation_recipients": []
        }
    
    def mitigate_risk(self, content: str, risk_assessment: Any, 
                     entities: List[PIIEntity] = None,
                     bias_detections: List[BiasDetection] = None,
                     adversarial_detections: List[AdversarialDetection] = None) -> MitigationResult:
        """
        Apply comprehensive risk mitigation
        
        Args:
            content: Content to mitigate
            risk_assessment: Risk assessment result
            entities: Detected PII entities
            bias_detections: Bias detection results
            adversarial_detections: Adversarial detection results
            
        Returns:
            MitigationResult with applied mitigations
        """
        start_time = time.time()
        actions_taken = []
        warnings = []
        audit_trail = []
        
        try:
            # Step 1: Evaluate risk and determine actions
            actions = self._evaluate_mitigation_actions(
                risk_assessment, entities, bias_detections, adversarial_detections
            )
            
            mitigated_content = content
            
            # Step 2: Apply token replacement if needed
            if MitigationAction.SANITIZE in actions:
                mitigated_content, replacement_audit = self.token_replacer.replace_tokens(
                    content, entities or []
                )
                audit_trail.extend(replacement_audit)
                actions_taken.append(MitigationAction.SANITIZE)
            
            # Step 3: Apply blocking if needed
            if MitigationAction.BLOCK in actions:
                mitigated_content = "[CONTENT_BLOCKED_DUE_TO_SECURITY_RISK]"
                actions_taken.append(MitigationAction.BLOCK)
                warnings.append("Content blocked due to high security risk")
            
            # Step 4: Handle escalation
            escalation_required = MitigationAction.ESCALATE in actions
            escalation_level = self._determine_escalation_level(risk_assessment) if escalation_required else None
            
            if escalation_required:
                actions_taken.append(MitigationAction.ESCALATE)
                self._handle_escalation(escalation_level, risk_assessment, content)
            
            # Step 5: Calculate risk reduction
            risk_reduction = self._calculate_risk_reduction(
                risk_assessment.overall_risk_score if hasattr(risk_assessment, 'overall_risk_score') else 0.0,
                actions_taken
            )
            
            # Step 6: Update statistics
            self._update_mitigation_stats(actions_taken, risk_reduction)
            
            processing_time_ms = (time.time() - start_time) * 1000
            
            return MitigationResult(
                original_content=content,
                mitigated_content=mitigated_content,
                actions_taken=actions_taken,
                risk_reduction=risk_reduction,
                processing_time_ms=processing_time_ms,
                warnings=warnings,
                escalation_required=escalation_required,
                escalation_level=escalation_level,
                audit_trail=audit_trail
            )
            
        except Exception as e:
            logger.error(f"Error in risk mitigation: {e}")
            warnings.append(f"Mitigation error: {str(e)}")
            
            return MitigationResult(
                original_content=content,
                mitigated_content="[CONTENT_BLOCKED_DUE_TO_MITIGATION_ERROR]",
                actions_taken=[MitigationAction.BLOCK],
                risk_reduction=0.0,
                processing_time_ms=(time.time() - start_time) * 1000,
                warnings=warnings,
                escalation_required=True,
                escalation_level=EscalationLevel.CRITICAL,
                audit_trail=[{"error": str(e), "timestamp": datetime.now().isoformat()}]
            )
    
    def _evaluate_mitigation_actions(self, risk_assessment: Any, 
                                   entities: List[PIIEntity] = None,
                                   bias_detections: List[BiasDetection] = None,
                                   adversarial_detections: List[AdversarialDetection] = None) -> List[MitigationAction]:
        """Evaluate which mitigation actions to take"""
        actions = []
        
        # Check risk level
        risk_score = getattr(risk_assessment, 'overall_risk_score', 0.0)
        
        if risk_score >= self.risk_thresholds["block_threshold"]:
            actions.append(MitigationAction.BLOCK)
        elif risk_score >= self.risk_thresholds["sanitize_threshold"]:
            actions.append(MitigationAction.SANITIZE)
        
        # Check for critical adversarial content
        if adversarial_detections:
            for detection in adversarial_detections:
                if detection.risk_level == RiskLevel.CRITICAL and detection.confidence > 0.8:
                    actions.append(MitigationAction.BLOCK)
                    actions.append(MitigationAction.ESCALATE)
                    break
        
        # Check for high PII risk
        if entities and len(entities) > 3:
            actions.append(MitigationAction.SANITIZE)
        
        # Check for bias detection
        if bias_detections and any(b.confidence > 0.7 for b in bias_detections):
            actions.append(MitigationAction.ESCALATE)
        
        # Always log
        actions.append(MitigationAction.LOG_ONLY)
        
        return list(set(actions))  # Remove duplicates
    
    def _determine_escalation_level(self, risk_assessment: Any) -> EscalationLevel:
        """Determine escalation level based on risk assessment"""
        risk_score = getattr(risk_assessment, 'overall_risk_score', 0.0)
        
        if risk_score >= 9.0:
            return EscalationLevel.EMERGENCY
        elif risk_score >= 8.0:
            return EscalationLevel.CRITICAL
        elif risk_score >= 6.0:
            return EscalationLevel.HIGH
        elif risk_score >= 4.0:
            return EscalationLevel.MEDIUM
        else:
            return EscalationLevel.LOW
    
    def _handle_escalation(self, level: EscalationLevel, risk_assessment: Any, content: str) -> None:
        """Handle escalation based on level"""
        escalation_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level.value,
            "risk_score": getattr(risk_assessment, 'overall_risk_score', 0.0),
            "content_preview": content[:100] + "..." if len(content) > 100 else content,
            "actions_taken": ["escalated"]
        }
        
        self.audit_log.append(escalation_entry)
        
        # Log escalation
        logger.warning(f"Risk escalation required: {level.value} - Score: {escalation_entry['risk_score']}")
        
        # TODO: Implement actual escalation channels (email, Slack, etc.)
        if level in [EscalationLevel.CRITICAL, EscalationLevel.EMERGENCY]:
            logger.critical(f"CRITICAL ESCALATION: {escalation_entry}")
    
    def _calculate_risk_reduction(self, original_risk: float, actions: List[MitigationAction]) -> float:
        """Calculate risk reduction from mitigation actions"""
        if MitigationAction.BLOCK in actions:
            return original_risk  # 100% risk reduction
        elif MitigationAction.SANITIZE in actions:
            return original_risk * 0.7  # 70% risk reduction
        else:
            return 0.0  # No risk reduction
    
    def _update_mitigation_stats(self, actions: List[MitigationAction], risk_reduction: float) -> None:
        """Update mitigation statistics"""
        self.mitigation_stats["total_processed"] += 1
        
        if MitigationAction.BLOCK in actions:
            self.mitigation_stats["total_blocked"] += 1
        
        if MitigationAction.SANITIZE in actions:
            self.mitigation_stats["total_sanitized"] += 1
        
        if MitigationAction.ESCALATE in actions:
            self.mitigation_stats["total_escalated"] += 1
        
        # Update average risk reduction
        current_avg = self.mitigation_stats["average_risk_reduction"]
        total_processed = self.mitigation_stats["total_processed"]
        
        self.mitigation_stats["average_risk_reduction"] = (
            (current_avg * (total_processed - 1) + risk_reduction) / total_processed
        )
    
    def get_mitigation_stats(self) -> Dict[str, Any]:
        """Get current mitigation statistics"""
        return self.mitigation_stats.copy()
    
    def get_audit_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent audit log entries"""
        return self.audit_log[-limit:] if self.audit_log else []
    
    def add_mitigation_rule(self, rule: MitigationRule) -> bool:
        """Add a new mitigation rule"""
        try:
            self.mitigation_rules.append(rule)
            self.mitigation_rules.sort(key=lambda x: x.priority)
            return True
        except Exception as e:
            logger.error(f"Error adding mitigation rule: {e}")
            return False
    
    def update_risk_thresholds(self, new_thresholds: Dict[str, float]) -> None:
        """Update risk thresholds"""
        self.risk_thresholds.update(new_thresholds)
