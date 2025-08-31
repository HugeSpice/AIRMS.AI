"""
Risk Detection API Endpoints

This module provides FastAPI endpoints for the risk detection and mitigation system.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field

from app.core.auth import get_current_active_user, get_api_key_context, require_api_key_permission
from app.core.database import db
from app.services.risk_detection import RiskAgent
from app.services.risk_detection.risk_agent import RiskAgentConfig, ProcessingMode
from app.services.risk_detection.config import ConfigPresets


# API Models
class RiskAnalysisRequest(BaseModel):
    """Request model for risk analysis"""
    text: str = Field(..., min_length=1, max_length=50000, description="Text to analyze")
    processing_mode: Optional[ProcessingMode] = Field(default=ProcessingMode.BALANCED, description="Processing mode")
    include_sanitized: bool = Field(default=True, description="Include sanitized text in response")
    include_detections: bool = Field(default=True, description="Include detailed detections")


class RiskAnalysisResponse(BaseModel):
    """Response model for risk analysis"""
    request_id: str
    overall_risk_score: float = Field(..., ge=0.0, le=10.0)
    risk_level: str
    is_safe: bool
    should_block: bool
    
    # Optional detailed information
    sanitized_text: Optional[str] = None
    pii_entities_count: Optional[int] = None
    bias_detections_count: Optional[int] = None
    risk_factors: Optional[List[str]] = None
    mitigation_suggestions: Optional[List[str]] = None
    
    # Metadata
    processing_time_ms: float
    text_length: int
    confidence: float


class SanitizationRequest(BaseModel):
    """Request model for text sanitization"""
    text: str = Field(..., min_length=1, max_length=50000)
    confidence_threshold: Optional[float] = Field(default=0.7, ge=0.0, le=1.0)


class SanitizationResponse(BaseModel):
    """Response model for text sanitization"""
    original_length: int
    sanitized_text: str
    entities_found: int
    entities_masked: int
    risk_reduced: float


class ChatCompletionRequestRisk(BaseModel):
    """Extended chat completion request with risk mitigation"""
    model: str
    messages: List[Dict[str, str]]
    temperature: Optional[float] = Field(default=1.0, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, ge=1)
    enable_risk_detection: bool = Field(default=True, description="Enable risk detection")
    processing_mode: Optional[ProcessingMode] = Field(default=ProcessingMode.BALANCED)
    max_risk_score: Optional[float] = Field(default=6.0, ge=0.0, le=10.0, description="Maximum acceptable risk score")
    

# Global risk agent instance
risk_agent = RiskAgent()

# Create router
router = APIRouter(prefix="/api/v1/risk", tags=["Risk Detection"])


@router.post("/analyze", response_model=RiskAnalysisResponse)
async def analyze_text_risk(
    request: RiskAnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Analyze text for risk factors including PII, bias, and harmful content
    """
    import uuid
    import time
    
    request_id = str(uuid.uuid4())
    
    try:
        # Configure risk agent for this request
        config = RiskAgentConfig(processing_mode=request.processing_mode)
        agent = RiskAgent(config)
        
        # Perform risk analysis
        result = agent.analyze_text(request.text)
        
        # Prepare response
        response = RiskAnalysisResponse(
            request_id=request_id,
            overall_risk_score=result.risk_assessment.overall_risk_score,
            risk_level=result.risk_assessment.risk_level.value,
            is_safe=result.is_safe,
            should_block=result.should_block,
            processing_time_ms=result.risk_assessment.processing_time_ms,
            text_length=len(request.text),
            confidence=result.risk_assessment.confidence
        )
        
        # Include optional details if requested
        if request.include_sanitized:
            response.sanitized_text = result.sanitized_text
        
        if request.include_detections:
            response.pii_entities_count = len(result.risk_assessment.pii_entities)
            response.bias_detections_count = len(result.risk_assessment.bias_detections)
            response.risk_factors = result.risk_assessment.risk_factors
            response.mitigation_suggestions = result.risk_assessment.mitigation_suggestions
        
        # Log the analysis in background
        background_tasks.add_task(
            log_risk_analysis,
            user_id=current_user["id"],
            request_id=request_id,
            original_input=request.text,
            sanitized_input=result.sanitized_text,
            risk_score=result.risk_assessment.overall_risk_score,
            risks_detected=result.risk_assessment.pii_entities + result.risk_assessment.bias_detections,
            mitigation_applied=result.sanitization_result.to_dict() if result.sanitization_result else {},
            processing_time_ms=result.risk_assessment.processing_time_ms
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Risk analysis failed: {str(e)}"
        )


