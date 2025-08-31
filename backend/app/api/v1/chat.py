"""
Chat Completions API Endpoints with Risk Mitigation

OpenAI-compatible chat completions API with integrated risk detection and mitigation.
"""

import time
import uuid
import json
from typing import List, Dict, Any, Optional, AsyncGenerator
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.core.auth import get_current_active_user, get_api_key_context, require_api_key_permission
from app.core.config import settings
import httpx
from app.services.alert_system import process_risk_alert, process_usage_alert
from app.core.database import db
from app.models.models import ChatCompletionRequest, ChatCompletionResponse, ChatMessage, ChatChoice, ChatUsage
from app.services.risk_detection import RiskAgent
from app.services.risk_detection.risk_agent import RiskAgentConfig, ProcessingMode

# NEW: Import Secure Data Connector
from app.services.secure_data_connector import SecureDataConnector, DataSourceConfig, DataSourceType


# Global risk agent
risk_agent = RiskAgent()

# NEW: Global secure data connector
data_connector = SecureDataConnector(risk_agent=risk_agent)


# Extended models for risk-aware chat completions
class RiskAwareChatRequest(ChatCompletionRequest):
    """Chat completion request with risk mitigation options"""
    enable_risk_detection: bool = Field(default=True, description="Enable risk detection and mitigation")
    processing_mode: ProcessingMode = Field(default=ProcessingMode.BALANCED, description="Risk processing mode")
    max_risk_score: float = Field(default=6.0, ge=0.0, le=10.0, description="Maximum acceptable risk score")
    sanitize_input: bool = Field(default=True, description="Sanitize input before processing")
    sanitize_output: bool = Field(default=True, description="Sanitize output before returning")
    
    # NEW: Data access options
    enable_data_access: bool = Field(default=False, description="Enable secure access to external data sources")
    data_source_name: Optional[str] = Field(default=None, description="Name of data source to use")
    data_query: Optional[str] = Field(default=None, description="Query to execute on data source")
    data_params: Optional[Dict[str, Any]] = Field(default=None, description="Parameters for data query")


class RiskMetadata(BaseModel):
    """Risk assessment metadata for chat responses"""
    input_risk_score: float
    output_risk_score: float
    input_sanitized: bool
    output_sanitized: bool
    processing_time_ms: float
    risk_factors: List[str]
    mitigation_applied: List[str]


class RiskAwareChatResponse(ChatCompletionResponse):
    """Chat completion response with risk metadata"""
    risk_metadata: Optional[RiskMetadata] = None


# Create router
router = APIRouter(prefix="/v1", tags=["Chat Completions"])


