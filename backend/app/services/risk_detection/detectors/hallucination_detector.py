"""
Hallucination Detection Engine for AIRMS

This module detects hallucinations by:
1. Fact-checking LLM outputs against source data
2. Validating claims against trusted knowledge bases
3. Cross-referencing with database results
4. Scoring factual accuracy
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import re
import json
import time
from datetime import datetime

class HallucinationType(str, Enum):
    """Types of hallucinations that can be detected"""
    FACTUAL_INACCURACY = "factual_inaccuracy"
    SOURCE_MISATTRIBUTION = "source_misattribution"
    DATA_INCONSISTENCY = "data_inconsistency"
    UNVERIFIABLE_CLAIM = "unverifiable_claim"
    CONTRADICTORY_INFO = "contradictory_info"

class HallucinationSeverity(str, Enum):
    """Severity levels for hallucination detection"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class HallucinationDetection:
    """Result of hallucination detection"""
    type: HallucinationType
    severity: HallucinationSeverity
    confidence: float
    description: str
    source_text: str
    conflicting_data: Optional[Dict[str, Any]] = None
    suggested_correction: Optional[str] = None
    start_pos: Optional[int] = None
    end_pos: Optional[int] = None

@dataclass
class HallucinationAssessment:
    """Comprehensive hallucination assessment"""
    overall_hallucination_score: float  # 0-10, higher = more hallucination
    hallucination_level: str
    detections: List[HallucinationDetection]
    factual_accuracy: float  # 0-1, higher = more accurate
    verifiable_claims: int
    unverifiable_claims: int
    confidence: float
    processing_time_ms: float

