"""
Token Remapping System for AIRMS

This module provides secure storage and retrieval of masked values:
1. Secure token storage with encryption
2. Token mapping and retrieval
3. Audit trail for compliance
4. Automatic token expiration
"""

from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum
import uuid
import time
import json
import hashlib
import secrets
from datetime import datetime, timedelta
import sqlite3
import os
import base64
from Crypto.Cipher import AES

class TokenType(str, Enum):
    """Types of tokens that can be stored"""
    EMAIL = "email"
    PHONE = "phone"
    SSN = "ssn"
    CREDIT_CARD = "credit_card"
    ADDRESS = "address"
    NAME = "name"
    CUSTOM = "custom"

class TokenStatus(str, Enum):
    """Status of stored tokens"""
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    ARCHIVED = "archived"

@dataclass
class TokenMapping:
    """Token mapping record"""
    token_id: str
    original_value: str
    masked_value: str
    token_type: TokenType
    status: TokenStatus
    created_at: datetime
    expires_at: datetime
    access_count: int
    last_accessed: datetime
    metadata: Dict[str, Any]

@dataclass
class TokenAccessLog:
    """Log of token access attempts"""
    log_id: str
    token_id: str
    access_time: datetime
    access_type: str  # 'retrieve', 'validate', 'revoke'
    user_id: Optional[str]
    ip_address: Optional[str]
    success: bool
    metadata: Dict[str, Any]

