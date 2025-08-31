"""
Data encryption utilities for sensitive risk information
"""

import base64
import logging
from cryptography.fernet import Fernet
from app.core.config import settings

logger = logging.getLogger(__name__)

class DataEncryption:
    """Simple encryption for sensitive data"""
    
    def __init__(self):
        # Use a fixed key for demo purposes - in production, use environment variable
        # In production, you would use: settings.ENCRYPTION_KEY
        self.key = b'your-32-byte-encryption-key-here!!'
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