@router.post("/sanitize", response_model=SanitizationResponse)
async def sanitize_text(
    request: SanitizationRequest,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Sanitize text by masking PII and sensitive information
    """
    try:
        # Configure risk agent for sanitization
        config = RiskAgentConfig(
            sanitization_confidence_threshold=request.confidence_threshold
        )
        agent = RiskAgent(config)
        
        # Perform sanitization
        sanitized_text, metadata = agent.sanitize_text(request.text)
        
        return SanitizationResponse(
            original_length=len(request.text),
            sanitized_text=sanitized_text,
            entities_found=metadata["entities_found"],
            entities_masked=metadata["entities_sanitized"],
            risk_reduced=metadata["risk_score"]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Text sanitization failed: {str(e)}"
        )


@router.get("/check")
async def quick_safety_check(
    text: str,
    max_risk_score: float = 6.0,
    api_key_context: tuple = Depends(require_api_key_permission("risk.analyze"))
):
    """
    Quick safety check for content (API key only)
    """
    user, api_key = api_key_context
    
    try:
        is_safe = risk_agent.is_safe_content(text, max_risk_score)
        
        return {
            "is_safe": is_safe,
            "text_length": len(text),
            "max_risk_score": max_risk_score,
            "api_key_id": api_key["id"]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Safety check failed: {str(e)}"
        )


@router.get("/config")
async def get_risk_configuration(
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Get current risk detection configuration
    """
    return {
        "processing_modes": [mode.value for mode in ProcessingMode],
        "current_config": risk_agent.config.to_dict(),
        "available_presets": [
            "high_security",
            "balanced_general", 
            "low_restriction",
            "compliance_focused"
        ],
        "statistics": risk_agent.get_statistics()
    }


@router.put("/config")
async def update_risk_configuration(
    processing_mode: ProcessingMode,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Update risk detection configuration (admin only)
    """
    # Note: In production, add admin role check here
    
    try:
        new_config = RiskAgentConfig(processing_mode=processing_mode)
        risk_agent.update_config(new_config)
        
        return {
            "message": "Configuration updated successfully",
            "new_config": risk_agent.config.to_dict()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Configuration update failed: {str(e)}"
        )


@router.get("/presets/{preset_name}")
async def apply_configuration_preset(
    preset_name: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Apply a configuration preset
    """
    preset_map = {
        "high_security": ConfigPresets.high_security,
        "balanced_general": ConfigPresets.balanced_general,
        "low_restriction": ConfigPresets.low_restriction,
        "compliance_focused": ConfigPresets.compliance_focused
    }
    
    if preset_name not in preset_map:
        raise HTTPException(
            status_code=404,
            detail=f"Preset '{preset_name}' not found"
        )
    
    try:
        preset_config = preset_map[preset_name]()
        
        # Convert to RiskAgentConfig
        agent_config = RiskAgentConfig(
            processing_mode=preset_config.processing_mode,
            pii_confidence_threshold=preset_config.pii_config.confidence_threshold,
            bias_confidence_threshold=preset_config.bias_config.confidence_threshold,
            sanitization_confidence_threshold=preset_config.sanitization_config.confidence_threshold
        )
        
        risk_agent.update_config(agent_config)
        
        return {
            "message": f"Applied preset: {preset_name}",
            "preset_config": preset_config.to_dict()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to apply preset: {str(e)}"
        )


@router.get("/statistics")
async def get_risk_statistics(
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Get processing statistics and performance metrics
    """
    stats = risk_agent.get_statistics()
    health = risk_agent.health_check()
    
    return {
        "processing_statistics": stats,
        "health_status": health,
        "agent_info": {
            "version": "1.0.0",
            "components_enabled": health["components"],
            "configuration": risk_agent.config.to_dict()
        }
    }


@router.get("/health")
async def risk_engine_health():
    """
    Health check for risk detection engine (public endpoint)
    """
    health = risk_agent.health_check()
    
    return {
        "status": health["overall_status"],
        "components": health["components"],
        "last_test": health["last_test"]
    }


# Background task functions
async def log_risk_analysis(user_id: str, request_id: str, original_input: str,
                          sanitized_input: str, risk_score: float,
                          risks_detected: List, mitigation_applied: Dict,
                          processing_time_ms: float):
    """Log risk analysis to database"""
    try:
        log_data = {
            "user_id": user_id,
            "request_id": request_id,
            "original_input": original_input,
            "sanitized_input": sanitized_input,
            "risk_score": risk_score,
            "risks_detected": risks_detected,
            "mitigation_applied": mitigation_applied,
            "processing_time_ms": processing_time_ms,
            "llm_provider": "risk_analysis",
            "llm_model": "risk_detection_v1",
            "tokens_used": len(original_input.split())
        }
        
        await db.create_risk_log(log_data)
        
    except Exception as e:
        # Log error but don't fail the main request
        print(f"Failed to log risk analysis: {e}")
