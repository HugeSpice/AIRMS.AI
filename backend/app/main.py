"""
Risk Agent API - Main FastAPI application
OpenAI-compatible API service with Risk Detection & Mitigation Agent
"""

import logging
from datetime import timedelta, datetime, timezone
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from contextlib import asynccontextmanager

# Import local modules
from app.core.config import settings
from app.core.database import db
from app.core.auth import auth_manager, get_current_active_user, get_api_key_context
from app.models.models import (
    UserCreate, UserLogin, UserResponse, UserUpdate,
    APIKeyCreate, APIKeyResponse, APIKeyCreateResponse, APIKeyUpdate,
    UserSettingsCreate, UserSettingsResponse, UserSettingsUpdate,
    Token, ErrorResponse, HealthCheck
)
from app.api.v1.auth import router as auth_router
from app.api.v1.risk import router as risk_router
from app.api.v1.chat import router as chat_router

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Security
security = HTTPBearer()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting Risk Agent API...")
    
    # Test database connection
    db_healthy = await db.health_check()
    if not db_healthy:
        logger.error("Database connection failed!")
        raise Exception("Cannot connect to Supabase")
    
    logger.info("Database connection established")
    yield
    
    # Shutdown
    logger.info("Shutting down Risk Agent API...")


# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="OpenAI-compatible API service with Risk Detection & Mitigation Agent",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(risk_router)
app.include_router(chat_router)


# Health check endpoint
@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint"""
    db_status = "connected" if await db.health_check() else "disconnected"
    
    return HealthCheck(
        status="healthy" if db_status == "connected" else "unhealthy",
        database_status=db_status
    )


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Risk Agent API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


# Authentication Endpoints
@app.post(f"{settings.API_V1_STR}/auth/register", response_model=UserResponse)
async def register(user_data: UserCreate):
    """Register a new user"""
    
    # Check if user already exists
    existing_user = await db.get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    # Hash password
    hashed_password = auth_manager.hash_password(user_data.password)
    
    # Create user
    try:
        user = await db.create_user(
            email=user_data.email,
            hashed_password=hashed_password,
            full_name=user_data.full_name
        )
        
        # Create default user settings
        default_settings = {
            "user_id": user["id"],
            "risk_threshold": settings.DEFAULT_RISK_THRESHOLD,
            "strictness_level": "medium",
            "blocked_risks": [],
            "allowed_domains": [],
            "rate_limit_per_hour": settings.DEFAULT_RATE_LIMIT,
            "enable_logging": True,
            "enable_analytics": True
        }
        await db.create_user_settings(default_settings)
        
        return UserResponse(**user)
        
    except Exception as e:
        logger.error(f"User registration failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to create user"
        )


@app.post(f"{settings.API_V1_STR}/auth/login", response_model=Token)
async def login(login_data: UserLogin):
    """Login user and return JWT token"""
    
    # Find user
    user = await db.get_user_by_email(login_data.email)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password"
        )
    
    # Verify password
    if not auth_manager.verify_password(login_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password"
        )
    
    # Check if user is active
    if not user.get("is_active", False):
        raise HTTPException(
            status_code=400,
            detail="Inactive user account"
        )
    
    # Create access token
    access_token_expires = timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    access_token = auth_manager.create_access_token(
        data={"sub": user["id"]},
        expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=int(access_token_expires.total_seconds()),
        user=UserResponse(**user)
    )


@app.get(f"{settings.API_V1_STR}/auth/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Get current user information"""
    return UserResponse(**current_user)


