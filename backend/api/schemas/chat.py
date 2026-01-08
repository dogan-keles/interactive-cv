"""
API schemas for chat endpoints.
"""

from pydantic import BaseModel


class ChatRequest(BaseModel):
    """Request schema for chat endpoint."""
    query: str
    profile_id: int


class ChatResponse(BaseModel):
    """Response schema for chat endpoint."""
    response: str
    language: str






