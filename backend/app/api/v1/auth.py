"""
Authentication API endpoints using existing Supabase backend
"""

from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer

from app.core.database import db
from app.core.auth import auth_manager, get_current_active_user, get_api_key_context
from app.models.models import (
    UserCreate, UserLogin, UserResponse, UserUpdate,
    APIKeyCreate, APIKeyResponse, APIKeyCreateResponse, APIKeyUpdate,
    Token, ErrorResponse
)

router = APIRouter(prefix="/api/auth", tags=["authentication"])
security = HTTPBearer()


@router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin):
    """User login endpoint"""
    try:
        # Get user from Supabase
        user = await db.get_user_by_email(user_credentials.email)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verify password
        if not auth_manager.verify_password(user_credentials.password, user.get("hashed_password", "")):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create access token
        access_token = auth_manager.create_access_token(
            data={"sub": user["id"], "email": user["email"]}
        )
        
        # Get user's API keys
        api_keys = await db.get_user_api_keys(user["id"])
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=24 * 60 * 60,  # 24 hours in seconds
            user=UserResponse(
                id=user["id"],
                email=user["email"],
                full_name=user.get("full_name"),
                is_active=user.get("is_active", True),
                is_verified=user.get("is_verified", False),
                created_at=user.get("created_at", datetime.now(timezone.utc)),
                updated_at=user.get("updated_at", datetime.now(timezone.utc))
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )


@router.post("/register", response_model=UserResponse)
async def register_user(user_data: UserCreate):
    """Register a new user"""
    try:
        # Check if user already exists
        existing_user = await db.get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Hash password
        hashed_password = auth_manager.hash_password(user_data.password)
        
        # Create new user in Supabase
        user = await db.create_user(
            email=user_data.email,
            hashed_password=hashed_password,
            full_name=user_data.full_name
        )
        
        return UserResponse(
            id=user["id"],
            email=user["email"],
            full_name=user["full_name"],
            is_active=user.get("is_active", True),
            is_verified=user.get("is_verified", False),
            created_at=user.get("created_at", datetime.now(timezone.utc)),
            updated_at=user.get("updated_at", datetime.now(timezone.utc))
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user(current_user = Depends(get_current_active_user)):
    """Get current user information"""
    try:
        return UserResponse(
            id=current_user["id"],
            email=current_user["email"],
            full_name=current_user.get("full_name"),
            is_active=current_user.get("is_active", True),
            is_verified=current_user.get("is_verified", False),
            created_at=current_user.get("created_at", datetime.now(timezone.utc)),
            updated_at=current_user.get("updated_at", datetime.now(timezone.utc))
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user info: {str(e)}"
        )


@router.post("/api-keys", response_model=APIKeyCreateResponse)
async def create_api_key(
    api_key_data: APIKeyCreate,
    current_user = Depends(get_current_active_user)
):
    """Create a new API key for the current user"""
    try:
        # Generate API key using existing auth manager
        api_key, key_hash, key_prefix = auth_manager.generate_api_key()
        
        # Prepare API key data for Supabase
        api_key_data_supabase = {
            "user_id": current_user["id"],
            "key_name": api_key_data.key_name,
            "key_hash": key_hash,
            "key_prefix": key_prefix,
            "permissions": api_key_data.permissions or [],
            "usage_limit": api_key_data.usage_limit or 1000,
            "is_active": True,
            "usage_count": 0,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        if api_key_data.expires_at:
            api_key_data_supabase["expires_at"] = api_key_data.expires_at.isoformat()
        
        # Create API key in Supabase
        created_key = await db.create_api_key(api_key_data_supabase)
        
        # Convert to APIKeyResponse format
        key_response = APIKeyResponse(
            id=created_key["id"],
            user_id=created_key["user_id"],
            key_name=created_key["key_name"],
            key_prefix=created_key["key_prefix"],
            permissions=created_key.get("permissions", []),
            usage_limit=created_key.get("usage_limit"),
            usage_count=created_key.get("usage_count", 0),
            is_active=created_key["is_active"],
            expires_at=created_key.get("expires_at"),
            last_used_at=created_key.get("last_used_at"),
            created_at=datetime.fromisoformat(created_key["created_at"].replace('Z', '+00:00')),
            updated_at=datetime.fromisoformat(created_key["updated_at"].replace('Z', '+00:00'))
        )
        
        return APIKeyCreateResponse(
            key_data=key_response,
            api_key=api_key  # Only show once during creation
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create API key: {str(e)}"
        )


@router.get("/api-keys", response_model=List[APIKeyResponse])
async def get_user_api_keys(current_user = Depends(get_current_active_user)):
    """Get all API keys for the current user"""
    try:
        api_keys = await db.get_user_api_keys(current_user["id"])
        
        # Convert to APIKeyResponse format
        response_keys = []
        for key in api_keys:
            response_keys.append(APIKeyResponse(
                id=key["id"],
                user_id=key["user_id"],
                key_name=key["key_name"],
                key_prefix=key["key_prefix"],
                permissions=key.get("permissions", []),
                usage_limit=key.get("usage_limit"),
                usage_count=key.get("usage_count", 0),
                is_active=key["is_active"],
                expires_at=key.get("expires_at"),
                last_used_at=key.get("last_used_at"),
                created_at=datetime.fromisoformat(key["created_at"].replace('Z', '+00:00')),
                updated_at=datetime.fromisoformat(key["updated_at"].replace('Z', '+00:00'))
            ))
        
        return response_keys
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get API keys: {str(e)}"
        )


@router.delete("/api-keys/{key_id}")
async def revoke_api_key(
    key_id: str,
    current_user = Depends(get_current_active_user)
):
    """Revoke an API key"""
    try:
        # Get API key to check ownership
        api_keys = await db.get_user_api_keys(current_user["id"])
        target_key = None
        
        for key in api_keys:
            if key["id"] == key_id:
                target_key = key
                break
        
        if not target_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found"
            )
        
        # Revoke the key by setting is_active to False
        await db.update_api_key(key_id, {"is_active": False})
        
        return {"message": "API key revoked successfully"}
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revoke API key: {str(e)}"
        )


@router.post("/logout")
async def logout(current_user = Depends(get_current_active_user)):
    """User logout endpoint"""
    # In a real implementation, you might want to blacklist the token
    # For now, we'll just return a success message
    return {"message": "Logged out successfully"}


@router.get("/verify-token")
async def verify_token(current_user = Depends(get_current_active_user)):
    """Verify if the current token is valid"""
    return {"valid": True, "user_id": current_user["id"]}
