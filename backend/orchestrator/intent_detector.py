"""
Intent detection for user queries.

Classifies user input into one of the defined intent categories.
Uses keyword-based heuristics with optional LLM fallback for ambiguous cases.
"""

import re
from typing import Optional

from .types import Intent, Language


class IntentDetector:
    """
    Detects user intent from query text.
    
    Uses rule-based keyword matching first, with extensibility
    for LLM-based classification for ambiguous cases.
    """
    
    # Profile-related keywords
    PROFILE_KEYWORDS = {
        "skill", "skills", "experience", "background", "education",
        "know", "expertise", "proficient", "competent",
        "beceri", "deneyim", "eğitim", "bilgi", "uzmanlık",
        "what does", "what can", "tell me about",
        "ne biliyor", "hangi", "nedir", "nasıl",
    }
    
    # GitHub/project-related keywords
    GITHUB_KEYWORDS = {
        "github", "repository", "repo", "project", "projects",
        "code", "coding", "programming", "implementation",
        "proje", "kod", "repository", "github",
        "show me", "tell me about projects",
        "projeleri göster", "projeler hakkında",
    }
    
    # CV/document-related keywords
    CV_KEYWORDS = {
        "cv", "resume", "download", "pdf", "document",
        "get cv", "send cv", "cv link", "cv file",
        "özgeçmiş", "cv indir", "cv gönder", "cv dosyası",
    }
    
    # General question keywords
    GENERAL_KEYWORDS = {
        "vision", "goal", "career", "interest", "passion",
        "why", "what motivates", "what drives",
        "vizyon", "hedef", "kariyer", "ilgi", "tutku",
        "neden", "ne motivasyon", "ne ilham",
    }
    
    # Out-of-scope indicators
    OUT_OF_SCOPE_KEYWORDS = {
        "weather", "news", "sports", "politics",
        "hava", "haber", "spor", "siyaset",
    }
    
    def detect(
        self,
        text: str,
        language: Language,
    ) -> Intent:
        """
        Detect intent from user query.
        
        Args:
            text: User query text
            language: Detected language (for language-specific patterns)
            
        Returns:
            Detected intent (Intent enum)
        """
        if not text or not text.strip():
            return Intent.OUT_OF_SCOPE
        
        text_lower = text.lower()
        
        # Check for out-of-scope first
        if any(keyword in text_lower for keyword in self.OUT_OF_SCOPE_KEYWORDS):
            return Intent.OUT_OF_SCOPE
        
        # Count keyword matches for each intent
        cv_score = sum(1 for keyword in self.CV_KEYWORDS if keyword in text_lower)
        github_score = sum(1 for keyword in self.GITHUB_KEYWORDS if keyword in text_lower)
        profile_score = sum(1 for keyword in self.PROFILE_KEYWORDS if keyword in text_lower)
        general_score = sum(1 for keyword in self.GENERAL_KEYWORDS if keyword in text_lower)
        
        # CV requests are usually explicit
        if cv_score > 0:
            return Intent.CV_REQUEST
        
        # GitHub/project requests
        if github_score > 0:
            return Intent.GITHUB_INFO
        
        # Profile/skills/experience requests
        if profile_score > 0:
            return Intent.PROFILE_INFO
        
        # General questions
        if general_score > 0:
            return Intent.GENERAL_QUESTION
        
        # Default: treat as profile info if no clear match
        # (most questions about the candidate are profile-related)
        return Intent.PROFILE_INFO
    
    def detect_with_llm_fallback(
        self,
        text: str,
        language: Language,
        llm_provider: Optional[object] = None,
    ) -> Intent:
        """
        Detect intent with optional LLM fallback for ambiguous cases.
        
        This method can be extended to use LLM when keyword matching
        is insufficient. For now, it falls back to rule-based detection.
        
        Args:
            text: User query text
            language: Detected language
            llm_provider: Optional LLM provider for classification
            
        Returns:
            Detected intent
        """
        # For now, use rule-based detection
        # Future: Add LLM-based classification for ambiguous queries
        intent = self.detect(text, language)
        
        # If LLM provider is available and intent is ambiguous, use LLM
        # This is a placeholder for future enhancement
        if llm_provider and intent == Intent.PROFILE_INFO:
            # Could use LLM to disambiguate between PROFILE_INFO and GENERAL_QUESTION
            pass
        
        return intent


# Singleton instance
_intent_detector = IntentDetector()


def detect_intent(
    text: str,
    language: Language,
) -> Intent:
    """
    Convenience function for intent detection.
    
    Args:
        text: User query text
        language: Detected language
        
    Returns:
        Detected intent
    """
    return _intent_detector.detect(text, language)


