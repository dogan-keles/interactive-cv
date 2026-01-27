"""
Database model for conversations.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from backend.data_access.knowledge_base.postgres import Base


class Conversation(Base):
    """Model for storing chat conversations."""
    
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    session_id = Column(String(255), index=True)
    user_query = Column(Text, nullable=False)
    agent_response = Column(Text, nullable=False)
    agent_type = Column(String(50))
    language = Column(String(10))
    response_time_ms = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())