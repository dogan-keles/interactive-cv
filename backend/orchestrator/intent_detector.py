"""
Intent detection for user queries.
"""

import re
from typing import Optional

from .types import Intent, Language


class IntentDetector:
    """Detects user intent from query text using keyword matching."""
    
    PROFILE_KEYWORDS = {
        "skill", "skills", "experience", "background", "education",
        "know", "expertise", "proficient", "competent",
        "beceri", "deneyim", "eğitim", "bilgi", "uzmanlık",
        "what does", "what can", "tell me about",
        "ne biliyor", "hangi", "nedir", "nasıl",
    }
    
    GITHUB_KEYWORDS = {
        "github", "repository", "repo", "project", "projects",
        "code", "coding", "programming", "implementation",
        "proje", "kod", "repository", "github",
        "show me", "tell me about projects",
        "projeleri göster", "projeler hakkında",
    }
    
    CV_KEYWORDS = {
        "cv", "resume", "download", "pdf", "document",
        "get cv", "send cv", "cv link", "cv file",
        "özgeçmiş", "cv indir", "cv gönder", "cv dosyası",
    }
    
    GENERAL_KEYWORDS = {
        "vision", "goal", "career", "interest", "passion",
        "why", "what motivates", "what drives",
        "vizyon", "hedef", "kariyer", "ilgi", "tutku",
        "neden", "ne motivasyon", "ne ilham",
    }
    
    OUT_OF_SCOPE_KEYWORDS = {
        "weather", "news", "sports", "politics",
        "hava", "haber", "spor", "siyaset",
    }
    
    def detect(self, text: str, language: Language) -> Intent:
        """Detect intent from user query."""
        if not text or not text.strip():
            return Intent.OUT_OF_SCOPE
        
        text_lower = text.lower()
        
        if any(keyword in text_lower for keyword in self.OUT_OF_SCOPE_KEYWORDS):
            return Intent.OUT_OF_SCOPE
        
        cv_score = sum(1 for keyword in self.CV_KEYWORDS if keyword in text_lower)
        github_score = sum(1 for keyword in self.GITHUB_KEYWORDS if keyword in text_lower)
        profile_score = sum(1 for keyword in self.PROFILE_KEYWORDS if keyword in text_lower)
        general_score = sum(1 for keyword in self.GENERAL_KEYWORDS if keyword in text_lower)
        
        if cv_score > 0:
            return Intent.CV_REQUEST
        
        if github_score > 0:
            return Intent.GITHUB_INFO
        
        if profile_score > 0:
            return Intent.PROFILE_INFO
        
        if general_score > 0:
            return Intent.GENERAL_QUESTION
        
        return Intent.PROFILE_INFO


_intent_detector = IntentDetector()


def detect_intent(text: str, language: Language) -> Intent:
    """Convenience function for intent detection."""
    return _intent_detector.detect(text, language)