class HallucinationDetector:
    """Advanced hallucination detection engine"""
    
    def __init__(self, enable_fact_checking: bool = True, enable_source_validation: bool = True):
        self.enable_fact_checking = enable_fact_checking
        self.enable_source_validation = enable_source_validation
        self.trusted_patterns = self._setup_trusted_patterns()
        
    def _setup_trusted_patterns(self) -> Dict[str, List[str]]:
        """Setup patterns for trusted information"""
        return {
            "dates": [
                r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',  # MM/DD/YY or DD-MM-YYYY
                r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4}\b',  # Month DD, YYYY
                r'\b\d{4}-\d{2}-\d{2}\b'  # YYYY-MM-DD
            ],
            "numbers": [
                r'\b\d+(?:\.\d+)?\b',  # Integers and decimals
                r'\b(?:order|package|tracking)\s+#?\d+\b',  # Order numbers
                r'\b\d+\s+(?:days?|hours?|minutes?)\b'  # Time periods
            ],
            "identifiers": [
                r'\b[A-Z]{2,}\d{4,}\b',  # Tracking numbers
                r'\b[A-Z]{3}-\d{6}\b',  # Order IDs
                r'\b\d{10,}\b'  # Long numeric IDs
            ]
        }
    
    def detect_hallucinations(self, 
                            llm_output: str, 
                            source_data: Optional[Dict[str, Any]] = None,
                            query_context: Optional[str] = None) -> HallucinationAssessment:
        """
        Detect hallucinations in LLM output
        
        Args:
            llm_output: The LLM response to analyze
            source_data: Source data used to generate the response
            query_context: Context about what was queried
            
        Returns:
            HallucinationAssessment with detailed results
        """
        start_time = time.time()
        detections = []
        
        # Step 1: Extract claims and factual statements
        claims = self._extract_claims(llm_output)
        
        # Step 2: Validate against source data if available
        if source_data and self.enable_fact_checking:
            data_detections = self._validate_against_source_data(llm_output, source_data)
            detections.extend(data_detections)
        
        # Step 3: Check for unverifiable claims
        unverifiable_detections = self._detect_unverifiable_claims(llm_output, claims)
        detections.extend(unverifiable_detections)
        
        # Step 4: Check for contradictions
        contradiction_detections = self._detect_contradictions(llm_output)
        detections.extend(contradiction_detections)
        
        # Step 5: Calculate overall scores
        hallucination_score = self._calculate_hallucination_score(detections)
        factual_accuracy = self._calculate_factual_accuracy(detections, len(claims))
        
        # Step 6: Classify hallucination level
        hallucination_level = self._classify_hallucination_level(hallucination_score)
        
        processing_time_ms = (time.time() - start_time) * 1000
        
        return HallucinationAssessment(
            overall_hallucination_score=hallucination_score,
            hallucination_level=hallucination_level,
            detections=detections,
            factual_accuracy=factual_accuracy,
            verifiable_claims=len([c for c in claims if self._is_verifiable(c)]),
            unverifiable_claims=len([c for c in claims if not self._is_verifiable(c)]),
            confidence=self._calculate_confidence(detections),
            processing_time_ms=round(processing_time_ms, 2)
        )
    
    def _extract_claims(self, text: str) -> List[str]:
        """Extract factual claims from text"""
        claims = []
        
        # Pattern for factual statements
        claim_patterns = [
            r'(?:Your|The)\s+(?:order|package|item)\s+(?:is|was|will be)\s+([^.!?]+)',
            r'(?:Order|Package)\s+#?\d+\s+(?:is|was|will be)\s+([^.!?]+)',
            r'(?:ETA|Estimated delivery|Expected arrival)\s+(?:is|was|will be)\s+([^.!?]+)',
            r'(?:Status|Current status)\s+(?:is|was)\s+([^.!?]+)',
            r'(?:Location|Current location)\s+(?:is|was)\s+([^.!?]+)'
        ]
        
        for pattern in claim_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                claim = match.group(0).strip()
                if claim and len(claim) > 10:  # Filter out very short matches
                    claims.append(claim)
        
        return claims
    
    def _validate_against_source_data(self, llm_output: str, source_data: Dict[str, Any]) -> List[HallucinationDetection]:
        """Validate LLM output against source data"""
        detections = []
        
        # Check for order numbers
        order_numbers = self._extract_order_numbers(llm_output)
        if order_numbers and 'order_id' in source_data:
            if not any(str(order_num) in str(source_data['order_id']) for order_num in order_numbers):
                detections.append(HallucinationDetection(
                    type=HallucinationType.FACTUAL_INACCURACY,
                    severity=HallucinationSeverity.HIGH,
                    confidence=0.9,
                    description="Order number in response doesn't match source data",
                    source_text=llm_output,
                    conflicting_data={"claimed_order": order_numbers, "actual_order": source_data['order_id']}
                ))
        
        # Check for status information
        status_info = self._extract_status_info(llm_output)
        if status_info and 'status' in source_data:
            if not self._status_matches(status_info, source_data['status']):
                detections.append(HallucinationDetection(
                    type=HallucinationType.FACTUAL_INACCURACY,
                    severity=HallucinationSeverity.MEDIUM,
                    confidence=0.8,
                    description="Status information doesn't match source data",
                    source_text=llm_output,
                    conflicting_data={"claimed_status": status_info, "actual_status": source_data['status']}
                ))
        
        # Check for dates
        dates = self._extract_dates(llm_output)
        if dates and 'estimated_delivery' in source_data:
            if not self._dates_match(dates, source_data['estimated_delivery']):
                detections.append(HallucinationDetection(
                    type=HallucinationType.FACTUAL_INACCURACY,
                    severity=HallucinationSeverity.MEDIUM,
                    confidence=0.7,
                    description="Delivery date doesn't match source data",
                    source_text=llm_output,
                    conflicting_data={"claimed_date": dates, "actual_date": source_data['estimated_delivery']}
                ))
        
        return detections
    
    def _detect_unverifiable_claims(self, text: str, claims: List[str]) -> List[HallucinationDetection]:
        """Detect claims that cannot be verified"""
        detections = []
        
        unverifiable_patterns = [
            r'\b(?:always|never|everyone|nobody)\b',  # Absolute statements
            r'\b(?:definitely|certainly|absolutely)\b',  # Overconfident claims
            r'\b(?:studies show|research proves|experts say)\b',  # Vague attributions
            r'\b(?:it is known|it is clear|obviously)\b'  # Unsupported assertions
        ]
        
        for pattern in unverifiable_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                detections.append(HallucinationDetection(
                    type=HallucinationType.UNVERIFIABLE_CLAIM,
                    severity=HallucinationSeverity.LOW,
                    confidence=0.6,
                    description=f"Unverifiable claim: '{match.group(0)}'",
                    source_text=text,
                    start_pos=match.start(),
                    end_pos=match.end()
                ))
        
        return detections
    
    def _detect_contradictions(self, text: str) -> List[HallucinationDetection]:
        """Detect contradictory statements within the text"""
        detections = []
        
        # Check for contradictory status statements
        status_indicators = {
            'delivered': ['in transit', 'pending', 'processing'],
            'in_transit': ['delivered', 'returned', 'cancelled'],
            'pending': ['delivered', 'in transit', 'cancelled']
        }
        
        for status, contradictions in status_indicators.items():
            if re.search(rf'\b{status}\b', text, re.IGNORECASE):
                for contradiction in contradictions:
                    if re.search(rf'\b{contradiction}\b', text, re.IGNORECASE):
                        detections.append(HallucinationDetection(
                            type=HallucinationType.CONTRADICTORY_INFO,
                            severity=HallucinationSeverity.HIGH,
                            confidence=0.9,
                            description=f"Contradictory status: {status} vs {contradiction}",
                            source_text=text
                        ))
        
        return detections
    
    def _extract_order_numbers(self, text: str) -> List[str]:
        """Extract order numbers from text"""
        patterns = [
            r'\b(?:order|package|tracking)\s+#?(\d+)\b',
            r'\b(\d{6,})\b'  # 6+ digit numbers
        ]
        
        numbers = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            numbers.extend(matches)
        
        return numbers
    
    def _extract_status_info(self, text: str) -> List[str]:
        """Extract status information from text"""
        status_patterns = [
            r'\b(?:is|was|will be)\s+([^.!?]+?)(?:\s+and|\s+with|\.|!|\?)',
            r'\b(?:status|current status)\s+(?:is|was)\s+([^.!?]+)'
        ]
        
        statuses = []
        for pattern in status_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            statuses.extend(matches)
        
        return statuses
    
    def _extract_dates(self, text: str) -> List[str]:
        """Extract dates from text"""
        date_patterns = [
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4}\b',
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
            r'\b\d{4}-\d{2}-\d{2}\b'
        ]
        
        dates = []
        for pattern in date_patterns:
            matches = re.findall(pattern, text)
            dates.extend(matches)
        
        return dates
    
    def _status_matches(self, claimed_status: str, actual_status: str) -> bool:
        """Check if claimed status matches actual status"""
        # Normalize statuses for comparison
        claimed = re.sub(r'[^\w\s]', '', claimed_status.lower())
        actual = re.sub(r'[^\w\s]', '', actual_status.lower())
        
        # Check for exact match or semantic similarity
        if claimed == actual:
            return True
        
        # Check for semantic similarity
        status_mappings = {
            'in_transit': ['in transit', 'shipping', 'on the way', 'en route'],
            'delivered': ['delivered', 'completed', 'arrived', 'received'],
            'pending': ['pending', 'processing', 'preparing', 'waiting']
        }
        
        for key, values in status_mappings.items():
            if actual in values and any(val in claimed for val in values):
                return True
        
        return False
    
    def _dates_match(self, claimed_dates: List[str], actual_date: str) -> bool:
        """Check if claimed dates match actual date"""
        if not actual_date:
            return True  # Can't verify if no actual date
        
        # Simple string matching for now
        actual_normalized = re.sub(r'[^\w\s]', '', actual_date.lower())
        
        for claimed_date in claimed_dates:
            claimed_normalized = re.sub(r'[^\w\s]', '', claimed_date.lower())
            if claimed_normalized in actual_normalized or actual_normalized in claimed_normalized:
                return True
        
        return False
    
    def _is_verifiable(self, claim: str) -> bool:
        """Check if a claim can be verified"""
        # Claims with specific details are more verifiable
        verifiable_indicators = [
            r'\d+',  # Contains numbers
            r'\b(?:order|package|tracking)\s+#?\d+\b',  # Order numbers
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b',  # Dates
            r'\b(?:in transit|delivered|pending|processing)\b'  # Status
        ]
        
        return any(re.search(pattern, claim, re.IGNORECASE) for pattern in verifiable_indicators)
    
    def _calculate_hallucination_score(self, detections: List[HallucinationDetection]) -> float:
        """Calculate overall hallucination score (0-10)"""
        if not detections:
            return 0.0
        
        severity_weights = {
            HallucinationSeverity.LOW: 1.0,
            HallucinationSeverity.MEDIUM: 2.0,
            HallucinationSeverity.HIGH: 3.0,
            HallucinationSeverity.CRITICAL: 4.0
        }
        
        total_score = 0.0
        for detection in detections:
            weight = severity_weights.get(detection.severity, 1.0)
            total_score += weight * detection.confidence
        
        # Normalize to 0-10 scale
        max_possible_score = len(detections) * 4.0  # Max severity weight
        normalized_score = min(10.0, (total_score / max_possible_score) * 10.0) if max_possible_score > 0 else 0.0
        
        return round(normalized_score, 2)
    
    def _calculate_factual_accuracy(self, detections: List[HallucinationDetection], total_claims: int) -> float:
        """Calculate factual accuracy score (0-1)"""
        if total_claims == 0:
            return 1.0
        
        # Reduce accuracy based on detection severity
        accuracy_reduction = 0.0
        for detection in detections:
            if detection.severity == HallucinationSeverity.CRITICAL:
                accuracy_reduction += 0.3
            elif detection.severity == HallucinationSeverity.HIGH:
                accuracy_reduction += 0.2
            elif detection.severity == HallucinationSeverity.MEDIUM:
                accuracy_reduction += 0.1
            elif detection.severity == HallucinationSeverity.LOW:
                accuracy_reduction += 0.05
        
        accuracy = max(0.0, 1.0 - accuracy_reduction)
        return round(accuracy, 2)
    
    def _classify_hallucination_level(self, score: float) -> str:
        """Classify hallucination level based on score"""
        if score >= 8.0:
            return "critical"
        elif score >= 6.0:
            return "high"
        elif score >= 4.0:
            return "medium"
        elif score >= 2.0:
            return "low"
        else:
            return "minimal"
    
    def _calculate_confidence(self, detections: List[HallucinationDetection]) -> float:
        """Calculate confidence in the hallucination assessment"""
        if not detections:
            return 0.95  # High confidence in "no hallucination" assessment
        
        # Average confidence of detections
        confidences = [d.confidence for d in detections]
        avg_confidence = sum(confidences) / len(confidences)
        
        # Adjust based on detection count and severity
        high_severity_count = len([d for d in detections if d.severity in [HallucinationSeverity.HIGH, HallucinationSeverity.CRITICAL]])
        
        if high_severity_count > 0:
            avg_confidence += 0.1  # Higher confidence for high-severity detections
        
        return max(0.0, min(1.0, avg_confidence))
