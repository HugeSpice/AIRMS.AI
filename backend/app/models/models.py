"""
Pydantic models for the Risk Agent API
"""

from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field, validator, ConfigDict
from enum import Enum


class StrictnessLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class DatabaseType(str, Enum):
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    MONGODB = "mongodb"
    REST_API = "rest_api"


class TestStatus(str, Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"


# User Models
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(UserBase):
    id: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None


# API Key Models
class APIKeyCreate(BaseModel):
    key_name: str = Field(..., min_length=1, max_length=255)
    permissions: Optional[List[str]] = Field(default_factory=list)
    usage_limit: Optional[int] = Field(None, ge=0)
    expires_at: Optional[datetime] = None


class APIKeyResponse(BaseModel):
    id: str
    user_id: str
    key_name: str
    key_prefix: str
    permissions: List[str]
    usage_limit: Optional[int]
    usage_count: int
    is_active: bool
    expires_at: Optional[datetime]
    last_used_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class APIKeyCreateResponse(BaseModel):
    key_data: APIKeyResponse
    api_key: str  # The actual key - only shown once
    

class APIKeyUpdate(BaseModel):
    key_name: Optional[str] = None
    permissions: Optional[List[str]] = None
    usage_limit: Optional[int] = None
    is_active: Optional[bool] = None
    expires_at: Optional[datetime] = None


# Authentication Models
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class TokenPayload(BaseModel):
    sub: Optional[str] = None
    exp: Optional[int] = None


# Risk Log Models
class RiskDetection(BaseModel):
    type: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    original_text: str
    masked_text: str
    position: Dict[str, int]  # start, end positions


class MitigationApplied(BaseModel):
    sanitization: bool = False
    content_filtering: bool = False
    rate_limiting: bool = False
    custom_rules: List[str] = Field(default_factory=list)


class RiskLogCreate(BaseModel):
    request_id: str
    original_input: str
    sanitized_input: str
    llm_response: Optional[str] = None
    sanitized_response: Optional[str] = None
    risk_score: float = Field(..., ge=0.0, le=10.0)
    risks_detected: List[RiskDetection] = Field(default_factory=list)
    mitigation_applied: MitigationApplied = Field(default_factory=MitigationApplied)
    processing_time_ms: int = 0
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    tokens_used: int = 0


class RiskLogResponse(BaseModel):
    id: str
    user_id: str
    api_key_id: Optional[str]
    request_id: str
    risk_score: float
    risks_detected: List[RiskDetection]
    mitigation_applied: MitigationApplied
    processing_time_ms: int
    llm_provider: Optional[str]
    llm_model: Optional[str]
    tokens_used: int
    created_at: datetime

    class Config:
        from_attributes = True


# User Settings Models
class UserSettingsCreate(BaseModel):
    risk_threshold: float = Field(5.0, ge=0.0, le=10.0)
    strictness_level: StrictnessLevel = StrictnessLevel.MEDIUM
    blocked_risks: List[str] = Field(default_factory=list)
    allowed_domains: List[str] = Field(default_factory=list)
    rate_limit_per_hour: int = Field(1000, ge=1)
    enable_logging: bool = True
    enable_analytics: bool = True


class UserSettingsResponse(UserSettingsCreate):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserSettingsUpdate(BaseModel):
    risk_threshold: Optional[float] = Field(None, ge=0.0, le=10.0)
    strictness_level: Optional[StrictnessLevel] = None
    blocked_risks: Optional[List[str]] = None
    allowed_domains: Optional[List[str]] = None
    rate_limit_per_hour: Optional[int] = Field(None, ge=1)
    enable_logging: Optional[bool] = None
    enable_analytics: Optional[bool] = None


# Database Connection Models
class DatabaseConnectionCreate(BaseModel):
    connection_name: str = Field(..., min_length=1, max_length=255)
    db_type: DatabaseType
    connection_config: Dict[str, Any]
    encrypted_credentials: str


class DatabaseConnectionResponse(BaseModel):
    id: str
    user_id: str
    connection_name: str
    db_type: DatabaseType
    connection_config: Dict[str, Any]
    is_active: bool
    last_tested_at: Optional[datetime]
    test_status: TestStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DatabaseConnectionUpdate(BaseModel):
    connection_name: Optional[str] = None
    connection_config: Optional[Dict[str, Any]] = None
    encrypted_credentials: Optional[str] = None
    is_active: Optional[bool] = None


# Chat Completion Models (OpenAI Compatible)
class ChatMessage(BaseModel):
    role: str = Field(..., pattern="^(system|user|assistant)$")
    content: str


class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    temperature: Optional[float] = Field(1.0, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, ge=1)
    top_p: Optional[float] = Field(1.0, ge=0.0, le=1.0)
    frequency_penalty: Optional[float] = Field(0.0, ge=-2.0, le=2.0)
    presence_penalty: Optional[float] = Field(0.0, ge=-2.0, le=2.0)
    stop: Optional[List[str]] = None
    stream: Optional[bool] = False
    user: Optional[str] = None


class ChatChoice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: str


class ChatUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatChoice]
    usage: ChatUsage
    risk_metadata: Optional[Dict[str, Any]] = None


# Error Models
class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None




# Health Check Model
class HealthCheck(BaseModel):
    status: str = "healthy"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    version: str = "1.0.0"
    database_status: str = "connected"
