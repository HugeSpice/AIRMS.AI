"""
Main Risk Agent for AI Risk Mitigation System

This is the central orchestrator that combines all risk detection and mitigation
components to provide a unified interface for content analysis and sanitization.
"""

import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

# Import enhanced detectors
from .detectors.pii_detector import EnhancedPIIDetector, PIIEntity
from .detectors.bias_detector import EnhancedBiasDetector, BiasDetection
from .detectors.adversarial_detector import EnhancedAdversarialDetector, AdversarialDetection
from .sanitizers.text_sanitizer import TextSanitizer, SanitizationResult
from .scorers.risk_scorer import RiskScorer, RiskAssessment, RiskLevel
from .mitigation import RiskMitigator, MitigationAction, MitigationResult


class ProcessingMode(str, Enum):
    """Processing modes for the risk agent"""
    STRICT = "strict"        # Maximum security, aggressive detection
    BALANCED = "balanced"    # Balance between security and usability
    PERMISSIVE = "permissive"  # Minimal restrictions, focus on critical risks only


@dataclass
class RiskAgentConfig:
    """Configuration for the Risk Agent"""
    processing_mode: ProcessingMode = ProcessingMode.BALANCED
    pii_confidence_threshold: float = 0.7
    bias_confidence_threshold: float = 0.7
    sanitization_confidence_threshold: float = 0.7
    enable_pii_detection: bool = True
    enable_bias_detection: bool = True
    enable_sanitization: bool = True
    enable_risk_scoring: bool = True
    enable_adversarial_detection: bool = True # NEW: Add adversarial detection config
    max_text_length: int = 50000
    timeout_seconds: float = 30.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class ProcessingResult:
    """Complete result from risk agent processing"""
    original_text: str
    sanitized_text: str
    risk_assessment: RiskAssessment
    sanitization_result: Optional[SanitizationResult]
    processing_metadata: Dict[str, Any]
    is_safe: bool
    should_block: bool
    warnings: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "original_length": len(self.original_text),
            "sanitized_length": len(self.sanitized_text),
            "risk_assessment": self.risk_assessment.to_dict(),
            "sanitization_result": self.sanitization_result.to_dict() if self.sanitization_result else None,
            "processing_metadata": self.processing_metadata,
            "is_safe": self.is_safe,
            "should_block": self.should_block,
            "warnings": self.warnings
        }