@router.post("/chat/completions", response_model=RiskAwareChatResponse)
async def create_chat_completion(
    request: RiskAwareChatRequest,
    background_tasks: BackgroundTasks,
    api_key_context: tuple = Depends(require_api_key_permission("chat.completions"))
):
    """
    Create a chat completion with integrated risk detection and mitigation
    
    This endpoint is OpenAI-compatible but includes additional risk mitigation features.
    """
    user, api_key = api_key_context
    request_id = str(uuid.uuid4())
    
    print(f"🚀 create_chat_completion called with request_id: {request_id}")
    
    try:
        # Step 1: Extract and combine input text
        input_text = "\n".join([msg.content for msg in request.messages])
        
        # Step 2: Risk Detection and Input Sanitization
        input_risk_score = 0.0
        sanitized_input = input_text
        risk_factors = []
        mitigation_applied = []
        
        if request.enable_risk_detection:
            # Configure risk agent
            config = RiskAgentConfig(processing_mode=request.processing_mode)
            agent = RiskAgent(config)
            
            # Analyze input
            input_analysis = agent.analyze_text(input_text)
            input_risk_score = input_analysis.risk_assessment.overall_risk_score
            risk_factors = input_analysis.risk_assessment.risk_factors
            
            # Check if input should be blocked
            if input_analysis.should_block or input_risk_score > request.max_risk_score:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "Content blocked due to high risk score",
                        "risk_score": input_risk_score,
                        "max_allowed": request.max_risk_score,
                        "risk_factors": risk_factors
                    }
                )
            
            # Sanitize input if requested
            if request.sanitize_input and input_analysis.sanitization_result:
                sanitized_input = input_analysis.sanitized_text
                mitigation_applied.append("input_sanitization")
        
        # Step 3: Prepare sanitized messages for LLM (convert to dicts)
        sanitized_messages: List[Dict[str, str]] = [
            {"role": m.role, "content": m.content} for m in request.messages
        ]
        if sanitized_input != input_text:
            # Replace content in messages with sanitized versions
            sanitized_lines = sanitized_input.split("\n")
            for i in range(min(len(sanitized_messages), len(sanitized_lines))):
                sanitized_messages[i]["content"] = sanitized_lines[i]
        
        # NEW: Step 3.5: Data Access (if enabled)
        data_context = ""
        if request.enable_data_access and request.data_source_name and request.data_query:
            try:
                # Execute secure query
                data_result = await data_connector.execute_secure_query(
                    data_source_name=request.data_source_name,
                    query=request.data_query,
                    params=request.data_params,
                    enable_sanitization=True,
                    enable_risk_assessment=True
                )
                
                if data_result.is_safe and data_result.data:
                    # Add data context to the prompt
                    data_context = f"\n\n[EXTERNAL_DATA]\n{json.dumps(data_result.data, indent=2)}\n[/EXTERNAL_DATA]\n\n"
                    
                    # Add data context to the first user message
                    if sanitized_messages and sanitized_messages[0]["role"] == "user":
                        sanitized_messages[0]["content"] += data_context
                    
                    mitigation_applied.append("data_access_enabled")
                else:
                    mitigation_applied.append("data_access_blocked")
                    
            except Exception as e:
                mitigation_applied.append("data_access_failed")
        
        # Step 4: Generate LLM Response via provider (Groq default)
        provider = settings.DEFAULT_LLM_PROVIDER.lower() if settings.DEFAULT_LLM_PROVIDER else "groq"
        if provider == "groq":
            llm_response, provider_usage = await call_groq_chat_completions(sanitized_messages, request)
        else:
            # Fallback to mock until other providers are implemented
            llm_response = await generate_mock_llm_response(sanitized_messages, request)
            provider_usage = {
                "prompt_tokens": len(input_text.split()),
                "completion_tokens": len(llm_response.split()),
                "total_tokens": len(input_text.split()) + len(llm_response.split())
            }
        
        # Step 5: Risk Detection and Output Sanitization
        output_risk_score = 0.0
        final_response = llm_response
        
        if request.enable_risk_detection:
            # Analyze output
            output_analysis = agent.analyze_text(llm_response)
            output_risk_score = output_analysis.risk_assessment.overall_risk_score
            
            # Check if output should be blocked
            if output_analysis.should_block or output_risk_score > request.max_risk_score:
                final_response = "[RESPONSE_BLOCKED_DUE_TO_HIGH_RISK]"
                mitigation_applied.append("output_blocking")
            elif request.sanitize_output and output_analysis.sanitization_result:
                final_response = output_analysis.sanitized_text
                mitigation_applied.append("output_sanitization")
        
        # Step 6: Create response
        response = RiskAwareChatResponse(
            id=request_id,
            created=int(time.time()),
            model=request.model,
            choices=[
                ChatChoice(
                    index=0,
                    message=ChatMessage(role="assistant", content=final_response),
                    finish_reason="stop"
                )
            ],
            usage=ChatUsage(
                prompt_tokens=provider_usage.get("prompt_tokens", len(input_text.split())),
                completion_tokens=provider_usage.get("completion_tokens", len(final_response.split())),
                total_tokens=provider_usage.get("total_tokens", len(input_text.split()) + len(final_response.split()))
            )
        )
        
        # Add risk metadata if risk detection was enabled
        if request.enable_risk_detection:
            response.risk_metadata = RiskMetadata(
                input_risk_score=input_risk_score,
                output_risk_score=output_risk_score,
                input_sanitized=sanitized_input != input_text,
                output_sanitized=final_response != llm_response,
                processing_time_ms=100.0,  # Mock timing
                risk_factors=risk_factors,
                mitigation_applied=mitigation_applied
            )
        
        # Step 7: Log the interaction (synchronous for now to ensure it works)
        print(f"🔍 About to call log_chat_completion with request_id: {request_id}")
        try:
            await log_chat_completion(
                user_id=user["id"],
                api_key_id=api_key["id"],
                request_id=request_id,
                original_input=input_text,
                sanitized_input=sanitized_input,
                llm_response=llm_response,
                sanitized_response=final_response,
                input_risk_score=input_risk_score,
                output_risk_score=output_risk_score,
                model_used=request.model,
                tokens_used=response.usage.total_tokens,
                llm_provider=provider
            )
        except Exception as e:
            print(f"⚠️ Warning: Failed to log chat completion: {e}")
            # Don't fail the request if logging fails
        
        # Step 8: Process alerts if high risk detected
        max_risk_score = max(input_risk_score, output_risk_score)
        if max_risk_score >= 6.0:  # Configurable threshold
            risk_log_data = {
                "request_id": request_id,
                "user_id": user["id"],
                "api_key_id": api_key["id"],
                "risk_score": max_risk_score,
                "risks_detected": risk_factors,
                "mitigation_applied": {
                    "input_sanitization": sanitized_input != input_text,
                    "output_sanitization": final_response != llm_response,
                    "content_filtering": final_response == "[RESPONSE_BLOCKED_DUE_TO_HIGH_RISK]"
                },
                "llm_provider": provider
            }
            background_tasks.add_task(process_risk_alert, user["id"], max_risk_score, risk_log_data)
        
        # Check usage alerts
        background_tasks.add_task(
            process_usage_alert,
            user["id"],
            api_key["id"],
            api_key.get("usage_count", 0) + 1,
            api_key.get("usage_limit")
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Chat completion failed: {str(e)}"
        )


