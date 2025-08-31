"""
Text Sanitizer for masking and cleaning PII from text content.

This module provides comprehensive text sanitization capabilities including:
- PII masking with configurable patterns
- Context-aware replacement
- Preserving text structure and readability
- Detailed sanitization logs
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from ..detectors.pii_detector import PIIEntity, PIIType


class MaskingStrategy(str, Enum):
    """Different strategies for masking PII"""
    FULL_MASK = "full_mask"          # Replace with ***
    PARTIAL_MASK = "partial_mask"    # Show first/last characters
    PLACEHOLDER = "placeholder"      # Replace with [TYPE] placeholder
    HASH = "hash"                   # Replace with hash value
    REMOVE = "remove"               # Completely remove


@dataclass
class SanitizationRule:
    """Configuration for how to sanitize different PII types"""
    pii_type: PIIType
    strategy: MaskingStrategy
    preserve_length: bool = True
    preserve_format: bool = False
    custom_replacement: Optional[str] = None


@dataclass
class SanitizationResult:
    """Result of text sanitization"""
    original_text: str
    sanitized_text: str
    entities_found: List[PIIEntity]
    entities_masked: List[PIIEntity]
    sanitization_log: List[Dict[str, Any]]
    risk_reduced: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "original_length": len(self.original_text),
            "sanitized_length": len(self.sanitized_text),
            "entities_found": len(self.entities_found),
            "entities_masked": len(self.entities_masked),
            "risk_reduced": self.risk_reduced,
            "sanitization_log": self.sanitization_log
        }


class TextSanitizer:
    """Advanced text sanitization engine with configurable rules"""
    
    def __init__(self, custom_rules: Optional[Dict[PIIType, SanitizationRule]] = None):
        """
        Initialize text sanitizer with optional custom rules
        
        Args:
            custom_rules: Dictionary mapping PII types to sanitization rules
        """
        self.rules = self._get_default_rules()
        if custom_rules:
            self.rules.update(custom_rules)
    
    def _get_default_rules(self) -> Dict[PIIType, SanitizationRule]:
        """Get default sanitization rules for each PII type"""
        return {
            PIIType.EMAIL: SanitizationRule(
                pii_type=PIIType.EMAIL,
                strategy=MaskingStrategy.PARTIAL_MASK,
                preserve_length=True,
                preserve_format=True
            ),
            PIIType.PHONE_NUMBER: SanitizationRule(
                pii_type=PIIType.PHONE_NUMBER,
                strategy=MaskingStrategy.PARTIAL_MASK,
                preserve_length=True,
                preserve_format=True
            ),
            PIIType.SSN: SanitizationRule(
                pii_type=PIIType.SSN,
                strategy=MaskingStrategy.FULL_MASK,
                preserve_length=True,
                preserve_format=True
            ),
            PIIType.CREDIT_CARD: SanitizationRule(
                pii_type=PIIType.CREDIT_CARD,
                strategy=MaskingStrategy.PARTIAL_MASK,
                preserve_length=True,
                preserve_format=True
            ),
            PIIType.IP_ADDRESS: SanitizationRule(
                pii_type=PIIType.IP_ADDRESS,
                strategy=MaskingStrategy.PLACEHOLDER,
                preserve_length=False,
                custom_replacement="[IP_ADDRESS]"
            ),
            PIIType.ADDRESS: SanitizationRule(
                pii_type=PIIType.ADDRESS,
                strategy=MaskingStrategy.PLACEHOLDER,
                preserve_length=False,
                custom_replacement="[ADDRESS]"
            ),
            PIIType.URL: SanitizationRule(
                pii_type=PIIType.URL,
                strategy=MaskingStrategy.PLACEHOLDER,
                preserve_length=False,
                custom_replacement="[URL]"
            ),
            PIIType.DATE: SanitizationRule(
                pii_type=PIIType.DATE,
                strategy=MaskingStrategy.PLACEHOLDER,
                preserve_length=False,
                custom_replacement="[DATE]"
            ),
            PIIType.FINANCIAL: SanitizationRule(
                pii_type=PIIType.FINANCIAL,
                strategy=MaskingStrategy.FULL_MASK,
                preserve_length=True,
                preserve_format=True
            ),
            PIIType.NAME: SanitizationRule(
                pii_type=PIIType.NAME,
                strategy=MaskingStrategy.PLACEHOLDER,
                preserve_length=False,
                custom_replacement="[NAME]"
            ),
        }
    
    def sanitize_text(self, text: str, entities: List[PIIEntity], 
                     confidence_threshold: float = 0.7) -> SanitizationResult:
        """
        Sanitize text by masking detected PII entities
        
        Args:
            text: Original text to sanitize
            entities: List of detected PII entities
            confidence_threshold: Minimum confidence to apply sanitization
            
        Returns:
            SanitizationResult with sanitized text and metadata
        """
        if not entities:
            return SanitizationResult(
                original_text=text,
                sanitized_text=text,
                entities_found=entities,
                entities_masked=[],
                sanitization_log=[],
                risk_reduced=0.0
            )
        
        # Filter entities by confidence threshold
        entities_to_mask = [e for e in entities if e.confidence >= confidence_threshold]
        
        # Sort entities by start position (reverse order for replacement)
        entities_to_mask.sort(key=lambda x: x.start, reverse=True)
        
        sanitized_text = text
        sanitization_log = []
        
        # Apply sanitization to each entity
        for entity in entities_to_mask:
            rule = self.rules.get(entity.type)
            if not rule:
                continue
            
            replacement = self._generate_replacement(entity, rule)
            
            # Replace in text
            sanitized_text = (
                sanitized_text[:entity.start] + 
                replacement + 
                sanitized_text[entity.end:]
            )
            
            # Log the sanitization
            sanitization_log.append({
                "type": entity.type.value,
                "original": entity.value,
                "replacement": replacement,
                "strategy": rule.strategy.value,
                "position": {"start": entity.start, "end": entity.end},
                "confidence": entity.confidence
            })
        
        # Calculate risk reduction
        original_risk = self._calculate_text_risk(entities)
        remaining_risk = self._calculate_text_risk([e for e in entities if e not in entities_to_mask])
        risk_reduced = max(0.0, original_risk - remaining_risk)
        
        return SanitizationResult(
            original_text=text,
            sanitized_text=sanitized_text,
            entities_found=entities,
            entities_masked=entities_to_mask,
            sanitization_log=sanitization_log,
            risk_reduced=risk_reduced
        )
    
    def _generate_replacement(self, entity: PIIEntity, rule: SanitizationRule) -> str:
        """Generate replacement text based on sanitization rule"""
        
        if rule.custom_replacement:
            return rule.custom_replacement
        
        if rule.strategy == MaskingStrategy.FULL_MASK:
            return self._full_mask(entity.value, rule.preserve_length, rule.preserve_format)
        
        elif rule.strategy == MaskingStrategy.PARTIAL_MASK:
            return self._partial_mask(entity.value, entity.type, rule.preserve_format)
        
        elif rule.strategy == MaskingStrategy.PLACEHOLDER:
            return f"[{entity.type.value.upper()}]"
        
        elif rule.strategy == MaskingStrategy.HASH:
            return self._hash_value(entity.value)
        
        elif rule.strategy == MaskingStrategy.REMOVE:
            return ""
        
        else:
            return "***"  # Default fallback
    
    def _full_mask(self, value: str, preserve_length: bool, preserve_format: bool) -> str:
        """Create full mask replacement"""
        if not preserve_length:
            return "***"
        
        if preserve_format:
            # Preserve special characters, mask alphanumeric
            masked = ""
            for char in value:
                if char.isalnum():
                    masked += "*"
                else:
                    masked += char
            return masked
        else:
            return "*" * len(value)
    
    def _partial_mask(self, value: str, pii_type: PIIType, preserve_format: bool) -> str:
        """Create partial mask showing some characters"""
        
        if pii_type == PIIType.EMAIL:
            return self._mask_email(value)
        elif pii_type == PIIType.PHONE_NUMBER:
            return self._mask_phone(value)
        elif pii_type == PIIType.CREDIT_CARD:
            return self._mask_credit_card(value)
        else:
            # Default partial masking (show first and last 2 chars)
            if len(value) <= 4:
                return "*" * len(value)
            return value[:2] + "*" * (len(value) - 4) + value[-2:]
    
    def _mask_email(self, email: str) -> str:
        """Mask email address preserving domain"""
        if "@" not in email:
            return "***@***.***"
        
        username, domain = email.split("@", 1)
        
        if len(username) <= 2:
            masked_username = "*" * len(username)
        else:
            masked_username = username[0] + "*" * (len(username) - 2) + username[-1]
        
        # Keep domain or mask it partially
        if "." in domain:
            domain_parts = domain.split(".")
            if len(domain_parts) >= 2:
                # Show TLD, mask domain name
                masked_domain = "*" * len(domain_parts[0]) + "." + domain_parts[-1]
            else:
                masked_domain = domain
        else:
            masked_domain = domain
        
        return f"{masked_username}@{masked_domain}"
    
    def _mask_phone(self, phone: str) -> str:
        """Mask phone number showing last 4 digits"""
        # Extract digits only
        digits = re.sub(r'[^\d]', '', phone)
        
        if len(digits) < 4:
            return "*" * len(phone)
        
        # Preserve original format but mask digits
        masked = phone
        for i, char in enumerate(phone):
            if char.isdigit():
                digit_position = len(re.sub(r'[^\d]', '', phone[:i+1]))
                if digit_position <= len(digits) - 4:
                    masked = masked[:i] + "*" + masked[i+1:]
        
        return masked
    
    def _mask_credit_card(self, cc: str) -> str:
        """Mask credit card showing last 4 digits"""
        # Extract digits only
        digits = re.sub(r'[^\d]', '', cc)
        
        if len(digits) < 4:
            return "*" * len(cc)
        
        # Show last 4 digits, mask the rest
        masked = ""
        digit_count = 0
        
        for char in cc:
            if char.isdigit():
                digit_count += 1
                if digit_count > len(digits) - 4:
                    masked += char
                else:
                    masked += "*"
            else:
                masked += char
        
        return masked
    
    def _hash_value(self, value: str) -> str:
        """Create hash replacement"""
        import hashlib
        hash_obj = hashlib.md5(value.encode())
        return f"[HASH:{hash_obj.hexdigest()[:8]}]"
    
    def _calculate_text_risk(self, entities: List[PIIEntity]) -> float:
        """Calculate overall risk level for a list of entities"""
        if not entities:
            return 0.0
        
        # Risk weights for different PII types
        risk_weights = {
            PIIType.SSN: 10.0,
            PIIType.CREDIT_CARD: 9.0,
            PIIType.FINANCIAL: 8.0,
            PIIType.EMAIL: 6.0,
            PIIType.PHONE_NUMBER: 5.0,
            PIIType.ADDRESS: 4.0,
            PIIType.IP_ADDRESS: 3.0,
            PIIType.DATE: 2.0,
            PIIType.URL: 2.0,
            PIIType.NAME: 1.0,
        }
        
        total_risk = 0.0
        for entity in entities:
            weight = risk_weights.get(entity.type, 1.0)
            total_risk += weight * entity.confidence
        
        return min(10.0, total_risk)
    
    def set_rule(self, pii_type: PIIType, rule: SanitizationRule) -> None:
        """Set custom sanitization rule for a PII type"""
        self.rules[pii_type] = rule
    
    def get_rule(self, pii_type: PIIType) -> Optional[SanitizationRule]:
        """Get sanitization rule for a PII type"""
        return self.rules.get(pii_type)
    
    def preview_sanitization(self, text: str, entities: List[PIIEntity]) -> List[Dict[str, Any]]:
        """Preview what would be sanitized without actually doing it"""
        preview = []
        
        for entity in entities:
            rule = self.rules.get(entity.type)
            if rule:
                replacement = self._generate_replacement(entity, rule)
                preview.append({
                    "type": entity.type.value,
                    "original": entity.value,
                    "would_become": replacement,
                    "strategy": rule.strategy.value,
                    "confidence": entity.confidence,
                    "position": {"start": entity.start, "end": entity.end}
                })
        
        return preview
