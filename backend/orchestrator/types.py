"""
Type definitions for orchestrator layer.

Defines Intent enum, Language enum, and RequestContext dataclass.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class Language(str, Enum):
    """
    Supported languages for user input and responses.
    
    Note: Language detection is now handled by the LLM automatically.
    The LLM will detect and respond in ANY language the user uses.
    These enum values are kept for backwards compatibility and internal tracking.
    """
    AUTO = "auto"  # LLM auto-detects and matches user's language
    ENGLISH = "en"
    TURKISH = "tr"
    KURDISH = "ku"
    GERMAN = "de"
    FRENCH = "fr"
    SPANISH = "es"
    ITALIAN = "it"
    PORTUGUESE = "pt"
    RUSSIAN = "ru"
    ARABIC = "ar"
    CHINESE = "zh"
    JAPANESE = "ja"
    KOREAN = "ko"


class Intent(str, Enum):
    """User intent classification."""
    PROFILE_INFO = "profile_info"
    GITHUB_INFO = "github_info"
    CV_REQUEST = "cv_request"
    GENERAL_QUESTION = "general_question"
    OUT_OF_SCOPE = "out_of_scope"


@dataclass
class RequestContext:
    """
    Request-level context passed through the orchestrator to agents.
    
    Contains all metadata needed for request processing:
    - Original user query
    - Detected language (AUTO for LLM-based detection)
    - Detected intent
    - Profile ID
    - Optional RAG context (retrieved via tools)
    """
    user_query: str
    profile_id: int
    language: Language
    intent: Intent
    rag_context: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert context to dictionary for agent consumption."""
        return {
            "user_query": self.user_query,
            "profile_id": self.profile_id,
            "language": self.language.value,
            "intent": self.intent.value,
            "rag_context": self.rag_context,
        }