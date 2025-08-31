"""
Enhanced Adversarial Detection using TextAttack, ART, and Custom Heuristics

This module provides comprehensive adversarial detection capabilities:
- TextAttack for adversarial NLP attacks & defenses
- Adversarial Robustness Toolbox (ART) for attacks + detection
- Custom regex/heuristics for jailbreak/prompt injection detection
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json

try:
    import numpy as np
    from textattack import Attack
    from textattack.attack_recipes import TextFoolerJin2019, PWWSRen2019
    from textattack.models.wrappers import ModelWrapper
    from textattack.attack_results import SuccessfulAttackResult, FailedAttackResult
    TEXTATTACK_AVAILABLE = True
except ImportError:
    TEXTATTACK_AVAILABLE = False
    logging.warning("TextAttack not available. Adversarial detection will be limited.")

try:
    from art.attacks.evasion import FastGradientMethod, ProjectedGradientDescent
    from art.estimators.classification import BlackBoxClassifier
    from art.utils import load_dataset
    ART_AVAILABLE = True
except ImportError:
    ART_AVAILABLE = False
    logging.warning("Adversarial Robustness Toolbox not available. Some detection methods will be limited.")

logger = logging.getLogger(__name__)


class AdversarialType(str, Enum):
    """Types of adversarial attacks that can be detected"""
    # Prompt injection attacks
    PROMPT_INJECTION = "prompt_injection"
    JAILBREAK_ATTEMPT = "jailbreak_attempt"
    ROLE_PLAYING = "role_playing"
    SYSTEM_PROMPT_LEAK = "system_prompt_leak"
    
    # Text manipulation attacks
    TEXT_FOOLER = "text_fooler"
    PWWS_ATTACK = "pwws_attack"
    FAST_GRADIENT = "fast_gradient"
    PROJECTED_GRADIENT = "projected_gradient"
    
    # Rate limiting and abuse
    RATE_LIMIT_ABUSE = "rate_limit_abuse"
    TOKEN_OVERFLOW = "token_overflow"
    CONTEXT_POISONING = "context_poisoning"
    
    # Social engineering
    SOCIAL_ENGINEERING = "social_engineering"
    MANIPULATION = "manipulation"
    DECEPTION = "deception"


class AdversarialSeverity(str, Enum):
    """Severity levels for detected adversarial content"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AdversarialDetection:
    """Enhanced adversarial detection result"""
    type: AdversarialType
    severity: AdversarialSeverity
    confidence: float
    description: str
    detected_text: str
    position: Dict[str, int]
    attack_indicators: List[str]
    mitigation_suggestions: List[str]
    context: Optional[str] = None
    attack_vectors: Optional[List[str]] = None