@router.post("/completions")
async def create_completion(
    # Legacy completion endpoint - redirect to chat completions
    api_key_context: tuple = Depends(require_api_key_permission("chat.completions"))
):
    """
    Legacy completions endpoint
    """
    raise HTTPException(
        status_code=410,
        detail="Legacy completions endpoint is deprecated. Use /v1/chat/completions instead."
    )


async def generate_mock_llm_response(messages: List[Dict[str, str]], request: RiskAwareChatRequest) -> str:
    """
    Mock LLM response generator
    
    TODO: Replace with actual LLM provider integration (Groq, OpenAI, Anthropic)
    """
    
    # Extract the last user message
    user_messages = [msg for msg in messages if msg.get("role") == "user"]
    if not user_messages:
        return "I don't see any user messages to respond to."
    
    last_message = user_messages[-1]["content"]
    
    # Generate contextual mock response
    if "hello" in last_message.lower():
        return "Hello! I'm an AI assistant with built-in risk detection and mitigation. How can I help you today?"
    elif "risk" in last_message.lower():
        return "I use advanced risk detection to identify and mitigate potentially harmful content, including PII, bias, and inappropriate material."
    elif "what" in last_message.lower() and "you" in last_message.lower():
        return "I'm an AI assistant designed with safety and security in mind. I can help with various tasks while ensuring content is appropriate and safe."
    elif len(last_message) > 100:
        return f"I understand you have a detailed request. I've analyzed your message for potential risks and can provide a helpful response while maintaining safety standards."
    else:
        return f"I've received your message about '{last_message[:50]}...' and I'm happy to help! I've also checked it for any potential risks to ensure our conversation remains safe and appropriate."


async def call_groq_chat_completions(
    messages: List[Dict[str, str]],
    request: RiskAwareChatRequest
) -> tuple[str, Dict[str, int]]:
    """Call Groq's OpenAI-compatible chat.completions API and return text and usage.

    Returns: (text, usage_dict)
    """
    if not settings.GROQ_API_KEY:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY is not configured")

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload: Dict[str, Any] = {
        "model": request.model,
        "messages": messages,
        "temperature": request.temperature if request.temperature is not None else 1.0,
        "top_p": request.top_p if request.top_p is not None else 1.0,
        "stream": False
    }
    if request.max_tokens is not None:
        payload["max_tokens"] = request.max_tokens
    if request.stop:
        payload["stop"] = request.stop

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(url, headers=headers, json=payload)
        if resp.status_code >= 400:
            try:
                err = resp.json()
            except Exception:
                err = {"message": resp.text}
            raise HTTPException(status_code=502, detail={"provider": "groq", "error": err})

        data = resp.json()

    # Parse response (OpenAI-compatible shape)
    choices = data.get("choices", [])
    if not choices:
        raise HTTPException(status_code=502, detail="Groq returned no choices")

    message = choices[0].get("message", {})
    content = message.get("content", "")
    usage = data.get("usage", {})
    usage_parsed = {
        "prompt_tokens": int(usage.get("prompt_tokens", 0) or 0),
        "completion_tokens": int(usage.get("completion_tokens", 0) or 0),
        "total_tokens": int(usage.get("total_tokens", 0) or 0)
    }

    return content, usage_parsed


