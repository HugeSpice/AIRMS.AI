"""
Enhanced PII Detection using Microsoft Presidio, spaCy, and Custom Regex

This module provides comprehensive PII detection capabilities:
- Microsoft Presidio for standard PII types
- spaCy NER for custom entity extraction
- Custom regex patterns for tokens like API keys, CC numbers
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

try:
    from presidio_analyzer import AnalyzerEngine
    from presidio_analyzer.nlp_engine import NlpEngineProvider
    from presidio_anonymizer import AnonymizerEngine
    from presidio_anonymizer.entities import RecognizerResult
    import spacy
    PRESIDIO_AVAILABLE = True
except ImportError:
    PRESIDIO_AVAILABLE = False
    logging.warning("Presidio not available. PII detection will be limited.")

logger = logging.getLogger(__name__)


class PIIType(str, Enum):
    """Extended PII types supported by the system"""
    # Standard PII types (Presidio)
    EMAIL = "email"
    PHONE_NUMBER = "phone_number"
    SSN = "ssn"
    CREDIT_CARD = "credit_card"
    IBAN = "iban"
    IP_ADDRESS = "ip_address"
    DATE = "date"
    LOCATION = "location"
    PERSON = "person"
    ORGANIZATION = "organization"
    
    # Additional PII types for compatibility
    ADDRESS = "address"
    URL = "url"
    FINANCIAL = "financial"
    NAME = "name"
    
    # Custom PII types (Regex + spaCy)
    API_KEY = "api_key"
    DATABASE_CONNECTION = "database_connection"
    JWT_TOKEN = "jwt_token"
    SSH_KEY = "ssh_key"
    PASSWORD = "password"
    SECRET_KEY = "secret_key"
    ACCESS_TOKEN = "access_token"
    PRIVATE_KEY = "private_key"
    SESSION_ID = "session_id"
    USER_ID = "user_id"


@dataclass
class PIIEntity:
    """Enhanced PII entity with additional metadata"""
    type: PIIType
    value: str
    confidence: float
    start: int
    end: int
    detection_method: str  # "presidio", "spacy", "regex"
    original_text: str
    replacement_value: str
    risk_level: str  # "low", "medium", "high", "critical"
    context: Optional[str] = None


class EnhancedPIIDetector:
    """
    Enhanced PII detector combining Presidio, spaCy, and custom regex patterns
    """
    
    def __init__(self, strict_mode: bool = False):
        self.strict_mode = strict_mode
        self._initialize_components()
        self._setup_custom_patterns()
    
    def _initialize_components(self):
        """Initialize Presidio and spaCy components"""
        try:
            if PRESIDIO_AVAILABLE:
                # Initialize Presidio
                self.presidio_analyzer = AnalyzerEngine()
                self.presidio_anonymizer = AnonymizerEngine()
                
                # Initialize spaCy
                try:
                    self.spacy_nlp = spacy.load("en_core_web_sm")
                except OSError:
                    # Download if not available
                    import subprocess
                    subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
                    self.spacy_nlp = spacy.load("en_core_web_sm")
                
                logger.info("Enhanced PII detection components initialized successfully")
            else:
                logger.warning("Presidio not available. Using fallback detection only.")
                self.presidio_analyzer = None
                self.presidio_anonymizer = None
                self.spacy_nlp = None
                
        except Exception as e:
            logger.error(f"Failed to initialize PII detection components: {e}")
            self.presidio_analyzer = None
            self.presidio_anonymizer = None
            self.spacy_nlp = None
    
    def _setup_custom_patterns(self):
        """Setup custom regex patterns for specific PII types"""
        self.custom_patterns = {
            PIIType.API_KEY: [
                r'\b(?:sk|pk)_[a-zA-Z0-9]{24,}\b',  # Stripe-like keys
                r'\b[a-zA-Z0-9]{32,}\b',  # Generic long keys
                r'\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{36}\b',  # GitHub tokens
                r'\b(?:AIza|AIzaSy)[A-Za-z0-9_-]{35}\b',  # Google API keys
            ],
            PIIType.CREDIT_CARD: [
                r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3[0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\b',
            ],
            PIIType.SSN: [
                r'\b(?:[0-9]{3}-[0-9]{2}-[0-9]{4}|[0-9]{9})\b',
            ],
            PIIType.EMAIL: [
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            ],
            PIIType.PHONE_NUMBER: [
                r'\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b',
            ],
            PIIType.IP_ADDRESS: [
                r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
                r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b',  # IPv6
            ],
            PIIType.DATABASE_CONNECTION: [
                r'\b(?:postgresql|mysql|mongodb)://[^\s]+\b',
                r'\b(?:host|port|database|username|password)=[^\s]+\b',
            ],
            PIIType.JWT_TOKEN: [
                r'\beyJ[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*\b',
            ],
            PIIType.SSH_KEY: [
                r'\b(?:ssh-rsa|ssh-dss|ecdsa-sha2-nistp256|ecdsa-sha2-nistp384|ecdsa-sha2-nistp521) [A-Za-z0-9+/=]+[^\s]*\b',
            ],
            PIIType.PASSWORD: [
                r'\b(?:password|passwd|pwd)\s*[:=]\s*[^\s]+\b',
            ],
            PIIType.SECRET_KEY: [
                r'\b(?:secret|key|token)\s*[:=]\s*[^\s]+\b',
            ],
        }
    
    def detect_all(self, text: str, confidence_threshold: float = 0.7) -> List[PIIEntity]:
        """
        Comprehensive PII detection using all available methods
        
        Args:
            text: Text to analyze
            confidence_threshold: Minimum confidence for detection
            
        Returns:
            List of detected PII entities
        """
        all_entities = []
        
        # 1. Presidio detection (if available)
        if self.presidio_analyzer:
            presidio_entities = self._detect_with_presidio(text)
            all_entities.extend(presidio_entities)
        
        # 2. spaCy NER detection (if available)
        if self.spacy_nlp:
            spacy_entities = self._detect_with_spacy(text)
            all_entities.extend(spacy_entities)
        
        # 3. Custom regex detection
        regex_entities = self._detect_with_regex(text)
        all_entities.extend(regex_entities)
        
        # 4. Filter by confidence threshold
        filtered_entities = [
            entity for entity in all_entities 
            if entity.confidence >= confidence_threshold
        ]
        
        # 5. Remove duplicates and merge overlapping entities
        deduplicated_entities = self._deduplicate_entities(filtered_entities)
        
        return deduplicated_entities
    
    def _detect_with_presidio(self, text: str) -> List[PIIEntity]:
        """Detect PII using Microsoft Presidio"""
        try:
            # Analyze text with Presidio
            results = self.presidio_analyzer.analyze(
                text=text,
                language="en",
                entities=["EMAIL_ADDRESS", "PHONE_NUMBER", "CREDIT_CARD", "IBAN_CODE", 
                         "IP_ADDRESS", "DATE_TIME", "LOCATION", "PERSON", "ORGANIZATION"]
            )
            
            entities = []
            for result in results:
                pii_type = self._map_presidio_to_pii_type(result.entity_type)
                if pii_type:
                    entity = PIIEntity(
                        type=pii_type,
                        value=text[result.start:result.end],
                        confidence=result.score,
                        start=result.start,
                        end=result.end,
                        detection_method="presidio",
                        original_text=text[result.start:result.end],
                        replacement_value=self._generate_replacement(pii_type),
                        risk_level=self._calculate_risk_level(pii_type, result.score),
                        context=text[max(0, result.start-20):result.end+20]
                    )
                    entities.append(entity)
            
            return entities
            
        except Exception as e:
            logger.error(f"Presidio detection failed: {e}")
            return []
    
    def _detect_with_spacy(self, text: str) -> List[PIIEntity]:
        """Detect entities using spaCy NER"""
        try:
            doc = self.spacy_nlp(text)
            entities = []
            
            for ent in doc.ents:
                pii_type = self._map_spacy_to_pii_type(ent.label_)
                if pii_type:
                    entity = PIIEntity(
                        type=pii_type,
                        value=ent.text,
                        confidence=0.8,  # spaCy doesn't provide confidence scores
                        start=ent.start_char,
                        end=ent.end_char,
                        detection_method="spacy",
                        original_text=ent.text,
                        replacement_value=self._generate_replacement(pii_type),
                        risk_level=self._calculate_risk_level(pii_type, 0.8),
                        context=text[max(0, ent.start_char-20):ent.end_char+20]
                    )
                    entities.append(entity)
            
            return entities
            
        except Exception as e:
            logger.error(f"spaCy detection failed: {e}")
            return []
    
    def _detect_with_regex(self, text: str) -> List[PIIEntity]:
        """Detect PII using custom regex patterns"""
        entities = []
        
        for pii_type, patterns in self.custom_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    entity = PIIEntity(
                        type=pii_type,
                        value=match.group(),
                        confidence=0.9,  # High confidence for regex matches
                        start=match.start(),
                        end=match.end(),
                        detection_method="regex",
                        original_text=match.group(),
                        replacement_value=self._generate_replacement(pii_type),
                        risk_level=self._calculate_risk_level(pii_type, 0.9),
                        context=text[max(0, match.start()-20):match.end()+20]
                    )
                    entities.append(entity)
        
        return entities
    
    def _map_presidio_to_pii_type(self, presidio_type: str) -> Optional[PIIType]:
        """Map Presidio entity types to our PII types"""
        mapping = {
            "EMAIL_ADDRESS": PIIType.EMAIL,
            "PHONE_NUMBER": PIIType.PHONE_NUMBER,
            "CREDIT_CARD": PIIType.CREDIT_CARD,
            "IBAN_CODE": PIIType.IBAN,
            "IP_ADDRESS": PIIType.IP_ADDRESS,
            "DATE_TIME": PIIType.DATE,
            "LOCATION": PIIType.LOCATION,
            "PERSON": PIIType.PERSON,
            "ORGANIZATION": PIIType.ORGANIZATION,
        }
        return mapping.get(presidio_type)
    
    def _map_spacy_to_pii_type(self, spacy_label: str) -> Optional[PIIType]:
        """Map spaCy entity labels to our PII types"""
        mapping = {
            "PERSON": PIIType.PERSON,
            "ORG": PIIType.ORGANIZATION,
            "GPE": PIIType.LOCATION,
            "LOC": PIIType.LOCATION,
            "DATE": PIIType.DATE,
        }
        return mapping.get(spacy_label)
    
    def _generate_replacement(self, pii_type: PIIType) -> str:
        """Generate replacement text for PII entities"""
        replacements = {
            PIIType.EMAIL: "[EMAIL]",
            PIIType.PHONE_NUMBER: "[PHONE]",
            PIIType.SSN: "[SSN]",
            PIIType.CREDIT_CARD: "[CREDIT_CARD]",
            PIIType.IBAN: "[IBAN]",
            PIIType.IP_ADDRESS: "[IP_ADDRESS]",
            PIIType.DATE: "[DATE]",
            PIIType.LOCATION: "[LOCATION]",
            PIIType.PERSON: "[PERSON]",
            PIIType.ORGANIZATION: "[ORGANIZATION]",
            PIIType.API_KEY: "[API_KEY]",
            PIIType.DATABASE_CONNECTION: "[DB_CONNECTION]",
            PIIType.JWT_TOKEN: "[JWT_TOKEN]",
            PIIType.SSH_KEY: "[SSH_KEY]",
            PIIType.PASSWORD: "[PASSWORD]",
            PIIType.SECRET_KEY: "[SECRET_KEY]",
            PIIType.ACCESS_TOKEN: "[ACCESS_TOKEN]",
            PIIType.PRIVATE_KEY: "[PRIVATE_KEY]",
            PIIType.SESSION_ID: "[SESSION_ID]",
            PIIType.USER_ID: "[USER_ID]",
        }
        return replacements.get(pii_type, "[PII]")
    
    def _calculate_risk_level(self, pii_type: PIIType, confidence: float) -> str:
        """Calculate risk level based on PII type and confidence"""
        critical_types = {PIIType.SSN, PIIType.CREDIT_CARD, PIIType.API_KEY, PIIType.SSH_KEY}
        high_types = {PIIType.PASSWORD, PIIType.SECRET_KEY, PIIType.PRIVATE_KEY, PIIType.JWT_TOKEN}
        
        if pii_type in critical_types:
            return "critical"
        elif pii_type in high_types:
            return "high"
        elif confidence >= 0.9:
            return "medium"
        else:
            return "low"
    
    def _deduplicate_entities(self, entities: List[PIIEntity]) -> List[PIIEntity]:
        """Remove duplicate and overlapping entities"""
        if not entities:
            return []
        
        # Sort by start position
        sorted_entities = sorted(entities, key=lambda x: x.start)
        deduplicated = []
        
        for entity in sorted_entities:
            # Check if this entity overlaps with any existing entity
            is_duplicate = False
            for existing in deduplicated:
                if (entity.start < existing.end and entity.end > existing.start):
                    # Overlap detected, keep the one with higher confidence
                    if entity.confidence > existing.confidence:
                        deduplicated.remove(existing)
                        deduplicated.append(entity)
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                deduplicated.append(entity)
        
        return deduplicated
    
    def anonymize_text(self, text: str, entities: List[PIIEntity]) -> str:
        """Anonymize text by replacing PII entities"""
        if not entities:
            return text
        
        # Sort entities by start position (reverse order to avoid index shifting)
        sorted_entities = sorted(entities, key=lambda x: x.start, reverse=True)
        
        anonymized_text = text
        for entity in sorted_entities:
            anonymized_text = (
                anonymized_text[:entity.start] + 
                entity.replacement_value + 
                anonymized_text[entity.end:]
            )
        
        return anonymized_text
    
    def get_detection_summary(self, entities: List[PIIEntity]) -> Dict[str, Any]:
        """Get summary of PII detection results"""
        if not entities:
            return {
                "total_entities": 0,
                "risk_levels": {},
                "types_detected": {},
                "detection_methods": {}
            }
        
        risk_levels = {}
        types_detected = {}
        detection_methods = {}
        
        for entity in entities:
            # Count risk levels
            risk_levels[entity.risk_level] = risk_levels.get(entity.risk_level, 0) + 1
            
            # Count types
            types_detected[entity.type.value] = types_detected.get(entity.type.value, 0) + 1
            
            # Count detection methods
            detection_methods[entity.detection_method] = detection_methods.get(entity.detection_method, 0) + 1
        
        return {
            "total_entities": len(entities),
            "risk_levels": risk_levels,
            "types_detected": types_detected,
            "detection_methods": detection_methods,
            "highest_risk_level": max(risk_levels.keys()) if risk_levels else "none"
        }