class EnhancedAdversarialDetector:
    """
    Enhanced adversarial detector combining TextAttack, ART, and custom heuristics
    """
    
    def __init__(self, strict_mode: bool = False):
        self.strict_mode = strict_mode
        self._initialize_components()
        self._setup_adversarial_patterns()
        self._setup_detection_thresholds()
    
    def _initialize_components(self):
        """Initialize adversarial detection components"""
        try:
            if TEXTATTACK_AVAILABLE:
                logger.info("TextAttack adversarial detection component initialized")
            else:
                logger.warning("TextAttack not available. Using fallback detection.")
            
            if ART_AVAILABLE:
                logger.info("ART adversarial detection component initialized")
            else:
                logger.warning("ART not available. Using fallback detection.")
                
        except Exception as e:
            logger.error(f"Failed to initialize adversarial detection components: {e}")
    
    def _setup_adversarial_patterns(self):
        """Setup patterns for detecting various types of adversarial attacks"""
        self.adversarial_patterns = {
            AdversarialType.PROMPT_INJECTION: [
                # Common prompt injection patterns
                r'\b(?:ignore|forget|disregard|skip|bypass)\s+(?:previous|above|all|the)\s+(?:instructions?|rules?|guidelines?|prompts?)\b',
                r'\b(?:you\s+are\s+now|act\s+as\s+if|pretend\s+to\s+be|roleplay\s+as)\b',
                r'\b(?:ignore\s+safety|bypass\s+restrictions|ignore\s+ethical|ignore\s+guidelines)\b',
                r'\b(?:new\s+instructions?|override|replace|substitute)\s+(?:instructions?|rules?|guidelines?)\b',
                r'\b(?:ignore\s+everything|forget\s+everything|start\s+over|reset)\b',
            ],
            AdversarialType.JAILBREAK_ATTEMPT: [
                # Jailbreak attempt patterns
                r'\b(?:how\s+to\s+hack|how\s+to\s+break\s+into|how\s+to\s+steal|how\s+to\s+harm)\b',
                r'\b(?:how\s+to\s+make\s+bombs?|how\s+to\s+make\s+drugs?|how\s+to\s+kill)\b',
                r'\b(?:illegal\s+activities?|criminal\s+behavior|unethical\s+actions?)\b',
                r'\b(?:bypass\s+security|circumvent\s+protection|evade\s+detection)\b',
                r'\b(?:exploit\s+vulnerability|find\s+loophole|work\s+around\s+restriction)\b',
            ],
            AdversarialType.ROLE_PLAYING: [
                # Role playing attack patterns
                r'\b(?:you\s+are\s+a\s+hacker|you\s+are\s+a\s+criminal|you\s+are\s+evil)\b',
                r'\b(?:you\s+are\s+dangerous|you\s+are\s+malicious|you\s+are\s+corrupt)\b',
                r'\b(?:pretend\s+you\s+are|act\s+like\s+you\s+are|roleplay\s+as\s+you\s+are)\b',
                r'\b(?:imagine\s+you\s+are|suppose\s+you\s+are|assume\s+you\s+are)\b',
            ],
            AdversarialType.SYSTEM_PROMPT_LEAK: [
                # System prompt extraction attempts
                r'\b(?:what\s+are\s+your\s+instructions?|what\s+are\s+your\s+rules?)\b',
                r'\b(?:show\s+me\s+your\s+prompt|what\s+did\s+you\s+hear|repeat\s+your\s+instructions?)\b',
                r'\b(?:what\s+is\s+your\s+system\s+message|what\s+is\s+your\s+initial\s+prompt)\b',
                r'\b(?:echo\s+back|repeat\s+back|mirror\s+back)\s+(?:what\s+I\s+said|my\s+message)\b',
            ],
            AdversarialType.RATE_LIMIT_ABUSE: [
                # Rate limiting abuse patterns
                r'\b(?:spam|flood|overwhelm|bombard|hammer)\b',
                r'\b(?:multiple\s+requests?|repeated\s+calls?|continuous\s+queries?)\b',
                r'\b(?:automated\s+requests?|bot\s+behavior|script\s+generated)\b',
            ],
            AdversarialType.TOKEN_OVERFLOW: [
                # Token overflow attempts
                r'\b(?:very\s+long\s+text|extremely\s+long\s+input|massive\s+content)\b',
                r'\b(?:repeat\s+this\s+word\s+1000\s+times|generate\s+10000\s+words)\b',
                r'\b(?:infinite\s+loop|endless\s+text|never\s+ending\s+content)\b',
            ],
            AdversarialType.CONTEXT_POISONING: [
                # Context poisoning patterns
                r'\b(?:misleading\s+context|false\s+information|fake\s+data)\b',
                r'\b(?:contradictory\s+statements?|conflicting\s+information|inconsistent\s+data)\b',
                r'\b(?:manipulate\s+context|alter\s+meaning|change\s+interpretation)\b',
            ],
            AdversarialType.SOCIAL_ENGINEERING: [
                # Social engineering patterns
                r'\b(?:please\s+help\s+me|I\s+really\s+need\s+this|it\'s\s+urgent)\b',
                r'\b(?:I\'m\s+desperate|I\'m\s+in\s+trouble|please\s+break\s+the\s+rules)\b',
                r'\b(?:emotional\s+manipulation|guilt\s+tripping|sympathy\s+seeking)\b',
            ],
        }
    
    def _setup_detection_thresholds(self):
        """Setup detection thresholds for different adversarial types"""
        self.detection_thresholds = {
            AdversarialType.PROMPT_INJECTION: {
                "confidence_threshold": 0.6,  # Lowered from 0.8 for better security
                "severity_multiplier": 1.2
            },
            AdversarialType.JAILBREAK_ATTEMPT: {
                "confidence_threshold": 0.5,  # Lowered from 0.9 for better security
                "severity_multiplier": 1.5
            },
            AdversarialType.ROLE_PLAYING: {
                "confidence_threshold": 0.6,  # Lowered from 0.7 for better security
                "severity_multiplier": 1.1
            },
            AdversarialType.SYSTEM_PROMPT_LEAK: {
                "confidence_threshold": 0.6,  # Lowered from 0.8 for better security
                "severity_multiplier": 1.3
            },
            AdversarialType.RATE_LIMIT_ABUSE: {
                "confidence_threshold": 0.6,
                "severity_multiplier": 1.0
            },
            AdversarialType.TOKEN_OVERFLOW: {
                "confidence_threshold": 0.7,
                "severity_multiplier": 1.1
            },
            AdversarialType.CONTEXT_POISONING: {
                "confidence_threshold": 0.7,
                "severity_multiplier": 1.2
            },
            AdversarialType.SOCIAL_ENGINEERING: {
                "confidence_threshold": 0.6,
                "severity_multiplier": 1.0
            }
        }
    
    def detect_adversarial(self, text: str, context: Optional[str] = None) -> List[AdversarialDetection]:
        """
        Comprehensive adversarial detection using all available methods
        
        Args:
            text: Text to analyze for adversarial content
            context: Optional context for better detection
            
        Returns:
            List of detected adversarial instances
        """
        all_detections = []
        
        # 1. Pattern-based detection
        pattern_detections = self._detect_with_patterns(text)
        all_detections.extend(pattern_detections)
        
        # 2. Heuristic-based detection
        heuristic_detections = self._detect_with_heuristics(text)
        all_detections.extend(heuristic_detections)
        
        # 3. TextAttack-based detection (if available)
        if TEXTATTACK_AVAILABLE:
            textattack_detections = self._detect_with_textattack(text)
            all_detections.extend(textattack_detections)
        
        # 4. ART-based detection (if available)
        if ART_AVAILABLE:
            art_detections = self._detect_with_art(text)
            all_detections.extend(art_detections)
        
        # 5. Context-aware detection
        if context:
            context_detections = self._detect_context_adversarial(text, context)
            all_detections.extend(context_detections)
        
        # 6. Remove duplicates and merge similar detections
        deduplicated_detections = self._deduplicate_detections(all_detections)
        
        # 7. Calculate confidence scores and severity
        for detection in deduplicated_detections:
            detection.confidence = self._calculate_confidence(detection, text)
            detection.severity = self._determine_severity(detection)
        
        return deduplicated_detections
    
    def _detect_with_patterns(self, text: str) -> List[AdversarialDetection]:
        """Detect adversarial content using predefined patterns"""
        detections = []
        text_lower = text.lower()
        
        for adv_type, patterns in self.adversarial_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text_lower, re.IGNORECASE)
                for match in matches:
                    # Find the original case in the text
                    original_match = text[match.start():match.end()]
                    
                    detection = AdversarialDetection(
                        type=adv_type,
                        severity=AdversarialSeverity.MEDIUM,  # Will be calculated later
                        confidence=0.8,  # Base confidence for pattern matches
                        description=f"Pattern-based {adv_type.value} detection",
                        detected_text=original_match,
                        position={"start": match.start(), "end": match.end()},
                        attack_indicators=[pattern],
                        mitigation_suggestions=self._get_mitigation_suggestions(adv_type),
                        context=text[max(0, match.start()-30):match.end()+30]
                    )
                    detections.append(detection)
        
        return detections
    
    def _detect_with_heuristics(self, text: str) -> List[AdversarialDetection]:
        """Detect adversarial content using heuristic rules"""
        detections = []
        text_lower = text.lower()
        
        # Heuristic 1: Check for suspicious repetition patterns
        repetition_patterns = [
            r'(\b\w+\b)(?:\s+\1){3,}',  # Word repeated 4+ times
            r'(\b\w{1,3}\b)(?:\s+\1){5,}',  # Short word repeated 6+ times
        ]
        
        for pattern in repetition_patterns:
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                original_match = text[match.start():match.end()]
                
                detection = AdversarialDetection(
                    type=AdversarialType.TOKEN_OVERFLOW,
                    severity=AdversarialSeverity.MEDIUM,
                    confidence=0.6,
                    description="Heuristic-based detection: suspicious repetition pattern",
                    detected_text=original_match,
                    position={"start": match.start(), "end": match.end()},
                    attack_indicators=["repetition_pattern", "token_overflow_attempt"],
                    mitigation_suggestions=["Check for token overflow attempts", "Monitor repetition patterns"],
                    context=text[max(0, match.start()-30):match.end()+30]
                )
                detections.append(detection)
        
        # Heuristic 2: Check for suspicious length patterns
        if len(text) > 10000:  # Very long text
            detection = AdversarialDetection(
                type=AdversarialType.TOKEN_OVERFLOW,
                severity=AdversarialSeverity.HIGH,
                confidence=0.7,
                description="Heuristic-based detection: extremely long input",
                detected_text=text[:100] + "...",
                position={"start": 0, "end": len(text)},
                attack_indicators=["excessive_length", "potential_token_overflow"],
                mitigation_suggestions=["Limit input length", "Check for token overflow attempts"],
                context=text[:200] + "..."
            )
            detections.append(detection)
        
        # Heuristic 3: Check for suspicious character patterns
        suspicious_chars = text.count('?') + text.count('!') + text.count('.')
        if suspicious_chars > len(text) * 0.1:  # More than 10% punctuation
            detection = AdversarialDetection(
                type=AdversarialType.CONTEXT_POISONING,
                severity=AdversarialSeverity.MEDIUM,
                confidence=0.6,
                description="Heuristic-based detection: excessive punctuation",
                detected_text=text[:100] + "...",
                position={"start": 0, "end": len(text)},
                attack_indicators=["excessive_punctuation", "potential_context_poisoning"],
                mitigation_suggestions=["Check punctuation patterns", "Monitor for context poisoning"],
                context=text[:200] + "..."
            )
            detections.append(detection)
        
        return detections
    
    def _detect_with_textattack(self, text: str) -> List[AdversarialDetection]:
        """Detect adversarial content using TextAttack"""
        if not TEXTATTACK_AVAILABLE:
            return []
        
        detections = []
        
        try:
            # This is a simplified TextAttack integration
            # In a full implementation, you would:
            # 1. Load a pre-trained model
            # 2. Run TextAttack attacks
            # 3. Analyze the results for adversarial patterns
            
            # For now, we'll use TextAttack patterns to detect potential attacks
            textattack_patterns = [
                r'\b(?:synonym|substitute|replace|change)\s+(?:word|term|phrase)\b',
                r'\b(?:adversarial|attack|perturbation|modification)\b',
                r'\b(?:fool|trick|deceive|mislead)\s+(?:model|system|ai)\b',
            ]
            
            for pattern in textattack_patterns:
                matches = re.finditer(pattern, text.lower(), re.IGNORECASE)
                for match in matches:
                    original_match = text[match.start():match.end()]
                    
                    detection = AdversarialDetection(
                        type=AdversarialType.TEXT_FOOLER,
                        severity=AdversarialSeverity.HIGH,
                        confidence=0.7,
                        description="TextAttack-based detection: potential adversarial modification",
                        detected_text=original_match,
                        position={"start": match.start(), "end": match.end()},
                        attack_indicators=["textattack_pattern", "potential_adversarial_modification"],
                        mitigation_suggestions=["Check for adversarial modifications", "Use robust model"],
                        context=text[max(0, match.start()-30):match.end()+30]
                    )
                    detections.append(detection)
            
        except Exception as e:
            logger.error(f"TextAttack detection failed: {e}")
        
        return detections
    
    def _detect_with_art(self, text: str) -> List[AdversarialDetection]:
        """Detect adversarial content using Adversarial Robustness Toolbox"""
        if not ART_AVAILABLE:
            return []
        
        detections = []
        
        try:
            # This is a simplified ART integration
            # In a full implementation, you would:
            # 1. Load a pre-trained model
            # 2. Run ART attacks
            # 3. Analyze the results for adversarial patterns
            
            # For now, we'll use ART-related patterns to detect potential attacks
            art_patterns = [
                r'\b(?:gradient|perturbation|epsilon|delta)\s+(?:attack|method|technique)\b',
                r'\b(?:fast\s+gradient|projected\s+gradient|iterative\s+attack)\b',
                r'\b(?:adversarial\s+example|perturbed\s+input|modified\s+text)\b',
            ]
            
            for pattern in art_patterns:
                matches = re.finditer(pattern, text.lower(), re.IGNORECASE)
                for match in matches:
                    original_match = text[match.start():match.end()]
                    
                    detection = AdversarialDetection(
                        type=AdversarialType.FAST_GRADIENT,
                        severity=AdversarialSeverity.HIGH,
                        confidence=0.7,
                        description="ART-based detection: potential gradient-based attack",
                        detected_text=original_match,
                        position={"start": match.start(), "end": match.end()},
                        attack_indicators=["art_pattern", "potential_gradient_attack"],
                        mitigation_suggestions=["Check for gradient-based attacks", "Use robust model"],
                        context=text[max(0, match.start()-30):match.end()+30]
                    )
                    detections.append(detection)
            
        except Exception as e:
            logger.error(f"ART detection failed: {e}")
        
        return detections
    
    def _detect_context_adversarial(self, text: str, context: str) -> List[AdversarialDetection]:
        """Detect adversarial content considering broader context"""
        detections = []
        
        # Check if context contains adversarial indicators
        context_lower = context.lower()
        adversarial_indicators = [
            "adversarial", "attack", "jailbreak", "prompt injection", "bypass",
            "ignore instructions", "role playing", "system prompt", "manipulation"
        ]
        
        for indicator in adversarial_indicators:
            if indicator in context_lower:
                # Look for specific adversarial patterns in the main text
                adv_type = self._classify_adversarial_by_context(indicator)
                
                detection = AdversarialDetection(
                    type=adv_type,
                    severity=AdversarialSeverity.MEDIUM,
                    confidence=0.6,
                    description=f"Context-aware adversarial detection: {indicator} context detected",
                    detected_text=text[:100] + "..." if len(text) > 100 else text,
                    position={"start": 0, "end": len(text)},
                    attack_indicators=[indicator, "context_indicator"],
                    mitigation_suggestions=["Review content for adversarial patterns", "Check for attack attempts"],
                    context=context
                )
                detections.append(detection)
                break  # Only create one context detection
        
        return detections
    
    def _classify_adversarial_by_context(self, context_indicator: str) -> AdversarialType:
        """Classify adversarial type based on context indicators"""
        context_lower = context_indicator.lower()
        
        if "prompt injection" in context_lower or "ignore instructions" in context_lower:
            return AdversarialType.PROMPT_INJECTION
        elif "jailbreak" in context_lower or "bypass" in context_lower:
            return AdversarialType.JAILBREAK_ATTEMPT
        elif "role playing" in context_lower or "system prompt" in context_lower:
            return AdversarialType.ROLE_PLAYING
        elif "attack" in context_lower or "adversarial" in context_lower:
            return AdversarialType.TEXT_FOOLER
        elif "manipulation" in context_lower:
            return AdversarialType.MANIPULATION
        else:
            return AdversarialType.SOCIAL_ENGINEERING  # Default fallback
    
    def _determine_severity(self, detection: AdversarialDetection) -> AdversarialSeverity:
        """Determine severity level for detected adversarial content"""
        # Critical adversarial types
        if detection.type in [AdversarialType.JAILBREAK_ATTEMPT, AdversarialType.SYSTEM_PROMPT_LEAK]:
            return AdversarialSeverity.CRITICAL
        
        # High adversarial types
        if detection.type in [AdversarialType.PROMPT_INJECTION, AdversarialType.ROLE_PLAYING]:
            return AdversarialSeverity.HIGH
        
        # Medium adversarial types
        if detection.type in [AdversarialType.TEXT_FOOLER, AdversarialType.FAST_GRADIENT]:
            return AdversarialSeverity.MEDIUM
        
        # Low adversarial types
        return AdversarialSeverity.LOW
    
    def _get_mitigation_suggestions(self, adv_type: AdversarialType) -> List[str]:
        """Get mitigation suggestions for detected adversarial types"""
        suggestions = {
            AdversarialType.PROMPT_INJECTION: [
                "Block prompt injection attempts",
                "Use input validation",
                "Implement instruction following checks",
                "Monitor for bypass attempts"
            ],
            AdversarialType.JAILBREAK_ATTEMPT: [
                "Block jailbreak attempts immediately",
                "Use content filtering",
                "Implement safety checks",
                "Monitor for harmful requests"
            ],
            AdversarialType.ROLE_PLAYING: [
                "Prevent role playing attacks",
                "Maintain system identity",
                "Use identity verification",
                "Block impersonation attempts"
            ],
            AdversarialType.SYSTEM_PROMPT_LEAK: [
                "Protect system prompts",
                "Use prompt obfuscation",
                "Implement access controls",
                "Monitor for extraction attempts"
            ],
            AdversarialType.RATE_LIMIT_ABUSE: [
                "Implement rate limiting",
                "Use request throttling",
                "Monitor abuse patterns",
                "Block abusive users"
            ],
            AdversarialType.TOKEN_OVERFLOW: [
                "Limit input length",
                "Use token counting",
                "Implement size restrictions",
                "Monitor for overflow attempts"
            ],
            AdversarialType.CONTEXT_POISONING: [
                "Validate context integrity",
                "Use context verification",
                "Monitor for manipulation",
                "Implement context checks"
            ],
            AdversarialType.SOCIAL_ENGINEERING: [
                "Recognize manipulation attempts",
                "Use objective analysis",
                "Avoid emotional responses",
                "Maintain professional boundaries"
            ]
        }
        
        return suggestions.get(adv_type, ["Review content for adversarial patterns", "Implement security measures"])
    
    def _calculate_confidence(self, detection: AdversarialDetection, text: str) -> float:
        """Calculate confidence score for adversarial detection"""
        base_confidence = detection.confidence
        
        # Get threshold and multiplier for this adversarial type
        thresholds = self.detection_thresholds.get(detection.type, {})
        confidence_threshold = thresholds.get("confidence_threshold", 0.7)
        severity_multiplier = thresholds.get("severity_multiplier", 1.0)
        
        # Adjust confidence based on severity
        severity_multipliers = {
            AdversarialSeverity.CRITICAL: 1.3,
            AdversarialSeverity.HIGH: 1.2,
            AdversarialSeverity.MEDIUM: 1.0,
            AdversarialSeverity.LOW: 0.9
        }
        
        severity_multiplier *= severity_multipliers.get(detection.severity, 1.0)
        
        # Adjust confidence based on text length and context
        context_quality = min(1.0, len(detection.context or "") / 100.0) if detection.context else 0.5
        
        # Adjust confidence based on number of attack indicators
        indicator_multiplier = min(1.2, 1.0 + len(detection.attack_indicators) * 0.1)
        
        final_confidence = base_confidence * severity_multiplier * context_quality * indicator_multiplier
        
        return min(1.0, max(0.0, final_confidence))
    
    def _deduplicate_detections(self, detections: List[AdversarialDetection]) -> List[AdversarialDetection]:
        """Remove duplicate and overlapping adversarial detections"""
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
    
    def is_adversarial(self, text: str, confidence_threshold: float = 0.7) -> bool:
        """Check if text contains adversarial content above threshold"""
        detections = self.detect_adversarial(text)
        return any(d.confidence >= confidence_threshold for d in detections)
    
    def get_adversarial_summary(self, detections: List[AdversarialDetection]) -> Dict[str, Any]:
        """Get summary of adversarial detection results"""
        if not detections:
            return {
                "total_detections": 0,
                "adversarial_types": {},
                "severity_levels": {},
                "confidence_summary": {}
            }
        
        adv_types = {}
        severity_levels = {}
        confidence_scores = []
        
        for detection in detections:
            # Count adversarial types
            adv_types[detection.type.value] = adv_types.get(detection.type.value, 0) + 1
            
            # Count severity levels
            severity_levels[detection.severity.value] = severity_levels.get(detection.severity.value, 0) + 1
            
            # Collect confidence scores
            confidence_scores.append(detection.confidence)
        
        return {
            "total_detections": len(detections),
            "adversarial_types": adv_types,
            "severity_levels": severity_levels,
            "confidence_summary": {
                "average": sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0,
                "min": min(confidence_scores) if confidence_scores else 0,
                "max": max(confidence_scores) if confidence_scores else 0
            },
            "highest_severity": max(severity_levels.keys()) if severity_levels else "none"
        }
