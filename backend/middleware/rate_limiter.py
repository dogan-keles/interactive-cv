"""
Rate Limiter Middleware - Limits queries per user per day.

Owner (profile creator) has unlimited access.
Other users limited to 25 queries per day.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from fastapi import HTTPException

from backend.data_access.knowledge_base.postgres import Profile

logger = logging.getLogger(__name__)


# Model for tracking conversations (already exists)
# We'll use the Conversation table from postgres.py


class RateLimiter:
    """
    Rate limiting for chat queries.
    
    Rules:
    - Profile owner (creator): Unlimited
    - Other users: 25 queries per day
    """
    
    DEFAULT_DAILY_LIMIT = 25
    OWNER_PROFILE_ID = 1  # Doğan's profile
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def check_rate_limit(
        self, 
        profile_id: int, 
        user_identifier: Optional[str] = None
    ) -> bool:
        """
        Check if user has exceeded rate limit.
        
        Args:
            profile_id: Profile being queried
            user_identifier: IP address or session ID
            
        Returns:
            True if allowed, False if limit exceeded
            
        Raises:
            HTTPException: If rate limit exceeded
        """
        # Owner has unlimited access
        if profile_id == self.OWNER_PROFILE_ID and user_identifier == "OWNER":
            logger.debug(f"Owner access for profile {profile_id} - unlimited")
            return True
        
        # Get today's query count for this user
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Import here to avoid circular dependency
        from backend.data_access.knowledge_base.conversations import Conversation
        
        query_count = self.db.query(func.count(Conversation.id)).filter(
            and_(
                Conversation.profile_id == profile_id,
                Conversation.session_id == user_identifier,
                Conversation.created_at >= today_start
            )
        ).scalar()
        
        logger.info(f"Rate limit check: user={user_identifier}, count={query_count}/{self.DEFAULT_DAILY_LIMIT}")
        
        if query_count >= self.DEFAULT_DAILY_LIMIT:
            logger.warning(f"Rate limit exceeded: {user_identifier} has {query_count} queries today")
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Rate limit exceeded",
                    "message": f"You have reached the daily limit of {self.DEFAULT_DAILY_LIMIT} queries. Please try again tomorrow.",
                    "limit": self.DEFAULT_DAILY_LIMIT,
                    "used": query_count,
                    "reset_time": (today_start + timedelta(days=1)).isoformat()
                }
            )
        
        return True
    
    def get_remaining_queries(
        self, 
        profile_id: int, 
        user_identifier: str
    ) -> int:
        """Get number of remaining queries for today."""
        if profile_id == self.OWNER_PROFILE_ID and user_identifier == "OWNER":
            return -1  # Unlimited
        
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        from backend.data_access.knowledge_base.conversations import Conversation
        
        query_count = self.db.query(func.count(Conversation.id)).filter(
            and_(
                Conversation.profile_id == profile_id,
                Conversation.session_id == user_identifier,
                Conversation.created_at >= today_start
            )
        ).scalar()
        
        return max(0, self.DEFAULT_DAILY_LIMIT - query_count)