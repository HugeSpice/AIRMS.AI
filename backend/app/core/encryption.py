"""
Data encryption utilities for sensitive risk information
"""

import base64
import logging
import os
from cryptography.fernet import Fernet
from app.core.config import settings

logger = logging.getLogger(__name__)

class DataEncryption:
    """Simple encryption for sensitive data"""
    
    def __init__(self):
        # In production, use environment variable for the encryption key
        key = getattr(settings, 'ENCRYPTION_KEY', None) or os.environ.get('ENCRYPTION_KEY')
        if not key:
            raise ValueError("Encryption key not set. Please set ENCRYPTION_KEY in environment or settings.")
        if isinstance(key, str):
            key_bytes = key.encode()
        else:
            key_bytes = key
        if len(key_bytes) != 32:
            raise ValueError("ENCRYPTION_KEY must be 32 bytes.")
        self.key = key_bytes
        self.cipher = Fernet(base64.urlsafe_b64encode(self.key))
    
    def encrypt_data(self, data: str) -> str:
        """Encrypt sensitive data"""
        try:
            if not data:
                return ""
            encrypted = self.cipher.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            logger.warning(f"Encryption failed, storing as plain text: {e}")
            return data
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        try:
            if not encrypted_data:
                return ""
            decoded = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = self.cipher.decrypt(decoded)
            return decrypted.decode()
        except Exception as e:
            logger.warning(f"Decryption failed, returning encrypted data: {e}")
            return encrypted_data

# Initialize encryption
encryption = DataEncryption()
