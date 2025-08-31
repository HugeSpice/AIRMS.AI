"""
Configuration settings for the Risk Agent API
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # API Configuration
    PROJECT_NAME: str = Field(default="Risk Agent API", env="PROJECT_NAME")
    API_V1_STR: str = Field(default="/api/v1", env="API_V1_STR")
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    DEBUG: bool = Field(default=False, env="DEBUG")
    
    # Supabase Configuration
    SUPABASE_URL: str = Field(..., env="SUPABASE_URL")
    SUPABASE_KEY: str = Field(..., env="SUPABASE_KEY")
    SUPABASE_SERVICE_ROLE_KEY: str = Field(..., env="SUPABASE_SERVICE_ROLE_KEY")
    
    # JWT Configuration
    JWT_SECRET_KEY: str = Field(..., env="JWT_SECRET_KEY")
    JWT_ALGORITHM: str = Field(default="HS256", env="JWT_ALGORITHM")
    JWT_EXPIRATION_HOURS: int = Field(default=24, env="JWT_EXPIRATION_HOURS")
    
    # API Key Configuration
    API_KEY_PREFIX: str = Field(default="rsk_", env="API_KEY_PREFIX")
    API_KEY_LENGTH: int = Field(default=32, env="API_KEY_LENGTH")
    
    # Rate Limiting
    DEFAULT_RATE_LIMIT: int = Field(default=1000, env="DEFAULT_RATE_LIMIT")
    RATE_LIMIT_WINDOW_HOURS: int = Field(default=1, env="RATE_LIMIT_WINDOW_HOURS")
    
    # Risk Detection
    DEFAULT_RISK_THRESHOLD: float = Field(default=5.0, env="DEFAULT_RISK_THRESHOLD")
    MAX_INPUT_LENGTH: int = Field(default=50000, env="MAX_INPUT_LENGTH")
    
    # LLM Configuration
    DEFAULT_LLM_PROVIDER: str = Field(default="groq", env="DEFAULT_LLM_PROVIDER")
    GROQ_API_KEY: Optional[str] = Field(default=None, env="GROQ_API_KEY")
    OPENAI_API_KEY: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    
    # CORS Configuration
    ALLOWED_ORIGINS: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        env="ALLOWED_ORIGINS"
    )
    
    # Enhanced Component Configuration
    ENABLE_PRESIDIO: bool = Field(default=True, env="ENABLE_PRESIDIO")
    ENABLE_SPACY: bool = Field(default=True, env="ENABLE_SPACY")
    ENABLE_FAIRLEARN: bool = Field(default=True, env="ENABLE_FAIRLEARN")
    ENABLE_AIF360: bool = Field(default=True, env="ENABLE_AIF360")
    ENABLE_TEXTATTACK: bool = Field(default=True, env="ENABLE_TEXTATTACK")
    ENABLE_ART: bool = Field(default=True, env="ENABLE_ART")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create global settings instance
settings = Settings()
