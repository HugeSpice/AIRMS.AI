"""
Risk Scoring Engine for calculating comprehensive risk scores.

This module combines various risk factors including:
- PII detection results
- Bias detection results  
- Content analysis
- Context-aware scoring
- Configurable risk weights
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

from ..detectors.pii_detector import PIIEntity, PIIType
from ..detectors.bias_detector import BiasDetection, BiasType
from ..detectors.adversarial_detector import AdversarialDetection


class RiskLevel(str, Enum):
    """Risk level classifications"""
    SAFE = "safe"           # 0-2
    LOW = "low"             # 2-4
    MEDIUM = "medium"       # 4-6
    HIGH = "high"           # 6-8
    CRITICAL = "critical"   # 8-10


@dataclass
class RiskAssessment:
    """Comprehensive risk assessment result"""
    overall_risk_score: float
    risk_level: RiskLevel
    pii_risk_score: float
    bias_risk_score: float
    content_risk_score: float
    context_risk_score: float
    
    # Detailed breakdowns
    pii_entities: List[PIIEntity]
    bias_detections: List[BiasDetection]
    risk_factors: List[str]
    mitigation_suggestions: List[str]
    
    # Metadata
    text_length: int
    processing_time_ms: float
    confidence: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "overall_risk_score": self.overall_risk_score,
            "risk_level": self.risk_level.value,
            "pii_risk_score": self.pii_risk_score,
            "bias_risk_score": self.bias_risk_score,
            "content_risk_score": self.content_risk_score,
            "context_risk_score": self.context_risk_score,
            "pii_entities_count": len(self.pii_entities),
            "bias_detections_count": len(self.bias_detections),
            "risk_factors": self.risk_factors,
            "mitigation_suggestions": self.mitigation_suggestions,
            "text_length": self.text_length,
            "processing_time_ms": self.processing_time_ms,
            "confidence": self.confidence
        }


class RiskScorer:
    """Advanced risk scoring engine with configurable weights and thresholds"""
    
    def __init__(self, custom_weights: Optional[Dict[str, float]] = None, 
                 custom_thresholds: Optional[Dict[str, float]] = None):
        """
        Initialize risk scorer with optional custom configuration
        
        Args:
            custom_weights: Custom weights for different risk components
            custom_thresholds: Custom thresholds for risk level classification
        """
        self.weights = self._get_default_weights()
        self.thresholds = self._get_default_thresholds()
        
        if custom_weights:
            self.weights.update(custom_weights)
        
        if custom_thresholds:
            self.thresholds.update(custom_thresholds)
    
    def _get_default_weights(self) -> Dict[str, float]:
        """Get default weights for risk components"""
        return {
            # Component weights (must sum to 1.0)
            "pii_weight": 0.4,      # PII detection contributes 40%
            "bias_weight": 0.3,     # Bias detection contributes 30%
            "content_weight": 0.2,  # Content analysis contributes 20%
            "context_weight": 0.1,  # Context analysis contributes 10%
            
            # PII type weights (relative importance)
            "pii_ssn": 10.0,
            "pii_credit_card": 9.0,
            "pii_financial": 8.0,
            "pii_email": 6.0,
            "pii_phone": 5.0,
            "pii_address": 4.0,
            "pii_ip_address": 3.0,
            "pii_date": 2.0,
            "pii_url": 2.0,
            "pii_name": 1.0,
            
            # Bias severity weights
            "bias_critical": 10.0,
            "bias_high": 7.5,
            "bias_medium": 5.0,
            "bias_low": 2.5,
            
            # Content factors
            "content_length_factor": 0.1,
            "content_complexity_factor": 0.1,
            "content_urgency_factor": 0.2,
        }
    
    def _get_default_thresholds(self) -> Dict[str, float]:
        """Get default thresholds for risk level classification"""
        return {
            "safe_threshold": 2.0,
            "low_threshold": 4.0,
            "medium_threshold": 6.0,
            "high_threshold": 8.0,
            # Anything above high_threshold is critical
        }
    
    def calculate_risk_score(self, text: str, pii_entities: List[PIIEntity], 
                           bias_detections: List[BiasDetection],
                           processing_time_ms: float = 0.0,
                           adversarial_detections: List[AdversarialDetection] = None) -> RiskAssessment:
        """
        Calculate comprehensive risk score for given text and detections
        
        Args:
            text: Original text being analyzed
            pii_entities: List of detected PII entities
            bias_detections: List of detected bias instances
            processing_time_ms: Time taken for analysis
            
        Returns:
            RiskAssessment with comprehensive risk analysis
        """
        import time
        start_time = time.time()
        
        # Calculate individual risk components
        pii_risk = self._calculate_pii_risk(pii_entities)
        bias_risk = self._calculate_bias_risk(bias_detections)
        content_risk = self._calculate_content_risk(text)
        context_risk = self._calculate_context_risk(text, pii_entities, bias_detections)
        
        # Add adversarial risk calculation
        adversarial_risk = 0.0
        if adversarial_detections:
            # Critical risk for any adversarial content
            adversarial_risk = 10.0
        
        # Calculate weighted overall risk score
        overall_risk = (
            self.weights.get("pii_weight", 0.3) * pii_risk +
            self.weights.get("bias_weight", 0.3) * bias_risk +
            self.weights.get("content_weight", 0.2) * content_risk +
            self.weights.get("context_weight", 0.1) * context_risk +
            self.weights.get("adversarial_weight", 0.1) * adversarial_risk  # NEW
        )
        
        # Ensure score is within bounds
        overall_risk = max(0.0, min(10.0, overall_risk))
        
        # Determine risk level
        risk_level = self._classify_risk_level(overall_risk)
        
        # Calculate confidence
        confidence = self._calculate_confidence(text, pii_entities, bias_detections)
        
        # Generate risk factors and mitigation suggestions
        risk_factors = self._identify_risk_factors(pii_entities, bias_detections, content_risk, context_risk)
        mitigation_suggestions = self._generate_mitigation_suggestions(pii_entities, bias_detections, risk_level)
        
        # Calculate processing time
        if processing_time_ms == 0.0:
            processing_time_ms = (time.time() - start_time) * 1000
        
        return RiskAssessment(
            overall_risk_score=round(overall_risk, 2),
            risk_level=risk_level,
            pii_risk_score=round(pii_risk, 2),
            bias_risk_score=round(bias_risk, 2),
            content_risk_score=round(content_risk, 2),
            context_risk_score=round(context_risk, 2),
            pii_entities=pii_entities,
            bias_detections=bias_detections,
            risk_factors=risk_factors,
            mitigation_suggestions=mitigation_suggestions,
            text_length=len(text),
            processing_time_ms=round(processing_time_ms, 2),
            confidence=round(confidence, 2)
        )
    
    def _calculate_pii_risk(self, pii_entities: List[PIIEntity]) -> float:
        """Calculate risk score based on PII entities"""
        if not pii_entities:
            return 0.0
        
        total_risk = 0.0
        
        for entity in pii_entities:
            # Get weight for this PII type
            weight_key = f"pii_{entity.type.value}"
            weight = self.weights.get(weight_key, 1.0)
            
            # Calculate entity risk (weight * confidence)
            entity_risk = weight * entity.confidence
            total_risk += entity_risk
        
        # Normalize to 0-10 scale
        # Consider both the number of entities and their individual risks
        max_possible_risk = len(pii_entities) * 10.0
        normalized_risk = min(10.0, (total_risk / max_possible_risk) * 10.0) if max_possible_risk > 0 else 0.0
        
        # Apply multiplier for multiple high-risk entities
        if len([e for e in pii_entities if e.type in [PIIType.SSN, PIIType.CREDIT_CARD, PIIType.FINANCIAL]]) > 1:
            normalized_risk *= 1.2
        
        return min(10.0, normalized_risk)
    
    def _calculate_bias_risk(self, bias_detections: List[BiasDetection]) -> float:
        """Calculate risk score based on bias detections"""
        if not bias_detections:
            return 0.0
        
        total_risk = 0.0
        
        for detection in bias_detections:
            # Get weight for this bias severity
            weight_key = f"bias_{detection.severity}"
            weight = self.weights.get(weight_key, 1.0)
            
            # Calculate detection risk (weight * confidence)
            detection_risk = weight * detection.confidence
            total_risk += detection_risk
        
        # Normalize to 0-10 scale
        max_possible_risk = len(bias_detections) * 10.0
        normalized_risk = min(10.0, (total_risk / max_possible_risk) * 10.0) if max_possible_risk > 0 else 0.0
        
        # Apply penalty for multiple critical/high severity detections
        critical_high_count = len([d for d in bias_detections if d.severity in ["critical", "high"]])
        if critical_high_count > 1:
            normalized_risk *= 1.5
        
        return min(10.0, normalized_risk)
    
    def _calculate_content_risk(self, text: str) -> float:
        """Calculate risk score based on content characteristics"""
        content_risk = 0.0
        
        # Length factor (very long or very short texts might be riskier)
        length = len(text)
        if length < 10:  # Very short
            content_risk += 1.0
        elif length > 10000:  # Very long
            content_risk += 0.5
        
        # Complexity factors
        import re
        
        # Check for suspicious patterns
        suspicious_patterns = [
            r'\b(?:password|token|secret|key|credential)\s*[:=]\s*\w+',  # Credentials
            r'\b(?:api[_\s]?key|access[_\s]?token)\b',                   # API keys
            r'\b(?:admin|root|administrator)\s*[:=]',                    # Admin access
            r'\b(?:sql|inject|script|exec|eval)\b',                     # Injection patterns
            r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>',       # Script tags
            r'\b(?:localhost|127\.0\.0\.1|192\.168\.)',                 # Local addresses
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                content_risk += 1.0
        
        # Check for urgency indicators
        urgency_patterns = [
            r'\b(?:urgent|immediate|asap|emergency|critical|now)\b',
            r'\b(?:deadline|expire|limited\s+time|act\s+fast)\b',
            r'\b(?:don\'t\s+tell|keep\s+secret|confidential|private)\b',
        ]
        
        urgency_count = 0
        for pattern in urgency_patterns:
            urgency_count += len(re.findall(pattern, text, re.IGNORECASE))
        
        if urgency_count > 0:
            content_risk += min(2.0, urgency_count * 0.5)
        
        # Normalize to 0-10 scale
        return min(10.0, content_risk)
    
    def _calculate_context_risk(self, text: str, pii_entities: List[PIIEntity], 
                              bias_detections: List[BiasDetection]) -> float:
        """Calculate risk score based on context and entity relationships"""
        context_risk = 0.0
        
        # Risk from entity proximity (PII entities close together)
        if len(pii_entities) > 1:
            for i, entity1 in enumerate(pii_entities):
                for entity2 in pii_entities[i+1:]:
                    distance = abs(entity1.start - entity2.start)
                    if distance < 100:  # Entities within 100 characters
                        context_risk += 0.5
        
        # Risk from PII + bias combination
        if pii_entities and bias_detections:
            context_risk += 1.0
        
        # Risk from multiple high-confidence detections
        high_confidence_entities = [e for e in pii_entities if e.confidence > 0.8]
        high_confidence_bias = [b for b in bias_detections if b.confidence > 0.8]
        
        if len(high_confidence_entities) > 2 or len(high_confidence_bias) > 1:
            context_risk += 1.0
        
        # Risk from sensitive context keywords
        import re
        sensitive_contexts = [
            r'\b(?:login|signin|authenticate|authorize)\b',
            r'\b(?:payment|billing|financial|transaction)\b',
            r'\b(?:medical|health|diagnosis|treatment)\b',
            r'\b(?:legal|court|lawsuit|confidential)\b',
        ]
        
        for pattern in sensitive_contexts:
            if re.search(pattern, text, re.IGNORECASE):
                context_risk += 0.5
        
        return min(10.0, context_risk)
    
    def _classify_risk_level(self, risk_score: float) -> RiskLevel:
        """Classify risk score into risk level"""
        if risk_score >= self.thresholds["high_threshold"]:
            return RiskLevel.CRITICAL
        elif risk_score >= self.thresholds["medium_threshold"]:
            return RiskLevel.HIGH
        elif risk_score >= self.thresholds["low_threshold"]:
            return RiskLevel.MEDIUM
        elif risk_score >= self.thresholds["safe_threshold"]:
            return RiskLevel.LOW
        else:
            return RiskLevel.SAFE
    
    def _calculate_confidence(self, text: str, pii_entities: List[PIIEntity], 
                            bias_detections: List[BiasDetection]) -> float:
        """Calculate confidence in the risk assessment"""
        if not pii_entities and not bias_detections:
            return 0.95  # High confidence in "safe" assessment
        
        # Average confidence of detections
        all_confidences = []
        all_confidences.extend([e.confidence for e in pii_entities])
        all_confidences.extend([b.confidence for b in bias_detections])
        
        if not all_confidences:
            return 0.5
        
        avg_confidence = sum(all_confidences) / len(all_confidences)
        
        # Adjust based on text length and detection count
        text_length = len(text)
        detection_count = len(pii_entities) + len(bias_detections)
        
        # More detections in longer text = higher confidence
        if text_length > 100 and detection_count > 2:
            avg_confidence += 0.1
        elif text_length < 50 and detection_count > 0:
            avg_confidence -= 0.1
        
        return max(0.0, min(1.0, avg_confidence))
    
    def _identify_risk_factors(self, pii_entities: List[PIIEntity], 
                             bias_detections: List[BiasDetection],
                             content_risk: float, context_risk: float) -> List[str]:
        """Identify specific risk factors present in the content"""
        factors = []
        
        # PII-related factors
        if pii_entities:
            pii_types = [e.type.value for e in pii_entities]
            factors.append(f"Contains PII: {', '.join(set(pii_types))}")
            
            high_risk_pii = [e for e in pii_entities if e.type in [PIIType.SSN, PIIType.CREDIT_CARD, PIIType.FINANCIAL]]
            if high_risk_pii:
                factors.append("Contains high-risk financial/personal identifiers")
        
        # Bias-related factors
        if bias_detections:
            bias_types = [b.type.value for b in bias_detections]
            factors.append(f"Contains bias: {', '.join(set(bias_types))}")
            
            critical_bias = [b for b in bias_detections if b.severity in ["critical", "high"]]
            if critical_bias:
                factors.append("Contains critical or high-severity bias")
        
        # Content factors
        if content_risk > 3.0:
            factors.append("Content contains suspicious patterns or keywords")
        
        # Context factors
        if context_risk > 2.0:
            factors.append("Multiple risk indicators in close proximity")
        
        return factors
    
    def _generate_mitigation_suggestions(self, pii_entities: List[PIIEntity], 
                                       bias_detections: List[BiasDetection],
                                       risk_level: RiskLevel) -> List[str]:
        """Generate specific mitigation suggestions based on detected risks"""
        suggestions = []
        
        if risk_level == RiskLevel.CRITICAL:
            suggestions.append("CRITICAL: Block or heavily sanitize content before processing")
        
        if pii_entities:
            suggestions.append("Apply PII sanitization to mask sensitive personal information")
            
            financial_pii = [e for e in pii_entities if e.type in [PIIType.SSN, PIIType.CREDIT_CARD, PIIType.FINANCIAL]]
            if financial_pii:
                suggestions.append("Extra caution: Contains financial identifiers - consider blocking")
        
        if bias_detections:
            suggestions.append("Apply bias filtering to remove discriminatory content")
            
            hate_speech = [b for b in bias_detections if b.type == BiasType.HATE_SPEECH]
            if hate_speech:
                suggestions.append("WARNING: Contains hate speech - recommend blocking")
        
        if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            suggestions.append("Require human review before processing")
            suggestions.append("Log interaction for compliance and audit purposes")
        
        if risk_level in [RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]:
            suggestions.append("Apply stricter output filtering")
            suggestions.append("Monitor for policy violations")
        
        return suggestions
    
    def set_weight(self, component: str, weight: float) -> None:
        """Set custom weight for a risk component"""
        self.weights[component] = weight
    
    def set_threshold(self, level: str, threshold: float) -> None:
        """Set custom threshold for a risk level"""
        self.thresholds[f"{level}_threshold"] = threshold
    
    def get_risk_breakdown(self, assessment: RiskAssessment) -> Dict[str, Any]:
        """Get detailed breakdown of risk assessment"""
        return {
            "overall_score": assessment.overall_risk_score,
            "risk_level": assessment.risk_level.value,
            "component_scores": {
                "pii_risk": assessment.pii_risk_score,
                "bias_risk": assessment.bias_risk_score,
                "content_risk": assessment.content_risk_score,
                "context_risk": assessment.context_risk_score
            },
            "weighted_contributions": {
                "pii_contribution": assessment.pii_risk_score * self.weights["pii_weight"],
                "bias_contribution": assessment.bias_risk_score * self.weights["bias_weight"],
                "content_contribution": assessment.content_risk_score * self.weights["content_weight"],
                "context_contribution": assessment.context_risk_score * self.weights["context_weight"]
            },
            "detection_counts": {
                "pii_entities": len(assessment.pii_entities),
                "bias_detections": len(assessment.bias_detections)
            },
            "confidence": assessment.confidence,
            "processing_time_ms": assessment.processing_time_ms
        }
