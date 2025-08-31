"""
Configuration module for Risk Detection Engine

This module provides configuration classes and utilities for customizing
the behavior of the risk detection and mitigation system.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum

from .risk_agent import ProcessingMode


@dataclass
class PIIDetectionConfig:
    """Configuration for PII detection"""
    enabled: bool = True
    strict_mode: bool = False
    confidence_threshold: float = 0.7
    detect_emails: bool = True
    detect_phones: bool = True
    detect_ssns: bool = True
    detect_credit_cards: bool = True
    detect_ip_addresses: bool = True
    detect_addresses: bool = True
    detect_urls: bool = True
    detect_dates: bool = False  # Often too many false positives
    detect_financial: bool = True
    detect_names: bool = False  # High false positive rate
    
    custom_patterns: Dict[str, List[str]] = field(default_factory=dict)


@dataclass
class BiasDetectionConfig:
    """Configuration for bias detection"""
    enabled: bool = True
    strict_mode: bool = False
    confidence_threshold: float = 0.7
    detect_gender_bias: bool = True
    detect_racial_bias: bool = True
    detect_religious_bias: bool = True
    detect_age_bias: bool = True
    detect_disability_bias: bool = True
    detect_sexual_orientation_bias: bool = True
    detect_nationality_bias: bool = True
    detect_socioeconomic_bias: bool = True
    detect_appearance_bias: bool = True
    detect_hate_speech: bool = True
    detect_profanity: bool = True
    detect_violence: bool = True
    detect_sexual_content: bool = True
    
    custom_patterns: Dict[str, List[str]] = field(default_factory=dict)


@dataclass
class SanitizationConfig:
    """Configuration for text sanitization"""
    enabled: bool = True
    confidence_threshold: float = 0.7
    
    # PII sanitization strategies
    email_strategy: str = "partial_mask"
    phone_strategy: str = "partial_mask"
    ssn_strategy: str = "full_mask"
    credit_card_strategy: str = "partial_mask"
    ip_address_strategy: str = "placeholder"
    address_strategy: str = "placeholder"
    url_strategy: str = "placeholder"
    date_strategy: str = "placeholder"
    financial_strategy: str = "full_mask"
    name_strategy: str = "placeholder"
    
    # General settings
    preserve_length: bool = True
    preserve_format: bool = True
    
    custom_replacements: Dict[str, str] = field(default_factory=dict)


@dataclass
class RiskScoringConfig:
    """Configuration for risk scoring"""
    enabled: bool = True
    
    # Component weights (must sum to 1.0)
    pii_weight: float = 0.4
    bias_weight: float = 0.3
    content_weight: float = 0.2
    context_weight: float = 0.1
    
    # Risk level thresholds
    safe_threshold: float = 2.0
    low_threshold: float = 4.0
    medium_threshold: float = 6.0
    high_threshold: float = 8.0
    
    # PII type weights
    pii_weights: Dict[str, float] = field(default_factory=lambda: {
        "ssn": 10.0,
        "credit_card": 9.0,
        "financial": 8.0,
        "email": 6.0,
        "phone": 5.0,
        "address": 4.0,
        "ip_address": 3.0,
        "date": 2.0,
        "url": 2.0,
        "name": 1.0,
    })
    
    # Bias severity weights
    bias_weights: Dict[str, float] = field(default_factory=lambda: {
        "critical": 10.0,
        "high": 7.5,
        "medium": 5.0,
        "low": 2.5,
    })


@dataclass
class PerformanceConfig:
    """Configuration for performance and limits"""
    max_text_length: int = 50000
    timeout_seconds: float = 30.0
    enable_caching: bool = True
    cache_size: int = 1000
    enable_metrics: bool = True
    log_level: str = "INFO"


@dataclass
class ComplianceConfig:
    """Configuration for compliance and audit requirements"""
    enable_audit_logging: bool = True
    log_original_content: bool = False  # Security consideration
    log_sanitized_content: bool = True
    log_risk_scores: bool = True
    log_detections: bool = True
    retention_days: int = 90
    
    # GDPR/Privacy settings
    enable_data_minimization: bool = True
    enable_right_to_forget: bool = True
    anonymize_logs: bool = True


class RiskDetectionConfig:
    """Main configuration class for the entire risk detection system"""
    
    def __init__(self,
                 processing_mode: ProcessingMode = ProcessingMode.BALANCED,
                 pii_config: Optional[PIIDetectionConfig] = None,
                 bias_config: Optional[BiasDetectionConfig] = None,
                 sanitization_config: Optional[SanitizationConfig] = None,
                 scoring_config: Optional[RiskScoringConfig] = None,
                 performance_config: Optional[PerformanceConfig] = None,
                 compliance_config: Optional[ComplianceConfig] = None):
        
        self.processing_mode = processing_mode
        self.pii_config = pii_config or PIIDetectionConfig()
        self.bias_config = bias_config or BiasDetectionConfig()
        self.sanitization_config = sanitization_config or SanitizationConfig()
        self.scoring_config = scoring_config or RiskScoringConfig()
        self.performance_config = performance_config or PerformanceConfig()
        self.compliance_config = compliance_config or ComplianceConfig()
        
        # Apply processing mode adjustments
        self._apply_mode_adjustments()
    
    def _apply_mode_adjustments(self) -> None:
        """Apply configuration adjustments based on processing mode"""
        
        if self.processing_mode == ProcessingMode.STRICT:
            # More aggressive detection and lower thresholds
            self.pii_config.strict_mode = True
            self.pii_config.confidence_threshold = 0.5
            self.pii_config.detect_names = True
            self.pii_config.detect_dates = True
            
            self.bias_config.strict_mode = True
            self.bias_config.confidence_threshold = 0.5
            
            self.sanitization_config.confidence_threshold = 0.5
            
            # Lower risk thresholds (more things considered risky)
            self.scoring_config.safe_threshold = 1.5
            self.scoring_config.low_threshold = 3.0
            self.scoring_config.medium_threshold = 5.0
            self.scoring_config.high_threshold = 7.0
            
            # Higher weights for PII and bias
            self.scoring_config.pii_weight = 0.5
            self.scoring_config.bias_weight = 0.35
            self.scoring_config.content_weight = 0.1
            self.scoring_config.context_weight = 0.05
        
        elif self.processing_mode == ProcessingMode.PERMISSIVE:
            # Less aggressive detection and higher thresholds
            self.pii_config.strict_mode = False
            self.pii_config.confidence_threshold = 0.8
            self.pii_config.detect_names = False
            self.pii_config.detect_dates = False
            self.pii_config.detect_addresses = False
            
            self.bias_config.strict_mode = False
            self.bias_config.confidence_threshold = 0.8
            self.bias_config.detect_profanity = False
            self.bias_config.detect_appearance_bias = False
            
            self.sanitization_config.confidence_threshold = 0.8
            
            # Higher risk thresholds (fewer things considered risky)
            self.scoring_config.safe_threshold = 3.0
            self.scoring_config.low_threshold = 5.0
            self.scoring_config.medium_threshold = 7.0
            self.scoring_config.high_threshold = 9.0
            
            # Lower weights for PII and bias
            self.scoring_config.pii_weight = 0.3
            self.scoring_config.bias_weight = 0.2
            self.scoring_config.content_weight = 0.3
            self.scoring_config.context_weight = 0.2
        
        # BALANCED mode uses default settings
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            "processing_mode": self.processing_mode.value,
            "pii_config": {
                "enabled": self.pii_config.enabled,
                "strict_mode": self.pii_config.strict_mode,
                "confidence_threshold": self.pii_config.confidence_threshold,
                "detection_types": {
                    "emails": self.pii_config.detect_emails,
                    "phones": self.pii_config.detect_phones,
                    "ssns": self.pii_config.detect_ssns,
                    "credit_cards": self.pii_config.detect_credit_cards,
                    "ip_addresses": self.pii_config.detect_ip_addresses,
                    "addresses": self.pii_config.detect_addresses,
                    "urls": self.pii_config.detect_urls,
                    "dates": self.pii_config.detect_dates,
                    "financial": self.pii_config.detect_financial,
                    "names": self.pii_config.detect_names,
                }
            },
            "bias_config": {
                "enabled": self.bias_config.enabled,
                "strict_mode": self.bias_config.strict_mode,
                "confidence_threshold": self.bias_config.confidence_threshold,
                "detection_types": {
                    "gender_bias": self.bias_config.detect_gender_bias,
                    "racial_bias": self.bias_config.detect_racial_bias,
                    "religious_bias": self.bias_config.detect_religious_bias,
                    "age_bias": self.bias_config.detect_age_bias,
                    "disability_bias": self.bias_config.detect_disability_bias,
                    "sexual_orientation_bias": self.bias_config.detect_sexual_orientation_bias,
                    "nationality_bias": self.bias_config.detect_nationality_bias,
                    "socioeconomic_bias": self.bias_config.detect_socioeconomic_bias,
                    "appearance_bias": self.bias_config.detect_appearance_bias,
                    "hate_speech": self.bias_config.detect_hate_speech,
                    "profanity": self.bias_config.detect_profanity,
                    "violence": self.bias_config.detect_violence,
                    "sexual_content": self.bias_config.detect_sexual_content,
                }
            },
            "sanitization_config": {
                "enabled": self.sanitization_config.enabled,
                "confidence_threshold": self.sanitization_config.confidence_threshold,
                "preserve_length": self.sanitization_config.preserve_length,
                "preserve_format": self.sanitization_config.preserve_format,
            },
            "scoring_config": {
                "enabled": self.scoring_config.enabled,
                "component_weights": {
                    "pii_weight": self.scoring_config.pii_weight,
                    "bias_weight": self.scoring_config.bias_weight,
                    "content_weight": self.scoring_config.content_weight,
                    "context_weight": self.scoring_config.context_weight,
                },
                "risk_thresholds": {
                    "safe_threshold": self.scoring_config.safe_threshold,
                    "low_threshold": self.scoring_config.low_threshold,
                    "medium_threshold": self.scoring_config.medium_threshold,
                    "high_threshold": self.scoring_config.high_threshold,
                }
            },
            "performance_config": {
                "max_text_length": self.performance_config.max_text_length,
                "timeout_seconds": self.performance_config.timeout_seconds,
                "enable_caching": self.performance_config.enable_caching,
                "enable_metrics": self.performance_config.enable_metrics,
            },
            "compliance_config": {
                "enable_audit_logging": self.compliance_config.enable_audit_logging,
                "log_original_content": self.compliance_config.log_original_content,
                "retention_days": self.compliance_config.retention_days,
                "enable_data_minimization": self.compliance_config.enable_data_minimization,
            }
        }
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'RiskDetectionConfig':
        """Create configuration from dictionary"""
        processing_mode = ProcessingMode(config_dict.get("processing_mode", "balanced"))
        
        # Create sub-configurations
        pii_config = PIIDetectionConfig()
        if "pii_config" in config_dict:
            pii_data = config_dict["pii_config"]
            pii_config.enabled = pii_data.get("enabled", True)
            pii_config.confidence_threshold = pii_data.get("confidence_threshold", 0.7)
            # ... (set other fields as needed)
        
        # Similar for other configs...
        
        return cls(
            processing_mode=processing_mode,
            pii_config=pii_config,
            # ... other configs
        )
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of issues"""
        issues = []
        
        # Validate weights sum to 1.0
        total_weight = (
            self.scoring_config.pii_weight +
            self.scoring_config.bias_weight +
            self.scoring_config.content_weight +
            self.scoring_config.context_weight
        )
        
        if abs(total_weight - 1.0) > 0.01:
            issues.append(f"Risk scoring weights must sum to 1.0, current sum: {total_weight}")
        
        # Validate thresholds are in ascending order
        thresholds = [
            self.scoring_config.safe_threshold,
            self.scoring_config.low_threshold,
            self.scoring_config.medium_threshold,
            self.scoring_config.high_threshold
        ]
        
        if thresholds != sorted(thresholds):
            issues.append("Risk thresholds must be in ascending order")
        
        # Validate confidence thresholds
        for threshold in [
            self.pii_config.confidence_threshold,
            self.bias_config.confidence_threshold,
            self.sanitization_config.confidence_threshold
        ]:
            if not 0.0 <= threshold <= 1.0:
                issues.append(f"Confidence threshold must be between 0.0 and 1.0, got: {threshold}")
        
        # Validate performance settings
        if self.performance_config.max_text_length <= 0:
            issues.append("Max text length must be positive")
        
        if self.performance_config.timeout_seconds <= 0:
            issues.append("Timeout must be positive")
        
        return issues