class TokenRemapper:
    """Secure token remapping system"""
    
    def __init__(self, db_path: str = "token_store.db", encryption_key: Optional[str] = None):
        self.db_path = db_path
        self.encryption_key = encryption_key or self._generate_encryption_key()
        self.db_connection = None
        self._initialize_database()
        
    def _generate_encryption_key(self) -> str:
        """Generate a secure encryption key"""
        return secrets.token_hex(32)
    
    def _initialize_database(self):
        """Initialize the token storage database"""
        try:
            self.db_connection = sqlite3.connect(self.db_path)
            cursor = self.db_connection.cursor()
            
            # Create tokens table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS token_mappings (
                    token_id TEXT PRIMARY KEY,
                    original_value_hash TEXT NOT NULL,
                    masked_value TEXT NOT NULL,
                    token_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    access_count INTEGER DEFAULT 0,
                    last_accessed TEXT,
                    metadata TEXT,
                    encryption_salt TEXT NOT NULL,
                    encrypted_value TEXT
                )
            """)
            
            # Create access logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS token_access_logs (
                    log_id TEXT PRIMARY KEY,
                    token_id TEXT NOT NULL,
                    access_time TEXT NOT NULL,
                    access_type TEXT NOT NULL,
                    user_id TEXT,
                    ip_address TEXT,
                    success BOOLEAN NOT NULL,
                    metadata TEXT,
                    FOREIGN KEY (token_id) REFERENCES token_mappings (token_id)
                )
            """)
            
            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_token_type ON token_mappings (token_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_token_status ON token_mappings (status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_expires_at ON token_mappings (expires_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_masked_value ON token_mappings (masked_value)")
            
            self.db_connection.commit()
            
        except Exception as e:
            print(f"Failed to initialize token database: {e}")
            raise
    
    def _hash_value(self, value: str, salt: str) -> str:
        """Hash a value with salt for secure storage"""
        return hashlib.sha256((value + salt).encode()).hexdigest()
    
    def _encrypt_value(self, value: str, salt: str) -> str:
        """Encrypt value using AES-256-CBC with PKCS7 padding and per-token salt-derived key."""
        key = hashlib.pbkdf2_hmac('sha256', self.encryption_key.encode(), salt.encode(), 100000, dklen=32)
        iv = os.urandom(16)
        pad_len = 16 - (len(value.encode()) % 16)
        padded_value = value.encode() + bytes([pad_len] * pad_len)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        ct = cipher.encrypt(padded_value)
        return base64.b64encode(iv + ct).decode('utf-8')
    
    def _decrypt_value(self, encrypted_value: str, salt: str) -> str:
        try:
            data = base64.b64decode(encrypted_value)
            iv, ct = data[:16], data[16:]
            key = hashlib.pbkdf2_hmac('sha256', self.encryption_key.encode(), salt.encode(), 100000, dklen=32)
            cipher = AES.new(key, AES.MODE_CBC, iv)
            padded_value = cipher.decrypt(ct)
            pad_len = padded_value[-1]
            return padded_value[:-pad_len].decode('utf-8')
        except Exception:
            return ""
    
    def store_token(self, 
                   original_value: str, 
                   token_type: TokenType, 
                   expiration_hours: int = 24,
                   metadata: Optional[Dict[str, Any]] = None) -> str:
        try:
            token_id = str(uuid.uuid4())
            salt = secrets.token_hex(16)
            masked_value = self._create_masked_value(original_value, token_type)
            original_hash = self._hash_value(original_value, salt)
            encrypted_value = self._encrypt_value(original_value, salt)
            created_at = datetime.now()
            expires_at = created_at + timedelta(hours=expiration_hours)
            cursor = self.db_connection.cursor()
            cursor.execute("""
                INSERT INTO token_mappings (
                    token_id, original_value_hash, masked_value, token_type, status,
                    created_at, expires_at, access_count, last_accessed, metadata, encryption_salt, encrypted_value
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                token_id, original_hash, masked_value, token_type.value, TokenStatus.ACTIVE.value,
                created_at.isoformat(), expires_at.isoformat(), 0, created_at.isoformat(),
                json.dumps(metadata or {}), salt, encrypted_value
            ))
            self.db_connection.commit()
            self._log_access(token_id, "store", True, metadata)
            return masked_value
        except Exception as e:
            print(f"Failed to store token: {e}")
            raise
    
    def _create_masked_value(self, value: str, token_type: TokenType) -> str:
        if token_type == TokenType.EMAIL:
            if '@' in value:
                username, domain = value.split('@', 1)
                masked_username = username[0] + '*' * (len(username) - 1) if len(username) > 1 else username
                masked_domain = domain[0] + '*' * (len(domain) - 2) + domain[-1] if len(domain) > 2 else domain
                return f"{masked_username}@{masked_domain}"
            else:
                return value[0] + '*' * (len(value) - 1) if len(value) > 1 else value
        elif token_type == TokenType.PHONE:
            if len(value) >= 10:
                return value[:3] + '-' + '*' * 3 + '-' + '*' * 3 + '-' + value[-4:]
            else:
                return '*' * len(value)
        elif token_type == TokenType.SSN:
            if len(value) >= 9:
                return '*' * 3 + '-' + '*' * 2 + '-' + value[-4:]
            else:
                return '*' * len(value)
        elif token_type == TokenType.CREDIT_CARD:
            if len(value) >= 16:
                return '*' * 4 + '-' + '*' * 4 + '-' + '*' * 4 + '-' + value[-4:]
            else:
                return '*' * len(value)
        elif token_type == TokenType.ADDRESS:
            words = value.split()
            masked_words = []
            for word in words:
                if len(word) > 1:
                    masked_words.append(word[0] + '*' * (len(word) - 1))
                else:
                    masked_words.append(word)
            return ' '.join(masked_words)
        elif token_type == TokenType.NAME:
            words = value.split()
            masked_words = []
            for word in words:
                if len(word) > 1:
                    masked_words.append(word[0] + '*' * (len(word) - 1))
                else:
                    masked_words.append(word)
            return ' '.join(masked_words)
        else:
            if len(value) > 2:
                return value[0] + '*' * (len(value) - 2) + value[-1]
            else:
                return '*' * len(value)
    
    def retrieve_token(self, masked_value: str, token_type: Optional[TokenType] = None) -> Optional[str]:
        try:
            cursor = self.db_connection.cursor()
            query = "SELECT token_id, original_value_hash, encryption_salt, status, expires_at, encrypted_value FROM token_mappings WHERE masked_value = ?"
            params = [masked_value]
            if token_type:
                query += " AND token_type = ?"
                params.append(token_type.value)
            cursor.execute(query, params)
            row = cursor.fetchone()
            if not row:
                self._log_access("unknown", "retrieve", False, {"masked_value": masked_value})
                return None
            token_id, original_hash, salt, status, expires_at, encrypted_value = row
            if datetime.fromisoformat(expires_at) < datetime.now():
                self._update_token_status(token_id, TokenStatus.EXPIRED)
                self._log_access(token_id, "retrieve", False, {"reason": "expired"})
                return None
            if status == TokenStatus.REVOKED.value:
                self._log_access(token_id, "retrieve", False, {"reason": "revoked"})
                return None
            original_value = self._decrypt_value(encrypted_value, salt)
            cursor.execute("""
                UPDATE token_mappings 
                SET access_count = access_count + 1, last_accessed = ? 
                WHERE token_id = ?
            """, [datetime.now().isoformat(), token_id])
            self.db_connection.commit()
            self._log_access(token_id, "retrieve", True, {"token_type": token_type.value if token_type else "unknown"})
            return original_value
        except Exception as e:
            print(f"Failed to retrieve token: {e}")
            self._log_access("error", "retrieve", False, {"error": str(e)})
            return None
    
    def validate_token(self, masked_value: str, token_type: Optional[TokenType] = None) -> bool:
        try:
            cursor = self.db_connection.cursor()
            query = "SELECT token_id, status, expires_at FROM token_mappings WHERE masked_value = ?"
            params = [masked_value]
            if token_type:
                query += " AND token_type = ?"
                params.append(token_type.value)
            cursor.execute(query, params)
            row = cursor.fetchone()
            if not row:
                self._log_access("unknown", "validate", False, {"masked_value": masked_value})
                return False
            token_id, status, expires_at = row
            if datetime.fromisoformat(expires_at) < datetime.now():
                self._update_token_status(token_id, TokenStatus.EXPIRED)
                self._log_access(token_id, "validate", False, {"reason": "expired"})
                return False
            if status == TokenStatus.REVOKED.value:
                self._log_access(token_id, "validate", False, {"reason": "revoked"})
                return False
            self._log_access(token_id, "validate", True, {"token_type": token_type.value if token_type else "unknown"})
            return True
        except Exception as e:
            print(f"Failed to validate token: {e}")
            self._log_access("error", "validate", False, {"error": str(e)})
            return False
    
    def revoke_token(self, masked_value: str) -> bool:
        try:
            cursor = self.db_connection.cursor()
            cursor.execute("SELECT token_id FROM token_mappings WHERE masked_value = ?", [masked_value])
            row = cursor.fetchone()
            if not row:
                return False
            token_id = row[0]
            self._update_token_status(token_id, TokenStatus.REVOKED)
            self._log_access(token_id, "revoke", True, {"action": "token_revoked"})
            return True
        except Exception as e:
            print(f"Failed to revoke token: {e}")
            return False
    
    def _update_token_status(self, token_id: str, status: TokenStatus):
        try:
            cursor = self.db_connection.cursor()
            cursor.execute("""
                UPDATE token_mappings 
                SET status = ? 
                WHERE token_id = ?
            """, [status.value, token_id])
            self.db_connection.commit()
        except Exception as e:
            print(f"Failed to update token status: {e}")
    
    def _log_access(self, token_id: str, access_type: str, success: bool, metadata: Optional[Dict[str, Any]] = None):
        try:
            log_id = str(uuid.uuid4())
            access_time = datetime.now()
            cursor = self.db_connection.cursor()
            cursor.execute("""
                INSERT INTO token_access_logs (
                    log_id, token_id, access_time, access_type, user_id, ip_address, success, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                log_id, token_id, access_time.isoformat(), access_type, 
                metadata.get('user_id') if metadata else None,
                metadata.get('ip_address') if metadata else None,
                success, json.dumps(metadata or {})
            ))
            self.db_connection.commit()
        except Exception as e:
            print(f"Failed to log access: {e}")
    
    def get_token_info(self, masked_value: str) -> Optional[TokenMapping]:
        try:
            cursor = self.db_connection.cursor()
            cursor.execute("""
                SELECT token_id, masked_value, token_type, status, created_at, expires_at, 
                       access_count, last_accessed, metadata
                FROM token_mappings 
                WHERE masked_value = ?
            """, [masked_value])
            row = cursor.fetchone()
            if not row:
                return None
            token_id, masked_value, token_type, status, created_at, expires_at, access_count, last_accessed, metadata = row
            return TokenMapping(
                token_id=token_id,
                original_value="[HIDDEN]",  # Don't reveal original value
                masked_value=masked_value,
                token_type=TokenType(token_type),
                status=TokenStatus(status),
                created_at=datetime.fromisoformat(created_at),
                expires_at=datetime.fromisoformat(expires_at),
                access_count=access_count,
                last_accessed=datetime.fromisoformat(last_accessed) if last_accessed else None,
                metadata=json.loads(metadata) if metadata else {}
            )
        except Exception as e:
            print(f"Failed to get token info: {e}")
            return None
    
    def cleanup_expired_tokens(self) -> int:
        try:
            cursor = self.db_connection.cursor()
            cursor.execute("""
                SELECT token_id FROM token_mappings 
                WHERE expires_at < ? AND status = ?
            """, [datetime.now().isoformat(), TokenStatus.ACTIVE.value])
            expired_tokens = cursor.fetchall()
            for token in expired_tokens:
                self._update_token_status(token[0], TokenStatus.EXPIRED)
            return len(expired_tokens)
        except Exception as e:
            print(f"Failed to cleanup expired tokens: {e}")
            return 0
    
    def get_statistics(self) -> Dict[str, Any]:
        try:
            cursor = self.db_connection.cursor()
            cursor.execute("""
                SELECT token_type, COUNT(*) as count 
                FROM token_mappings 
                GROUP BY token_type
            """)
            type_counts = dict(cursor.fetchall())
            cursor.execute("""
                SELECT status, COUNT(*) as count 
                FROM token_mappings 
                GROUP BY status
            """)
            status_counts = dict(cursor.fetchall())
            cursor.execute("SELECT COUNT(*) FROM token_access_logs")
            total_accesses = cursor.fetchone()[0]
            yesterday = (datetime.now() - timedelta(days=1)).isoformat()
            cursor.execute("""
                SELECT COUNT(*) FROM token_access_logs 
                WHERE access_time > ?
            """, [yesterday])
            recent_accesses = cursor.fetchone()[0]
            return {
                "total_tokens": sum(type_counts.values()),
                "tokens_by_type": type_counts,
                "tokens_by_status": status_counts,
                "total_accesses": total_accesses,
                "recent_accesses_24h": recent_accesses,
                "expired_tokens": status_counts.get(TokenStatus.EXPIRED.value, 0),
                "active_tokens": status_counts.get(TokenStatus.ACTIVE.value, 0)
            }
        except Exception as e:
            print(f"Failed to get statistics: {e}")
            return {}
    
    def close(self):
        if self.db_connection:
            self.db_connection.close()
