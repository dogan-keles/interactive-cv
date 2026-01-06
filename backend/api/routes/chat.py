"""
Chat API routes.
"""

from fastapi import APIRouter, Depends, HTTPException

from api.schemas.chat import ChatRequest, ChatResponse
from orchestrator.orchestrator import Orchestrator

router = APIRouter(
    prefix="/api/chat",
    tags=["chat"],
)


# Global variable to store the dependency function
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


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    orchestrator: Orchestrator = Depends(get_orchestrator),
):
    """
    Chat endpoint for interactive CV queries.

    Args:
        request: Chat request with query and profile_id
        orchestrator: Orchestrator instance (injected by FastAPI)

    Returns:
        Chat response
    """
    try:
        response = await orchestrator.process_request(
            user_query=request.query,
            profile_id=request.profile_id,
        )

        return ChatResponse(
            response=response,
            language="en",
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Chat processing failed: {str(e)}",
        )