# Pre-configured settings for common use cases
class ConfigPresets:
    """Pre-configured settings for common use cases"""
    
    @staticmethod
    def high_security() -> RiskDetectionConfig:
        """High security configuration for sensitive environments"""
        return RiskDetectionConfig(
            processing_mode=ProcessingMode.STRICT,
            pii_config=PIIDetectionConfig(
                strict_mode=True,
                confidence_threshold=0.5,
                detect_names=True,
                detect_dates=True
            ),
            bias_config=BiasDetectionConfig(
                strict_mode=True,
                confidence_threshold=0.5
            ),
            scoring_config=RiskScoringConfig(
                safe_threshold=1.0,
                low_threshold=2.5,
                medium_threshold=4.0,
                high_threshold=6.0
            )
        )
    
    @staticmethod
    def balanced_general() -> RiskDetectionConfig:
        """Balanced configuration for general use"""
        return RiskDetectionConfig(processing_mode=ProcessingMode.BALANCED)
    
    @staticmethod
    def low_restriction() -> RiskDetectionConfig:
        """Low restriction configuration for open environments"""
        return RiskDetectionConfig(
            processing_mode=ProcessingMode.PERMISSIVE,
            pii_config=PIIDetectionConfig(
                confidence_threshold=0.8,
                detect_names=False,
                detect_dates=False,
                detect_addresses=False
            ),
            bias_config=BiasDetectionConfig(
                confidence_threshold=0.8,
                detect_profanity=False,
                detect_appearance_bias=False
            ),
            scoring_config=RiskScoringConfig(
                safe_threshold=4.0,
                low_threshold=6.0,
                medium_threshold=8.0,
                high_threshold=9.5
            )
        )
    
    @staticmethod
    def compliance_focused() -> RiskDetectionConfig:
        """Configuration focused on compliance and audit requirements"""
        config = RiskDetectionConfig(processing_mode=ProcessingMode.BALANCED)
        
        config.compliance_config.enable_audit_logging = True
        config.compliance_config.log_risk_scores = True
        config.compliance_config.log_detections = True
        config.compliance_config.anonymize_logs = True
        config.compliance_config.retention_days = 365  # Extended retention
        
        return config
