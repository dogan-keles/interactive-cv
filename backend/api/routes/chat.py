"""
Chat API routes with rate limiting.
"""
import time
import uuid
import os
import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from backend.infrastructure.database import SessionLocal
from backend.data_access.knowledge_base.conversations import Conversation
from backend.api.schemas.chat import ChatRequest, ChatResponse
from backend.orchestrator.orchestrator import Orchestrator
from backend.middleware.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)

router = APIRouter(tags=["chat"])


def get_db():
    """Database dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Global orchestrator dependency
_orchestrator_dependency = None


def set_orchestrator_dependency(func):
    """Set the orchestrator dependency function from main.py"""
    global _orchestrator_dependency
    _orchestrator_dependency = func


def get_orchestrator() -> Orchestrator:
    """Get orchestrator instance"""
    if _orchestrator_dependency is None:
        raise RuntimeError("Orchestrator dependency not initialized")
    return _orchestrator_dependency()


def get_user_identifier(request: Request, session_id: str) -> str:
    """
    Get unique user identifier for rate limiting.
    
    Uses session_id if provided, otherwise IP address.
    Owner gets special "OWNER" identifier (unlimited access).
    """
    # Check if this is the owner (could be determined by auth token, IP whitelist, etc.)
    # For now, using environment variable
    owner_ip = os.getenv("OWNER_IP")
    client_ip = request.client.host if request.client else "unknown"
    
    if owner_ip and client_ip == owner_ip:
        return "OWNER"
    
    return session_id or client_ip


@router.post("/chat")
async def chat(
    request_obj: ChatRequest, 
    http_request: Request,
    db: Session = Depends(get_db)
):
    """
    Handle chat request with rate limiting and conversation logging.
    
    Rate limits:
    - Owner: Unlimited
    - Others: 25 queries per day
    """
    start_time = time.time()
    session_id = getattr(request_obj, 'session_id', None) or str(uuid.uuid4())
    
    try:
        # Get user identifier
        user_id = get_user_identifier(http_request, session_id)
        
        # Check rate limit
        rate_limiter = RateLimiter(db)
        rate_limiter.check_rate_limit(request_obj.profile_id, user_id)
        
        # Get orchestrator and process request
        orchestrator = get_orchestrator()
        response_text = await orchestrator.process_request(
            request_obj.query,
            request_obj.profile_id
        )
        
        # Calculate response time
        response_time_ms = int((time.time() - start_time) * 1000)
        
        # Detect language
        detected_language = 'tr' if any(c in response_text for c in 'ğüşıöçĞÜŞİÖÇ') else 'en'
        
        # Save conversation
        enable_logging = os.getenv("ENABLE_CONVERSATION_LOGGING", "true").lower() == "true"
        
        if enable_logging:
            try:
                conversation = Conversation(
                    profile_id=request_obj.profile_id,
                    session_id=session_id,
                    user_query=request_obj.query,
                    agent_response=response_text,
                    agent_type='unknown',
                    language=detected_language,
                    response_time_ms=response_time_ms,
                )
                db.add(conversation)
                db.commit()
                logger.info(f"✅ Conversation logged: ID={conversation.id}")
            except Exception as log_error:
                logger.error(f"Failed to log conversation: {log_error}")
                db.rollback()
        
        # Get remaining queries (for info)
        remaining = rate_limiter.get_remaining_queries(request_obj.profile_id, user_id)
        if remaining >= 0:
            logger.info(f"User {user_id} has {remaining} queries remaining today")
        
        return ChatResponse(
            response=response_text,
            language=detected_language,
        )
        
    except HTTPException:
        # Re-raise rate limit errors
        raise
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/rate-limit-status")
async def get_rate_limit_status(
    profile_id: int,
    http_request: Request,
    db: Session = Depends(get_db)
):
    """Get current rate limit status for user."""
    session_id = http_request.headers.get("X-Session-ID", "unknown")
    user_id = get_user_identifier(http_request, session_id)
    
    rate_limiter = RateLimiter(db)
    remaining = rate_limiter.get_remaining_queries(profile_id, user_id)
    
    return {
        "profile_id": profile_id,
        "daily_limit": 25 if remaining >= 0 else "unlimited",
        "remaining": remaining if remaining >= 0 else "unlimited",
        "is_owner": user_id == "OWNER"
    }