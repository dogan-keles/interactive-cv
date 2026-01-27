"""
Chat API routes.
"""
import time
import uuid
import os
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.infrastructure.database import SessionLocal
from backend.data_access.knowledge_base.conversations import Conversation
from backend.api.schemas.chat import ChatRequest, ChatResponse
from backend.orchestrator.orchestrator import Orchestrator

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


@router.post("/chat")
async def chat(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Handle chat request with optional conversation logging.
    
    Args:
        request: Chat request with query and profile_id
        db: Database session
        
    Returns:
        ChatResponse with response text and language
    """
    start_time = time.time()
    session_id = getattr(request, 'session_id', None) or str(uuid.uuid4())
    
    try:
        # Get orchestrator and process request
        orchestrator = get_orchestrator()
        response_text = await orchestrator.process_request(
            request.query,
            request.profile_id
        )
        
        # Calculate response time
        response_time_ms = int((time.time() - start_time) * 1000)
        
        # Detect language (simple detection based on response)
        # You can improve this with a proper language detection library
        detected_language = 'tr' if any(c in response_text for c in 'ğüşıöçĞÜŞİÖÇ') else 'en'
        
        # Save conversation if enabled
        enable_logging = os.getenv("ENABLE_CONVERSATION_LOGGING", "true").lower() == "true"
        
        if enable_logging:
            try:
                conversation = Conversation(
                    profile_id=request.profile_id,
                    session_id=session_id,
                    user_query=request.query,
                    agent_response=response_text,
                    agent_type='unknown',  # Orchestrator doesn't return intent
                    language=detected_language,
                    response_time_ms=response_time_ms,
                )
                db.add(conversation)
                db.commit()
                logger.info(f"✅ Conversation logged: ID={conversation.id}")
            except Exception as log_error:
                logger.error(f"❌ Failed to log conversation: {log_error}")
                db.rollback()
        
        return ChatResponse(
            response=response_text,
            language=detected_language,
        )
        
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))