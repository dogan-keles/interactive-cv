"""
Database models for CV download tracking.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from backend.data_access.knowledge_base.postgres import Base


class CVDownloadRequest(Base):
    """Model for tracking CV download requests."""
    
    __tablename__ = "cv_download_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    user_name = Column(String(255), nullable=False)
    user_email = Column(String(255), nullable=False)
    user_company = Column(String(255), nullable=True)
    download_token = Column(String(255), unique=True, nullable=False, index=True)
    downloaded = Column(Boolean, default=False)
    downloaded_at = Column(DateTime(timezone=True), nullable=True)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())