async def log_chat_completion(user_id: str, api_key_id: str, request_id: str,
                            original_input: str, sanitized_input: str,
                            llm_response: str, sanitized_response: str,
                            input_risk_score: float, output_risk_score: float,
                            model_used: str, tokens_used: int, llm_provider: str = "mock_provider"):
    """Log chat completion to database"""
    print(f"🚀 log_chat_completion called with request_id: {request_id}")
    try:
        # Combine input and output risk scores
        overall_risk_score = max(input_risk_score, output_risk_score)
        
        # Create risks detected summary
        risks_detected = []
        if input_risk_score > 4.0:
            risks_detected.append({
                "type": "input_risk",
                "score": input_risk_score,
                "description": "High risk detected in user input"
            })
        if output_risk_score > 4.0:
            risks_detected.append({
                "type": "output_risk", 
                "score": output_risk_score,
                "description": "High risk detected in LLM output"
            })
        
        # Create mitigation summary
        mitigation_applied = {}
        if sanitized_input != original_input:
            mitigation_applied["input_sanitization"] = True
        if sanitized_response != llm_response:
            mitigation_applied["output_sanitization"] = True
        
        log_data = {
            "user_id": user_id,
            "api_key_id": api_key_id,
            "request_id": request_id,
            "original_input": original_input,
            "sanitized_input": sanitized_input,
            "llm_response": llm_response,
            "sanitized_response": sanitized_response,
            "risk_score": overall_risk_score,
            "risks_detected": risks_detected,
            "mitigation_applied": mitigation_applied,
            "processing_time_ms": 100,  # Mock timing
            "llm_provider": llm_provider,
            "llm_model": model_used,
            "tokens_used": tokens_used
        }
        
        print(f"📝 Attempting to log risk data: {json.dumps(log_data, indent=2)}")
        
        result = await db.create_risk_log(log_data)
        print(f"✅ Risk log created successfully: {result}")
        
    except Exception as e:
        print(f"❌ Failed to log chat completion: {e}")
        import traceback
        traceback.print_exc()


# Additional utility endpoints
@router.get("/models")
async def list_models():
    """List available models (OpenAI-compatible)"""
    return {
        "object": "list",
        "data": [
            {
                "id": "gpt-3.5-turbo",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "risk-agent-api"
            },
            {
                "id": "gpt-4",
                "object": "model", 
                "created": int(time.time()),
                "owned_by": "risk-agent-api"
            }
        ]
    }


@router.get("/chat/risk-settings")
async def get_chat_risk_settings(
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Get risk detection settings for chat completions"""
    
    # Get user settings
    user_settings = await db.get_user_settings(current_user["id"])
    
    if not user_settings:
        # Return default settings
        return {
            "enable_risk_detection": True,
            "processing_mode": "balanced",
            "max_risk_score": 6.0,
            "sanitize_input": True,
            "sanitize_output": True,
            "risk_threshold": 5.0
        }
    
    return {
        "enable_risk_detection": user_settings.get("enable_logging", True),
        "processing_mode": "balanced",  # Could be stored in user settings
        "max_risk_score": user_settings.get("risk_threshold", 5.0),
        "sanitize_input": True,
        "sanitize_output": True,
        "risk_threshold": user_settings.get("risk_threshold", 5.0)
    }


@router.put("/chat/risk-settings")
async def update_chat_risk_settings(
    enable_risk_detection: bool = True,
    max_risk_score: float = 6.0,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Update risk detection settings for chat completions"""
    
    try:
        # Update user settings
        update_data = {
            "enable_logging": enable_risk_detection,
            "risk_threshold": max_risk_score
        }
        
        await db.update_user_settings(current_user["id"], update_data)
        
        return {
            "message": "Risk settings updated successfully",
            "enable_risk_detection": enable_risk_detection,
            "max_risk_score": max_risk_score
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update settings: {str(e)}"
        )