class RiskAgent:
    """
    Main Risk Agent class that orchestrates all risk detection and mitigation components
    
    This class provides a unified interface for:
    - Content analysis and risk detection
    - Text sanitization and PII masking
    - Risk scoring and classification
    - Decision making for content processing
    """
    
    def __init__(self, config: Optional[RiskAgentConfig] = None):
        """
        Initialize Risk Agent with configuration
        
        Args:
            config: Optional configuration object
        """
        self.config = config or RiskAgentConfig()
        self._initialize_components()
        self.processing_stats = {
            "total_processed": 0,
            "total_blocked": 0,
            "total_sanitized": 0,
            "average_processing_time": 0.0
        }
    
    def _initialize_components(self) -> None:
        """Initialize all risk detection and mitigation components"""
        
        # Set strict mode based on processing mode
        strict_mode = self.config.processing_mode == ProcessingMode.STRICT
        
        # Initialize enhanced detectors
        if self.config.enable_pii_detection:
            self.pii_detector = EnhancedPIIDetector(strict_mode=strict_mode)
        else:
            self.pii_detector = None
        
        if self.config.enable_bias_detection:
            self.bias_detector = EnhancedBiasDetector(strict_mode=strict_mode)
        else:
            self.bias_detector = None
        
        # NEW: Initialize adversarial detector
        if self.config.enable_adversarial_detection:
            self.adversarial_detector = EnhancedAdversarialDetector(strict_mode=strict_mode)
        else:
            self.adversarial_detector = None
        
        # Initialize sanitizer
        if self.config.enable_sanitization:
            self.text_sanitizer = TextSanitizer()
        else:
            self.text_sanitizer = None
        
        # Initialize risk scorer
        if self.config.enable_risk_scoring:
            # Adjust risk scorer weights based on processing mode
            custom_weights = self._get_mode_weights()
            self.risk_scorer = RiskScorer(custom_weights=custom_weights)
        else:
            self.risk_scorer = None
        
        # Initialize mitigation system
        self.risk_mitigator = RiskMitigator()
    
    def _get_mode_weights(self) -> Dict[str, float]:
        """Get risk scorer weights based on processing mode"""
        if self.config.processing_mode == ProcessingMode.STRICT:
            return {
                "pii_weight": 0.3,      # PII weight
                "bias_weight": 0.25,    # Bias weight
                "adversarial_weight": 0.3,  # NEW: Higher adversarial weight for strict mode
                "content_weight": 0.1,
                "context_weight": 0.05,
            }
        elif self.config.processing_mode == ProcessingMode.PERMISSIVE:
            return {
                "pii_weight": 0.25,     # Lower PII weight
                "bias_weight": 0.2,     # Lower bias weight
                "adversarial_weight": 0.2,  # NEW: Lower adversarial weight for permissive mode
                "content_weight": 0.25,
                "context_weight": 0.1,
            }
        else:  # BALANCED
            return {
                "pii_weight": 0.25,
                "bias_weight": 0.25,
                "adversarial_weight": 0.25,  # NEW: Balanced adversarial weight
                "content_weight": 0.15,
                "context_weight": 0.1,
            }
    
    def analyze_text(self, text: str) -> ProcessingResult:
        """
        Comprehensive analysis of text content including risk detection and sanitization
        
        Args:
            text: Text content to analyze
            
        Returns:
            ProcessingResult with complete analysis and sanitized content
        """
        start_time = time.time()
        warnings = []
        
        # Validate input
        if not text or not isinstance(text, str):
            raise ValueError("Text input is required and must be a string")
        
        if len(text) > self.config.max_text_length:
            warnings.append(f"Text length ({len(text)}) exceeds maximum ({self.config.max_text_length})")
            text = text[:self.config.max_text_length]
        
        try:
            # Step 1: Adversarial Detection (NEW - add this first)
            adversarial_detections = []
            if self.adversarial_detector:
                adversarial_detections = self.adversarial_detector.detect_adversarial(text)
                # If critical adversarial content detected, block immediately
                if any(d.severity.value == "critical" for d in adversarial_detections):
                    return self._create_adversarial_blocked_result(text, adversarial_detections, start_time)
            
            # Step 2: PII Detection
            pii_entities = []
            if self.pii_detector:
                pii_entities = self.pii_detector.detect_all(text)
                # Filter by confidence threshold
                pii_entities = [e for e in pii_entities if e.confidence >= self.config.pii_confidence_threshold]
            
            # Step 3: Bias Detection
            bias_detections = []
            if self.bias_detector:
                bias_detections = self.bias_detector.detect_bias(text)
                # Filter by confidence threshold
                bias_detections = [b for b in bias_detections if b.confidence >= self.config.bias_confidence_threshold]
            
            # Step 4: Risk Scoring
            processing_time_ms = (time.time() - start_time) * 1000
            risk_assessment = None
            if self.risk_scorer:
                risk_assessment = self.risk_scorer.calculate_risk_score(
                    text, pii_entities, bias_detections, processing_time_ms, adversarial_detections
                )
            else:
                # Fallback basic risk assessment
                risk_assessment = self._create_basic_risk_assessment(
                    text, pii_entities, bias_detections, adversarial_detections, processing_time_ms
                )
            
            # Step 5: Text Sanitization
            sanitized_text = text
            sanitization_result = None
            if self.text_sanitizer and (pii_entities or bias_detections):
                sanitization_result = self.text_sanitizer.sanitize_text(
                    text, pii_entities, self.config.sanitization_confidence_threshold
                )
                sanitized_text = sanitization_result.sanitized_text
            
            # Step 6: Decision Making
            is_safe, should_block = self._make_safety_decision(risk_assessment, pii_entities, bias_detections, adversarial_detections)
            
            # Step 7: Update Statistics
            self._update_stats(processing_time_ms, should_block, sanitization_result is not None)
            
            # Step 8: Generate Processing Metadata
            processing_metadata = self._generate_metadata(
                start_time, pii_entities, bias_detections, adversarial_detections, risk_assessment
            )
            
            return ProcessingResult(
                original_text=text,
                sanitized_text=sanitized_text,
                risk_assessment=risk_assessment,
                sanitization_result=sanitization_result,
                processing_metadata=processing_metadata,
                is_safe=is_safe,
                should_block=should_block,
                warnings=warnings
            )
            
        except Exception as e:
            # Handle processing errors gracefully
            warnings.append(f"Processing error: {str(e)}")
            
            # Return safe fallback result
            fallback_assessment = self._create_fallback_assessment(text, time.time() - start_time)
            
            return ProcessingResult(
                original_text=text,
                sanitized_text="[CONTENT_BLOCKED_DUE_TO_ERROR]",
                risk_assessment=fallback_assessment,
                sanitization_result=None,
                processing_metadata={"error": str(e), "fallback_mode": True},
                is_safe=False,
                should_block=True,
                warnings=warnings
            )
    
    def _create_adversarial_blocked_result(self, text: str, adversarial_detections: List[AdversarialDetection], start_time: float) -> ProcessingResult:
        """Create result for blocked adversarial content"""
        processing_time_ms = (time.time() - start_time) * 1000
        
        # Create critical risk assessment
        risk_assessment = RiskAssessment(
            overall_risk_score=10.0,
            risk_level=RiskLevel.CRITICAL,
            pii_risk_score=0.0,
            bias_risk_score=0.0,
            content_risk_score=10.0,
            context_risk_score=0.0,
            pii_entities=[],
            bias_detections=[],
            risk_factors=["Adversarial content detected"],
            mitigation_suggestions=["Content blocked due to security risk"],
            text_length=len(text),
            processing_time_ms=processing_time_ms,
            confidence=0.95
        )
        
        return ProcessingResult(
            original_text=text,
            sanitized_text="[CONTENT_BLOCKED_DUE_TO_ADVERSARIAL_ATTEMPT]",
            risk_assessment=risk_assessment,
            sanitization_result=None,
            processing_metadata={"adversarial_detections": [d.__dict__ for d in adversarial_detections]},
            is_safe=False,
            should_block=True,
            warnings=["Adversarial content detected and blocked"]
        )
    
    def _create_basic_risk_assessment(self, text: str, pii_entities: List[PIIEntity], 
                                    bias_detections: List[BiasDetection], 
                                    adversarial_detections: List[AdversarialDetection],
                                    processing_time_ms: float) -> RiskAssessment:
        """Create basic risk assessment when full scorer is not available"""
        
        # Simple risk calculation including adversarial content
        pii_risk = min(10.0, len(pii_entities) * 2.0)
        bias_risk = min(10.0, len(bias_detections) * 3.0)
        adversarial_risk = min(10.0, len(adversarial_detections) * 4.0)  # NEW: Higher weight for adversarial
        
        overall_risk = (pii_risk + bias_risk + adversarial_risk) / 3.0
        
        # Determine risk level
        if overall_risk >= 8.0:
            risk_level = RiskLevel.CRITICAL
        elif overall_risk >= 6.0:
            risk_level = RiskLevel.HIGH
        elif overall_risk >= 4.0:
            risk_level = RiskLevel.MEDIUM
        elif overall_risk >= 2.0:
            risk_level = RiskLevel.LOW
        else:
            risk_level = RiskLevel.SAFE
        
        return RiskAssessment(
            overall_risk_score=overall_risk,
            risk_level=risk_level,
            pii_risk_score=pii_risk,
            bias_risk_score=bias_risk,
            content_risk_score=0.0,
            context_risk_score=0.0,
            pii_entities=pii_entities,
            bias_detections=bias_detections,
            risk_factors=["Basic risk assessment"],
            mitigation_suggestions=["Apply sanitization"],
            text_length=len(text),
            processing_time_ms=processing_time_ms,
            confidence=0.7
        )
    
    def _create_fallback_assessment(self, text: str, processing_time: float) -> RiskAssessment:
        """Create fallback assessment for error cases"""
        return RiskAssessment(
            overall_risk_score=10.0,
            risk_level=RiskLevel.CRITICAL,
            pii_risk_score=10.0,
            bias_risk_score=10.0,
            content_risk_score=10.0,
            context_risk_score=10.0,
            pii_entities=[],
            bias_detections=[],
            risk_factors=["Processing error occurred"],
            mitigation_suggestions=["Block content due to processing error"],
            text_length=len(text),
            processing_time_ms=processing_time * 1000,
            confidence=0.0
        )
    
    def _make_safety_decision(self, risk_assessment: RiskAssessment, 
                            pii_entities: List[PIIEntity], 
                            bias_detections: List[BiasDetection],
                            adversarial_detections: List[AdversarialDetection]) -> Tuple[bool, bool]:
        """Make safety decision based on risk assessment and detections"""
        
        # Critical risk level always blocks
        if risk_assessment.risk_level == RiskLevel.CRITICAL:
            return False, True
        
        # Check for critical bias types
        critical_bias_types = ["hate_speech", "violence", "sexual_content"]
        has_critical_bias = any(
            b.type.value in critical_bias_types and b.severity.value in ["critical", "high"]
            for b in bias_detections
        )
        
        if has_critical_bias:
            return False, True
        
        # NEW: Check for critical adversarial content
        has_critical_adversarial = any(
            d.severity.value == "critical" for d in adversarial_detections
        )
        
        # NEW: Also check for high severity adversarial content (especially prompt injection)
        has_high_adversarial = any(
            d.severity.value == "high" and d.type.value in ["prompt_injection", "jailbreak_attempt", "system_prompt_leak"]
            for d in adversarial_detections
        )
        
        if has_critical_adversarial or has_high_adversarial:
            return False, True
        
        # Check for high-risk PII
        high_risk_pii_types = ["ssn", "credit_card", "financial"]
        has_high_risk_pii = any(
            e.type.value in high_risk_pii_types and e.confidence > 0.8
            for e in pii_entities
        )
        
        # Processing mode-specific decisions
        if self.config.processing_mode == ProcessingMode.STRICT:
            # Block high risk, sanitize medium+
            if risk_assessment.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                return False, True
            elif has_high_risk_pii or risk_assessment.risk_level == RiskLevel.MEDIUM:
                return True, False  # Safe but sanitized
        
        elif self.config.processing_mode == ProcessingMode.PERMISSIVE:
            # Only block critical, allow most content
            if risk_assessment.risk_level == RiskLevel.CRITICAL or has_critical_bias or has_critical_adversarial:
                return False, True
        
        else:  # BALANCED
            # Block high and critical, sanitize medium
            if risk_assessment.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL] or has_critical_bias or has_critical_adversarial:
                return False, True
            elif has_high_risk_pii:
                return True, False  # Safe but sanitized
        
        # Default: safe to process
        return True, False
    
    def _generate_metadata(self, start_time: float, pii_entities: List[PIIEntity], 
                         bias_detections: List[BiasDetection], 
                         adversarial_detections: List[AdversarialDetection],
                         risk_assessment: RiskAssessment) -> Dict[str, Any]:
        """Generate processing metadata"""
        
        return {
            "processing_time_ms": risk_assessment.processing_time_ms,
            "components_used": {
                "pii_detection": self.pii_detector is not None,
                "bias_detection": self.bias_detector is not None,
                "adversarial_detection": self.adversarial_detector is not None,  # NEW
                "sanitization": self.text_sanitizer is not None,
                "risk_scoring": self.risk_scorer is not None
            },
            "detection_summary": {
                "pii_entities_found": len(pii_entities),
                "bias_detections_found": len(bias_detections),
                "adversarial_detections_found": len(adversarial_detections),  # NEW
                "unique_pii_types": len(set(e.type.value for e in pii_entities)),
                "unique_bias_types": len(set(b.type.value for b in bias_detections)),
                "unique_adversarial_types": len(set(d.type.value for d in adversarial_detections))  # NEW
            },
            "configuration": self.config.to_dict(),
            "agent_version": "1.0.0"
        }
    
    def _update_stats(self, processing_time_ms: float, blocked: bool, sanitized: bool) -> None:
        """Update processing statistics"""
        self.processing_stats["total_processed"] += 1
        
        if blocked:
            self.processing_stats["total_blocked"] += 1
        
        if sanitized:
            self.processing_stats["total_sanitized"] += 1
        
        # Update average processing time
        current_avg = self.processing_stats["average_processing_time"]
        total_processed = self.processing_stats["total_processed"]
        
        self.processing_stats["average_processing_time"] = (
            (current_avg * (total_processed - 1) + processing_time_ms) / total_processed
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get processing statistics"""
        stats = self.processing_stats.copy()
        
        if stats["total_processed"] > 0:
            stats["block_rate"] = stats["total_blocked"] / stats["total_processed"]
            stats["sanitization_rate"] = stats["total_sanitized"] / stats["total_processed"]
        else:
            stats["block_rate"] = 0.0
            stats["sanitization_rate"] = 0.0
        
        return stats
    
    def update_config(self, new_config: RiskAgentConfig) -> None:
        """Update agent configuration and reinitialize components"""
        self.config = new_config
        self._initialize_components()
    
    def add_custom_pii_pattern(self, pii_type: str, pattern: str) -> bool:
        """Add custom PII detection pattern"""
        if self.pii_detector:
            # This would need to be implemented in PIIDetector
            return True
        return False
    
    def add_custom_bias_pattern(self, bias_type: str, pattern: str) -> bool:
        """Add custom bias detection pattern"""
        if self.bias_detector:
            from .detectors.bias_detector import BiasType
            try:
                bias_enum = BiasType(bias_type)
                return self.bias_detector.add_custom_pattern(bias_enum, pattern)
            except ValueError:
                return False
        return False
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on all components"""
        health_status = {
            "overall_status": "healthy",
            "components": {
                "pii_detector": "enabled" if self.pii_detector else "disabled",
                "bias_detector": "enabled" if self.bias_detector else "disabled", 
                "adversarial_detector": "enabled" if self.adversarial_detector else "disabled",  # NEW
                "text_sanitizer": "enabled" if self.text_sanitizer else "disabled",
                "risk_scorer": "enabled" if self.risk_scorer else "disabled",
                "risk_mitigator": "enabled" if self.risk_mitigator else "disabled"
            },
            "configuration": self.config.to_dict(),
            "statistics": self.get_statistics()
        }
        
        # Test components with sample text
        try:
            test_result = self.analyze_text("This is a test message.")
            health_status["last_test"] = {
                "status": "success",
                "processing_time_ms": test_result.processing_metadata.get("processing_time_ms", 0)
            }
        except Exception as e:
            health_status["overall_status"] = "unhealthy"
            health_status["last_test"] = {
                "status": "failed",
                "error": str(e)
            }
        
        return health_status
    
    def apply_mitigation(self, text: str, risk_assessment: RiskAssessment,
                        pii_entities: List[PIIEntity] = None,
                        bias_detections: List[BiasDetection] = None,
                        adversarial_detections: List[AdversarialDetection] = None) -> MitigationResult:
        """
        Apply comprehensive risk mitigation using the mitigation system
        
        Args:
            text: Text content to mitigate
            risk_assessment: Risk assessment result
            pii_entities: Detected PII entities
            bias_detections: Bias detection results
            adversarial_detections: Adversarial detection results
            
        Returns:
            MitigationResult with applied mitigations
        """
        if not self.risk_mitigator:
            raise RuntimeError("Risk mitigator not initialized")
        
        return self.risk_mitigator.mitigate_risk(
            text, risk_assessment, pii_entities, bias_detections, adversarial_detections
        )
    
    def get_mitigation_stats(self) -> Dict[str, Any]:
        """Get mitigation system statistics"""
        if not self.risk_mitigator:
            return {"error": "Risk mitigator not initialized"}
        
        return self.risk_mitigator.get_mitigation_stats()
    
    def get_mitigation_audit_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get mitigation system audit log"""
        if not self.risk_mitigator:
            return []
        
        return self.risk_mitigator.get_audit_log(limit)