@app.put(f"{settings.API_V1_STR}/auth/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Update current user information"""
    
    update_data = user_update.model_dump(exclude_unset=True)
    
    # If email is being updated, check if it's already taken
    if "email" in update_data:
        existing_user = await db.get_user_by_email(update_data["email"])
        if existing_user and existing_user["id"] != current_user["id"]:
            raise HTTPException(
                status_code=400,
                detail="Email already in use"
            )
    
    try:
        updated_user = await db.update_user(current_user["id"], update_data)
        return UserResponse(**updated_user)
    except Exception as e:
        logger.error(f"User update failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to update user"
        )


# API Key Management Endpoints
@app.post(f"{settings.API_V1_STR}/api-keys", response_model=APIKeyCreateResponse)
async def create_api_key(
    key_data: APIKeyCreate,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Create a new API key"""
    
    # Generate API key
    api_key, key_hash, key_prefix = auth_manager.generate_api_key()
    
    # Prepare API key data
    api_key_data = {
        "user_id": current_user["id"],
        "key_name": key_data.key_name,
        "key_hash": key_hash,
        "key_prefix": key_prefix,
        "permissions": key_data.permissions or [],
        "usage_limit": key_data.usage_limit,
        "expires_at": key_data.expires_at.isoformat() if key_data.expires_at else None,
        "is_active": True,
        "usage_count": 0
    }
    
    try:
        created_key = await db.create_api_key(api_key_data)
        
        return APIKeyCreateResponse(
            key_data=APIKeyResponse(**created_key),
            api_key=api_key  # Only shown once
        )
        
    except Exception as e:
        logger.error(f"API key creation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to create API key"
        )


@app.get(f"{settings.API_V1_STR}/api-keys", response_model=List[APIKeyResponse])
async def list_api_keys(
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """List all API keys for the current user"""
    
    try:
        api_keys = await db.get_user_api_keys(current_user["id"])
        return [APIKeyResponse(**key) for key in api_keys]
    except Exception as e:
        logger.error(f"Failed to list API keys: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve API keys"
        )


@app.put(f"{settings.API_V1_STR}/api-keys/{{key_id}}", response_model=APIKeyResponse)
async def update_api_key(
    key_id: str,
    key_update: APIKeyUpdate,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Update an API key"""
    
    # Get current API key to verify ownership
    api_keys = await db.get_user_api_keys(current_user["id"])
    api_key = next((key for key in api_keys if key["id"] == key_id), None)
    
    if not api_key:
        raise HTTPException(
            status_code=404,
            detail="API key not found"
        )
    
    update_data = key_update.model_dump(exclude_unset=True)
    
    # Convert datetime to string if present
    if "expires_at" in update_data and update_data["expires_at"]:
        update_data["expires_at"] = update_data["expires_at"].isoformat()
    
    try:
        updated_key = await db.update_api_key(key_id, update_data)
        return APIKeyResponse(**updated_key)
    except Exception as e:
        logger.error(f"API key update failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to update API key"
        )


@app.delete(f"{settings.API_V1_STR}/api-keys/{{key_id}}")
async def delete_api_key(
    key_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Delete (deactivate) an API key"""
    
    try:
        success = await db.delete_api_key(key_id, current_user["id"])
        if not success:
            raise HTTPException(
                status_code=404,
                detail="API key not found"
            )
        
        return {"message": "API key deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API key deletion failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to delete API key"
        )


# User Settings Endpoints
@app.get(f"{settings.API_V1_STR}/settings", response_model=UserSettingsResponse)
async def get_user_settings(
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Get user settings"""
    
    settings_data = await db.get_user_settings(current_user["id"])
    if not settings_data:
        # Create default settings if they don't exist
        default_settings = {
            "user_id": current_user["id"],
            "risk_threshold": settings.DEFAULT_RISK_THRESHOLD,
            "strictness_level": "medium",
            "blocked_risks": [],
            "allowed_domains": [],
            "rate_limit_per_hour": settings.DEFAULT_RATE_LIMIT,
            "enable_logging": True,
            "enable_analytics": True
        }
        settings_data = await db.create_user_settings(default_settings)
    
    return UserSettingsResponse(**settings_data)


@app.put(f"{settings.API_V1_STR}/settings", response_model=UserSettingsResponse)
async def update_user_settings(
    settings_update: UserSettingsUpdate,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Update user settings"""
    
    update_data = settings_update.model_dump(exclude_unset=True)
    
    try:
        updated_settings = await db.update_user_settings(current_user["id"], update_data)
        return UserSettingsResponse(**updated_settings)
    except Exception as e:
        logger.error(f"Settings update failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to update settings"
        )


# API Key validation endpoint (for testing)
@app.get(f"{settings.API_V1_STR}/validate-key")
async def validate_api_key(
    api_key_context: tuple[Dict[str, Any], Dict[str, Any]] = Depends(get_api_key_context)
):
    """Validate API key (test endpoint)"""
    user, api_key_data = api_key_context
    
    return {
        "valid": True,
        "user_id": user["id"],
        "user_email": user["email"],
        "key_name": api_key_data["key_name"],
        "key_id": api_key_data["id"],
        "permissions": api_key_data["permissions"],
        "usage_count": api_key_data["usage_count"],
        "usage_limit": api_key_data["usage_limit"]
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )

