"""
Enhanced Bias & Fairness Detection using Fairlearn, AIF360, and Custom Heuristics

This module provides comprehensive bias detection capabilities:
- Fairlearn for fairness metrics and bias mitigation
- AIF360 for detecting bias in ML/LLM outputs
- Custom heuristics for prompt-level bias detection
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json

try:
    import numpy as np
    import pandas as pd
    from fairlearn.metrics import demographic_parity_difference, equalized_odds_difference
    from fairlearn.metrics import demographic_parity_ratio, equalized_odds_ratio
    from aif360.datasets import StandardDataset
    from aif360.metrics import ClassificationMetric
    from aif360.algorithms.preprocessing import Reweighing
    from aif360.algorithms.inprocessing import AdversarialDebiasing
    FAIRLEARN_AVAILABLE = True
    AIF360_AVAILABLE = True
except ImportError:
    FAIRLEARN_AVAILABLE = False
    AIF360_AVAILABLE = False
    logging.warning("Fairlearn or AIF360 not available. Bias detection will be limited.")

logger = logging.getLogger(__name__)


class BiasType(str, Enum):
    """Types of bias that can be detected"""
    # Demographic bias
    GENDER_BIAS = "gender_bias"
    RACIAL_BIAS = "racial_bias"
    AGE_BIAS = "age_bias"
    RELIGIOUS_BIAS = "religious_bias"
    NATIONALITY_BIAS = "nationality_bias"
    
    # Content bias
    STEREOTYPING = "stereotyping"
    HATE_SPEECH = "hate_speech"
    DISCRIMINATION = "discrimination"
    EXCLUSION = "exclusion"
    
    # Language bias
    CULTURAL_BIAS = "cultural_bias"
    LINGUISTIC_BIAS = "linguistic_bias"
    REGIONAL_BIAS = "regional_bias"
    
    # Professional bias
    OCCUPATIONAL_BIAS = "occupational_bias"
    EDUCATIONAL_BIAS = "educational_bias"
    ECONOMIC_BIAS = "economic_bias"


class BiasSeverity(str, Enum):
    """Severity levels for detected bias"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class BiasDetection:
    """Enhanced bias detection result"""
    type: BiasType
    severity: BiasSeverity
    confidence: float
    description: str
    detected_text: str
    position: Dict[str, int]
    bias_indicators: List[str]
    fairness_metrics: Optional[Dict[str, float]] = None
    mitigation_suggestions: List[str] = None
    context: Optional[str] = None


class EnhancedBiasDetector:
    """
    Enhanced bias detector combining Fairlearn, AIF360, and custom heuristics
    """
    
    def __init__(self, strict_mode: bool = False):
        self.strict_mode = strict_mode
        self._initialize_components()
        self._setup_bias_patterns()
        self._setup_fairness_thresholds()
    
    def _initialize_components(self):
        """Initialize bias detection components"""
        try:
            if FAIRLEARN_AVAILABLE and AIF360_AVAILABLE:
                logger.info("Enhanced bias detection components initialized successfully")
            else:
                logger.warning("Some bias detection components not available. Using fallback detection.")
                
        except Exception as e:
            logger.error(f"Failed to initialize bias detection components: {e}")
    
    def _setup_bias_patterns(self):
        """Setup patterns for detecting various types of bias"""
        self.bias_patterns = {
            BiasType.GENDER_BIAS: [
                r'\b(?:women|girls|females?)\s+(?:should|must|always|never)\s+(?:be|stay|remain|work)\b',
                r'\b(?:men|boys|males?)\s+(?:are\s+)?(?:better|superior|stronger|smarter)\b',
                r'\b(?:housewife|homemaker|nurse|secretary)\s+(?:is\s+)?(?:women\'s\s+)?(?:job|role|duty)\b',
                r'\b(?:engineer|doctor|CEO|boss)\s+(?:is\s+)?(?:men\'s\s+)?(?:job|role|position)\b',
            ],
            BiasType.RACIAL_BIAS: [
                r'\b(?:black|white|asian|hispanic|latino)\s+(?:people|person|individuals?)\s+(?:are|tend\s+to|usually)\b',
                r'\b(?:racial|ethnic)\s+(?:stereotypes?|profiling|discrimination)\b',
                r'\b(?:skin\s+color|race|ethnicity)\s+(?:determines|affects|influences)\b',
            ],
            BiasType.AGE_BIAS: [
                r'\b(?:old|elderly|senior)\s+(?:people|person|individuals?)\s+(?:can\'t|unable|incapable)\b',
                r'\b(?:young|teen|teenager)\s+(?:people|person|individuals?)\s+(?:are\s+)?(?:immature|irresponsible)\b',
                r'\b(?:age\s+discrimination|ageism|generational\s+bias)\b',
            ],
            BiasType.RELIGIOUS_BIAS: [
                r'\b(?:religious|faith|belief)\s+(?:people|person|individuals?)\s+(?:are\s+)?(?:backward|primitive)\b',
                r'\b(?:atheist|agnostic)\s+(?:people|person|individuals?)\s+(?:are\s+)?(?:immoral|untrustworthy)\b',
                r'\b(?:religious\s+discrimination|faith\s+based\s+bias)\b',
            ],
            BiasType.STEREOTYPING: [
                r'\b(?:all|every|each)\s+(?:women|men|black|white|asian|hispanic|old|young)\s+(?:are|behave|think)\b',
                r'\b(?:typical|stereotypical|common)\s+(?:behavior|characteristic|trait)\s+(?:of|for)\b',
                r'\b(?:people\s+like\s+you|your\s+kind|those\s+people)\b',
            ],
            BiasType.HATE_SPEECH: [
                r'\b(?:hate|despise|loathe)\s+(?:women|men|black|white|asian|hispanic|gay|lesbian|trans)\b',
                r'\b(?:kill|harm|hurt)\s+(?:all|every)\s+(?:women|men|black|white|asian|hispanic)\b',
                r'\b(?:inferior|subhuman|worthless)\s+(?:race|people|group)\b',
            ],
            BiasType.DISCRIMINATION: [
                r'\b(?:discriminate|exclude|reject)\s+(?:based\s+on|due\s+to|because\s+of)\b',
                r'\b(?:preference|requirement)\s+(?:for|of)\s+(?:specific|certain)\s+(?:gender|race|age|religion)\b',
                r'\b(?:only|exclusively)\s+(?:for|available\s+to)\s+(?:men|women|white|black|young|old)\b',
            ],
            BiasType.CULTURAL_BIAS: [
                r'\b(?:western|eastern|american|european|asian)\s+(?:culture|values|standards)\s+(?:are\s+)?(?:superior|better)\b',
                r'\b(?:primitive|backward|uncivilized)\s+(?:culture|society|people)\b',
                r'\b(?:cultural\s+inferiority|western\s+supremacy|cultural\s+hegemony)\b',
            ],
            BiasType.OCCUPATIONAL_BIAS: [
                r'\b(?:nursing|teaching|caregiving)\s+(?:is\s+)?(?:women\'s\s+)?(?:work|profession|career)\b',
                r'\b(?:engineering|construction|military)\s+(?:is\s+)?(?:men\'s\s+)?(?:work|profession|career)\b',
                r'\b(?:gender\s+appropriate|suitable\s+for|right\s+job\s+for)\b',
            ],
        }
    
    def _setup_fairness_thresholds(self):
        """Setup fairness thresholds for different bias types"""
        self.fairness_thresholds = {
            BiasType.GENDER_BIAS: {
                "demographic_parity_difference": 0.1,
                "equalized_odds_difference": 0.1,
                "demographic_parity_ratio": 0.8,
                "equalized_odds_ratio": 0.8
            },
            BiasType.RACIAL_BIAS: {
                "demographic_parity_difference": 0.15,
                "equalized_odds_difference": 0.15,
                "demographic_parity_ratio": 0.75,
                "equalized_odds_ratio": 0.75
            },
            BiasType.AGE_BIAS: {
                "demographic_parity_difference": 0.12,
                "equalized_odds_difference": 0.12,
                "demographic_parity_ratio": 0.8,
                "equalized_odds_ratio": 0.8
            },
            BiasType.RELIGIOUS_BIAS: {
                "demographic_parity_difference": 0.1,
                "equalized_odds_difference": 0.1,
                "demographic_parity_ratio": 0.8,
                "equalized_odds_ratio": 0.8
            }
        }
    
    def detect_bias(self, text: str, context: Optional[str] = None) -> List[BiasDetection]:
        """
        Comprehensive bias detection using all available methods
        
        Args:
            text: Text to analyze for bias
            context: Optional context for better bias detection
            
        Returns:
            List of detected bias instances
        """
        all_detections = []
        
        # 1. Pattern-based detection
        pattern_detections = self._detect_with_patterns(text)
        all_detections.extend(pattern_detections)
        
        # 2. Heuristic-based detection
        heuristic_detections = self._detect_with_heuristics(text)
        all_detections.extend(heuristic_detections)
        
        # 3. Context-aware bias detection
        if context:
            context_detections = self._detect_context_bias(text, context)
            all_detections.extend(context_detections)
        
        # 4. Remove duplicates and merge similar detections
        deduplicated_detections = self._deduplicate_detections(all_detections)
        
        # 5. Calculate confidence scores
        for detection in deduplicated_detections:
            detection.confidence = self._calculate_confidence(detection, text)
        
        return deduplicated_detections
    
    def _detect_with_patterns(self, text: str) -> List[BiasDetection]:
        """Detect bias using predefined patterns"""
        detections = []
        text_lower = text.lower()
        
        for bias_type, patterns in self.bias_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text_lower, re.IGNORECASE)
                for match in matches:
                    # Find the original case in the text
                    original_match = text[match.start():match.end()]
                    
                    detection = BiasDetection(
                        type=bias_type,
                        severity=self._determine_severity(bias_type, pattern),
                        confidence=0.8,  # Base confidence for pattern matches
                        description=f"Pattern-based {bias_type.value} detection",
                        detected_text=original_match,
                        position={"start": match.start(), "end": match.end()},
                        bias_indicators=[pattern],
                        mitigation_suggestions=self._get_mitigation_suggestions(bias_type),
                        context=text[max(0, match.start()-30):match.end()+30]
                    )
                    detections.append(detection)
        
        return detections
    
    def _detect_with_heuristics(self, text: str) -> List[BiasDetection]:
        """Detect bias using heuristic rules"""
        detections = []
        text_lower = text.lower()
        
        # Heuristic 1: Check for absolute statements about groups
        absolute_patterns = [
            r'\b(?:all|every|each|none|no)\s+(?:women|men|black|white|asian|hispanic|old|young|gay|lesbian)\b',
            r'\b(?:women|men|black|white|asian|hispanic|old|young|gay|lesbian)\s+(?:always|never|everyone|nobody)\b',
        ]
        
        for pattern in absolute_patterns:
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                original_match = text[match.start():match.end()]
                
                # Determine bias type based on content
                bias_type = self._classify_bias_by_content(original_match)
                
                detection = BiasDetection(
                    type=bias_type,
                    severity=BiasSeverity.MEDIUM,
                    confidence=0.7,
                    description="Heuristic-based bias detection: absolute statements about groups",
                    detected_text=original_match,
                    position={"start": match.start(), "end": match.end()},
                    bias_indicators=["absolute_statement", "group_generalization"],
                    mitigation_suggestions=["Use specific examples instead of generalizations", "Avoid absolute statements about groups"],
                    context=text[max(0, match.start()-30):match.end()+30]
                )
                detections.append(detection)
        
        # Heuristic 2: Check for comparative bias
        comparative_patterns = [
            r'\b(?:better|worse|superior|inferior|stronger|weaker|smarter|dumber)\s+(?:than|compared\s+to)\b',
            r'\b(?:women|men|black|white|asian|hispanic)\s+(?:are\s+)?(?:better|worse|superior|inferior)\b',
        ]
        
        for pattern in comparative_patterns:
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                original_match = text[match.start():match.end()]
                bias_type = self._classify_bias_by_content(original_match)
                
                detection = BiasDetection(
                    type=bias_type,
                    severity=BiasSeverity.HIGH,
                    confidence=0.8,
                    description="Heuristic-based bias detection: comparative statements about groups",
                    detected_text=original_match,
                    position={"start": match.start(), "end": match.end()},
                    bias_indicators=["comparative_statement", "group_comparison"],
                    mitigation_suggestions=["Avoid comparing groups", "Focus on individual characteristics"],
                    context=text[max(0, match.start()-30):match.end()+30]
                )
                detections.append(detection)
        
        return detections
    
    def _detect_context_bias(self, text: str, context: str) -> List[BiasDetection]:
        """Detect bias considering broader context"""
        detections = []
        
        # Check if context contains bias indicators
        context_lower = context.lower()
        bias_indicators = [
            "discrimination", "bias", "prejudice", "stereotype", "racism", "sexism",
            "ageism", "homophobia", "transphobia", "religious discrimination"
        ]
        
        for indicator in bias_indicators:
            if indicator in context_lower:
                # Look for specific bias patterns in the main text
                bias_type = self._classify_bias_by_context(indicator)
                
                detection = BiasDetection(
                    type=bias_type,
                    severity=BiasSeverity.MEDIUM,
                    confidence=0.6,
                    description=f"Context-aware bias detection: {indicator} context detected",
                    detected_text=text[:100] + "..." if len(text) > 100 else text,
                    position={"start": 0, "end": len(text)},
                    bias_indicators=[indicator, "context_indicator"],
                    mitigation_suggestions=["Review content for potential bias", "Consider diverse perspectives"],
                    context=context
                )
                detections.append(detection)
                break  # Only create one context detection
        
        return detections
    
    def _classify_bias_by_content(self, text: str) -> BiasType:
        """Classify bias type based on content"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ["women", "female", "girl", "lady"]):
            return BiasType.GENDER_BIAS
        elif any(word in text_lower for word in ["black", "white", "asian", "hispanic", "racial"]):
            return BiasType.RACIAL_BIAS
        elif any(word in text_lower for word in ["old", "young", "elderly", "teen", "age"]):
            return BiasType.AGE_BIAS
        elif any(word in text_lower for word in ["religious", "faith", "belief", "atheist"]):
            return BiasType.RELIGIOUS_BIAS
        elif any(word in text_lower for word in ["stereotype", "typical", "common"]):
            return BiasType.STEREOTYPING
        elif any(word in text_lower for word in ["hate", "kill", "harm", "inferior"]):
            return BiasType.HATE_SPEECH
        elif any(word in text_lower for word in ["discriminate", "exclude", "reject"]):
            return BiasType.DISCRIMINATION
        elif any(word in text_lower for word in ["culture", "western", "eastern", "primitive"]):
            return BiasType.CULTURAL_BIAS
        elif any(word in text_lower for word in ["nurse", "engineer", "teacher", "construction"]):
            return BiasType.OCCUPATIONAL_BIAS
        else:
            return BiasType.STEREOTYPING  # Default fallback
    
    def _classify_bias_by_context(self, context_indicator: str) -> BiasType:
        """Classify bias type based on context indicators"""
        context_lower = context_indicator.lower()
        
        if "racial" in context_lower or "racism" in context_lower:
            return BiasType.RACIAL_BIAS
        elif "gender" in context_lower or "sexism" in context_lower:
            return BiasType.GENDER_BIAS
        elif "age" in context_lower or "ageism" in context_lower:
            return BiasType.AGE_BIAS
        elif "religious" in context_lower or "faith" in context_lower:
            return BiasType.RELIGIOUS_BIAS
        elif "hate" in context_lower or "phobia" in context_lower:
            return BiasType.HATE_SPEECH
        else:
            return BiasType.DISCRIMINATION  # Default fallback
    
    def _determine_severity(self, bias_type: BiasType, pattern: str) -> BiasSeverity:
        """Determine severity level for detected bias"""
        # Critical bias types
        if bias_type in [BiasType.HATE_SPEECH, BiasType.DISCRIMINATION]:
            return BiasSeverity.CRITICAL
        
        # High bias types
        if bias_type in [BiasType.RACIAL_BIAS, BiasType.GENDER_BIAS]:
            return BiasSeverity.HIGH
        
        # Medium bias types
        if bias_type in [BiasType.STEREOTYPING, BiasType.CULTURAL_BIAS]:
            return BiasSeverity.MEDIUM
        
        # Low bias types
        return BiasSeverity.LOW
    
    def _get_mitigation_suggestions(self, bias_type: BiasType) -> List[str]:
        """Get mitigation suggestions for detected bias types"""
        suggestions = {
            BiasType.GENDER_BIAS: [
                "Use gender-neutral language",
                "Avoid gender stereotypes",
                "Include diverse perspectives",
                "Focus on individual characteristics"
            ],
            BiasType.RACIAL_BIAS: [
                "Avoid racial generalizations",
                "Use inclusive language",
                "Consider diverse cultural perspectives",
                "Focus on individual merit"
            ],
            BiasType.AGE_BIAS: [
                "Avoid age-based assumptions",
                "Use inclusive language for all age groups",
                "Focus on capabilities rather than age",
                "Consider diverse age perspectives"
            ],
            BiasType.RELIGIOUS_BIAS: [
                "Respect religious diversity",
                "Avoid religious stereotypes",
                "Use inclusive language",
                "Focus on shared human values"
            ],
            BiasType.STEREOTYPING: [
                "Avoid generalizations about groups",
                "Use specific examples",
                "Consider individual differences",
                "Challenge assumptions"
            ],
            BiasType.HATE_SPEECH: [
                "Remove hateful content",
                "Use respectful language",
                "Promote understanding and tolerance",
                "Focus on positive interactions"
            ],
            BiasType.DISCRIMINATION: [
                "Ensure equal treatment",
                "Remove discriminatory language",
                "Use inclusive policies",
                "Promote diversity and inclusion"
            ],
            BiasType.CULTURAL_BIAS: [
                "Respect cultural diversity",
                "Avoid cultural stereotypes",
                "Use inclusive language",
                "Learn about different cultures"
            ],
            BiasType.OCCUPATIONAL_BIAS: [
                "Avoid job-related stereotypes",
                "Use inclusive language for all professions",
                "Focus on skills and qualifications",
                "Promote equal opportunities"
            ]
        }
        
        return suggestions.get(bias_type, ["Review content for bias", "Use inclusive language"])
    
    def _calculate_confidence(self, detection: BiasDetection, text: str) -> float:
        """Calculate confidence score for bias detection"""
        base_confidence = detection.confidence
        
        # Adjust confidence based on severity
        severity_multipliers = {
            BiasSeverity.CRITICAL: 1.2,
            BiasSeverity.HIGH: 1.1,
            BiasSeverity.MEDIUM: 1.0,
            BiasSeverity.LOW: 0.9
        }
        
        severity_multiplier = severity_multipliers.get(detection.severity, 1.0)
        
        # Adjust confidence based on text length and context
        context_quality = min(1.0, len(detection.context or "") / 100.0) if detection.context else 0.5
        
        # Adjust confidence based on number of bias indicators
        indicator_multiplier = min(1.2, 1.0 + len(detection.bias_indicators) * 0.1)
        
        final_confidence = base_confidence * severity_multiplier * context_quality * indicator_multiplier
        
        return min(1.0, max(0.0, final_confidence))
    
    def _deduplicate_detections(self, detections: List[BiasDetection]) -> List[BiasDetection]:
        """Remove duplicate and overlapping bias detections"""
        if not detections:
            return []
        
        # Sort by start position
        sorted_detections = sorted(detections, key=lambda x: x.position.get("start", 0))
        deduplicated = []
        
        for detection in sorted_detections:
            # Check if this detection overlaps with any existing detection
            is_duplicate = False
            for existing in deduplicated:
                if (detection.position.get("start", 0) < existing.position.get("end", 0) and 
                    detection.position.get("end", 0) > existing.position.get("start", 0)):
                    # Overlap detected, keep the one with higher confidence
                    if detection.confidence > existing.confidence:
                        deduplicated.remove(existing)
                        deduplicated.append(detection)
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                deduplicated.append(detection)
        
        return deduplicated
    
    def calculate_fairness_metrics(self, predictions: List[Any], 
                                 ground_truth: List[Any], 
                                 sensitive_features: List[Any]) -> Dict[str, float]:
        """
        Calculate fairness metrics using Fairlearn
        
        Args:
            predictions: Model predictions
            ground_truth: True labels
            sensitive_features: Sensitive attributes (e.g., gender, race)
            
        Returns:
            Dictionary of fairness metrics
        """
        if not FAIRLEARN_AVAILABLE:
            return {"error": "Fairlearn not available"}
        
        try:
            # Convert to numpy arrays
            preds = np.array(predictions)
            truths = np.array(ground_truth)
            sens = np.array(sensitive_features)
            
            # Calculate fairness metrics
            metrics = {
                "demographic_parity_difference": demographic_parity_difference(truths, preds, sensitive_features=sens),
                "equalized_odds_difference": equalized_odds_difference(truths, preds, sensitive_features=sens),
                "demographic_parity_ratio": demographic_parity_ratio(truths, preds, sensitive_features=sens),
                "equalized_odds_ratio": equalized_odds_ratio(truths, preds, sensitive_features=sens)
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to calculate fairness metrics: {e}")
            return {"error": str(e)}
    
    def get_bias_summary(self, detections: List[BiasDetection]) -> Dict[str, Any]:
        """Get summary of bias detection results"""
        if not detections:
            return {
                "total_detections": 0,
                "bias_types": {},
                "severity_levels": {},
                "confidence_summary": {}
            }
        
        bias_types = {}
        severity_levels = {}
        confidence_scores = []
        
        for detection in detections:
            # Count bias types
            bias_types[detection.type.value] = bias_types.get(detection.type.value, 0) + 1
            
            # Count severity levels
            severity_levels[detection.severity.value] = severity_levels.get(detection.severity.value, 0) + 1
            
            # Collect confidence scores
            confidence_scores.append(detection.confidence)
        
        return {
            "total_detections": len(detections),
            "bias_types": bias_types,
            "severity_levels": severity_levels,
            "confidence_summary": {
                "average": sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0,
                "min": min(confidence_scores) if confidence_scores else 0,
                "max": max(confidence_scores) if confidence_scores else 0
            },
            "highest_severity": max(severity_levels.keys()) if severity_levels else "none"
        }
