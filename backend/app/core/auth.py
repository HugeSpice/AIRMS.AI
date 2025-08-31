"""
Authentication utilities and middleware
"""

import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings
from app.core.database import db
from app.models.models import TokenPayload
import logging

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer for API keys and JWT tokens
security = HTTPBearer()


class AuthManager:
    """Authentication and authorization manager"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(hours=settings.JWT_EXPIRATION_HOURS)
        
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(
            to_encode,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> Optional[TokenPayload]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            
            token_data = TokenPayload(**payload)
            return token_data
            
        except JWTError as e:
            logger.error(f"JWT verification failed: {e}")
            return None
    
    @staticmethod
    def generate_api_key() -> tuple[str, str, str]:
        """Generate a new API key
        
        Returns:
            tuple: (api_key, key_hash, key_prefix)
        """
        # Generate random key
        random_part = secrets.token_urlsafe(settings.API_KEY_LENGTH)
        api_key = f"{settings.API_KEY_PREFIX}{random_part}"
        
        # Create hash for storage
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        # Extract prefix for indexing
        key_prefix = api_key[:len(settings.API_KEY_PREFIX) + 8]
        
        return api_key, key_hash, key_prefix
    
    @staticmethod
    def hash_api_key(api_key: str) -> str:
        """Hash an API key for storage"""
        return hashlib.sha256(api_key.encode()).hexdigest()


# Dependency functions for FastAPI
async def get_current_user_from_token(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> Dict[str, Any]:
    """Get current user from JWT token"""
    
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token_data = AuthManager.verify_token(credentials.credentials)
        if token_data is None or token_data.sub is None:
            raise credentials_exception
        
        user = await db.get_user_by_id(token_data.sub)
        if user is None:
            raise credentials_exception
        
        if not user.get("is_active", False):
            raise HTTPException(status_code=400, detail="Inactive user")
        
        return user
        
    except Exception as e:
        logger.error(f"Token validation error: {e}")
        raise credentials_exception


async def get_current_user_from_api_key(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> tuple[Dict[str, Any], Dict[str, Any]]:
    """Get current user from API key
    
    Returns:
        tuple: (user_data, api_key_data)
    """
    
    credentials_exception = HTTPException(
        status_code=401,
        detail="Invalid API key",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        api_key = credentials.credentials
        
        # Validate API key format
        if not api_key.startswith(settings.API_KEY_PREFIX):
            raise credentials_exception
        
        # Hash the key to find it in database
        key_hash = AuthManager.hash_api_key(api_key)
        
        # Find API key in database
        api_key_data = await db.get_api_key_by_hash(key_hash)
        if not api_key_data:
            raise credentials_exception
        
        # Check if API key is active
        if not api_key_data.get("is_active", False):
            raise HTTPException(status_code=401, detail="API key is inactive")
        
        # Check expiration
        expires_at = api_key_data.get("expires_at")
        if expires_at and datetime.fromisoformat(expires_at.replace('Z', '+00:00')) < datetime.now(timezone.utc):
            raise HTTPException(status_code=401, detail="API key has expired")
        
        # Get user associated with API key
        user = await db.get_user_by_id(api_key_data["user_id"])
        if not user or not user.get("is_active", False):
            raise HTTPException(status_code=401, detail="User account is inactive")
        
        # Increment usage count (async, don't wait)
        try:
            await db.increment_api_key_usage(api_key_data["id"])
        except Exception as e:
            if "usage limit exceeded" in str(e).lower():
                raise HTTPException(status_code=429, detail="API key usage limit exceeded")
            logger.warning(f"Failed to increment API key usage: {e}")
        
        return user, api_key_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API key validation error: {e}")
        raise credentials_exception


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> Dict[str, Any]:
    """Get current user from either JWT token or API key"""
    
    try:
        # Try JWT token first
        return await get_current_user_from_token(credentials)
    except HTTPException:
        pass
    
    try:
        # Try API key
        user, _ = await get_current_user_from_api_key(credentials)
        return user
    except HTTPException:
        pass
    
    # If both fail, raise authentication error
    raise HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_active_user(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get current active user"""
    if not current_user.get("is_active", False):
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


# API Key specific dependency
async def get_api_key_context(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> tuple[Dict[str, Any], Dict[str, Any]]:
    """Get user and API key context (for API key protected routes only)"""
    return await get_current_user_from_api_key(credentials)


# Permission checking utilities
def check_api_key_permission(api_key_data: Dict[str, Any], required_permission: str) -> bool:
    """Check if API key has required permission"""
    permissions = api_key_data.get("permissions", [])
    return required_permission in permissions or "admin" in permissions


def require_api_key_permission(required_permission: str):
    """Decorator to require specific API key permission"""
    def permission_dependency(
        api_key_context: tuple[Dict[str, Any], Dict[str, Any]] = Depends(get_api_key_context)
    ):
        user, api_key_data = api_key_context
        
        if not check_api_key_permission(api_key_data, required_permission):
            raise HTTPException(
                status_code=403,
                detail=f"API key does not have required permission: {required_permission}"
            )
        
        return user, api_key_data
    
    return permission_dependency


# Initialize auth manager
auth_manager = AuthManager()
